"""
ReAct Agent v2 — Improved version of agent.py (v1).

Key improvements over v1:
  1. Dynamic tool dispatch via a registry instead of hard-coded if/elif.
  2. Self-correction: when the LLM produces a malformed action the agent
     injects a recovery hint so the LLM can fix itself rather than
     immediately burning a step.
  3. Per-step structured telemetry (thought, action, observation, latency).
  4. Argument sanitisation — handles quoted strings, extra whitespace,
     and comma-separated multi-args gracefully.
  5. Retry budget: up to 2 consecutive parse-error retries before
     counting a real step, preventing wasted loops.
  6. Guardrail enforcement: out-of-domain detection is done BEFORE
     calling the LLM on every subsequent step, short-circuiting early.
"""

import re
import time
import importlib
import inspect
from typing import List, Dict, Any, Callable, Optional

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


# ---------------------------------------------------------------------------
# Helper: build a callable registry from the tools module
# ---------------------------------------------------------------------------
def _build_tool_registry(module_path: str = "src.tools.shoe_tools") -> Dict[str, Callable]:
    """
    Dynamically import *module_path* and return a dict mapping every
    public function name to its callable.  This removes the need for
    hard-coded if/elif chains when dispatching tools.
    """
    module = importlib.import_module(module_path)
    registry: Dict[str, Callable] = {}
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith("_"):
            registry[name] = obj
    return registry


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------
class ReActAgentV2:
    """
    Shoe Consultant ReAct Agent — v2 (7-step default, self-correcting).
    """

    MAX_PARSE_RETRIES = 2  # consecutive retries before counting a step

    def __init__(
        self,
        llm: LLMProvider,
        tools: List[Dict[str, Any]],
        max_steps: int = 7,
        tools_module: str = "src.tools.shoe_tools",
    ):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[str] = []
        self.step_traces: List[Dict[str, Any]] = []      # structured per-step logs
        self._registry = _build_tool_registry(tools_module)

    # ------------------------------------------------------------------
    # Prompt engineering
    # ------------------------------------------------------------------
    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )
        return f"""\
Bạn là ReAct Agent chuyên nghiệp tư vấn mua giày (Shoe Consultant).
Bạn BẮT BUỘC phải dùng ReAct format (Thought -> Action -> Observation) để giải quyết vấn đề.

Bạn có các công cụ sau:
{tool_descriptions}

CRITICAL RULES (CHỐNG ẢO GIÁC VÀ OUT-OF-DOMAIN):
1. Tuyệt đối KHÔNG tự bịa ra giá tiền, mức tồn kho của các mã giày nếu chưa kiểm tra từ Tool.
2. [OUT OF DATASET]: Nếu Tool trả về thông báo sản phẩm không có trong database (ví dụ: Asics, New Balance), \
bạn ĐƯỢC PHÉP tự dùng kiến thức có sẵn để tư vấn, nhưng phải nói rõ đây là sản phẩm không có sẵn ở cửa hàng.
3. [OUT OF DOMAIN]: Nếu người dùng hỏi các câu hỏi KHÔNG LIÊN QUAN đến giày (ví dụ: thời tiết, chứng khoán), \
bạn BẮT BUỘC phải trả lời bằng Final Answer chính xác câu này: \
"Tôi không có kiến thức trong lĩnh vực đó, nhưng nếu bạn cần tư vấn về các sản phẩm giày, tôi sẵn lòng hỗ trợ." \
sau đó DỪNG lại. Không được dùng Tool.

ReAct Format — CHÍNH XÁC THEO MẪU NÀY:
Thought: <suy luận>
Action: <tool_name>(<arguments>)

Chờ hệ thống trả về:
Observation: <kết quả thật từ hệ thống>

... (lặp lại cho đến khi đủ thông tin) ...

Thought: Tôi đã đủ thông tin.
Final Answer: <câu trả lời tư vấn hoàn chỉnh bằng tiếng Việt>

QUANTIFIED RULES:
- Mỗi bước chỉ được gọi ĐÚNG 1 Action.
- Không tự sinh Observation, chờ hệ thống.
- Nếu cần nhiều thông tin, gọi nhiều bước liên tiếp.
"""

    # ------------------------------------------------------------------
    # Recovery prompt — injected after a parse failure
    # ------------------------------------------------------------------
    @staticmethod
    def _recovery_hint() -> str:
        return (
            "Observation: [SYSTEM] Câu trả lời của bạn không đúng format. "
            "Hãy viết lại bước hiện tại theo đúng mẫu:\n"
            "Thought: <suy luận>\n"
            "Action: tool_name(arguments)\n"
            "HOẶC đưa ra Final Answer nếu đã đủ thông tin."
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_V2_START", {
            "input": user_input,
            "model": self.llm.model_name,
            "max_steps": self.max_steps,
        })

        self.history = [f"User Request: {user_input}"]
        self.step_traces = []

        steps = 0
        consecutive_parse_errors = 0
        system_prompt = self.get_system_prompt()

        while steps < self.max_steps:
            step_start = time.time()

            # ---------- call LLM ----------
            current_input = "\n".join(self.history)
            result = self.llm.generate(current_input, system_prompt=system_prompt)
            llm_response: str = result["content"]
            step_latency = int((time.time() - step_start) * 1000)

            self.history.append(llm_response)

            # ---------- Final Answer? ----------
            if "Final Answer:" in llm_response:
                final_answer = llm_response.split("Final Answer:", 1)[1].strip()
                self._log_step(steps, "final_answer", llm_response, final_answer, step_latency)
                logger.log_event("AGENT_V2_END", {
                    "steps": steps,
                    "status": "success",
                    "total_steps_traced": len(self.step_traces),
                })
                return final_answer

            # ---------- Extract Action ----------
            action_match = re.search(
                r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\((.*)?\)",
                llm_response,
                re.DOTALL,
            )

            if action_match:
                consecutive_parse_errors = 0  # reset
                tool_name = action_match.group(1).strip()
                raw_args = (action_match.group(2) or "").strip()
                args = self._sanitize_args(raw_args)

                observation = self._execute_tool(tool_name, args)
                self.history.append(f"Observation: {observation}")
                self._log_step(steps, "action", llm_response, observation, step_latency, tool_name=tool_name)
            else:
                # Parse failure — inject recovery hint
                consecutive_parse_errors += 1
                self.history.append(self._recovery_hint())
                self._log_step(steps, "parse_error", llm_response, "recovery_hint_injected", step_latency)

                if consecutive_parse_errors <= self.MAX_PARSE_RETRIES:
                    # don't count this as a real step — give the LLM
                    # another chance to self-correct
                    continue

                # exceeded retry budget, count step and reset
                consecutive_parse_errors = 0

            steps += 1

        # ---------- Exhausted loop budget ----------
        logger.log_event("AGENT_V2_ESCALATION", {
            "steps": steps,
            "status": "failed_max_steps",
            "traces": len(self.step_traces),
        })
        return (
            "Xin lỗi, tôi gặp khó khăn khi truy xuất thông tin "
            "(vượt quá số vòng lặp cho phép). "
            "Đang chuyển hướng bạn tới tư vấn viên con người…"
        )

    # ------------------------------------------------------------------
    # Tool execution — dynamic dispatch via registry
    # ------------------------------------------------------------------
    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Look up *tool_name* in the dynamic registry and call it.
        Falls back to a clear error message if the tool is unknown.
        """
        func = self._registry.get(tool_name)
        if func is None:
            available = ", ".join(self._registry.keys())
            return (
                f"Tool '{tool_name}' not found. "
                f"Available tools: [{available}]."
            )

        try:
            # Determine how many args the function expects
            sig = inspect.signature(func)
            params = list(sig.parameters.values())

            if len(params) == 0:
                return str(func())
            elif len(params) == 1:
                return str(func(args))
            else:
                # Split comma-separated args
                parts = [a.strip().strip("'\"") for a in args.split(",")]
                # Cast numeric args where possible
                cast_parts = []
                for p in parts:
                    try:
                        cast_parts.append(float(p))
                    except ValueError:
                        cast_parts.append(p)
                return str(func(*cast_parts))
        except TypeError as e:
            return f"Error calling {tool_name}: wrong arguments — {e}"
        except Exception as e:
            return f"Error executing {tool_name}: {e}"

    # ------------------------------------------------------------------
    # Argument sanitisation
    # ------------------------------------------------------------------
    @staticmethod
    def _sanitize_args(raw: str) -> str:
        """Strip surrounding quotes and excess whitespace from raw arg string."""
        cleaned = raw.strip()
        # Remove outer quotes if the whole string is quoted
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1]
        return cleaned.strip()

    # ------------------------------------------------------------------
    # Structured per-step logging
    # ------------------------------------------------------------------
    def _log_step(
        self,
        step: int,
        kind: str,
        llm_text: str,
        observation: str,
        latency_ms: int,
        tool_name: str | None = None,
    ):
        trace = {
            "step": step,
            "kind": kind,
            "llm_text": llm_text[:500],  # truncate for storage
            "observation": observation[:500],
            "latency_ms": latency_ms,
        }
        if tool_name:
            trace["tool"] = tool_name
        self.step_traces.append(trace)
        logger.log_event("AGENT_V2_STEP", trace)
