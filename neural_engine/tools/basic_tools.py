"""
Basic tools for NOOGH - Implements core functionality expected by trained model
Enhanced with comprehensive system interrogation tools
"""

import subprocess
import shlex
import os
import json
import psutil
import platform
import socket
from typing import Dict, Any
from datetime import datetime, timedelta

# SECURITY: Allowed base directories for file operations
_ALLOWED_BASES = ("/home/noogh/", "/tmp/noogh_", "/tmp/")

def _validate_path(path: str) -> str:
    """Resolve and validate a file path against allowed base directories."""
    resolved = os.path.realpath(os.path.expanduser(path))
    if not any(resolved.startswith(base) for base in _ALLOWED_BASES):
        raise PermissionError(f"Path outside allowed directories: {resolved}")
    return resolved

# ============================================================================
# FILE TOOLS
# ============================================================================

def read_file(path: str) -> str:
    """Read file contents (with path validation)"""
    try:
        # SECURITY: Validate path against allowed directories
        safe_path = _validate_path(path)
        
        if not os.path.exists(safe_path):
            return f"❌ Error: File not found: {path}"
        
        if not os.path.isfile(safe_path):
            return f"❌ Error: Not a file: {path}"
        
        with open(safe_path, 'r') as f:
            content = f.read()
        
        return f"✅ File: {safe_path}\n\n{content}"
    
    except PermissionError:
        return f"❌ Error: Permission denied: {path}"
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"


def write_file(path: str, content: str) -> str:
    """Write content to file (with path validation)"""
    try:
        # SECURITY: Validate path against allowed directories
        safe_path = _validate_path(path)
        
        directory = os.path.dirname(safe_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(safe_path, 'w') as f:
            f.write(content)
        
        return f"✅ Written {len(content)} bytes to {safe_path}"
    
    except PermissionError:
        return f"❌ Error: Permission denied: {path}"
    except Exception as e:
        return f"❌ Error writing file: {str(e)}"


def find_file(filename: str) -> str:
    """Find a file by name and return its path"""
    try:
        if not filename:
            return "❌ يجب تحديد اسم الملف"
        
        # Search in project directory
        project_root = "/home/noogh/projects/noogh_unified_system/src"
        found_files = []
        
        for root, dirs, files in os.walk(project_root):
            # Skip hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if filename in file:
                    full_path = os.path.join(root, file)
                    found_files.append(full_path)
        
        if not found_files:
            return f"❌ لم يتم العثور على ملف: {filename}"
        
        result = [f"### 🔍 نتائج البحث عن: {filename}\n"]
        for i, path in enumerate(found_files[:10], 1):  # Limit to 10 results
            result.append(f"{i}. `{path}`")
        
        if len(found_files) > 10:
            result.append(f"\n... و {len(found_files) - 10} ملفات أخرى")
        
        return "\n".join(result)
    
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def analyze_file(filename: str) -> str:
    """Analyze a file: find it, show path, count lines/functions/classes"""
    import re
    
    try:
        if not filename:
            return "❌ يجب تحديد اسم الملف"
        
        # First find the file
        project_root = "/home/noogh/projects/noogh_unified_system/src"
        found_path = None
        
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for file in files:
                if file == filename or filename in file:
                    found_path = os.path.join(root, file)
                    break
            if found_path:
                break
        
        if not found_path:
            return f"❌ لم يتم العثور على ملف: {filename}"
        
        # Read and analyze
        with open(found_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Count functions and classes (for Python files)
        functions = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
        classes = re.findall(r'^class\s+(\w+)\s*[:\(]', content, re.MULTILINE)
        
        # Get file size
        file_size = os.path.getsize(found_path)
        
        result = f"""### 📊 تحليل الملف

**المسار:** `{found_path}`

**الإحصائيات:**
- 📝 عدد الأسطر: {len(lines)}
- 📦 الحجم: {file_size:,} بايت ({file_size / 1024:.1f} KB)
- 🔧 عدد الدوال: {len(functions)}
- 🏗️ عدد الكلاسات: {len(classes)}
"""
        
        if classes:
            result += f"\n**الكلاسات:** {', '.join(classes[:5])}"
            if len(classes) > 5:
                result += f" ... (+{len(classes) - 5})"
        
        if functions:
            result += f"\n**الدوال الرئيسية:** {', '.join(functions[:8])}"
            if len(functions) > 8:
                result += f" ... (+{len(functions) - 8})"
        
        return result
    
    except UnicodeDecodeError:
        return f"❌ الملف ليس نصياً: {filename}"
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


# ============================================================================
# COMMAND EXECUTION
# ============================================================================

def execute_command(command: str) -> str:
    """Execute shell command"""
    try:
        dangerous_commands = ['rm -rf /', 'dd if=', 'mkfs', ':(){:|:&};:']
        if any(danger in command for danger in dangerous_commands):
            return f"❌ Security: Dangerous command blocked"
        
        # Fix: Force C.UTF-8 locale to prevent Arabic encoding corruption
        import os
        env = os.environ.copy()
        env['LC_ALL'] = 'C.UTF-8'
        env['LANG'] = 'C.UTF-8'
        
        # SECURITY FIX (HIGH-06): shell=False prevents command injection
        result = subprocess.run(
            shlex.split(command),
            shell=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=env  # Use clean UTF-8 environment
        )
        
        output = result.stdout if result.stdout else result.stderr
        if not output:
            output = f"✅ Command completed (no output)"
        
        return f"Command: {command}\n\n{output}"
    
    except subprocess.TimeoutExpired:
        return f"❌ Error: Command timeout (30s limit)"
    except Exception as e:
        return f"❌ Error executing command: {str(e)}"


# ============================================================================
# SYSTEM MONITORING TOOLS
# ============================================================================

def get_system_status() -> str:
    """Comprehensive system status check"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # CPU status
        cpu_status = "🟢" if cpu_percent < 60 else "🟡" if cpu_percent < 85 else "�"
        mem_status = "🟢" if memory.percent < 70 else "🟡" if memory.percent < 85 else "🔴"
        disk_status = "🟢" if disk.percent < 75 else "🟡" if disk.percent < 90 else "🔴"
        
        result = f"""### 🖥️ حالة النظام

**المعالج (CPU):** {cpu_status} `{cpu_percent}%`
**الذاكرة (RAM):** {mem_status} `{memory.percent}%` ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)
**القرص:** {disk_status} `{disk.percent}%` ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)

**معلومات إضافية:**
- النظام: {platform.system()} {platform.release()}
- الجهاز: {socket.gethostname()}
"""
        
        # Uptime
        boot_time = psutil.boot_time()
        uptime = datetime.now().timestamp() - boot_time
        uptime_str = str(timedelta(seconds=uptime)).split('.')[0]
        result += f"- وقت التشغيل: {uptime_str}\n"
        
        # Load average
        if hasattr(os, 'getloadavg'):
            load1, load5, load15 = os.getloadavg()
            result += f"- متوسط الحمل: {load1:.2f}, {load5:.2f}, {load15:.2f}\n"
        
        # GPU
        try:
            import torch
            if torch.cuda.is_available():
                gpu_mem = torch.cuda.memory_allocated() / 1024**3
                gpu_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                result += f"- GPU: {gpu_mem:.1f}GB / {gpu_total:.1f}GB\n"
        except:
            pass
        
        return result
    
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def get_top_processes(limit: int = 10, sort_by: str = "memory") -> str:
    """Get top processes by resource usage"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if sort_by == "cpu":
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        else:
            processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
        
        result = [f"### 📊 أعلى {limit} عمليات\n"]
        result.append(f"| PID | الاسم | CPU% | Mem% |")
        result.append(f"|-----|-------|------|------|")
        
        for proc in processes[:limit]:
            pid = proc['pid']
            name = (proc['name'] or "N/A")[:15]
            cpu = proc['cpu_percent'] or 0
            mem = proc['memory_percent'] or 0
            result.append(f"| {pid} | {name} | {cpu:.1f}% | {mem:.1f}% |")
        
        return "\n".join(result)
    
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def check_disk_usage(directory: str = "/") -> str:
    """Check disk usage"""
    try:
        if not os.path.exists(directory):
            return f"❌ المسار غير موجود: {directory}"
        
        usage = psutil.disk_usage(directory)
        status = "🟢" if usage.percent < 75 else "🟡" if usage.percent < 90 else "🔴"
        
        return f"""### 💿 استخدام القرص: {directory}

{status} **النسبة:** `{usage.percent}%`
- الإجمالي: {usage.total / (1024**3):.1f} GB
- المستخدم: {usage.used / (1024**3):.1f} GB
- المتاح: {usage.free / (1024**3):.1f} GB
"""
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def get_network_info() -> str:
    """Get network information"""
    try:
        result = ["### 🌐 معلومات الشبكة\n"]
        
        addrs = psutil.net_if_addrs()
        for interface, addr_list in addrs.items():
            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    result.append(f"**{interface}:** `{addr.address}`")
        
        net_io = psutil.net_io_counters()
        result.append(f"\n**الإحصائيات:**")
        result.append(f"- إرسال: {net_io.bytes_sent / (1024**3):.2f} GB")
        result.append(f"- استقبال: {net_io.bytes_recv / (1024**3):.2f} GB")
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def get_system_uptime() -> str:
    """Get system uptime"""
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time
        
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        
        boot_dt = datetime.fromtimestamp(boot_time)
        
        result = f"""### ⏱️ وقت التشغيل

**تاريخ التشغيل:** {boot_dt.strftime('%Y-%m-%d %H:%M:%S')}
**المدة:** {int(days)} يوم, {int(hours)} ساعة, {int(minutes)} دقيقة
"""
        
        if hasattr(os, 'getloadavg'):
            load1, load5, load15 = os.getloadavg()
            result += f"\n**متوسط الحمل:** {load1:.2f}, {load5:.2f}, {load15:.2f}"
        
        return result
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


# ============================================================================
# USER MANAGEMENT TOOLS
# ============================================================================

def get_active_users() -> str:
    """Get active users"""
    try:
        result = ["### 👥 المستخدمون النشطون\n"]
        
        cmd = "who"
        output = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
        if output:
            result.append(f"```\n{output}\n```")
        else:
            result.append("لا يوجد مستخدمون نشطون")
        
        cmd = "last -5"
        output = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
        result.append(f"\n**آخر عمليات الدخول:**\n```\n{output}\n```")
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def check_user_permissions(username: str = None) -> str:
    """Check user permissions"""
    try:
        if username is None:
            username = os.getenv('USER') or os.getenv('LOGNAME')
        
        result = [f"### 🔐 صلاحيات: {username}\n"]
        
        cmd = f"groups {username}"
        groups = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
        result.append(f"**المجموعات:** {groups}")
        
        cmd = f"id {username}"
        user_id = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
        result.append(f"\n**المعرف:** `{user_id}`")
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


# ============================================================================
# BACKUP TOOLS
# ============================================================================

def check_backup_status() -> str:
    """Check backup status"""
    try:
        result = ["### 💾 حالة النسخ الاحتياطي\n"]
        
        backup_locations = ["/backup", "/var/backups", f"/home/{os.getenv('USER')}/backup"]
        found = False
        
        for location in backup_locations:
            if os.path.exists(location):
                found = True
                try:
                    cmd = f"du -sh '{location}' 2>/dev/null"
                    size = subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
                    result.append(f"📁 **{location}:** {size.split()[0]}")
                except:
                    result.append(f"📁 **{location}:** موجود")
        
        if not found:
            result.append("⚠️ **لا توجد مجلدات نسخ احتياطي**")
            result.append("\n**للإنشاء:**")
            result.append("```bash")
            result.append("sudo mkdir -p /backup")
            result.append("tar -czvf /backup/backup_$(date +%Y%m%d).tar.gz /path/to/data")
            result.append("```")
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


# ============================================================================
# SECURITY TOOLS
# ============================================================================

def check_security_status() -> str:
    """Check security status"""
    try:
        result = ["### 🛡️ الحالة الأمنية\n"]
        
        # Firewall
        result.append("**جدار الحماية:**")
        try:
            cmd = "sudo ufw status 2>/dev/null | head -3"
            fw_status = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
            result.append(f"```\n{fw_status}\n```")
        except:
            result.append("⚠️ غير متاح")
        
        # Failed logins
        result.append("\n**محاولات الدخول الفاشلة:**")
        try:
            cmd = "grep -i 'failed' /var/log/auth.log 2>/dev/null | tail -3"
            fails = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
            if fails:
                result.append(f"```\n{fails[:300]}\n```")
            else:
                result.append("✅ لا توجد محاولات فاشلة")
        except:
            result.append("⚠️ غير متاح")
        
        # Open ports
        result.append("\n**المنافذ المفتوحة:**")
        try:
            cmd = "ss -tulpn 2>/dev/null | grep LISTEN | head -5"
            ports = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
            if ports:
                result.append(f"```\n{ports}\n```")
        except:
            result.append("⚠️ غير متاح")
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def monitor_system_logs() -> str:
    """Monitor system logs"""
    try:
        result = ["### 📋 سجلات النظام\n"]
        
        logs = [
            ("/var/log/syslog", "النظام"),
            ("/var/log/auth.log", "المصادقة")
        ]
        
        for log_path, log_name in logs:
            if os.path.exists(log_path):
                try:
                    cmd = f"tail -5 '{log_path}' 2>/dev/null"
                    content = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
                    result.append(f"**{log_name}:**\n```\n{content[:400]}\n```")
                except:
                    result.append(f"**{log_name}:** ⚠️ لا يمكن القراءة")
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


# ============================================================================
# GENERAL INFO TOOLS
# ============================================================================

def get_time() -> str:
    """Get current time"""
    now = datetime.now()
    return f"""### 🕐 الوقت الحالي

**التاريخ:** {now.strftime('%Y-%m-%d')}
**الوقت:** {now.strftime('%H:%M:%S')}
**Timestamp:** {now.timestamp():.0f}
"""


def monitor_gpu() -> str:
    """Monitor GPU status"""
    try:
        import torch
        
        if not torch.cuda.is_available():
            return "❌ لا يوجد GPU متاح"
        
        gpu_name = torch.cuda.get_device_name(0)
        gpu_allocated = torch.cuda.memory_allocated() / 1024**3
        gpu_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        return f"""### 🎮 حالة GPU

**الجهاز:** {gpu_name}
**المستخدم:** {gpu_allocated:.2f} GB
**الإجمالي:** {gpu_total:.2f} GB
**النسبة:** {(gpu_allocated / gpu_total * 100):.1f}%
"""
    
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def get_os_info() -> str:
    """Get OS information"""
    try:
        result = [f"### 🖥️ معلومات النظام\n"]
        
        result.append(f"**النظام:** {platform.system()} {platform.release()}")
        result.append(f"**المعمارية:** {platform.machine()}")
        result.append(f"**الجهاز:** {socket.gethostname()}")
        
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                for line in f:
                    if 'PRETTY_NAME' in line:
                        name = line.split('=')[1].strip('"\n')
                        result.append(f"**التوزيعة:** {name}")
                        break
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def get_installed_packages() -> str:
    """Get installed packages"""
    try:
        result = ["### 📦 الحزم المثبتة\n"]
        
        if os.path.exists("/etc/debian_version"):
            cmd = "dpkg -l | tail -n +6 | wc -l"
            count = subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
            result.append(f"**العدد (dpkg):** {count}")
            
            cmd = "apt list --upgradable 2>/dev/null | tail -n +2 | wc -l"
            upgradable = subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
            result.append(f"**قابلة للتحديث:** {upgradable}")
            
            if int(upgradable) > 0:
                result.append("\n**للتحديث:**")
                result.append("```bash")
                result.append("sudo apt update && sudo apt upgrade -y")
                result.append("```")
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def get_services_status() -> str:
    """Get services status"""
    try:
        result = ["### ⚙️ حالة الخدمات\n"]
        
        critical_services = ["sshd", "nginx", "mysql", "cron", "redis"]
        
        for service in critical_services:
            try:
                cmd = f"systemctl is-active {service} 2>/dev/null"
                status = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
                icon = "✅" if status == "active" else "⚠️" if status == "inactive" else "❌"
                result.append(f"{icon} **{service}:** {status}")
            except:
                result.append(f"⚪ **{service}:** غير متاح")
        
        return "\n".join(result)
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def search_memory(query: str) -> str:
    """Search in system logs and files"""
    if not query:
        return "❌ يجب تحديد استعلام البحث"
    
    result = [f"### 🔍 بحث عن: {query}\n"]
    
    # Search in syslog
    try:
        cmd = f"grep -i '{query}' /var/log/syslog 2>/dev/null | tail -5"
        output = subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
        if output:
            result.append(f"**سجل النظام:**\n```\n{output[:400]}\n```")
        else:
            result.append("**سجل النظام:** لا توجد نتائج")
    except:
        result.append("**سجل النظام:** غير متاح")
    
    # Search in journal
    try:
        cmd = f"journalctl --since '1 hour ago' 2>/dev/null | grep -i '{query}' | tail -3"
        output = subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
        if output:
            result.append(f"\n**سجلات systemd:**\n```\n{output[:300]}\n```")
    except:
        pass
    
    return "\n".join(result)


def update_memory(content: str) -> str:
    """Update memory"""
    return f"💾 تم حفظ: {content[:100]}..."


# ============================================================================
# TOOL REGISTRATION (SUPERSEDED)
# ============================================================================

def register_basic_tools():
    """NO-OP: Tools are now defined in unified_core.tools.definitions.
    
    This function previously registered tools with the deprecated
    neural_engine.tools.tool_registry. All tools are now managed
    statically via unified_core.tool_registry.
    """
    import logging
    logging.getLogger(__name__).debug(
        "register_basic_tools() is superseded by unified_core.tools.definitions"
    )


# Auto-register on import (backward compat — now a no-op)
register_basic_tools()

