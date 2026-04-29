"""Endpoints de metricas del indice vectorial."""

import os
import time
from fastapi import APIRouter

from app.core import rag
import psutil

router = APIRouter()

_process = psutil.Process(os.getpid())
_last_cpu_total: float | None = None
_last_cpu_ts: float | None = None


@router.get("")
async def get_stats():
    """Devuelve contadores basicos del indice y metadatos asociados."""
    return rag.instance.get_stats()


@router.get("/system")
async def get_system_stats():
    """Devuelve consumo de recursos del proceso backend y del sistema."""
    global _last_cpu_total, _last_cpu_ts

    memory = _process.memory_info()
    disk = psutil.disk_usage("/")
    now = time.monotonic()
    cpu_total = _process.cpu_times().user + _process.cpu_times().system

    if _last_cpu_total is None or _last_cpu_ts is None:
        process_cpu_percent = 0.0
    else:
        elapsed = now - _last_cpu_ts
        if elapsed <= 0:
            process_cpu_percent = 0.0
        else:
            used_cpu_seconds = max(0.0, cpu_total - _last_cpu_total)
            process_cpu_percent = (used_cpu_seconds / elapsed) * 100.0

    _last_cpu_total = cpu_total
    _last_cpu_ts = now

    return {
        "process_cpu_percent": round(process_cpu_percent, 2),
        "process_memory_mb": round(memory.rss / (1024 * 1024), 2),
        "process_memory_percent": round((memory.rss / max(1, psutil.virtual_memory().total)) * 100.0, 2),
        "system_cpu_percent": psutil.cpu_percent(interval=None),
        "system_memory_percent": psutil.virtual_memory().percent,
        "disk_percent": disk.percent,
        "threads": _process.num_threads(),
    }
