"""
NOOGH Brain Tools — الأيدي التنفيذية للعقل

يعطي العقل القدرة على:
  📖  قراءة أي ملف في النظام
  ✏️  كتابة وتعديل الملفات
  🖥️  تنفيذ أوامر Shell
  ⚙️  التحكم بخدمات systemd
  🔄  إدارة العمليات
  🗃️  استعلام وتعديل قواعد البيانات
  🔧  تعديل ملفات الإعداد (.env / .json / .yaml)
  💉  حقن المعرفة في ذاكرته
  📋  قراءة السجلات
  🌐  طلبات HTTP

كل أمر يُسجَّل ويُراجَع.
"""

import os
import re
import sys
import json
import time
import subprocess
import sqlite3
import shutil
import logging
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("brain_tools")

# ─── المسارات الأساسية ────────────────────────────────────────
SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"
VENV_PY = f"{SRC}/.venv/bin/python3"
NOOGH_HOME = "/home/noogh/.noogh"
AUDIT_LOG  = f"{SRC}/logs/brain_tool_audit.log"

# ─── سجل التدقيق ─────────────────────────────────────────────
def _audit(tool: str, args: dict, result: str, success: bool):
    """يسجل كل استخدام للأدوات"""
    entry = {
        "ts": datetime.now().isoformat(),
        "tool": tool,
        "args": {k: str(v)[:100] for k, v in args.items()},
        "success": success,
        "result_preview": str(result)[:200],
    }
    Path(AUDIT_LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.debug(f"[TOOL] {tool} → {'✅' if success else '❌'}")


# ══════════════════════════════════════════════════════════════
# 📖 أدوات القراءة
# ══════════════════════════════════════════════════════════════

def read_file(path: str, encoding: str = "utf-8", max_bytes: int = 50000) -> Dict:
    """
    يقرأ أي ملف في النظام.
    
    Args:
        path: المسار الكامل للملف
        encoding: الترميز (utf-8 افتراضي)
        max_bytes: الحد الأقصى للبايتات
    
    Returns:
        {"success": bool, "content": str, "size": int, "lines": int}
    """
    try:
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": f"الملف غير موجود: {path}"}
        size = p.stat().st_size
        with open(path, encoding=encoding, errors="ignore") as f:
            content = f.read(max_bytes)
        result = {
            "success": True,
            "path": str(path),
            "content": content,
            "size_bytes": size,
            "lines": content.count("\n") + 1,
            "truncated": size > max_bytes,
        }
        _audit("read_file", {"path": path}, f"{size} bytes", True)
        return result
    except Exception as e:
        _audit("read_file", {"path": path}, str(e), False)
        return {"success": False, "error": str(e)}


def write_file(path: str, content: str, mode: str = "w", backup: bool = True) -> Dict:
    """
    يكتب إلى أي ملف. ينشئ المجلدات تلقائياً.
    Security: يتحقق من المسار قبل الكتابة.
    
    Args:
        path: المسار الكامل
        content: المحتوى المراد كتابته
        mode: "w" للكتابة الكاملة، "a" للإضافة
        backup: ينشئ نسخة احتياطية قبل التعديل
    
    Returns:
        {"success": bool, "bytes_written": int, "backup_path": str}
    """
    try:
        # 🛡️ Path validation
        try:
            from unified_core.integration.security_hardening import get_command_validator
            validator = get_command_validator()
            allowed, reason = validator.validate_write_path(path)
            if not allowed:
                _audit("write_file", {"path": path}, f"BLOCKED: {reason}", False)
                return {"success": False, "blocked": True, "error": f"🛡️ حظر الكتابة: {reason}"}
        except ImportError:
            pass

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        backup_path = None

        if backup and p.exists() and p.stat().st_size > 0:
            backup_path = f"{path}.bak_{int(time.time())}"
            shutil.copy2(path, backup_path)

        with open(path, mode, encoding="utf-8") as f:
            f.write(content)

        result = {
            "success": True,
            "path": str(path),
            "bytes_written": len(content.encode("utf-8")),
            "backup_path": backup_path,
        }
        _audit("write_file", {"path": path, "mode": mode}, f"{len(content)} chars", True)
        return result
    except Exception as e:
        _audit("write_file", {"path": path}, str(e), False)
        return {"success": False, "error": str(e)}


def list_directory(path: str, pattern: str = "*", recursive: bool = False) -> Dict:
    """
    يعرض محتويات مجلد.
    
    Args:
        path: مسار المجلد
        pattern: نمط البحث (مثل "*.py")
        recursive: البحث في المجلدات الفرعية
    
    Returns:
        {"success": bool, "items": list, "count": int}
    """
    try:
        p = Path(path)
        if not p.exists():
            return {"success": False, "error": f"المجلد غير موجود: {path}"}

        if recursive:
            items_raw = list(p.rglob(pattern))
        else:
            items_raw = list(p.glob(pattern))

        items = []
        for item in sorted(items_raw)[:500]:
            try:
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "dir" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except Exception:
                items.append({"name": item.name, "path": str(item), "type": "unknown"})

        result = {"success": True, "path": str(path), "items": items, "count": len(items)}
        _audit("list_dir", {"path": path, "pattern": pattern}, f"{len(items)} items", True)
        return result
    except Exception as e:
        _audit("list_dir", {"path": path}, str(e), False)
        return {"success": False, "error": str(e)}


def search_in_files(directory: str, query: str, ext: str = ".py",
                    case_sensitive: bool = False, max_results: int = 50) -> Dict:
    """
    يبحث عن نص داخل الملفات.
    
    Returns:
        {"success": bool, "matches": [{"file": str, "line": int, "content": str}]}
    """
    try:
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(query, flags)
        
        for fp in Path(directory).rglob(f"*{ext}"):
            if ".venv" in str(fp) or "__pycache__" in str(fp):
                continue
            try:
                for i, line in enumerate(fp.read_text(errors="ignore").split("\n"), 1):
                    if pattern.search(line):
                        matches.append({
                            "file": str(fp),
                            "line": i,
                            "content": line.strip()[:120],
                        })
                        if len(matches) >= max_results:
                            break
            except Exception:
                pass
            if len(matches) >= max_results:
                break

        result = {"success": True, "matches": matches, "total": len(matches)}
        _audit("search_files", {"dir": directory, "query": query}, f"{len(matches)} matches", True)
        return result
    except Exception as e:
        _audit("search_files", {"dir": directory, "query": query}, str(e), False)
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
# 🖥️  تنفيذ الأوامر
# ══════════════════════════════════════════════════════════════

def execute_command(cmd: str, cwd: str = SRC, timeout: int = 30,
                    capture: bool = True, force: bool = False) -> Dict:
    """
    ينفذ أمر Shell مع تحقق أمني.
    
    Args:
        cmd: الأمر (مثل "ls -la" أو "systemctl status noogh-agent")
        cwd: مجلد التنفيذ
        timeout: مهلة الانتظار بالثواني
        capture: التقاط الإخراج
        force: تجاوز whitelist (لا يتجاوز blacklist)
    
    Returns:
        {"success": bool, "stdout": str, "stderr": str, "exit_code": int}
    """
    # 🛡️ Command validation
    try:
        from unified_core.integration.security_hardening import get_command_validator
        validator = get_command_validator()
        allowed, reason = validator.validate_shell_cmd(cmd)
        if not allowed:
            if reason.startswith("Dangerous pattern"):
                # Blacklist — never override
                _audit("execute_cmd", {"cmd": cmd[:100]}, f"BLOCKED: {reason}", False)
                return {"success": False, "blocked": True, "error": f"🛡️ أمر محظور: {reason}", "command": cmd}
            elif not force:
                # Whitelist miss — can override with force=True
                _audit("execute_cmd", {"cmd": cmd[:100]}, f"BLOCKED(whitelist): {reason}", False)
                return {"success": False, "blocked": True, "error": f"🛡️ أمر غير معروف: {reason}", "command": cmd}
    except ImportError:
        pass

    try:
        r = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=capture, text=True,
            timeout=timeout
        )
        result = {
            "success": r.returncode == 0,
            "stdout": r.stdout[:5000] if r.stdout else "",
            "stderr": r.stderr[:1000] if r.stderr else "",
            "exit_code": r.returncode,
            "command": cmd,
        }
        _audit("execute_cmd", {"cmd": cmd[:100]}, f"exit={r.returncode}", r.returncode == 0)
        return result
    except subprocess.TimeoutExpired:
        _audit("execute_cmd", {"cmd": cmd[:100]}, "TIMEOUT", False)
        return {"success": False, "error": f"انتهت المهلة ({timeout}s)", "command": cmd}
    except Exception as e:
        _audit("execute_cmd", {"cmd": cmd[:100]}, str(e), False)
        return {"success": False, "error": str(e), "command": cmd}


def execute_python(code: str, timeout: int = 30) -> Dict:
    """
    ينفذ كود Python مباشرة مع تحقق أمني.
    
    Returns:
        {"success": bool, "output": str, "error": str}
    """
    import tempfile, traceback

    # 🛡️ Python code validation
    try:
        from unified_core.integration.security_hardening import get_command_validator
        validator = get_command_validator()
        allowed, reason = validator.validate_python_code(code)
        if not allowed:
            _audit("exec_python", {"code_len": len(code)}, f"BLOCKED: {reason}", False)
            return {"success": False, "blocked": True, "error": f"🛡️ كود محظور: {reason}"}
    except ImportError:
        pass

    try:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, dir="/tmp") as f:
            f.write(f"import sys; sys.path.insert(0, '{SRC}')\n")
            f.write(code)
            tmp = f.name
        r = subprocess.run(
            [VENV_PY, tmp],
            capture_output=True, text=True, timeout=timeout, cwd=SRC
        )
        os.unlink(tmp)
        result = {
            "success": r.returncode == 0,
            "output": r.stdout[:3000],
            "error": r.stderr[:1000],
            "exit_code": r.returncode,
        }
        _audit("exec_python", {"code_len": len(code)}, f"exit={r.returncode}", r.returncode == 0)
        return result
    except Exception as e:
        _audit("exec_python", {"code_len": len(code)}, str(e), False)
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
# ⚙️  التحكم بالخدمات
# ══════════════════════════════════════════════════════════════

def service_control(name: str, action: str) -> Dict:
    """
    يتحكم بخدمة systemd.
    
    Args:
        name: اسم الخدمة (مثل "noogh-agent")
        action: "start" | "stop" | "restart" | "status" | "enable" | "disable"
    
    Returns:
        {"success": bool, "output": str, "status": str}
    """
    ALLOWED = {"start", "stop", "restart", "status", "enable", "disable", "reload"}
    if action not in ALLOWED:
        return {"success": False, "error": f"أمر غير مسموح: {action}. المسموح: {ALLOWED}"}

    try:
        import os as _os
        env = _os.environ.copy()

        # نحاول بدون sudo أولاً (للقراءة)
        r = subprocess.run(
            f"systemctl {action} {name}",
            shell=True, capture_output=True, text=True, timeout=15, env=env
        )

        # إذا فشل نستخدم askpass
        if r.returncode != 0:
            pwd = _os.environ.get("NOOGH_SUDO_PASS", "")
            if pwd:
                r = subprocess.run(
                    f"echo '{pwd}' | sudo -S systemctl {action} {name}",
                    shell=True, capture_output=True, text=True, timeout=20
                )

        if action == "status":
            status_r = subprocess.run(
                f"systemctl show {name} --property=ActiveState,SubState,MainPID,MemoryCurrent",
                shell=True, capture_output=True, text=True, timeout=5
            )
            props = {}
            for line in status_r.stdout.strip().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    props[k] = v
        else:
            props = {}

        result = {
            "success": r.returncode == 0,
            "service": name,
            "action": action,
            "output": r.stdout[:1000] or r.stderr[:500],
            "active": props.get("ActiveState", "?"),
            "pid": props.get("MainPID", "?"),
        }
        _audit("service_ctrl", {"name": name, "action": action}, result["active"], result["success"])
        return result
    except Exception as e:
        _audit("service_ctrl", {"name": name, "action": action}, str(e), False)
        return {"success": False, "error": str(e)}


def get_all_services_status() -> Dict:
    """يجلب حالة جميع خدمات NOOGH دفعة واحدة"""
    services = ["noogh-agent", "noogh-neural", "noogh-gateway",
                "noogh-console", "noogh-autonomic", "noogh-watchdog"]
    return {
        "success": True,
        "services": {svc: service_control(svc, "status") for svc in services}
    }


# ══════════════════════════════════════════════════════════════
# 🗃️  قاعدة البيانات
# ══════════════════════════════════════════════════════════════

def db_query(sql: str, params: tuple = (), db: str = DB_PATH) -> Dict:
    """
    ينفذ استعلام SQL على ذاكرة NOOGH.
    
    Args:
        sql: استعلام SQL
        params: المعاملات
        db: مسار قاعدة البيانات
    
    Returns:
        {"success": bool, "rows": list, "count": int}
    """
    try:
        conn = sqlite3.connect(db, timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        
        if sql.strip().upper().startswith("SELECT"):
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            result = {"success": True, "rows": rows, "count": len(rows)}
        else:
            conn.commit()
            affected = cur.rowcount
            conn.close()
            result = {"success": True, "rows": [], "affected_rows": affected}

        _audit("db_query", {"sql": sql[:80]}, f"{result.get('count', result.get('affected_rows', 0))} rows", True)
        return result
    except Exception as e:
        _audit("db_query", {"sql": sql[:80]}, str(e), False)
        return {"success": False, "error": str(e)}


def db_inject_belief(key: str, value: Any, utility: float = 0.8) -> Dict:
    """
    يحقن أو يحدث belief في ذاكرة NOOGH.
    
    Returns:
        {"success": bool}
    """
    return db_query(
        "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
        (key, json.dumps(value, ensure_ascii=False, default=str), utility, time.time())
    )


def db_inject_observation(key: str, data: Dict) -> Dict:
    """يحقن observation في ذاكرة NOOGH"""
    return db_query(
        "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
        (key, json.dumps(data, ensure_ascii=False, default=str), time.time())
    )


def db_get_beliefs(pattern: str = "%", limit: int = 50) -> Dict:
    """يجلب beliefs من الذاكرة"""
    return db_query(
        "SELECT key, value, utility_score, updated_at FROM beliefs WHERE key LIKE ? ORDER BY utility_score DESC LIMIT ?",
        (pattern, limit)
    )


# ══════════════════════════════════════════════════════════════
# 🔧 تعديل الإعدادات
# ══════════════════════════════════════════════════════════════

def read_config(path: str) -> Dict:
    """
    يقرأ ملف إعداد (JSON / YAML / .env / INI).
    يُحلل المحتوى تلقائياً.
    """
    try:
        content = Path(path).read_text(encoding="utf-8", errors="ignore")
        parsed = None
        ext = Path(path).suffix.lower()

        if ext == ".json":
            parsed = json.loads(content)
        elif ext in (".yaml", ".yml"):
            try:
                import yaml
                parsed = yaml.safe_load(content)
            except ImportError:
                parsed = {"raw": content}
        elif ext == ".env" or path.endswith(".env"):
            parsed = {}
            for line in content.split("\n"):
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    parsed[k.strip()] = v.strip()
        else:
            parsed = {"raw": content}

        _audit("read_config", {"path": path}, f"parsed {ext}", True)
        return {"success": True, "path": path, "format": ext, "content": content, "parsed": parsed}
    except Exception as e:
        _audit("read_config", {"path": path}, str(e), False)
        return {"success": False, "error": str(e)}


def update_env_var(key: str, value: str, env_file: str = f"{SRC}/.env") -> Dict:
    """
    يضيف أو يحدث متغير في ملف .env.
    
    Args:
        key: اسم المتغير
        value: القيمة الجديدة
        env_file: مسار الملف
    
    Returns:
        {"success": bool, "action": "updated"|"added"}
    """
    try:
        p = Path(env_file)
        content = p.read_text(errors="ignore") if p.exists() else ""
        lines = content.split("\n")

        pattern = re.compile(rf"^{re.escape(key)}\s*=", re.MULTILINE)
        found = False
        new_lines = []
        for line in lines:
            if re.match(rf"^{re.escape(key)}\s*=", line):
                new_lines.append(f"{key}={value}")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{key}={value}")

        # نسخة احتياطية
        if p.exists():
            shutil.copy2(env_file, f"{env_file}.bak_{int(time.time())}")

        p.write_text("\n".join(new_lines), encoding="utf-8")
        action = "updated" if found else "added"
        _audit("update_env", {"key": key, "file": env_file}, action, True)
        return {"success": True, "action": action, "key": key}
    except Exception as e:
        _audit("update_env", {"key": key}, str(e), False)
        return {"success": False, "error": str(e)}


def update_json_config(path: str, updates: Dict) -> Dict:
    """
    يحدث مفاتيح في ملف JSON.
    
    Args:
        path: مسار ملف JSON
        updates: القاموس بالتحديثات {"key": value, "nested.key": value}
    
    Returns:
        {"success": bool, "changed_keys": list}
    """
    try:
        p = Path(path)
        data = json.loads(p.read_text()) if p.exists() else {}

        # نسخة احتياطية
        shutil.copy2(path, f"{path}.bak_{int(time.time())}")

        changed = []
        for dotted_key, value in updates.items():
            keys = dotted_key.split(".")
            obj = data
            for k in keys[:-1]:
                obj = obj.setdefault(k, {})
            obj[keys[-1]] = value
            changed.append(dotted_key)

        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        _audit("update_json", {"path": path, "keys": str(changed)[:80]}, "ok", True)
        return {"success": True, "changed_keys": changed}
    except Exception as e:
        _audit("update_json", {"path": path}, str(e), False)
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
# 📋 السجلات
# ══════════════════════════════════════════════════════════════

def read_logs(service_or_file: str = "noogh-agent", lines: int = 50,
              filter_level: str = "") -> Dict:
    """
    يقرأ سجلات خدمة أو ملف.
    
    Args:
        service_or_file: اسم خدمة systemd أو مسار ملف log
        lines: عدد الأسطر
        filter_level: "ERROR" | "WARNING" | "" للكل
    
    Returns:
        {"success": bool, "entries": list, "errors_count": int}
    """
    try:
        raw = ""
        # ملف مباشر
        if "/" in service_or_file or service_or_file.endswith(".log"):
            if Path(service_or_file).exists():
                all_lines = Path(service_or_file).read_text(errors="ignore").split("\n")
                raw = "\n".join(all_lines[-lines:])
            else:
                # ابحث في مجلد logs
                potential = Path(f"{SRC}/logs/{service_or_file}")
                if potential.exists():
                    all_lines = potential.read_text(errors="ignore").split("\n")
                    raw = "\n".join(all_lines[-lines:])
        else:
            # journalctl
            r = subprocess.run(
                f"journalctl -u {service_or_file} -n {lines} --no-pager 2>/dev/null",
                shell=True, capture_output=True, text=True, timeout=10
            )
            raw = r.stdout

        entries = [l for l in raw.split("\n") if l.strip()]
        if filter_level:
            entries = [l for l in entries if filter_level.upper() in l]

        errors = [l for l in entries if "ERROR" in l or "CRITICAL" in l]
        result = {
            "success": True,
            "source": service_or_file,
            "entries": entries[-lines:],
            "count": len(entries),
            "errors_count": len(errors),
            "recent_errors": errors[-5:],
        }
        _audit("read_logs", {"source": service_or_file, "lines": lines}, f"{len(entries)} entries", True)
        return result
    except Exception as e:
        _audit("read_logs", {"source": service_or_file}, str(e), False)
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
# 🌐 طلبات HTTP
# ══════════════════════════════════════════════════════════════

def http_get(url: str, headers: Dict = None, timeout: int = 10) -> Dict:
    """
    يُرسل طلب GET.
    
    Returns:
        {"success": bool, "status": int, "content": str}
    """
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent": "NOOGH/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            content = r.read().decode("utf-8", errors="ignore")[:10000]
        result = {
            "success": True, "url": url,
            "status": r.status, "content": content,
            "content_type": r.headers.get("Content-Type", "?"),
        }
        _audit("http_get", {"url": url[:80]}, f"HTTP {r.status}", True)
        return result
    except Exception as e:
        _audit("http_get", {"url": url[:80]}, str(e), False)
        return {"success": False, "error": str(e), "url": url}


def http_post(url: str, data: Dict, headers: Dict = None, timeout: int = 15) -> Dict:
    """يُرسل طلب POST بـ JSON"""
    try:
        body = json.dumps(data).encode("utf-8")
        h = {"Content-Type": "application/json", "User-Agent": "NOOGH/1.0"}
        h.update(headers or {})
        req = urllib.request.Request(url, data=body, headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            content = r.read().decode("utf-8", errors="ignore")[:5000]
        result = {
            "success": True, "url": url,
            "status": r.status, "content": content,
        }
        _audit("http_post", {"url": url[:80]}, f"HTTP {r.status}", True)
        return result
    except Exception as e:
        _audit("http_post", {"url": url[:80]}, str(e), False)
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
# 🔄 إدارة العمليات
# ══════════════════════════════════════════════════════════════

def process_list(filter_name: str = "") -> Dict:
    """يجلب قائمة العمليات الجارية"""
    r = execute_command(f"ps aux --sort=-%mem | {'grep ' + filter_name + ' |' if filter_name else ''} head -30")
    return {"success": r["success"], "output": r["stdout"]}


def process_kill(pid: int, signal: str = "15") -> Dict:
    """
    يوقف عملية مع تحقق أمني.
    
    Args:
        pid: رقم العملية
        signal: 15=SIGTERM (ناعم), 9=SIGKILL (قسري)
    
    Returns:
        {"success": bool}
    """
    # 🛡️ PID validation
    try:
        from unified_core.integration.security_hardening import get_command_validator
        validator = get_command_validator()
        allowed, reason = validator.validate_pid(pid)
        if not allowed:
            _audit("process_kill", {"pid": pid, "signal": signal}, f"BLOCKED: {reason}", False)
            return {"success": False, "blocked": True, "error": f"🛡️ PID محمي: {reason}"}
    except ImportError:
        pass

    result = execute_command(f"kill -{signal} {pid}", timeout=10, force=True)
    _audit("process_kill", {"pid": pid, "signal": signal}, "ok" if result["success"] else "fail", result["success"])
    return result


def process_start(script: str, args: List[str] = None, log_file: str = None) -> Dict:
    """
    يُشغّل عملية Python في الخلفية.
    
    Returns:
        {"success": bool, "pid": int}
    """
    try:
        cmd = [VENV_PY, script] + (args or [])
        log = open(log_file or "/tmp/noogh_proc.log", "a")
        proc = subprocess.Popen(cmd, cwd=SRC, stdout=log, stderr=log)
        result = {"success": True, "pid": proc.pid, "script": script}
        _audit("process_start", {"script": script}, f"PID={proc.pid}", True)
        return result
    except Exception as e:
        _audit("process_start", {"script": script}, str(e), False)
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
# 📊 لوحة الأدوات — قائمة كاملة
# ══════════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    # قراءة
    "read_file":         {"fn": read_file,         "desc": "يقرأ أي ملف"},
    "write_file":        {"fn": write_file,         "desc": "يكتب إلى ملف"},
    "list_directory":    {"fn": list_directory,     "desc": "يعرض محتوى مجلد"},
    "search_in_files":   {"fn": search_in_files,    "desc": "يبحث داخل الملفات"},
    # تنفيذ
    "execute_command":   {"fn": execute_command,    "desc": "ينفذ أمر shell"},
    "execute_python":    {"fn": execute_python,     "desc": "ينفذ كود Python"},
    # خدمات
    "service_control":   {"fn": service_control,    "desc": "يتحكم بخدمة systemd"},
    "get_all_services":  {"fn": get_all_services_status, "desc": "حالة كل الخدمات"},
    # قاعدة البيانات
    "db_query":          {"fn": db_query,           "desc": "استعلام SQL"},
    "db_inject_belief":  {"fn": db_inject_belief,   "desc": "يحقن belief"},
    "db_inject_obs":     {"fn": db_inject_observation, "desc": "يحقن observation"},
    "db_get_beliefs":    {"fn": db_get_beliefs,     "desc": "يجلب beliefs"},
    # إعدادات
    "read_config":       {"fn": read_config,        "desc": "يقرأ ملف إعداد"},
    "update_env_var":    {"fn": update_env_var,     "desc": "يحدث متغير .env"},
    "update_json":       {"fn": update_json_config, "desc": "يحدث ملف JSON"},
    # سجلات
    "read_logs":         {"fn": read_logs,          "desc": "يقرأ السجلات"},
    # شبكة
    "http_get":          {"fn": http_get,           "desc": "طلب HTTP GET"},
    "http_post":         {"fn": http_post,          "desc": "طلب HTTP POST"},
    # عمليات
    "process_list":      {"fn": process_list,       "desc": "يعرض العمليات"},
    "process_kill":      {"fn": process_kill,       "desc": "يوقف عملية"},
    "process_start":     {"fn": process_start,      "desc": "يُشغّل عملية"},
}


def use_tool(tool_name: str, **kwargs) -> Dict:
    """
    الواجهة الموحدة لاستخدام أي أداة.
    
    Args:
        tool_name: اسم الأداة من TOOL_REGISTRY
        **kwargs: معاملات الأداة
    
    Returns:
        نتيجة الأداة
    
    Example:
        result = use_tool("read_file", path="/etc/os-release")
        result = use_tool("execute_command", cmd="df -h")
        result = use_tool("service_control", name="noogh-agent", action="status")
        result = use_tool("db_inject_belief", key="test", value={"x":1}, utility=0.9)
    """
    if tool_name not in TOOL_REGISTRY:
        available = list(TOOL_REGISTRY.keys())
        return {"success": False, "error": f"أداة غير موجودة: {tool_name}", "available": available}

    fn = TOOL_REGISTRY[tool_name]["fn"]
    try:
        return fn(**kwargs)
    except TypeError as e:
        return {"success": False, "error": f"معاملات خاطئة: {e}"}


def list_tools() -> List[Dict]:
    """يعرض قائمة الأدوات المتاحة"""
    return [
        {"name": k, "description": v["desc"], "function": v["fn"].__name__}
        for k, v in TOOL_REGISTRY.items()
    ]


# ══════════════════════════════════════════════════════════════
# اختبار مباشر عند التشغيل
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 60)
    print("🧠 NOOGH Brain Tools — اختبار شامل")
    print("═" * 60)

    tests = [
        ("read_file",       {"path": f"{SRC}/.env"}),
        ("execute_command", {"cmd": "uname -a"}),
        ("service_control", {"name": "noogh-agent", "action": "status"}),
        ("db_get_beliefs",  {"pattern": "learned_concept:%", "limit": 5}),
        ("read_logs",       {"service_or_file": "autonomous_learner.log", "lines": 5}),
        ("list_directory",  {"path": f"{SRC}/agents", "pattern": "*.py"}),
    ]

    for tool, args in tests:
        print(f"\n{'─'*50}")
        print(f"🔧 {tool}({', '.join(f'{k}={str(v)[:30]}' for k,v in args.items())})")
        r = use_tool(tool, **args)
        if r.get("success"):
            # عرض مختصر
            if "content" in r:
                print(f"  ✅ {len(r['content'])} chars")
            elif "rows" in r:
                print(f"  ✅ {len(r['rows'])} rows")
                for row in r["rows"][:3]:
                    print(f"     {str(row)[:80]}")
            elif "entries" in r:
                print(f"  ✅ {r['count']} entries | {r['errors_count']} errors")
                for e in r["entries"][-2:]:
                    print(f"     {e[:80]}")
            elif "items" in r:
                print(f"  ✅ {r['count']} items")
                for i in r["items"][:4]:
                    print(f"     {i['name']}")
            elif "stdout" in r:
                print(f"  ✅ {r['stdout'][:150]}")
            elif "active" in r:
                print(f"  ✅ {r.get('service')} = {r.get('active')}")
            else:
                print(f"  ✅ {str(r)[:150]}")
        else:
            print(f"  ❌ {r.get('error','?')}")

    print(f"\n{'═'*60}")
    print(f"✅ {len(TOOL_REGISTRY)} أداة متاحة للعقل")
    print("\n📋 الأدوات المتاحة:")
    for t in list_tools():
        print(f"  • {t['name']:<25} — {t['description']}")
