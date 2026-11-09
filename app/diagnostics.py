"""Safe, read-only local host and network diagnostics."""
import socket
import time
from typing import Any

import psutil

STARTED = time.monotonic()


def host_snapshot() -> dict[str, Any]:
    disk = psutil.disk_usage("/")
    memory = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": memory.percent,
        "memory_available_mb": round(memory.available / 1024**2, 1),
        "disk_percent": disk.percent,
        "uptime_seconds": int(time.monotonic() - STARTED),
        "status": "ok" if max(memory.percent, disk.percent) < 90 else "capacity_warning",
    }


def check_tcp(host: str, port: int, timeout: float = 2.0) -> dict[str, Any]:
    """Resolve and attempt one bounded TCP connection; no shell commands run."""
    started = time.monotonic()
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)})
        with socket.create_connection((host, port), timeout=timeout):
            pass
        return {"host": host, "port": port, "reachable": True, "addresses": addresses,
                "latency_ms": round((time.monotonic() - started) * 1000, 2), "error": None}
    except (OSError, socket.timeout) as exc:
        return {"host": host, "port": port, "reachable": False, "addresses": [],
                "latency_ms": round((time.monotonic() - started) * 1000, 2), "error": str(exc)}
