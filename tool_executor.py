"""
Tool Executor - runs the selected tool with sanitized inputs.
"""
from typing import Dict, Any, Callable
from audit_log import get_audit_logger

# Import tool functions
from tools.network_scan import network_scan
from tools.log_check import check_auth_log
from tools.system_health import system_health
from tools.process_list import list_processes


# Tool registry mapping names to functions
TOOL_FUNCTIONS: Dict[str, Callable] = {
    "network_scan": network_scan,
    "check_auth_log": check_auth_log,
    "system_health": system_health,
    "list_processes": list_processes,
}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool
    
    Returns:
        Tool execution result
    """
    if tool_name not in TOOL_FUNCTIONS:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
    
    func = TOOL_FUNCTIONS[tool_name]
    
    try:
        # Call the tool function with arguments
        result = func(**arguments)
    except TypeError as e:
        return {
            "success": False,
            "error": f"Invalid arguments for {tool_name}: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }
    
    # Audit log
    logger = get_audit_logger()
    logger.log_step(
        step="tool_executor",
        action=f"execute_{tool_name}",
        input_data={"tool_name": tool_name, "arguments": arguments},
        output_data=result
    )
    
    return result