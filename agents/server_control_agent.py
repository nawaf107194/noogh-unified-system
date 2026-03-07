#!/usr/bin/env python3
"""
NOOGH Server Control Agent — السيطرة الكاملة على السيرفر

العقل يرى ويتحكم بـ:
  • جميع خدمات NOOGH (systemd)
  • العمليات الجارية (Python agents)
  • الموارد: CPU / RAM / Disk / Network
  • السجلات الحية
  • التعافي الذاتي عند الفشل
"""

import os
import sys
import json
import time
import subprocess
import sqlite3
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | server_control | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/server_control.log"
        ),
    ]
)
logger = logging.getLogger("server_control")

# ─── تعريف الخدمات ───────────────────────────────────────────
NOOGH_SERVICES = {
    "noogh-agent":     {"desc": "العقل الرئيسي",       "critical": True,  "memory_limit_mb": 15000},
    "noogh-neural":    {"desc": "محرك LLM",             "critical": True,  "memory_limit_mb": 14000},
    "noogh-gateway":   {"desc": "بوابة API",            "critical": True,  "memory_limit_mb": 4000},
    "noogh-console":   {"desc": "واجهة المستخدم",       "critical": False, "memory_limit_mb": 500},
    "noogh-autonomic": {"desc": "نظام المهام الذاتية",  "critical": False, "memory_limit_mb": 3000},
    "noogh-watchdog":  {"desc": "حارس النظام",          "critical": False, "memory_limit_mb": 500},
}

NOOGH_PROCESSES = {
    "autonomous_learner": {
        "pid_file": "/home/noogh/.noogh/autonomous_learner.pid",
        "desc": "وكيل التعلم الذاتي",
        "script": "agents/autonomous_learner_agent.py",
        "args": ["--interval", "1800"],
        "critical": False,
    }
}

DB_PATH = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
VENV_PY = "/home/noogh/projects/noogh_unified_system/src/.venv/bin/python3"
SRC     = "/home/noogh/projects/noogh_unified_system/src"


class NooghServerControl:
    """NOOGH يسيطر على السيرفر بالكامل"""

    def __init__(self):
        self._restart_counts: Dict[str, int] = {}
        self._last_alert: Dict[str, float] = {}
        logger.info("🖥️  Server Control Agent initialized")
        logger.info(f"   Services: {len(NOOGH_SERVICES)} | Processes: {len(NOOGH_PROCESSES)}")

    # ══ 1. قراءة حالة الخدمات ══════════════════════════════════
    def get_service_status(self, name: str) -> Dict:
        """حالة خدمة systemd واحدة"""
        try:
            r = subprocess.run(
                ["systemctl", "show", name,
                 "--property=ActiveState,SubState,MainPID,MemoryCurrent,CPUUsageNSec"],
                capture_output=True, text=True, timeout=5
            )
            props = {}
            for line in r.stdout.strip().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    props[k] = v

            active = props.get("ActiveState", "unknown")
            mem_bytes = int(props.get("MemoryCurrent", "0") or 0)
            cpu_ns = int(props.get("CPUUsageNSec", "0") or 0)

            return {
                "name": name,
                "active": active,
                "sub": props.get("SubState", "?"),
                "pid": props.get("MainPID", "0"),
                "memory_mb": round(mem_bytes / 1024 / 1024, 1),
                "cpu_sec": round(cpu_ns / 1e9, 1),
                "ok": active == "active",
            }
        except Exception as e:
            return {"name": name, "active": "error", "ok": False, "error": str(e)}

    def get_all_services(self) -> List[Dict]:
        return [self.get_service_status(svc) for svc in NOOGH_SERVICES]

    # ══ 2. قراءة حالة العمليات ═════════════════════════════════
    def get_process_status(self, name: str, config: Dict) -> Dict:
        """حالة عملية Python في الخلفية"""
        pid_file = config.get("pid_file", "")
        pid = None
        if pid_file and Path(pid_file).exists():
            try:
                pid = int(Path(pid_file).read_text().strip())
            except Exception:
                pass

        if pid:
            try:
                r = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "pid,pcpu,pmem,etime,comm", "--no-header"],
                    capture_output=True, text=True, timeout=3
                )
                if r.returncode == 0 and r.stdout.strip():
                    parts = r.stdout.strip().split()
                    return {
                        "name": name,
                        "pid": pid,
                        "cpu": float(parts[1]) if len(parts) > 1 else 0,
                        "mem_pct": float(parts[2]) if len(parts) > 2 else 0,
                        "uptime": parts[3] if len(parts) > 3 else "?",
                        "ok": True,
                        "desc": config["desc"],
                    }
            except Exception:
                pass

        return {"name": name, "pid": None, "ok": False, "desc": config["desc"]}

    # ══ 3. موارد النظام ════════════════════════════════════════
    def get_system_resources(self) -> Dict:
        """CPU / RAM / Disk / Network"""
        resources = {}

        # CPU
        try:
            r = subprocess.run(
                ["top", "-bn1"],
                capture_output=True, text=True, timeout=5
            )
            for line in r.stdout.split("\n"):
                if "Cpu(s)" in line or "%Cpu" in line:
                    m = __import__("re").search(r"(\d+\.?\d*)\s*us", line)
                    if m:
                        resources["cpu_user"] = float(m.group(1))
                    m = __import__("re").search(r"(\d+\.?\d*)\s*id", line)
                    if m:
                        resources["cpu_idle"] = float(m.group(1))
                        resources["cpu_used"] = round(100 - float(m.group(1)), 1)
                    break
        except Exception:
            resources["cpu_used"] = -1

        # RAM
        try:
            with open("/proc/meminfo") as f:
                mem = {}
                for line in f:
                    k, v = line.split(":", 1)
                    mem[k.strip()] = int(v.strip().split()[0])
            total = mem.get("MemTotal", 0)
            avail = mem.get("MemAvailable", 0)
            used  = total - avail
            resources["ram_total_gb"] = round(total / 1024 / 1024, 1)
            resources["ram_used_gb"]  = round(used  / 1024 / 1024, 1)
            resources["ram_pct"]      = round(used / total * 100, 1) if total else 0
        except Exception:
            resources["ram_pct"] = -1

        # Disk
        try:
            r = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True, text=True, timeout=5
            )
            for line in r.stdout.split("\n")[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        resources["disk_total"] = parts[1]
                        resources["disk_used"]  = parts[2]
                        resources["disk_avail"] = parts[3]
                        resources["disk_pct"]   = parts[4].rstrip("%")
                    break
        except Exception:
            pass

        # Uptime
        try:
            with open("/proc/uptime") as f:
                secs = float(f.read().split()[0])
            h, m = divmod(int(secs) // 60, 60)
            resources["uptime"] = f"{h}h {m}m"
        except Exception:
            resources["uptime"] = "?"

        return resources

    # ══ 4. إعادة التشغيل ════════════════════════════════════════
    def restart_service(self, name: str) -> bool:
        """إعادة تشغيل خدمة systemd"""
        try:
            r = subprocess.run(
                ["sudo", "systemctl", "restart", name],
                capture_output=True, text=True, timeout=30
            )
            ok = r.returncode == 0
            if ok:
                logger.info(f"  ✅ Restarted: {name}")
                self._inject_event(f"restart:{name}", "service_restart", True)
            else:
                logger.warning(f"  ❌ Restart failed: {name} | {r.stderr[:100]}")
            return ok
        except Exception as e:
            logger.error(f"  ❌ restart error {name}: {e}")
            return False

    def restart_process(self, name: str, config: Dict) -> bool:
        """إعادة تشغيل عملية Python"""
        # أوقف القديم
        pid_file = config.get("pid_file", "")
        if pid_file and Path(pid_file).exists():
            try:
                pid = int(Path(pid_file).read_text().strip())
                subprocess.run(["kill", str(pid)], capture_output=True, timeout=5)
                time.sleep(2)
            except Exception:
                pass

        # ابدأ الجديد
        script = config.get("script", "")
        args = config.get("args", [])
        log_file = f"{SRC}/logs/{name}.log"
        try:
            proc = subprocess.Popen(
                [VENV_PY, f"{SRC}/{script}"] + args,
                cwd=SRC,
                stdout=open(log_file, "a"),
                stderr=subprocess.STDOUT,
            )
            if pid_file:
                Path(pid_file).parent.mkdir(parents=True, exist_ok=True)
                Path(pid_file).write_text(str(proc.pid))
            logger.info(f"  ✅ Restarted process: {name} (PID={proc.pid})")
            return True
        except Exception as e:
            logger.error(f"  ❌ Process restart failed {name}: {e}")
            return False

    # ══ 5. حقن الأحداث في الذاكرة ═════════════════════════════
    def _inject_event(self, key: str, event_type: str, success: bool, detail: str = ""):
        """يحقن حدث في ذاكرة NOOGH"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            obs_key = f"server_ctrl_{key}_{int(time.time())}"
            cur.execute(
                "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
                (obs_key, json.dumps({
                    "source": "server_control_agent",
                    "type": event_type,
                    "key": key,
                    "success": success,
                    "detail": detail,
                    "ts": datetime.now().isoformat(),
                }), time.time())
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _inject_system_snapshot(self, resources: Dict, services: List[Dict]):
        """يحقن لقطة النظام الكاملة كـ belief"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "resources": resources,
                "services": {s["name"]: {"ok": s["ok"], "mem_mb": s.get("memory_mb", 0)}
                             for s in services},
                "healthy_services": sum(1 for s in services if s["ok"]),
                "total_services": len(services),
            }

            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
                ("server:system_snapshot",
                 json.dumps(snapshot, ensure_ascii=False),
                 0.95, time.time())
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ══ 6. الدورة الرئيسية ═════════════════════════════════════
    def run_once(self):
        """دورة مراقبة وتحكم واحدة"""
        now = datetime.now().strftime("%H:%M:%S")
        logger.info("═" * 58)
        logger.info(f"🖥️  SERVER CONTROL CYCLE | {now}")
        logger.info("═" * 58)

        # ① موارد النظام
        res = self.get_system_resources()
        cpu = res.get("cpu_used", "?")
        ram = res.get("ram_pct", "?")
        disk = res.get("disk_pct", "?")
        uptime = res.get("uptime", "?")
        logger.info(
            f"\n📊 الموارد:\n"
            f"   CPU: {cpu}% | RAM: {res.get('ram_used_gb','?')}/{res.get('ram_total_gb','?')} GB ({ram}%)\n"
            f"   Disk: {res.get('disk_used','?')}/{res.get('disk_total','?')} ({disk}%) | Uptime: {uptime}"
        )

        # تحذير موارد
        if isinstance(cpu, (int, float)) and cpu > 90:
            logger.warning(f"  ⚠️ CPU مرتفع جداً: {cpu}%")
            self._inject_event("cpu_high", "resource_alert", False, f"CPU={cpu}%")
        if isinstance(ram, (int, float)) and ram > 85:
            logger.warning(f"  ⚠️ RAM مرتفع جداً: {ram}%")
            self._inject_event("ram_high", "resource_alert", False, f"RAM={ram}%")

        # ② حالة خدمات systemd
        logger.info("\n🔧 خدمات NOOGH:")
        services = self.get_all_services()
        healed = 0
        for svc in services:
            name = svc["name"]
            cfg  = NOOGH_SERVICES.get(name, {})
            status_icon = "✅" if svc["ok"] else "❌"
            mem_warn = ""
            if svc.get("memory_mb", 0) > cfg.get("memory_limit_mb", 99999) * 0.9:
                mem_warn = " ⚠️MEM"
            logger.info(
                f"  {status_icon} {name} ({cfg.get('desc','')}) "
                f"| {svc.get('memory_mb',0)} MB | {svc.get('cpu_sec',0)}s CPU{mem_warn}"
            )

            # تعافٍ ذاتي للخدمات الحرجة
            if not svc["ok"] and cfg.get("critical", False):
                count = self._restart_counts.get(name, 0)
                if count < 3:
                    logger.warning(f"  🔄 إعادة تشغيل {name} (محاولة {count+1}/3)")
                    if self.restart_service(name):
                        self._restart_counts[name] = count + 1
                        healed += 1
                else:
                    logger.error(f"  🚨 {name} فشل 3 مرات! يحتاج تدخلاً يدوياً")
                    self._inject_event(f"critical_failure:{name}", "critical_failure", False)
            elif svc["ok"]:
                self._restart_counts[name] = 0  # reset

        # ③ العمليات الخلفية
        logger.info("\n⚙️  العمليات الخلفية:")
        for proc_name, proc_cfg in NOOGH_PROCESSES.items():
            status = self.get_process_status(proc_name, proc_cfg)
            if status["ok"]:
                logger.info(
                    f"  ✅ {proc_name} (PID={status['pid']}) "
                    f"| CPU={status.get('cpu',0)}% | uptime={status.get('uptime','?')}"
                )
            else:
                logger.warning(f"  ❌ {proc_name} لا يعمل")
                if proc_cfg.get("critical", False):
                    logger.info(f"  🔄 إعادة تشغيل {proc_name}")
                    self.restart_process(proc_name, proc_cfg)

        # ④ حفظ اللقطة في الذاكرة
        self._inject_system_snapshot(res, services)

        # ⑤ ملخص
        healthy = sum(1 for s in services if s["ok"])
        total   = len(services)
        logger.info(
            f"\n✅ Cycle done | Services: {healthy}/{total} | "
            f"Healed: {healed} | CPU: {cpu}% | RAM: {ram}%"
        )
        return {"healthy": healthy, "total": total, "healed": healed}

    # ══ الحلقة الرئيسية ════════════════════════════════════════
    def run_forever(self, interval: int = 300):
        """يراقب كل {interval} ثانية"""
        logger.info(f"🚀 Server Control Loop started (every {interval//60} min)")
        while True:
            try:
                self.run_once()
            except KeyboardInterrupt:
                logger.info("⛔ Stopped")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}", exc_info=True)
            logger.info(f"💤 Next check in {interval//60} min...")
            time.sleep(interval)


# ─── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NOOGH Server Control Agent")
    parser.add_argument("--once",     action="store_true", help="run once and exit")
    parser.add_argument("--interval", type=int, default=300,
                        help="check interval seconds (default: 300)")
    parser.add_argument("--status",   action="store_true", help="show status and exit")
    args = parser.parse_args()

    ctrl = NooghServerControl()

    if args.status or args.once:
        ctrl.run_once()
    else:
        ctrl.run_forever(args.interval)
