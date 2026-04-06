import os
import re
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
import ast

class ReActAgent:
    """
    Shoe Consultant ReAct Agent - v1 (5 loop limit) and v2 (7 loop limit readiness).
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5): # v1 defaults to 5
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
        Bạn là ReAct Agent chuyên nghiệp tư vấn mua giày (Shoe Consultant). 
        Bạn BẮT BUỘC phải dùng ReAct format (Thought -> Action -> Observation) để giải quyết vấn đề.
        
        Bạn có các công cụ sau:
        {tool_descriptions}

        CRITICAL RULES (CHỐNG ẢO GIÁC VÀ OUT-OF-DOMAIN):
        1. Tuyệt đối KHÔNG tự bịa ra giá tiền, mức tồn kho của các mã giày trong hệ thống nếu chưa kiểm tra từ Tool.
        2. [OUT OF DATASET]: Nếu Tool trả về thông báo sản phẩm không có trong database (ví dụ: Asics, New Balance), bạn ĐƯỢC PHÉP tự dùng kiến thức OpenAI có sẵn để tư vấn thông tin về đôi giày đó, nhưng phải nói rõ đây là sản phẩm không có sẵn ở cửa hàng.
        3. [OUT OF DOMAIN]: Nếu người dùng hỏi các câu hỏi KHÔNG LIÊN QUAN đến giày (ví dụ: thời tiết, chứng khoán, thể thao chung chung), bạn BẮT BUỘC phải trả lời bằng format Final Answer chính xác câu này: "Tôi không có kiến thức trong lĩnh vực đó, nhưng nếu bạn cần tư vấn về các sản phẩm giày, tôi sẵn lòng hỗ trợ." sau đó DỪNG lại. Không được dùng Tool.

        ReAct Format:
        Thought: suy luận của bạn về bước tiếp theo.
        Action: tool_name(arguments)
        Observation: (hệ thống sẽ tự điền kết quả vào đây, bạn không được tự suy diễn Observation)
        
        ... (lặp lại cho đến khi đủ thông tin)
        
        Thought: Tôi đã đủ thông tin.
        Final Answer: câu trả lời tư vấn hoàn chỉnh bằng tiếng Việt.
        """

    def run(self, user_input: str) -> str:
        logger.configure(agent_mode="agent_v1", model=self.llm.model_name)
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        steps = 0
        system_prompt = self.get_system_prompt()
        self.history.append(f"User Request: {user_input}")

        while steps < self.max_steps:
            current_input = "\n".join(self.history)
            result = self.llm.generate(current_input, system_prompt=system_prompt)
            llm_response = result["content"]
            
            self.history.append(f"{llm_response}")

            # Exit if Final Answer reached
            if "Final Answer:" in llm_response:
                final_answer = llm_response.split("Final Answer:")[1].strip()
                logger.log_event("AGENT_END", {"steps": steps, "status": "success"})
                return final_answer
            
            # Extract Action
            action_match = re.search(r"Action:\s*([a-zA-Z0-9_-]+)\((.*?)\)", llm_response)
            
            if action_match:
                tool_name = action_match.group(1).strip()
                args_str = action_match.group(2).strip()
                
                observation = self._execute_tool(tool_name, args_str)
                self.history.append(f"Observation: {observation}")
            else:
                self.history.append("Observation: Error - Action not mathematically formatted. Use 'Action: tool_name(args)' or 'Final Answer:'.")
            
            steps += 1
            
        logger.log_event("AGENT_ESCALATION", {"steps": steps, "status": "failed_max_steps"})
        return "Xin lỗi, tôi gặp khó khăn khi truy xuất thông tin (vượt quá số vòng lặp cho phép). Đang chuyển hướng bạn tới tư vấn viên con người..."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        for tool in self.tools:
            if tool['name'] == tool_name:
                try:
                    from src.tools.shoe_tools import search_shoes_by_brand, check_shoe_availability, check_price
                    
                    if tool_name == "search_shoes_by_brand":
                        brand = args.strip().strip("'\"")
                        return str(search_shoes_by_brand(brand))
                    elif tool_name == "check_shoe_availability":
                        sku = args.strip().strip("'\"")
                        return str(check_shoe_availability(sku))
                    elif tool_name == "check_price":
                        sku = args.strip().strip("'\"")
                        return str(check_price(sku))
                except Exception as e:
                    return f"Error executing {tool_name}: {e}"
        return f"Tool {tool_name} not found."
