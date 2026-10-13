"""
Process listing tool with optional name filtering.
"""
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    username: str
    create_time: float


def list_processes(filter: Optional[str] = None) -> Dict:
    """
    List running processes, optionally filtered by name.
    
    Args:
        filter: Optional process name filter (case-insensitive substring match)
    
    Returns:
        Dict with list of processes
    """
    if not PSUTIL_AVAILABLE:
        return {
            "success": False,
            "error": "psutil not installed. Install with: pip install psutil",
            "filter": filter,
            "count": 0,
            "processes": []
        }
    
    try:
        processes = []
        filter_lower = filter.lower() if filter else None
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                          'memory_info', 'status', 'username', 'create_time']):
            try:
                info = proc.info
                name = info['name'] or 'unknown'
                
                # Apply filter if provided
                if filter_lower and filter_lower not in name.lower():
                    continue
                
                mem_info = info['memory_info']
                memory_mb = (mem_info.rss / 1024 / 1024) if mem_info else 0
                
                processes.append(ProcessInfo(
                    pid=info['pid'],
                    name=name,
                    cpu_percent=info['cpu_percent'] or 0,
                    memory_percent=info['memory_percent'] or 0,
                    memory_mb=memory_mb,
                    status=info['status'] or 'unknown',
                    username=info['username'] or 'unknown',
                    create_time=info['create_time'] or 0
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by PID for consistent output
        processes.sort(key=lambda p: p.pid)
        
        return {
            "success": True,
            "filter": filter,
            "count": len(processes),
            "processes": [asdict(p) for p in processes]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list processes: {str(e)}",
            "filter": filter,
            "count": 0,
            "processes": []
        }