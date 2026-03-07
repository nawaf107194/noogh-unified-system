import os
import sys

# Set Production Mode
os.environ["NOOGH_ENV"] = "production"

# Clear Secrets (simulating missing env)
if "NOOGH_JOB_SIGNING_SECRET" in os.environ:
    del os.environ["NOOGH_JOB_SIGNING_SECRET"]
if "NOOGH_ADMIN_TOKEN" in os.environ:
    del os.environ["NOOGH_ADMIN_TOKEN"]

print("--- TESTING FAIL-CLOSED ---")
try:
    from gateway.app.core.config import get_settings
    settings = get_settings()
    print("FAIL: Config loaded without required secrets!")
    sys.exit(1)
except Exception as e:
    print(f"PASS: Config failed as expected: {e}")

try:
    from gateway.app.core.jobs import get_job_store_safe
    # Remove REDIS_URL to test prod enforcement
    if "REDIS_URL" in os.environ:
         del os.environ["REDIS_URL"]
    get_job_store_safe()
    print("FAIL: get_job_store_safe allowed execution without Redis in PROD!")
except ImportError:
    pass # If jobs.py import failed earlier
except RuntimeError as e:
    print(f"PASS: JobStore failed as expected: {e}")
except Exception as e:
    print(f"PASS: JobStore failed with: {e}")
