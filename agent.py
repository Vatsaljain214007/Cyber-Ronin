"""
Main agent loop: parse → gate → execute → summarize
"""
from typing import Dict, Any, Optional
from intent_parser import parse_intent
from safety import requires_confirmation, format_confirmation_prompt
from tool_executor import execute_tool
from summarizer import summarize_result, fallback_summarize
from audit_log import get_audit_logger
from llm_client import create_llm_client, LLMClient


class CyberRoninAgent:
    """Main Cyber Ronin agent orchestrating the pipeline."""
    
    def __init__(self, llm_client: LLMClient = None, interactive: bool = True):
        self.llm_client = llm_client or create_llm_client("mock")
        self.interactive = interactive
        self.logger = get_audit_logger()
    
    def run(self, user_input: str) -> str:
        """
        Run the full pipeline for a user request.
        
        Args:
            user_input: Natural language request from user
        
        Returns:
            Human-readable response
        """
        # Step 1: Parse Intent
        intent_result = parse_intent(user_input, self.llm_client)
        tool_name = intent_result["tool_name"]
        arguments = intent_result["arguments"]
        
        if not tool_name:
            return "I couldn't understand your request. Try something like 'scan this host for open ports' or 'check system health'."
        
        # Step 2: Safety/Permission Gate
        if requires_confirmation(tool_name, arguments):
            if self.interactive:
                prompt = format_confirmation_prompt(tool_name, arguments)
                try:
                    response = input(prompt).strip().lower()
                    confirmed = response in ('y', 'yes')
                except (EOFError, KeyboardInterrupt):
                    confirmed = False
                
                if not confirmed:
                    self.logger.log_step(
                        step="safety_gate",
                        action="user_denied",
                        input_data={"tool_name": tool_name, "arguments": arguments},
                        output_data={"confirmed": False},
                        confirmed_by_user=False
                    )
                    return "Action cancelled by user."
                
                self.logger.log_step(
                    step="safety_gate",
                    action="user_confirmed",
                    input_data={"tool_name": tool_name, "arguments": arguments},
                    output_data={"confirmed": True},
                    confirmed_by_user=True
                )
            else:
                # Non-interactive mode: deny sensitive actions
                return f"Sensitive action '{tool_name}' requires confirmation (run in interactive mode)."
        
        # Step 3: Execute Tool
        tool_result = execute_tool(tool_name, arguments)
        
        # Step 4: Summarize Result
        try:
            summary = summarize_result(tool_name, tool_result, self.llm_client)
        except Exception:
            summary = fallback_summarize(tool_name, tool_result)
        
        return summary


def create_agent(llm_provider: str = "mock", **kwargs) -> CyberRoninAgent:
    """Factory function to create agent with specified LLM provider."""
    llm_client = create_llm_client(llm_provider, **kwargs)
    return CyberRoninAgent(llm_client=llm_client)