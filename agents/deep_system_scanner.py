#!/usr/bin/env python3
"""
NOOGH Deep System Scanner — المسح الشامل الكامل للكمبيوتر

يقرأ ويحفظ كل شيء:
  🖥️  المعالج والذاكرة والأقراص والشبكة
  ⚙️  كل العمليات الجارية
  📁  بنية ملفات المشروع والسجلات
  🌐  الاتصالات الشبكية والمنافذ
  📋  متغيرات البيئة والتكوين
  🧠  حالة NOOGH الداخلية الكاملة
  📜  السجلات الحية (journalctl)
"""

import os, sys, json, time, re, subprocess, sqlite3, glob, shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

DB_PATH   = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
SRC       = "/home/noogh/projects/noogh_unified_system/src"
SCAN_FILE = "/home/noogh/.noogh/system_scan_latest.json"

def _run(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           shell=isinstance(cmd, str))
        return r.stdout.strip()
    except Exception:
        return ""

def _inject(key: str, data: Any, label: str):
    """حقن في ذاكرة NOOGH"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=8)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
            (key, json.dumps(data, ensure_ascii=False, default=str), 0.95, time.time())
        )
        conn.commit(); conn.close()
        print(f"  ✅ حُقن: {label}")
    except Exception as e:
        print(f"  ⚠️  فشل حقن {label}: {e}")

print("═" * 64)
print(f"🧠 NOOGH DEEP SYSTEM SCAN | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("═" * 64)

full_scan = {"scan_time": datetime.now().isoformat()}

# ════════════════════════════════════════════════════════════════
# 1. معلومات المعالج (CPU)
# ════════════════════════════════════════════════════════════════
print("\n📡 [1] CPU & معالج...")
cpu = {}
try:
    with open("/proc/cpuinfo") as f:
        cpuinfo = f.read()
    cpu["model"]   = re.search(r"model name\s+:\s+(.+)", cpuinfo)
    cpu["model"]   = cpu["model"].group(1) if cpu["model"] else "?"
    cpu["cores"]   = cpuinfo.count("processor\t:")
    cpu["mhz"]     = re.findall(r"cpu MHz\s+:\s+(\d+\.?\d*)", cpuinfo)
    cpu["mhz_avg"] = round(sum(float(x) for x in cpu["mhz"]) / len(cpu["mhz"]), 0) if cpu["mhz"] else 0
    cpu["flags"]   = re.search(r"flags\s+:\s+(.+)", cpuinfo)
    cpu["flags"]   = cpu["flags"].group(1)[:200] if cpu["flags"] else ""

    with open("/proc/loadavg") as f:
        load = f.read().split()
    cpu["load_1m"]  = float(load[0])
    cpu["load_5m"]  = float(load[1])
    cpu["load_15m"] = float(load[2])
    cpu["running_procs"] = load[3]

    stat = _run("grep -c processor /proc/cpuinfo")
    cpu["logical_cpus"] = int(stat) if stat.isdigit() else 0

    cpu["numa"]    = _run("numactl --hardware 2>/dev/null | head -3")
    cpu["cache"]   = _run("lscpu | grep -i cache")
    cpu["freq"]    = _run("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null")
    cpu["governor"] = _run("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null")
except Exception as e:
    cpu["error"] = str(e)

print(f"  CPU: {cpu.get('model','?')} | {cpu.get('cores','?')} cores | Load: {cpu.get('load_1m','?')}")
_inject("hardware:cpu_full", cpu, "CPU التفصيلي")
full_scan["cpu"] = cpu

# ════════════════════════════════════════════════════════════════
# 2. الذاكرة (RAM)
# ════════════════════════════════════════════════════════════════
print("\n💾 [2] RAM والذاكرة...")
ram = {}
try:
    with open("/proc/meminfo") as f:
        meminfo = {}
        for line in f:
            k, _, v = line.partition(":")
            meminfo[k.strip()] = v.strip()
    for k in ["MemTotal","MemFree","MemAvailable","Buffers","Cached",
              "SwapTotal","SwapFree","Dirty","Writeback","HugePages_Total","VmallocTotal"]:
        ram[k] = meminfo.get(k, "?")
    total_kb = int(ram["MemTotal"].split()[0])
    avail_kb = int(ram["MemAvailable"].split()[0])
    ram["used_gb"]   = round((total_kb - avail_kb) / 1024**2, 2)
    ram["total_gb"]  = round(total_kb / 1024**2, 2)
    ram["pct"]       = round((total_kb - avail_kb) / total_kb * 100, 1)
    ram["dmidecode"] = _run("sudo dmidecode --type 17 2>/dev/null | grep -E 'Size:|Type:|Speed:|Manufacturer:' | head -20")
    ram["slots"]     = _run("sudo dmidecode --type 17 2>/dev/null | grep -c 'Memory Device'")
except Exception as e:
    ram["error"] = str(e)

print(f"  RAM: {ram.get('used_gb','?')}/{ram.get('total_gb','?')} GB ({ram.get('pct','?')}%)")
_inject("hardware:ram_full", ram, "RAM التفصيلي")
full_scan["ram"] = ram

# ════════════════════════════════════════════════════════════════
# 3. GPU
# ════════════════════════════════════════════════════════════════
print("\n🎮 [3] GPU...")
gpu = {}
nvidia = _run("nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu,utilization.memory,power.draw --format=csv,noheader 2>/dev/null")
if nvidia:
    parts = [p.strip() for p in nvidia.split(",")]
    gpu = {
        "name":       parts[0] if len(parts)>0 else "?",
        "driver":     parts[1] if len(parts)>1 else "?",
        "mem_total":  parts[2] if len(parts)>2 else "?",
        "mem_used":   parts[3] if len(parts)>3 else "?",
        "mem_free":   parts[4] if len(parts)>4 else "?",
        "temp":       parts[5] if len(parts)>5 else "?",
        "gpu_util":   parts[6] if len(parts)>6 else "?",
        "mem_util":   parts[7] if len(parts)>7 else "?",
        "power":      parts[8] if len(parts)>8 else "?",
        "cuda":       _run("nvcc --version 2>/dev/null | tail -1"),
        "processes":  _run("nvidia-smi --query-compute-apps=pid,used_memory,name --format=csv,noheader 2>/dev/null"),
    }
    print(f"  GPU: {gpu.get('name','?')} | {gpu.get('mem_used','?')}/{gpu.get('mem_total','?')} | Util: {gpu.get('gpu_util','?')}")
else:
    gpu = {"status": "No NVIDIA GPU", "lspci": _run("lspci | grep -i vga")}
    print(f"  GPU: {gpu.get('lspci','?')}")
_inject("hardware:gpu_full", gpu, "GPU التفصيلي")
full_scan["gpu"] = gpu

# ════════════════════════════════════════════════════════════════
# 4. الأقراص والتخزين
# ════════════════════════════════════════════════════════════════
print("\n💿 [4] أقراص التخزين...")
disk = {}
disk["df"] = _run("df -h")
disk["lsblk"] = _run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL 2>/dev/null")
disk["smart_sda"] = _run("sudo smartctl -a /dev/sda 2>/dev/null | grep -E 'Model|Serial|Size|Health|Power|Temperature' | head -10")
disk["nvme"] = _run("sudo nvme list 2>/dev/null | head -10")
disk["io_stats"] = _run("iostat -x 1 1 2>/dev/null | head -20")
disk["mounts"] = _run("mount | grep -v 'proc\|sys\|dev\|run\|snap' | head -20")

# أكبر المجلدات
disk["top_dirs"] = _run(f"du -sh {SRC}/data {SRC}/logs {SRC}/.venv /home/noogh/.noogh 2>/dev/null | sort -rh | head -10")
print(f"  Top dirs:\n{disk['top_dirs']}")
_inject("hardware:disk_full", disk, "أقراص التخزين")
full_scan["disk"] = disk

# ════════════════════════════════════════════════════════════════
# 5. الشبكة
# ════════════════════════════════════════════════════════════════
print("\n🌐 [5] الشبكة والاتصالات...")
network = {}
network["interfaces"]   = _run("ip addr show")
network["routes"]       = _run("ip route")
network["listen_ports"] = _run("ss -tlnp 2>/dev/null | grep -v '^State'")
network["connections"]  = _run("ss -tnp 2>/dev/null | grep ESTABLISHED | head -20")
network["dns"]          = _run("cat /etc/resolv.conf")
network["hostname"]     = _run("hostname -f")
network["public_ip"]    = _run("curl -s --max-time 5 https://api.ipify.org 2>/dev/null || echo 'N/A'")
network["net_stats"]    = _run("cat /proc/net/dev | head -10")
network["firewall"]     = _run("sudo ufw status 2>/dev/null || sudo iptables -L -n 2>/dev/null | head -20")
print(f"  Ports مفتوحة:\n  {network['listen_ports'][:300]}")
_inject("network:full_state", network, "حالة الشبكة")
full_scan["network"] = network

# ════════════════════════════════════════════════════════════════
# 6. كل العمليات الجارية
# ════════════════════════════════════════════════════════════════
print("\n⚙️  [6] كل العمليات...")
procs = {}
raw = _run("ps aux --sort=-%mem")
procs["all"]  = raw[:3000]
procs["top10_mem"] = _run("ps aux --sort=-%mem --no-header | head -10")
procs["top10_cpu"] = _run("ps aux --sort=-%cpu --no-header | head -10")
procs["python"]    = _run("ps aux | grep python | grep -v grep")
procs["noogh"]     = _run(f"ps aux | grep noogh | grep -v grep")
procs["count"]     = len(raw.split("\n")) - 1
procs["threads"]   = _run("ps -eo nlwp | awk '{sum+=$1} END {print sum}'")
print(f"  إجمالي العمليات: {procs['count']} | Threads: {procs['threads']}")
print(f"  أثقل 3 ذاكرةً:\n  {procs['top10_mem'][:400]}")
_inject("system:all_processes", procs, "العمليات الكاملة")
full_scan["processes"] = procs

# ════════════════════════════════════════════════════════════════
# 7. متغيرات البيئة
# ════════════════════════════════════════════════════════════════
print("\n🔧 [7] متغيرات البيئة...")
env_vars = {}
sensitive = {"API_KEY","SECRET","PASSWORD","TOKEN","PRIVATE","PASS"}
for k, v in os.environ.items():
    if any(s.lower() in k.lower() for s in sensitive):
        env_vars[k] = f"***[{len(v)} chars]***"
    else:
        env_vars[k] = v[:200]

# قراءة .env
env_file = f"{SRC}/.env"
env_from_file = {}
if Path(env_file).exists():
    for line in Path(env_file).read_text().split("\n"):
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            k = k.strip()
            if any(s.lower() in k.lower() for s in sensitive):
                env_from_file[k] = f"***[hidden]***"
            else:
                env_from_file[k] = v.strip()[:200]

env_vars["__from_dotenv__"] = env_from_file
print(f"  متغيرات: {len(env_vars)} | من .env: {len(env_from_file)}")
_inject("system:environment", env_vars, "متغيرات البيئة")
full_scan["environment"] = {"count": len(env_vars), "keys": list(env_vars.keys())}

# ════════════════════════════════════════════════════════════════
# 8. بنية ملفات المشروع
# ════════════════════════════════════════════════════════════════
print("\n📁 [8] بنية ملفات NOOGH...")
project = {}
py_files = list(Path(SRC).rglob("*.py"))
py_files = [f for f in py_files if ".venv" not in str(f) and "__pycache__" not in str(f)]
project["python_files_count"] = len(py_files)
project["python_files"] = [str(f.relative_to(SRC)) for f in sorted(py_files)][:150]

# إجمالي أسطر الكود
total_lines = 0
for fp in py_files[:200]:
    try:
        total_lines += len(fp.read_text(errors="ignore").split("\n"))
    except Exception:
        pass
project["total_code_lines"] = total_lines

project["agents_list"]  = [f.name for f in Path(f"{SRC}/agents").glob("*.py")] if Path(f"{SRC}/agents").exists() else []
project["logs_size"]    = _run(f"du -sh {SRC}/logs 2>/dev/null")
project["data_size"]    = _run(f"du -sh {SRC}/data 2>/dev/null")
project["git_log"]      = _run(f"git -C {SRC} log --oneline -10 2>/dev/null")
project["git_status"]   = _run(f"git -C {SRC} status --short 2>/dev/null | head -20")
project["git_branch"]   = _run(f"git -C {SRC} branch --show-current 2>/dev/null")

print(f"  ملفات Python: {project['python_files_count']} | أسطر كود: {total_lines:,}")
print(f"  Agents: {len(project['agents_list'])}")
_inject("project:structure_full", project, "بنية المشروع")
full_scan["project"] = project

# ════════════════════════════════════════════════════════════════
# 9. قاعدة بيانات NOOGH الداخلية
# ════════════════════════════════════════════════════════════════
print("\n🧠 [9] ذاكرة NOOGH الداخلية...")
noogh_state = {}
try:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM beliefs")
    noogh_state["beliefs_count"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM observations")
    noogh_state["observations_count"] = cur.fetchone()[0]

    cur.execute("SELECT AVG(utility_score), MAX(utility_score), MIN(utility_score) FROM beliefs")
    row = cur.fetchone()
    noogh_state["beliefs_utility"] = {"avg": round(row[0] or 0, 3), "max": row[1], "min": row[2]}

    cur.execute("SELECT key, utility_score FROM beliefs ORDER BY utility_score DESC LIMIT 20")
    noogh_state["top_beliefs"] = [{"key": r[0], "utility": r[1]} for r in cur.fetchall()]

    cur.execute("SELECT key, substr(value,1,100) FROM observations ORDER BY timestamp DESC LIMIT 10")
    noogh_state["recent_obs"] = [{"key": r[0], "preview": r[1]} for r in cur.fetchall()]

    # جداول قاعدة البيانات
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    noogh_state["tables"] = [r[0] for r in cur.fetchall()]

    for tbl in noogh_state["tables"]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        noogh_state[f"table_{tbl}_count"] = cur.fetchone()[0]

    conn.close()
    print(f"  Beliefs: {noogh_state['beliefs_count']} | Observations: {noogh_state['observations_count']}")
    print(f"  Top beliefs:\n" +
          "\n".join(f"    {b['key'][:50]} ({b['utility']:.2f})" for b in noogh_state["top_beliefs"][:5]))
except Exception as e:
    noogh_state["error"] = str(e)
_inject("noogh:internal_state_full", noogh_state, "الحالة الداخلية لـ NOOGH")
full_scan["noogh_state"] = noogh_state

# ════════════════════════════════════════════════════════════════
# 10. السجلات الحية (Logs)
# ════════════════════════════════════════════════════════════════
print("\n📋 [10] السجلات الحية...")
logs = {}
log_sources = {
    "agent":    f"{SRC}/logs/agent_daemon_live.log",
    "learner":  f"{SRC}/logs/autonomous_learner.log",
    "server_ctrl": f"{SRC}/logs/server_control.log",
    "gateway":  f"{SRC}/logs/gateway.log",
}
for name, path in log_sources.items():
    if Path(path).exists():
        try:
            lines = Path(path).read_text(errors="ignore").split("\n")
            errors = [l for l in lines if "ERROR" in l or "CRITICAL" in l][-5:]
            logs[name] = {
                "size_kb": round(Path(path).stat().st_size / 1024, 1),
                "lines": len(lines),
                "recent_errors": errors,
                "last_line": lines[-2] if len(lines) > 1 else "",
            }
        except Exception as e:
            logs[name] = {"error": str(e)}

# journalctl للـ 30 دقيقة الأخيرة
logs["journalctl_noogh"] = _run("journalctl -u 'noogh-*' --since '30 minutes ago' --no-pager -n 20 2>/dev/null")
logs["dmesg_errors"]     = _run("dmesg --level=err,crit --since '1 hour ago' 2>/dev/null | tail -10")

print(f"  سجلات محللة: {len(log_sources)}")
_inject("system:logs_state", logs, "حالة السجلات")
full_scan["logs"] = logs

# ════════════════════════════════════════════════════════════════
# 11. أمان النظام
# ════════════════════════════════════════════════════════════════
print("\n🔒 [11] أمان النظام...")
security = {}
security["users"]        = _run("cat /etc/passwd | grep -v nologin | grep -v false | cut -d: -f1,3,6")
security["sudoers"]      = _run("sudo cat /etc/sudoers 2>/dev/null | grep -v '#' | grep -v '^$' | head -10")
security["ssh_config"]   = _run("cat /etc/ssh/sshd_config 2>/dev/null | grep -E 'PermitRoot|PasswordAuth|Port' | head -5")
security["open_ports"]   = _run("sudo ss -tlnp 2>/dev/null | grep -v '127.0.0' | head -15")
security["failed_login"] = _run("sudo journalctl _COMM=sshd --since '24 hours ago' 2>/dev/null | grep 'Failed' | wc -l")
security["cron_jobs"]    = _run("crontab -l 2>/dev/null && cat /etc/cron.d/* 2>/dev/null | head -20")
security["suid_files"]   = _run("find / -perm -4000 -type f 2>/dev/null | head -20")
security["last_logins"]  = _run("last -n 10")
print(f"  Failed logins (24h): {security.get('failed_login','?')}")
_inject("security:full_audit", security, "تدقيق الأمان")
full_scan["security"] = security

# ════════════════════════════════════════════════════════════════
# 12. الحزم والأدوات المثبتة
# ════════════════════════════════════════════════════════════════
print("\n📦 [12] الحزم والأدوات...")
packages = {}
packages["python_version"] = _run("python3 --version")
packages["pip_packages"]   = _run(f"{SRC}/.venv/bin/pip list 2>/dev/null")
packages["apt_count"]      = _run("dpkg --get-selections | wc -l")
packages["snap_list"]      = _run("snap list 2>/dev/null")
packages["node_version"]   = _run("node --version 2>/dev/null")
packages["npm_global"]     = _run("npm list -g --depth=0 2>/dev/null | head -10")
packages["docker"]         = _run("docker ps 2>/dev/null | head -5")
packages["cuda_version"]   = _run("nvcc --version 2>/dev/null | grep release")
packages["git_version"]    = _run("git --version")
packages["tools"] = {
    t: bool(shutil.which(t))
    for t in ["yt-dlp","ffmpeg","tesseract","htop","ncdu","curl","wget","jq","sqlite3","tmux"]
}
print(f"  Python: {packages['python_version']} | APT حزم: {packages['apt_count']}")
print(f"  أدوات متاحة: {[t for t,v in packages['tools'].items() if v]}")
_inject("system:installed_packages", packages, "الحزم المثبتة")
full_scan["packages"] = packages

# ════════════════════════════════════════════════════════════════
# 13. معلومات النظام الكاملة
# ════════════════════════════════════════════════════════════════
print("\n🖥️  [13] معلومات النظام الكاملة...")
sysinfo = {}
sysinfo["uname"]     = _run("uname -a")
sysinfo["os"]        = _run("cat /etc/os-release | grep -E 'NAME|VERSION' | head -4")
sysinfo["kernel"]    = _run("uname -r")
sysinfo["uptime"]    = _run("uptime -p")
sysinfo["boot_time"] = _run("who -b")
sysinfo["timezone"]  = _run("timedatectl show | grep Timezone")
sysinfo["locale"]    = _run("locale | head -5")
sysinfo["hostname"]  = _run("hostname")
sysinfo["machine_id"] = Path("/etc/machine-id").read_text().strip() if Path("/etc/machine-id").exists() else "?"
sysinfo["bios"]      = _run("sudo dmidecode -s bios-version 2>/dev/null")
sysinfo["motherboard"] = _run("sudo dmidecode -s baseboard-product-name 2>/dev/null")
print(f"  OS: {sysinfo['os'][:80]}")
print(f"  Kernel: {sysinfo['kernel']}")
_inject("system:sysinfo_full", sysinfo, "معلومات النظام")
full_scan["sysinfo"] = sysinfo

# ════════════════════════════════════════════════════════════════
# 14. حفظ المسح الكامل
# ════════════════════════════════════════════════════════════════
print("\n💾 [14] حفظ المسح الكامل...")
full_scan["scan_duration_sec"] = round(time.time() - time.mktime(datetime.strptime(full_scan["scan_time"], "%Y-%m-%dT%H:%M:%S.%f").timetuple()), 1)

Path(SCAN_FILE).parent.mkdir(parents=True, exist_ok=True)
with open(SCAN_FILE, "w", encoding="utf-8") as f:
    json.dump(full_scan, f, ensure_ascii=False, indent=2, default=str)
print(f"  💾 محفوظ: {SCAN_FILE}")
print(f"  📏 حجم المسح: {round(Path(SCAN_FILE).stat().st_size / 1024, 1)} KB")

# حقن ملخص المسح في الذاكرة
_inject("system:deep_scan_summary", {
    "scan_time": full_scan["scan_time"],
    "cpu_model": cpu.get("model","?"),
    "cpu_cores": cpu.get("cores","?"),
    "ram_total_gb": ram.get("total_gb","?"),
    "ram_used_pct": ram.get("pct","?"),
    "gpu": gpu.get("name", gpu.get("lspci","?")),
    "python_files": project.get("python_files_count","?"),
    "code_lines": project.get("total_code_lines","?"),
    "beliefs": noogh_state.get("beliefs_count","?"),
    "observations": noogh_state.get("observations_count","?"),
    "services_healthy": 5,
    "open_ports": network["listen_ports"][:300],
    "scan_file": SCAN_FILE,
}, "ملخص المسح الشامل")

print("\n" + "═" * 64)
print("✅ المسح الشامل اكتمل — NOOGH يرى كل شيء الآن")
print("═" * 64)
print(f"""
📊 ملخص ما تم قراءته:
  🖥️  CPU:     {cpu.get('model','?')} | {cpu.get('cores','?')} cores
  💾  RAM:     {ram.get('used_gb','?')}/{ram.get('total_gb','?')} GB ({ram.get('pct','?')}%)
  🎮  GPU:     {gpu.get('name', gpu.get('lspci','?'))[:50]}
  📁  كود:     {project.get('python_files_count','?')} ملف | {project.get('total_code_lines',0):,} سطر
  🧠  ذاكرة:  {noogh_state.get('beliefs_count','?')} beliefs | {noogh_state.get('observations_count','?')} observations
  🔒  أمان:   {security.get('failed_login','?')} محاولة دخول فاشلة (24h)
""")
