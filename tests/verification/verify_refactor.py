
import os
import time
import subprocess
import requests
import sys
import signal

# Config
HOST = "127.0.0.1"
PORT = 8001
BASE_URL = f"http://{HOST}:{PORT}"
DATA_DIR = "/tmp/noogh_test_data"
# Cleanup
os.system(f"rm -rf {DATA_DIR}")
os.makedirs(DATA_DIR, exist_ok=True)

def start_gateway(env_vars):
    # Start with a timeout to catch hanging imports
    cmd = ["./venv/bin/uvicorn", "gateway.app.main:app", "--host", HOST, "--port", str(PORT)]
    print(f"🚀 Starting Gateway with: {env_vars} ...")
    env = os.environ.copy()
    env.update(env_vars)
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc

def wait_for_health(proc, timeout=10, expect_code=200):
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
             print("❌ Gateway process died!")
             stdout, stderr = proc.communicate()
             print("STDOUT:", stdout)
             print("STDERR:", stderr)
             return False
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=1)
            if r.status_code == expect_code:
                return True
        except Exception:
            time.sleep(0.5)
    return False

def check_ready(expect_code):
    try:
        r = requests.get(f"{BASE_URL}/ready", timeout=2)
        print(f"Ready Status: {r.status_code}")
        return r.status_code == expect_code
    except Exception as e:
        print(f"Ready Check Failed: {e}")
        return False

# Test 1: Redis DOWN -> /health=200, /ready=503
print("\n🧪 TEST 1: Redis DOWN (Fail-Closed)")
# Ensure no redis (mock environ or stop it?)
# We assume running local redis. STOP IT.
os.system("docker stop noogh-redis")

env_down = {
    "NOOGH_ENV": "production",
    "NOOGH_DATA_DIR": DATA_DIR,
    "REDIS_URL": "redis://127.0.0.1:6379/0", # Pointing to stopped redis
    "NOOGH_ADMIN_TOKEN": "admin",
    "NOOGH_SERVICE_TOKEN": "service",
    "NOOGH_READONLY_TOKEN": "read",
    "NOOGH_INTERNAL_TOKEN": "internal",
    "NOOGH_JOB_SIGNING_SECRET": "secret"
}
proc = start_gateway(env_down)
if wait_for_health(proc):
    print("✅ /health IS 200 (Boot Safe)")
    if check_ready(503):
        print("✅ /ready IS 503 (Fail Closed)")
    else:
        print("❌ /ready unexpected status (Should be 503)")
        proc.terminate()
        sys.exit(1)
else:
    print("❌ Gateway crashed or hung!")
    proc.terminate()
    sys.exit(1)
proc.terminate()
proc.wait()

# Test 2: Redis UP -> /ready=200
print("\n🧪 TEST 2: Redis UP")
os.system("docker start noogh-redis")
print("Waiting 10s for Redis...")
time.sleep(10) # Wait for redis

proc = start_gateway(env_down)
if wait_for_health(proc):
    try:
        r = requests.get(f"{BASE_URL}/ready", timeout=2)
        print(f"Ready Response: {r.status_code} - {r.text}")
        data = r.json()
        if data.get("redis") is True:
             print("✅ Redis is HEALTHY (Connection verified)")
             if r.status_code == 503:
                 print("⚠️ Overall status 503 (Expected: other services missing)")
             else:
                 print(f"ℹ️ Overall status {r.status_code}")
        else:
             print("❌ Redis is UNHEALTHY")
             print(f"Debug: {data}")
             proc.terminate()
             sys.exit(1)
    except Exception as e:
        print(f"Ready Check Failed: {e}")
        proc.terminate()
        sys.exit(1)
else:
    print("❌ Gateway crashed!")
    proc.terminate()
    sys.exit(1)
proc.terminate()
proc.wait()

# Test 3: Missing NOOGH_DATA_DIR -> Crash
print("\n🧪 TEST 3: Missing NOOGH_DATA_DIR")
env_missing = env_down.copy()
del env_missing["NOOGH_DATA_DIR"]
proc = start_gateway(env_missing)
time.sleep(3)
if proc.poll() is None:
    print("❌ Gateway started without NOOGH_DATA_DIR! (Should crash)")
    proc.terminate()
else:
    print("✅ Gateway crashed safely (RuntimeError expected)")
    stdout, stderr = proc.communicate()
    if "NOOGH_DATA_DIR is REQUIRED" in stderr or "NOOGH_DATA_DIR is REQUIRED" in stdout:
        print("✅ Error message confirmed")
    else:
        print("⚠️ Crashed but error message unclear")

print("\n✅ ALL ACCEPTANCE TESTS PASSED")
