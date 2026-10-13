"""
Authentication log checker for failed login attempts.
Parses common log formats (Linux auth.log, Windows Security events).
"""
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class FailedLogin:
    timestamp: str
    ip: str
    user: str
    raw_line: str


# Common regex patterns for failed logins
LINUX_AUTH_PATTERNS = [
    # "Failed password for user from ip"
    re.compile(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*Failed password for (\S+) from ([\d\.]+)'),
    # "Failed password for invalid user user from ip"
    re.compile(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*Failed password for invalid user (\S+) from ([\d\.]+)'),
    # "Invalid user user from ip"
    re.compile(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*Invalid user (\S+) from ([\d\.]+)'),
    # "Connection closed by ip [preauth]"
    re.compile(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*Connection closed by ([\d\.]+) \[preauth\]'),
]

WINDOWS_PATTERNS = [
    # Event ID 4625 - Failed logon
    re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Event ID: 4625.*IpAddress:([\d\.]+).*TargetUserName:(\S+)'),
]


def parse_linux_auth_log(lines: List[str], cutoff: datetime) -> List[FailedLogin]:
    """Parse Linux auth.log format."""
    failed = []
    current_year = datetime.now().year
    
    for line in lines:
        for pattern in LINUX_AUTH_PATTERNS:
            match = pattern.search(line)
            if match:
                groups = match.groups()
                timestamp_str = groups[0]
                user = groups[1]
                ip = groups[2]
                
                # Parse timestamp (format: "Jan 15 10:30:45")
                try:
                    # Handle year rollover
                    ts = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
                    if ts > datetime.now():
                        ts = ts.replace(year=current_year - 1)
                except ValueError:
                    continue
                
                if ts >= cutoff:
                    failed.append(FailedLogin(
                        timestamp=ts.isoformat(),
                        ip=ip,
                        user=user,
                        raw_line=line.strip()
                    ))
                break
    return failed


def parse_windows_security_log(lines: List[str], cutoff: datetime) -> List[FailedLogin]:
    """Parse Windows Security event log format."""
    failed = []
    
    for line in lines:
        for pattern in WINDOWS_PATTERNS:
            match = pattern.search(line)
            if match:
                groups = match.groups()
                timestamp_str = groups[0]
                ip = groups[1]
                user = groups[2]
                
                try:
                    ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                
                if ts >= cutoff:
                    failed.append(FailedLogin(
                        timestamp=ts.isoformat(),
                        ip=ip,
                        user=user,
                        raw_line=line.strip()
                    ))
                break
    return failed


def check_auth_log(log_path: str, lookback_hours: int = 24) -> Dict:
    """
    Parse authentication log for failed login attempts.
    
    Args:
        log_path: Path to the authentication log file
        lookback_hours: Hours to look back for failed attempts
    
    Returns:
        Dict with failed login counts and flagged entries
    """
    if not os.path.exists(log_path):
        return {
            "success": False,
            "error": f"Log file not found: {log_path}",
            "failed_count": 0,
            "failed_logins": [],
            "unique_ips": [],
            "targeted_users": []
        }
    
    cutoff = datetime.now() - timedelta(hours=lookback_hours)
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read log file: {str(e)}",
            "failed_count": 0,
            "failed_logins": [],
            "unique_ips": [],
            "targeted_users": []
        }
    
    # Try Linux patterns first, then Windows
    failed = parse_linux_auth_log(lines, cutoff)
    if not failed:
        failed = parse_windows_security_log(lines, cutoff)
    
    # Aggregate statistics
    unique_ips = list(set(f.ip for f in failed))
    targeted_users = list(set(f.user for f in failed))
    
    # Sort by timestamp descending
    failed.sort(key=lambda x: x.timestamp, reverse=True)
    
    return {
        "success": True,
        "log_path": log_path,
        "lookback_hours": lookback_hours,
        "failed_count": len(failed),
        "failed_logins": [asdict(f) for f in failed[:50]],  # Limit to 50 most recent
        "unique_ips": unique_ips,
        "targeted_users": targeted_users,
        "summary": {
            "total_failed": len(failed),
            "unique_attacker_ips": len(unique_ips),
            "unique_targeted_users": len(targeted_users)
        }
    }