#!/usr/bin/env python3
"""
Production Verification Script
Verifies that the NOOGH system is running, secure, and operational.
"""
import sys
import time
import requests
import os
import json

# Configuration
BASE_URL = "http://localhost:8001"
NEURAL_URL = "http://localhost:8000"
ADMIN_TOKEN = os.getenv("NOOGH_ADMIN_TOKEN", "test_admin_token")

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, success=None):
    if success is None:
        print(f"[INFO] {msg}")
    elif success:
        print(f"[{GREEN}PASS{RESET}] {msg}")
    else:
        print(f"[{RED}FAIL{RESET}] {msg}")

def check_health(url, name):
    try:
        r = requests.get(f"{url}/health", timeout=5)
        if r.status_code == 200:
            log(f"{name} is healthy", True)
            return True
        else:
            log(f"{name} returned {r.status_code}", False)
            return False
    except Exception as e:
        log(f"{name} unreachable: {e}", False)
        return False

def verify_auth():
    # 1. No token -> Should fail
    try:
        r = requests.post(f"{BASE_URL}/task", json={"task": "ping"})
        if r.status_code == 401:
            log("Authorization enforced (missing token)", True)
        else:
            log(f"Authorization NOT enforced (got {r.status_code})", False)
            return False
    except Exception:
        pass

    # 2. Invalid token -> Should fail
    try:
        r = requests.post(f"{BASE_URL}/task", 
                         headers={"Authorization": "Bearer invalid"},
                         json={"task": "ping"})
        if r.status_code == 401:
            log("Authorization enforced (invalid token)", True)
        else:
            log(f"Authorization NOT enforced (invalid token got {r.status_code})", False)
            return False
    except Exception:
        pass

    return True

def main():
    log("Starting Production Verification...")
    
    # 1. Health Checks
    if not check_health(BASE_URL, "NOOGH Gateway"):
        sys.exit(1)

    # 1b. Check Dashboard
    if not check_health("http://localhost:8501", "Dashboard"):
        print(f"{YELLOW}[WARN] Dashboard running? (Check port 8501){RESET}")

    # 2. Security Checks (Auth)
    if not verify_auth():
        sys.exit(1)

    # 3. Autonomy Check (Worker)
    log("Verifying Autonomy Engine...")
    try:
        # Submit a quick job
        headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        payload = {
            "task": "Perform a rigorous self-check calculation: 123 * 456",
            "budgets": {"max_steps": 2, "max_total_time_ms": 10000}
        }
        r = requests.post(f"{BASE_URL}/jobs", json=payload, headers=headers)
        if r.status_code == 200:
            job_id = r.json()["job_id"]
            log(f"Job submitted successfully: {job_id}", True)
            
            # Poll for completion
            for _ in range(10):
                time.sleep(2)
                r_job = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
                status = r_job.json()["status"]
                if status == "SUCCEEDED":
                    log(f"Job {job_id} COMPLETED successfully", True)
                    break
                elif status == "FAILED":
                    log(f"Job {job_id} FAILED", False)
                    sys.exit(1)
                print(f"   [Job Status: {status}]", end="\r", flush=True)
            else:
                log(f"Job {job_id} timed out (Worker might be down)", False)
                sys.exit(1)
        else:
            log(f"Job submission failed: {r.status_code} - {r.text}", False)
            sys.exit(1)

    except Exception as e:
        log(f"Autonomy check failed: {e}", False)
        sys.exit(1)

    log("All systems GO.", True)

if __name__ == "__main__":
    main()
