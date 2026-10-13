"""
Summarizer - uses LLM to convert raw tool output into human-readable response.
"""
import json
from typing import Dict, Any
from llm_client import create_llm_client, LLMClient
from audit_log import get_audit_logger


# System prompt for summarization
SUMMARIZER_PROMPT = """You are Cyber Ronin's response summarizer. Convert the raw tool output into a clear, concise, human-readable response for the user.

Guidelines:
- Be concise (2-4 sentences max)
- Highlight key findings (open ports, failed logins, high CPU, etc.)
- Use plain English, avoid technical jargon
- If there's an error, explain it simply and suggest next steps
- Don't repeat raw data; summarize it
- For security findings, be informative but not alarmist"""


def summarize_result(tool_name: str, tool_result: Dict[str, Any], 
                     llm_client: LLMClient = None) -> str:
    """
    Summarize tool output into human-readable response.
    
    Args:
        tool_name: Name of the tool that was executed
        tool_result: Raw result from tool execution
        llm_client: LLM client instance (creates mock if not provided)
    
    Returns:
        Human-readable summary string
    """
    if llm_client is None:
        llm_client = create_llm_client("mock")
    
    messages = [
        {"role": "system", "content": SUMMARIZER_PROMPT},
        {"role": "user", "content": f"Tool: {tool_name}\nResult: {json.dumps(tool_result, indent=2)}"}
    ]
    
    response = llm_client.chat_completion(messages, temperature=0.3)
    
    summary = response["choices"][0]["message"].get("content", "No summary available.")
    
    # Audit log
    logger = get_audit_logger()
    logger.log_step(
        step="summarizer",
        action="summarize",
        input_data={"tool_name": tool_name, "tool_result": tool_result},
        output_data={"summary": summary}
    )
    
    return summary


# Fallback summarizers for when LLM is unavailable
def fallback_summarize(tool_name: str, tool_result: Dict[str, Any]) -> str:
    """Simple rule-based summarization without LLM."""
    if not tool_result.get("success", True):
        return f"Error: {tool_result.get('error', 'Unknown error')}"
    
    if tool_name == "network_scan":
        ports = tool_result.get("open_ports", [])
        if ports:
            port_str = ", ".join(f"{p['port']}/{p['protocol']} ({p['service']})" for p in ports)
            return f"Found {len(ports)} open port(s) on {tool_result.get('target')}: {port_str}"
        return f"No open ports found on {tool_result.get('target')}"
    
    elif tool_name == "check_auth_log":
        count = tool_result.get("failed_count", 0)
        if count > 0:
            ips = tool_result.get("unique_ips", [])
            users = tool_result.get("targeted_users", [])
            return f"Found {count} failed login attempt(s) from {len(ips)} unique IP(s) targeting {len(users)} user(s)."
        return "No failed login attempts found in the specified time window."
    
    elif tool_name == "system_health":
        cpu = tool_result.get("cpu", {}).get("total_percent", 0)
        mem = tool_result.get("memory", {}).get("percent", 0)
        return f"System health: CPU at {cpu:.1f}%, Memory at {mem:.1f}%."
    
    elif tool_name == "list_processes":
        count = tool_result.get("count", 0)
        filter_str = tool_result.get("filter", "")
        filter_msg = f" matching '{filter_str}'" if filter_str else ""
        return f"Found {count} process(es){filter_msg}."
    
    return "Task completed."