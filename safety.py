"""
Safety/Permission Gate - determines if an action requires user confirmation.
"""
from typing import Dict, Any
from tool_registry import load_tool_registry


# Cache the registry
_registry = None


def get_tool_registry() -> Dict:
    """Load and cache the tool registry."""
    global _registry
    if _registry is None:
        _registry = load_tool_registry()
    return _registry


def is_sensitive_action(tool_name: str) -> bool:
    """Check if a tool is marked as sensitive (requires confirmation)."""
    registry = get_tool_registry()
    for tool in registry.get("tools", []):
        if tool["name"] == tool_name:
            return tool.get("sensitive", False)
    return False


def get_tool_description(tool_name: str) -> str:
    """Get the description of a tool for confirmation prompts."""
    registry = get_tool_registry()
    for tool in registry.get("tools", []):
        if tool["name"] == tool_name:
            return tool.get("description", "")
    return ""


def requires_confirmation(tool_name: str, arguments: Dict[str, Any]) -> bool:
    """
    Determine if an action requires explicit user confirmation.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool
    
    Returns:
        True if confirmation is required, False otherwise
    """
    return is_sensitive_action(tool_name)


def format_confirmation_prompt(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Format a user-friendly confirmation prompt."""
    desc = get_tool_description(tool_name)
    args_str = ", ".join(f"{k}={v}" for k, v in arguments.items())
    return (
        f"\n[!] Sensitive Action Requires Confirmation\n"
        f"Tool: {tool_name}\n"
        f"Description: {desc}\n"
        f"Arguments: {args_str}\n"
        f"\nProceed? (y/n): "
    )