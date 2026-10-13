"""
Network scanning tool using Nmap.
Wraps Nmap via subprocess with parameterized calls for safety.
"""
import subprocess
import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class PortInfo:
    port: int
    protocol: str
    state: str
    service: str
    version: str = ""


def validate_target(target: str) -> bool:
    """Validate target looks like a hostname or IP address."""
    # Basic validation - allow hostnames, IPs, CIDR
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$'
    return bool(re.match(hostname_pattern, target) or re.match(ip_pattern, target))


def parse_nmap_output(output: str) -> List[PortInfo]:
    """Parse Nmap output into structured PortInfo objects."""
    ports = []
    # Match lines like: "80/tcp open  http    Apache httpd 2.4.41"
    port_pattern = re.compile(
        r'^(\d+)/(tcp|udp)\s+(open|closed|filtered)\s+(\S+)\s*(.*)$'
    )
    
    for line in output.split('\n'):
        match = port_pattern.match(line.strip())
        if match:
            port, protocol, state, service, version = match.groups()
            ports.append(PortInfo(
                port=int(port),
                protocol=protocol,
                state=state,
                service=service,
                version=version.strip() if version else ""
            ))
    return ports


def network_scan(target: str, ports: str = "top-1000") -> Dict:
    """
    Scan a target host for open ports using Nmap.
    
    Args:
        target: Target hostname or IP address
        ports: Port specification (e.g., 'top-1000', '1-1000', '80,443,8080')
    
    Returns:
        Dict with scan results including open ports and metadata
    """
    if not validate_target(target):
        return {
            "success": False,
            "error": f"Invalid target format: {target}",
            "open_ports": [],
            "target": target
        }
    
    # Build Nmap command using list form (no shell=True)
    cmd = [
        "nmap",
        "-sS",           # SYN scan
        "-p", ports,     # Port specification
        "-T4",           # Faster timing
        "--open",        # Only show open ports
        target
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Nmap failed: {result.stderr}",
                "open_ports": [],
                "target": target
            }
        
        open_ports = parse_nmap_output(result.stdout)
        
        return {
            "success": True,
            "target": target,
            "ports_scanned": ports,
            "open_ports": [asdict(p) for p in open_ports],
            "raw_output": result.stdout
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Scan timed out after 120 seconds",
            "open_ports": [],
            "target": target
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Nmap not found. Please install nmap.",
            "open_ports": [],
            "target": target
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "open_ports": [],
            "target": target
        }