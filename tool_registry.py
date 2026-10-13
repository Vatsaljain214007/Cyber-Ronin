"""
Tool registry loader - loads tool definitions from JSON file.
"""
import json
import os
from typing import Dict, Any


def load_tool_registry(registry_path: str = None) -> Dict[str, Any]:
    """
    Load the tool registry from JSON file.
    
    Args:
        registry_path: Optional path to registry file. Defaults to tool_registry.json in same directory.
    
    Returns:
        Dict containing tool registry
    """
    if registry_path is None:
        registry_path = os.path.join(os.path.dirname(__file__), "tool_registry.json")
    
    with open(registry_path, 'r') as f:
        return json.load(f)


def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """Get the JSON schema for a specific tool."""
    registry = load_tool_registry()
    for tool in registry.get("tools", []):
        if tool["name"] == tool_name:
            return tool
    return {}


def get_all_tool_schemas() -> Dict[str, Any]:
    """Get all tool schemas formatted for LLM function calling."""
    registry = load_tool_registry()
    return {tool["name"]: tool for tool in registry.get("tools", [])}