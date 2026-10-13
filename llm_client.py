"""
LLM client for intent parsing and summarization.
Replace with your actual LLM API (OpenAI, Anthropic, local model, etc.)
"""
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def chat_completion(self, messages: list, functions: list = None, 
                        function_call: str = "auto", temperature: float = 0.1) -> Dict[str, Any]:
        """Call the LLM with chat completion."""
        pass


class MockLLMClient(LLMClient):
    """Mock LLM client for testing without API key."""
    
    def chat_completion(self, messages: list, functions: list = None, 
                        function_call: str = "auto", temperature: float = 0.1) -> Dict[str, Any]:
        """Mock response based on keywords in user message."""
        import json
        import re
        user_msg = ""
        system_msg = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_msg = msg.get("content", "").lower()
            elif msg.get("role") == "system":
                system_msg = msg.get("content", "").lower()
        
        # Check if this is a summarization request (no functions provided, or system prompt mentions summarizer)
        is_summarize = "summarizer" in system_msg or functions is None
        
        if is_summarize:
            # Return a simple summary based on the tool result in user message
            try:
                # Extract tool result from user message
                result_start = user_msg.find("result: ")
                if result_start != -1:
                    result_str = user_msg[result_start + 8:]
                    tool_result = json.loads(result_str)
                else:
                    tool_result = {}
            except:
                tool_result = {}
            
            # Simple fallback summaries
            if "network_scan" in user_msg:
                ports = tool_result.get("open_ports", [])
                if ports:
                    port_str = ", ".join(f"{p['port']}/{p['protocol']} ({p['service']})" for p in ports)
                    return {"choices": [{"message": {"role": "assistant", "content": f"Found {len(ports)} open port(s) on {tool_result.get('target')}: {port_str}"}}]}
                return {"choices": [{"message": {"role": "assistant", "content": f"No open ports found on {tool_result.get('target')}"}}]}
            
            elif "check_auth_log" in user_msg:
                count = tool_result.get("failed_count", 0)
                if count > 0:
                    ips = tool_result.get("unique_ips", [])
                    users = tool_result.get("targeted_users", [])
                    return {"choices": [{"message": {"role": "assistant", "content": f"Found {count} failed login attempt(s) from {len(ips)} unique IP(s) targeting {len(users)} user(s)."}}]}
                return {"choices": [{"message": {"role": "assistant", "content": "No failed login attempts found in the specified time window."}}]}
            
            elif "system_health" in user_msg:
                cpu = tool_result.get("cpu", {}).get("total_percent", 0)
                mem = tool_result.get("memory", {}).get("percent", 0)
                return {"choices": [{"message": {"role": "assistant", "content": f"System health: CPU at {cpu:.1f}%, Memory at {mem:.1f}%."}}]}
            
            elif "list_processes" in user_msg:
                count = tool_result.get("count", 0)
                filter_str = tool_result.get("filter", "")
                filter_msg = f" matching '{filter_str}'" if filter_str else ""
                return {"choices": [{"message": {"role": "assistant", "content": f"Found {count} process(es){filter_msg}."}}]}
            
            if not tool_result.get("success", True):
                return {"choices": [{"message": {"role": "assistant", "content": f"Error: {tool_result.get('error', 'Unknown error')}"}}]}
            
            return {"choices": [{"message": {"role": "assistant", "content": "Task completed."}}]}
        
        # Intent parsing logic (original)
        # Simple keyword-based routing for demo
        if any(kw in user_msg for kw in ["scan", "port", "nmap", "open port"]):
            # Extract target from message - look for IP address or hostname pattern
            # IP pattern: x.x.x.x
            ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', user_msg)
            if ip_match:
                target = ip_match.group(1)
            else:
                # Look for hostname-like patterns anywhere in the message
                host_match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', user_msg)
                if host_match:
                    target = host_match.group(1)
                else:
                    # Fallback: scan/host/ip/target followed by word (but not "for" + common words)
                    target_match = re.search(r'(?:scan|host|ip|target)\s+(\S+)', user_msg)
                    if target_match:
                        candidate = target_match.group(1)
                        # Skip common non-target words
                        if candidate.lower() not in ['for', 'the', 'a', 'an', 'ports', 'open', 'listening']:
                            target = candidate
                        else:
                            target = "127.0.0.1"
                    else:
                        target = "127.0.0.1"
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": "network_scan",
                            "arguments": json.dumps({"target": target, "ports": "top-1000"})
                        }
                    }
                }]
            }
        elif any(kw in user_msg for kw in ["failed login", "auth log", "login attempt", "brute force"]):
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": "check_auth_log",
                            "arguments": json.dumps({"log_path": "/var/log/auth.log", "lookback_hours": 24})
                        }
                    }
                }]
            }
        elif any(kw in user_msg for kw in ["system health", "cpu", "memory", "disk", "resource"]):
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": "system_health",
                            "arguments": "{}"
                        }
                    }
                }]
            }
        elif any(kw in user_msg for kw in ["process", "running", "pid", "task"]):
            filter_match = re.search(r'(?:filter|name|named|called|if|running)\s+(\S+)', user_msg)
            filter_val = filter_match.group(1) if filter_match else None
            # Exclude common words that aren't actual process names
            if filter_val and filter_val.lower() in ['all', 'processes', 'running', 'the', 'a', 'an']:
                filter_val = None
            args = {"filter": filter_val} if filter_val else {}
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": "list_processes",
                            "arguments": json.dumps(args)
                        }
                    }
                }]
            }
        else:
            # Default to system health
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "I'll check your system health.",
                        "function_call": {
                            "name": "system_health",
                            "arguments": "{}"
                        }
                    }
                }]
            }


class OpenAILLMClient(LLMClient):
    """OpenAI API client for production use."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
    
    def chat_completion(self, messages: list, functions: list = None, 
                        function_call: str = "auto", temperature: float = 0.1) -> Dict[str, Any]:
        """Call OpenAI chat completion API."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        if functions:
            kwargs["tools"] = [{"type": "function", "function": f} for f in functions]
            kwargs["tool_choice"] = function_call
        
        response = self.client.chat.completions.create(**kwargs)
        
        # Convert to our standard format
        msg = response.choices[0].message
        result = {
            "choices": [{
                "message": {
                    "role": msg.role,
                    "content": msg.content
                }
            }]
        }
        if msg.tool_calls:
            result["choices"][0]["message"]["function_call"] = {
                "name": msg.tool_calls[0].function.name,
                "arguments": msg.tool_calls[0].function.arguments
            }
        return result


def create_llm_client(provider: str = "mock", **kwargs) -> LLMClient:
    """Factory function to create LLM client."""
    if provider == "openai":
        return OpenAILLMClient(**kwargs)
    return MockLLMClient()