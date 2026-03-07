import os
import shutil
import time
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger("unified_core.skills.mirror_shield")

class MirrorShield:
    """
    Skill: Hierarchical Multi-Disk Backup (Mirror Shield v2.4)
    Ensures system survival by replicating critical data and forensic logs across the 4-disk array.
    """
    def __init__(self):
        self.primary_db = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
        self.evolution_ledger = "/home/noogh/.noogh/evolution/evolution_ledger.jsonl"
        self.amla_logs = "/home/noogh/projects/noogh_unified_system/src/data/amla_audit.jsonl"
        self.project_root = "/home/noogh/projects/noogh_unified_system"
        
        # Defined Hierarchy
        self.targets = {
            "L2_HOT_MIRROR": "/media/noogh/New Volume/noogh_hot_backup",
            "L3_VAULT": "/media/noogh/NOOGH_BACKUP/archives",
            "L4_DEEP_SLEEP": "/media/noogh/TOSHIBA EXT/noogh_deep_storage"
        }

    async def execute_mirror_sync(self):
        """Perform the hierarchical sync process (Physical-Hardening)."""
        results = {"success": True, "details": []}
        timestamp = int(time.time())
        
        try:
            # 1. Select Tier (L2 -> L4 -> L3)
            # L2 is preferred (SSD), L4 is next (Large Ext HDD), L3 is last (Permission check required)
            tier_order = ["L2_HOT_MIRROR", "L4_DEEP_SLEEP", "L3_VAULT"]
            target_path = None
            tier = None
            
            for t in tier_order:
                path = Path(self.targets[t])
                parent = path.parent
                if parent.exists() and self._check_space(parent, min_mb=1000):
                    # Test write permission
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        test_file = path / ".perstest"
                        test_file.write_text("ok")
                        test_file.unlink()
                        target_path = path
                        tier = t
                        break
                    except Exception:
                        continue
            
            if not target_path:
                results["success"] = False
                results["error"] = "CRITICAL: No writeable backup tier found with sufficient space."
                logger.error(results["error"])
                return results

            if tier != "L2_HOT_MIRROR":
                 logger.warning(f"⚠️ Primary Mirror failed/full. Falling back to {tier} for primary replication.")
            
            # Replicate key forensic assets
            assets = {
                "db": (self.primary_db, "shared_memory.sqlite.bak"),
                "ledger": (self.evolution_ledger, "evolution_ledger.jsonl.bak"),
                "amla": (self.amla_logs, "amla_audit.jsonl.bak")
            }
            
            for name, (src, dst_name) in assets.items():
                if os.path.exists(src):
                    shutil.copy2(src, target_path / dst_name)
                    results["details"].append(f"{tier} {name} updated.")

            # 2. Cross-Tier Redundancy: Update Deep Sleep Heartbeat if not used as target
            if tier != "L4_DEEP_SLEEP":
                l4_parent = Path(self.targets["L4_DEEP_SLEEP"]).parent
                if l4_parent.exists():
                    l4_path = Path(self.targets["L4_DEEP_SLEEP"])
                    try:
                        l4_path.mkdir(parents=True, exist_ok=True)
                        marker = l4_path / "survival.heartbeat"
                        marker.write_text(f"NOOGH_ALIVE:{timestamp}")
                        results["details"].append("L4 Deep Sleep heartbeat pulsing.")
                    except: pass

            logger.info(f"🛡️ Mirror Shield v2.4.2 Cycle Complete: {results['details']}")
            return results
            
        except Exception as e:
            logger.error(f"Mirror Shield Failed: {e}")
            return {"success": False, "error": str(e)}

    def _check_space(self, path: Path, min_mb: int) -> bool:
        """Check if target path has enough free space in MB."""
        try:
            if not path.exists():
                path = path.parent
            usage = shutil.disk_usage(path)
            free_mb = usage.free / (1024 * 1024)
            return free_mb > min_mb
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        status = {}
        for level, path in self.targets.items():
            path_obj = Path(path)
            parent = path_obj.parent
            exists = parent.exists()
            
            info = {"state": "CONNECTED" if exists else "DISCONNECTED"}
            if exists:
                try:
                    usage = shutil.disk_usage(parent)
                    info["free_gb"] = round(usage.free / (1024**3), 2)
                    info["pressure"] = "HIGH" if (usage.free / usage.total) < 0.05 else "NORMAL"
                except Exception: pass
            
            status[level] = info
        return status
