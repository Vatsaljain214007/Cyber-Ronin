"""
Intent Parser - uses LLM to parse user input and select appropriate tool.
"""
import json
from typing import Dict, Any, Optional
from tool_registry import get_all_tool_schemas
from llm_client import create_llm_client, LLMClient
from audit_log import get_audit_logger


# System prompt for intent parsing
INTENT_PARSER_PROMPT = """You are Cyber Ronin's intent parser. Your job is to analyze the user's natural language request and select the appropriate tool from the registry.

Available tools:
{tool_schemas}

Rules:
1. Select the BEST matching tool for the user's request
2. Extract all required parameters from the user's message
3. Use sensible defaults for optional parameters
4. Return ONLY a function call with the tool name and arguments
5. If the request is ambiguous, pick the most likely tool and note assumptions

Return your response as a function call only."""


def parse_intent(user_input: str, llm_client: LLMClient = None) -> Dict[str, Any]:
    """
    Parse user intent and select tool with arguments.
    
    Args:
        user_input: Natural language request from user
        llm_client: LLM client instance (creates mock if not provided)
    
    Returns:
        Dict with tool_name, arguments, and raw LLM response
    """
    if llm_client is None:
        llm_client = create_llm_client("mock")
    
    # Load tool schemas
    tool_schemas = get_all_tool_schemas()
    schemas_str = json.dumps(tool_schemas, indent=2)
    
    messages = [
        {"role": "system", "content": INTENT_PARSER_PROMPT.format(tool_schemas=schemas_str)},
        {"role": "user", "content": user_input}
    ]
    
    # Convert tool schemas to function calling format
    functions = []
    for name, schema in tool_schemas.items():
        functions.append({
            "name": name,
            "description": schema.get("description", ""),
            "parameters": schema.get("parameters", {})
        })
    
    response = llm_client.chat_completion(messages, functions=functions, function_call="auto")
    
    # Extract function call
    choice = response["choices"][0]
    msg = choice["message"]
    
    result = {
        "tool_name": None,
        "arguments": {},
        "raw_response": response
    }
    
    if msg.get("function_call"):
        fc = msg["function_call"]
        result["tool_name"] = fc["name"]
        try:
            result["arguments"] = json.loads(fc["arguments"])
        except json.JSONDecodeError:
            result["arguments"] = {}
    elif msg.get("content"):
        # Fallback: try to parse from content
        result["tool_name"] = "system_health"
        result["arguments"] = {}
    
    # Audit log
    logger = get_audit_logger()
    logger.log_step(
        step="intent_parser",
        action="parse_intent",
        input_data={"user_input": user_input},
        output_data=result
    )
    
    return result