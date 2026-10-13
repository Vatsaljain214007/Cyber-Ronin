"""
System health monitoring using psutil.
Returns CPU, memory, and top processes by resource usage.
"""
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float


def system_health() -> Dict:
    """
    Get system health metrics including CPU, memory, and top processes.
    
    Returns:
        Dict with system health information
    """
    if not PSUTIL_AVAILABLE:
        return {
            "success": False,
            "error": "psutil not installed. Install with: pip install psutil",
            "cpu": {},
            "memory": {},
            "swap": {},
            "disk": {},
            "top_processes_by_cpu": [],
            "top_processes_by_memory": []
        }
    
    try:
        # CPU usage (interval=1 for accurate reading)
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        
        # Memory usage
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk usage (root partition)
        disk = psutil.disk_usage('/')
        
        # Top processes by CPU
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
            try:
                info = proc.info
                if info['cpu_percent'] is not None and info['cpu_percent'] > 0:
                    processes.append(ProcessInfo(
                        pid=info['pid'],
                        name=info['name'] or 'unknown',
                        cpu_percent=info['cpu_percent'],
                        memory_percent=info['memory_percent'] or 0,
                        memory_mb=(info['memory_info'].rss / 1024 / 1024) if info['memory_info'] else 0
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage and take top 10
        top_cpu = sorted(processes, key=lambda p: p.cpu_percent, reverse=True)[:10]
        # Sort by memory usage and take top 10
        top_memory = sorted(processes, key=lambda p: p.memory_percent, reverse=True)[:10]
        
        return {
            "success": True,
            "cpu": {
                "total_percent": cpu_percent,
                "per_core": cpu_per_core,
                "core_count": psutil.cpu_count(),
                "core_count_logical": psutil.cpu_count(logical=True)
            },
            "memory": {
                "total_mb": memory.total / 1024 / 1024,
                "available_mb": memory.available / 1024 / 1024,
                "used_mb": memory.used / 1024 / 1024,
                "percent": memory.percent
            },
            "swap": {
                "total_mb": swap.total / 1024 / 1024,
                "used_mb": swap.used / 1024 / 1024,
                "percent": swap.percent
            },
            "disk": {
                "total_gb": disk.total / 1024 / 1024 / 1024,
                "used_gb": disk.used / 1024 / 1024 / 1024,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "percent": (disk.used / disk.total) * 100
            },
            "top_processes_by_cpu": [asdict(p) for p in top_cpu],
            "top_processes_by_memory": [asdict(p) for p in top_memory]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get system health: {str(e)}",
            "cpu": {},
            "memory": {},
            "swap": {},
            "disk": {},
            "top_processes_by_cpu": [],
            "top_processes_by_memory": []
        }