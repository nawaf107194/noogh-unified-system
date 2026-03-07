import os
from pathlib import Path
from typing import Any, Dict

import httpx


def read_last_lines(path: str, n: int = 200) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    with p.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        block = 4096
        data = b""
        while size > 0 and data.count(b"\n") <= n:
            step = min(block, size)
            size -= step
            f.seek(size)
            data = f.read(step) + data
        lines = []
        # Filter logic to prevent chat history loops
        decoded_lines = [line.decode("utf-8", "replace") for line in data.splitlines()]
        for line in decoded_lines[-n:]:
            if "/uc3/chat" not in line and "POST /api/v1/process" not in line:
                lines.append(line)
        return "\n".join(lines)


async def prom_query(prom_url: str, expr: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{prom_url}/api/v1/query", params={"query": expr})
            return {"ok": r.status_code == 200, "data": r.json() if r.status_code == 200 else r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# SECURITY: subprocess removed (CHAOS-003 FIX)

import psutil

# Torch for GPU stats
try:
    import torch
    TORCH_AVAILABLE = torch.cuda.is_available()
except ImportError:
    TORCH_AVAILABLE = False


def get_gpu_context() -> dict:
    """Get GPU stats using torch only (no subprocess)"""
    # CHAOS-003 FIX: Use torch instead of nvidia-smi subprocess
    if TORCH_AVAILABLE:
        try:
            free, total = torch.cuda.mem_get_info(0)
            util = 100 * (1 - free / total)
            return {"gpu_vram_gb": round(total / (1024**3), 2), "gpu_util": round(util, 1)}
        except Exception:
            pass
    return {"gpu_vram_gb": 0, "gpu_util": 0}


async def build_context(settings, include_logs=True, include_metrics=True) -> Dict[str, Any]:
    ctx: Dict[str, Any] = {}

    if include_logs:
        ctx["gateway_log_tail"] = read_last_lines(settings.GATEWAY_LOG, 50)
        ctx["neural_log_tail"] = read_last_lines(settings.NEURAL_LOG, 50)

    if include_metrics:
        # Use DIRECT system metrics (psutil/nvidia-smi) instead of broken Prometheus queries
        gpu = get_gpu_context()
        ctx["metrics"] = {
            "cpu_util": psutil.cpu_percent(interval=0.1),
            "mem_used_gb": round((psutil.virtual_memory().total - psutil.virtual_memory().available) / (1024**3), 2),
            "gpu_util": gpu["gpu_util"],
            "gpu_vram_mb": gpu["gpu_vram_gb"] * 1024,  # consistent unit
        }

    return ctx
