"""
Audit logger - logs all decisions and actions to a JSON-lines file.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AuditEntry:
    timestamp: str
    step: str
    action: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    confirmed_by_user: bool = False
    user_id: Optional[str] = None


class AuditLogger:
    """Logs all agent actions to a JSON-lines audit log file."""
    
    def __init__(self, log_path: str = "audit_log.jsonl"):
        self.log_path = log_path
    
    def log(self, entry: AuditEntry) -> None:
        """Write an audit entry to the log file."""
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(entry)) + '\n')
    
    def log_step(self, step: str, action: str, input_data: Dict[str, Any], 
                 output_data: Dict[str, Any], confirmed_by_user: bool = False,
                 user_id: Optional[str] = None) -> None:
        """Convenience method to log a pipeline step."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            step=step,
            action=action,
            input_data=input_data,
            output_data=output_data,
            confirmed_by_user=confirmed_by_user,
            user_id=user_id
        )
        self.log(entry)
    
    def read_log(self, limit: int = 100) -> list:
        """Read recent audit log entries."""
        if not os.path.exists(self.log_path):
            return []
        
        entries = []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        
        return entries[-limit:]


# Global logger instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger