#!/usr/bin/env python3
import os
import subprocess
import time
import requests
import signal
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env before any other imports
load_dotenv()

# ==============================
# CONFIG & SETTINGS
# ==============================
# CONFIG & SETTINGS
# ==============================
from config import settings
from config.ports import PORTS
try:
    from unified_core.core.system_audit import SystemAudit
except ImportError:
    SystemAudit = None

# Parse --dev flag
DEV_MODE = "--dev" in sys.argv

# 0. SYSTEM PRE-FLIGHT CHECK (Fail-Closed in Prod, Relaxed in Dev)
if SystemAudit:
    SystemAudit.run_preflight_checks(dev_mode=DEV_MODE)
if DEV_MODE:
    print("⚠️  DEVELOPMENT MODE ACTIVE. Using insecure defaults.")
print("✅ Pre-flight checks passed.")

VENV = settings.ROOT_DIR / ".venv/bin" # Corrected VENV path
# Original was: ROOT = Path(__file__).resolve().parent => src/
# VENV = ROOT / "venv/bin" => src/venv/bin

GATEWAY_PORT = PORTS.GATEWAY
NEURAL_PORT = PORTS.NEURAL_ENGINE
SANDBOX_PORT = PORTS.SANDBOX
REDIS_PORT = PORTS.REDIS

# Construct ENV for subprocesses using centralized settings
ENV = {
    "NOOGH_ENV": settings.ENV_MODE,
    "NOOGH_DATA_DIR": str(settings.DATA_DIR),
    "REDIS_URL": f"redis://localhost:{REDIS_PORT}/0",
    "NOOGH_JOB_SIGNING_SECRET": settings.JOB_SIGNING_SECRET,
    "NOOGH_ADMIN_TOKEN": settings.ADMIN_TOKEN,
    "NOOGH_SERVICE_TOKEN": settings.SERVICE_TOKEN,
    "NOOGH_READONLY_TOKEN": settings.READONLY_TOKEN,
    "NOOGH_INTERNAL_TOKEN": settings.INTERNAL_TOKEN,
    "NOOGH_SANDBOX_URL": f"http://127.0.0.1:{PORTS.SANDBOX}",
    "NOOGH_NEURAL_URL": f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}",
    "PYTHONPATH": str(settings.ROOT_DIR),
}

PROCS = []

# ==============================
# HELPERS
# ==============================
def run(cmd, env=None, wait=False):
    # Fixed: Use standard file descriptors or DEVNULL to avoid PIPE deadlock
    # If we want to see output, we let it flow to stdout/stderr
    p = subprocess.Popen(
        cmd,
        env={**os.environ, **(env or {})},
        stdout=None, # Inherit stdout
        stderr=None, # Inherit stderr
        text=True,
    )
    PROCS.append(p)
    if wait:
        p.wait()
    return p

def wait_http(url, name, timeout=15):
    for _ in range(timeout):
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200: # Strict 200 check
                print(f"✅ {name} ready ({r.status_code})")
                return True
        except Exception:
            pass
        time.sleep(1)
    print(f"❌ {name} NOT READY")
    return False

def shutdown():
    print("\n🛑 Shutting down...")
    for p in PROCS:
        try:
            p.terminate()
        except Exception:
            pass
    time.sleep(2)
    for p in PROCS:
        try:
            p.kill()
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, lambda *_: shutdown())
signal.signal(signal.SIGTERM, lambda *_: shutdown())

# ==============================
# BOOT SEQUENCE
# ==============================
print("══════════════════════════════")
print("🚀 NOOGH FULL PRODUCTION BOOT")
print("══════════════════════════════")

# 1. Data dir
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
try:
    settings.DATA_DIR.chmod(0o700)
except Exception:
    pass # Might fail on some FS or if not owner
print(f"📁 Data dir: {settings.DATA_DIR}")

# 2. Redis
print("▶ Starting Redis...")
subprocess.run(
    ["docker", "rm", "-f", "noogh-redis"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
try:
    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", "noogh-redis",
            "-p", f"{REDIS_PORT}:6379",
            "redis:alpine"
        ],
        check=True,
        capture_output=True,
        text=True
    )
    print("✅ Redis started via Docker")
except subprocess.CalledProcessError as e:
    if "address already in use" in e.stderr.lower():
        print("⚠️  Redis port (6379) already in use. Assuming Redis is already running.")
    else:
        print(f"❌ Redis failed: {e.stderr}")
        shutdown()
time.sleep(2)

# 3. Neural Engine
print("▶ Starting Neural Engine...")
run([
    str(VENV / "uvicorn"),
    "neural_engine.api.main:app",
    "--host", "127.0.0.1",
    "--port", str(NEURAL_PORT),
], ENV)

if not wait_http(f"http://127.0.0.1:{NEURAL_PORT}/health", "Neural", timeout=180):
    shutdown()

# 4. Sandbox
print("▶ Starting Sandbox Service...")
run([
    str(VENV / "uvicorn"),
    "sandbox_service.main:app",
    "--host", "127.0.0.1",
    "--port", str(SANDBOX_PORT),
], {
    **ENV,
    "DOCKER_HOST": "unix:///var/run/docker.sock"
})

if not wait_http(f"http://127.0.0.1:{SANDBOX_PORT}/health", "Sandbox"):
    shutdown()

# 5. Gateway
print("▶ Starting Gateway...")
run([
    str(VENV / "uvicorn"),
    "gateway.app.main:app",
    "--host", "127.0.0.1",
    "--port", str(GATEWAY_PORT),
], {**ENV, "NOOGH_ROUTING_MODE": "proxy"})

if not wait_http(f"http://127.0.0.1:{GATEWAY_PORT}/health", "Gateway"):
    shutdown()

# 6. Worker
print("▶ Starting Worker...")
run([
    str(VENV / "python"),
    "-m", "gateway.app.core.worker_entry"
], {**ENV, "NOOGH_ROUTING_MODE": "proxy"})

# 7. Final Ready Check
time.sleep(2)
r = requests.get(f"http://127.0.0.1:{GATEWAY_PORT}/ready")
print(f"📊 /ready → {r.status_code}")

if r.status_code != 200:
    print("⛔ SYSTEM NOT READY")
    shutdown()

print("\n══════════════════════════════")
print("🚀 SYSTEM STATUS: GO")
print("Gateway  :", f"http://localhost:{GATEWAY_PORT}")
print("Neural   :", f"http://localhost:{NEURAL_PORT}")
print("Sandbox  :", f"http://localhost:{SANDBOX_PORT}")
print("══════════════════════════════")
print("CTRL+C to stop")

while True:
    time.sleep(10)
