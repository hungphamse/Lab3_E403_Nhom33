import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
import ast

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        TODO: Implement the system prompt that instructs the agent to follow ReAct.
        Should include:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
        You are an intelligent assistant. You have access to the following tools:
        {tool_descriptions}

        Use the following format:
        Thought: your line of reasoning.
        Action: tool_name(arguments)
        Observation: result of the tool call.
        ... (repeat Thought/Action/Observation if needed)
        Final Answer: your final response.
        """

    def run(self, user_input: str) -> str:
        """
        TODO: Implement the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        system_prompt = self.get_system_prompt()

        # initialize history for building the next prompt
        self.history = []
        self.history.append(f"User: {user_input}")

        steps = 0
        final_answer = None

        while steps < self.max_steps:
            # TODO: Generate LLM response
            # result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            # TODO: Parse Thought/Action from result
            # TODO: If Action found -> Call tool -> Append Observation
            # TODO: If Final Answer found -> Break loop
            # Build the prompt by joining history
            prompt = "\n".join(self.history) + "\n"

            # Call the LLM provider to get assistant output
            try:
                result = self.llm.generate(prompt, system_prompt=system_prompt)
                if isinstance(result, dict):
                    text = result.get("content") or result.get("text") or ""
                else:
                    text = str(result)
            except Exception as e:
                logger.log_event("AGENT_ERROR", {"error": str(e)})
                return f"Error during LLM generation: {e}"

            # Record assistant output
            self.history.append(f"Assistant: {text}")

            # Check for a Final Answer
            m_final = re.search(r"Final Answer:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
            if m_final:
                final_answer = m_final.group(1).strip()
                logger.log_event("AGENT_END", {"steps": steps + 1})
                return final_answer

            # Parse an Action: expect format `Action: tool_name(args)`
            m_action = re.search(r"Action:\s*([A-Za-z0-9_]+)\((.*?)\)", text, re.IGNORECASE | re.DOTALL)
            if m_action:
                tool_name = m_action.group(1).strip()
                args = m_action.group(2).strip()
                logger.log_event("AGENT_ACTION", {"tool": tool_name, "args": args})

                # Execute the tool and append the observation
                observation = self._execute_tool(tool_name, args)
                self.history.append(f"Observation: {observation}")

                logger.log_event("AGENT_OBERVATION", {"tool": tool_name, "observation": observation});

                steps += 1
                continue

            # If no action and no final answer, treat the assistant text as the final answer
            logger.log_event("AGENT_END", {"steps": steps + 1, "note": "no action found"})
            return text.strip()

        # Reached max steps without final answer
        logger.log_event("AGENT_END", {"steps": steps})
        return final_answer or "No final answer produced within max steps."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools by name.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                # TODO: Implement dynamic function calling or simple if/else
                # Prefer a callable under common keys (func, callable, run, execute)
                func = tool.get('func') or tool.get('callable') or tool.get('run') or tool.get('execute')
                if callable(func):
                    try:
                        parsed_args = ast.literal_eval(args) if args else ()
                        # Try calling with the raw args string first
                        return str(func(*parsed_args))
                    except TypeError:
                        try:
                            # Try calling without args
                            return str(func())
                        except Exception as e:
                            return f"Error executing {tool_name}: {e}"
                    except Exception as e:
                        return f"Error executing {tool_name}: {e}"

                # Fallback: return a placeholder message if no callable provided
                return f"Result of {tool_name}"
        return f"Tool {tool_name} not found."
