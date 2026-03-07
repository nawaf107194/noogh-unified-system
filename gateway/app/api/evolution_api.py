"""
Evolution Dashboard API — REST endpoints for monitoring self-improvement.
Version: 1.1.0

Provides:
- /api/evolution/stats               — Overall evolution statistics
- /api/evolution/recent              — Recent proposals + outcomes
- /api/evolution/promoted            — All files promoted to production
- /api/evolution/fragile             — Currently fragile (skip-listed) files
- /api/evolution/distillation        — Distillation collector stats
- /api/evolution/distillation/export — Export training data
"""

import json
import os
import time
import logging
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger("gateway.evolution_api")

router = APIRouter(prefix="/api/evolution", tags=["evolution"])

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = PROJECT_ROOT / "src"
LEDGER_FILE = Path.home() / ".noogh" / "evolution" / "evolution_ledger.jsonl"
MEMORY_DIR = SRC_ROOT / "data" / "evolution_memory"


def _read_ledger(limit: int = 500) -> List[Dict[str, Any]]:
    """Read last N entries from evolution ledger."""
    entries = []
    if not LEDGER_FILE.exists():
        return entries
    
    try:
        with open(LEDGER_FILE, 'r') as f:
            lines = f.readlines()
        
        for line in lines[-limit:]:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Ledger read error: {e}")
    
    return entries


def _find_backup_files() -> List[Dict[str, Any]]:
    """Find all .backup.* files (evolved code)."""
    backups = []
    try:
        for backup_file in SRC_ROOT.rglob("*.backup.*"):
            stat = backup_file.stat()
            # Extract timestamp from filename
            ts_str = backup_file.suffix.lstrip('.')
            try:
                ts = int(ts_str)
            except ValueError:
                ts = int(stat.st_mtime)
            
            original_file = str(backup_file).split('.backup.')[0]
            backups.append({
                "original_file": original_file,
                "backup_file": str(backup_file),
                "filename": Path(original_file).name,
                "timestamp": ts,
                "time_human": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts)),
                "size_bytes": stat.st_size
            })
    except Exception as e:
        logger.error(f"Backup scan error: {e}")
    
    return sorted(backups, key=lambda x: x["timestamp"], reverse=True)


def _read_fragile_files() -> Dict[str, float]:
    """Read fragile files from evolution memory."""
    fragile_path = MEMORY_DIR / "fragile_files.json"
    if not fragile_path.exists():
        return {}
    
    try:
        with open(fragile_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


@router.get("/stats")
async def evolution_stats():
    """Get comprehensive evolution statistics."""
    entries = _read_ledger()
    
    # Count by type
    type_counts = {}
    for e in entries:
        t = e.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    
    # Promoted files
    promoted = [e for e in entries if e.get("type") == "promoted"]
    
    # Canary results
    canary_pass = [e for e in entries if e.get("type") == "canary_success"]
    canary_fail = [e for e in entries if e.get("type") == "canary_failure"]
    
    # Fragile files
    fragile = _read_fragile_files()
    active_fragile = {k: v for k, v in fragile.items() if v > time.time()}
    
    # Backup files (evolved files)
    backups = _find_backup_files()
    
    return JSONResponse({
        "total_ledger_entries": len(entries),
        "type_counts": type_counts,
        "promoted_count": len(promoted),
        "canary_pass_count": len(canary_pass),
        "canary_fail_count": len(canary_fail),
        "evolved_files_count": len(backups),
        "fragile_files_count": len(active_fragile),
        "safe_mode": any(
            e.get("type") == "safe_mode_enter" 
            for e in entries[-5:]  # Check last 5 entries
        ) and not any(
            e.get("type") == "safe_mode_exit"
            for e in entries[-5:]
        ),
        "timestamp": time.time()
    })


@router.get("/recent")
async def evolution_recent(limit: int = 20):
    """Get recent evolution activity."""
    entries = _read_ledger(limit=limit * 3)  # Read more to filter
    
    # Return last N entries, cleaned up
    result = []
    for e in entries[-limit:]:
        result.append({
            "type": e.get("type", "unknown"),
            "timestamp": e.get("timestamp", 0),
            "time_human": time.strftime(
                '%H:%M:%S', 
                time.localtime(e.get("timestamp", 0))
            ),
            "data": {
                k: v for k, v in e.get("data", {}).items()
                if k not in ("original_code", "refactored_code")  # Don't expose code
            },
            "proposal_id": e.get("data", {}).get("proposal_id", ""),
        })
    
    return JSONResponse({
        "count": len(result),
        "entries": result
    })


@router.get("/promoted")
async def evolution_promoted():
    """Get all files that were promoted to production."""
    backups = _find_backup_files()
    
    # Also get from ledger
    entries = _read_ledger()
    promoted_entries = [e for e in entries if e.get("type") == "promoted"]
    
    # Merge info
    promoted_list = []
    for b in backups:
        # Find matching ledger entry
        matching = None
        for p in promoted_entries:
            target = p.get("data", {}).get("metrics_after", {}).get("target", "")
            if target and target in b.get("original_file", ""):
                matching = p
                break
        
        promoted_list.append({
            "file": b["filename"],
            "full_path": b["original_file"],
            "timestamp": b["timestamp"],
            "time_human": b["time_human"],
            "function": matching.get("data", {}).get("metrics_after", {}).get("function", "unknown") if matching else "unknown",
            "confidence": matching.get("data", {}).get("metrics_after", {}).get("confidence", 0) if matching else 0,
            "proposal_id": matching.get("data", {}).get("proposal_id", "") if matching else "",
        })
    
    return JSONResponse({
        "count": len(promoted_list),
        "promoted": promoted_list
    })


@router.get("/fragile")
async def evolution_fragile():
    """Get currently fragile (skip-listed) files."""
    fragile = _read_fragile_files()
    now = time.time()
    
    result = []
    for filepath, expiry in fragile.items():
        remaining_hours = max(0, (expiry - now) / 3600)
        result.append({
            "file": Path(filepath).name,
            "full_path": filepath,
            "expiry": expiry,
            "remaining_hours": round(remaining_hours, 1),
            "active": expiry > now,
            "expiry_human": time.strftime('%Y-%m-%d %H:%M', time.localtime(expiry))
        })
    
    active = [r for r in result if r["active"]]
    expired = [r for r in result if not r["active"]]
    
    return JSONResponse({
        "active_count": len(active),
        "expired_count": len(expired),
        "active": active,
        "expired": expired
    })


DISTILLATION_DIR = SRC_ROOT / "data" / "distillation"


@router.get("/distillation")
async def distillation_stats():
    """Get distillation collector statistics."""
    trajectories_file = DISTILLATION_DIR / "teacher_trajectories.jsonl"
    export_file = DISTILLATION_DIR / "training_ready.jsonl"
    
    # Count trajectories
    trajectory_count = 0
    categories = {}
    quality_sum = 0.0
    
    if trajectories_file.exists():
        try:
            with open(trajectories_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            trajectory_count += 1
                            cat = entry.get("category", "unknown")
                            categories[cat] = categories.get(cat, 0) + 1
                            quality_sum += entry.get("quality_score", 0.5)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Trajectories read error: {e}")
    
    # Count exported
    export_count = 0
    if export_file.exists():
        try:
            with open(export_file, 'r') as f:
                export_count = sum(1 for line in f if line.strip())
        except Exception:
            pass
    
    return JSONResponse({
        "trajectory_count": trajectory_count,
        "export_count": export_count,
        "categories": categories,
        "avg_quality": round(quality_sum / max(1, trajectory_count), 3),
        "trajectories_file": str(trajectories_file),
        "export_file": str(export_file),
        "ready_for_training": export_count > 0,
        "timestamp": time.time()
    })


@router.post("/distillation/export")
async def distillation_export(min_quality: float = 0.6):
    """Export high-quality trajectories as training data."""
    try:
        import sys
        sys.path.insert(0, str(SRC_ROOT))
        from unified_core.evolution.distillation_collector import get_distillation_collector
        
        collector = get_distillation_collector()
        stats = collector.export_training_data(min_quality=min_quality)
        
        return JSONResponse({
            "success": True,
            "message": "Training data exported",
            "stats": stats,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"Distillation export error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
