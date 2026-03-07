#!/usr/bin/env python3
"""
NOOGH Complete System Startup Script
=====================================
سكربت موحد لتشغيل النظام الكامل بشكل آمن ومرن.

Usage:
    ./start_noogh_system.py                    # تشغيل كامل
    ./start_noogh_system.py --gateway-only     # Gateway فقط
    ./start_noogh_system.py --no-redis         # بدون Redis (إذا كان يعمل)
    ./start_noogh_system.py --dev              # وضع التطوير

Environment Variables (required):
    NOOGH_DATA_DIR          - مسار البيانات
    NOOGH_ADMIN_TOKEN       - Admin token (32+ chars)
    NOOGH_JOB_SIGNING_SECRET - Job signing secret (32+ chars)
    
Environment Variables (optional):
    REDIS_URL               - Redis connection (default: redis://localhost:6379/0)
    NOOGH_PORT              - Gateway port (default: 8001)
    NOOGH_ENV               - Environment (production/development)
"""

import os
import sys
import time
import signal
import argparse
import subprocess
import requests
from pathlib import Path
from typing import List, Optional

# ============================================================================
# Configuration
# ============================================================================

# Auto-detect project root
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR
VENV_BIN = PROJECT_ROOT / "venv" / "bin"

# Color output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(symbol: str, message: str, color: str = ''):
    """Print colored status message"""
    print(f"{color}{symbol} {message}{Colors.END}")

def print_success(message: str):
    print_status("✅", message, Colors.GREEN)

def print_error(message: str):
    print_status("❌", message, Colors.RED)

def print_warning(message: str):
    print_status("⚠️ ", message, Colors.YELLOW)

def print_info(message: str):
    print_status("ℹ️ ", message, Colors.BLUE)

def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}")
    print(f"  {message}")
    print(f"{'='*50}{Colors.END}\n")

# ============================================================================
# Process Management
# ============================================================================

class ProcessManager:
    """Manages all system processes"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for cleanup"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print_warning("\nReceived shutdown signal...")
        self.shutdown()
        sys.exit(0)
    
    def start_process(self, cmd: List[str], name: str, env: dict = None) -> subprocess.Popen:
        """Start a process and track it"""
        print_info(f"Starting {name}...")
        
        proc_env = os.environ.copy()
        if env:
            proc_env.update(env)
        
        # Redirect output to log files
        log_file = open(f"{name.lower()}.log", "w")
        proc = subprocess.Popen(
            cmd,
            env=proc_env,
            stdout=log_file,
            stderr=log_file,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        self.processes.append(proc)
        print_success(f"{name} started (PID: {proc.pid})")
        return proc
    
    def wait_for_http(self, url: str, name: str, timeout: int = 30) -> bool:
        """Wait for HTTP service to be ready"""
        print_info(f"Waiting for {name} to be ready...")
        
        for i in range(timeout):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code < 500:
                    print_success(f"{name} is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            if i > 0 and i % 10 == 0:
                print_warning(f"Still waiting for {name}... ({i}s)")
        
        print_error(f"{name} failed to become ready after {timeout}s")
        return False
    
    def shutdown(self):
        """Shutdown all processes gracefully"""
        if not self.processes:
            return
        
        print_header("Shutting Down System")
        
        # Terminate gracefully
        for proc in self.processes:
            try:
                proc.terminate()
                print_info(f"Sent TERM to PID {proc.pid}")
            except Exception as e:
                print_warning(f"Error terminating PID {proc.pid}: {e}")
        
        # Wait a bit
        time.sleep(3)
        
        # Force kill if needed
        for proc in self.processes:
            try:
                if proc.poll() is None:
                    proc.kill()
                    print_warning(f"Force killed PID {proc.pid}")
            except Exception:
                pass
        
        print_success("All processes stopped")

# ============================================================================
# Environment Validation
# ============================================================================

def validate_environment(is_dev: bool = False) -> dict:
    """Validate and return environment configuration"""
    print_header("Environment Validation")
    
    errors = []
    warnings = []
    
    # Required variables
    required_vars = {
        "NOOGH_DATA_DIR": None,
        "NOOGH_ADMIN_TOKEN": 32,
        "NOOGH_JOB_SIGNING_SECRET": 32,
    }
    
    env_config = {}
    
    for var, min_length in required_vars.items():
        value = os.getenv(var)
        
        if not value:
            errors.append(f"Missing required variable: {var}")
            continue
        
        env_config[var] = value
        
        # Check length for secrets/tokens
        if min_length and len(value) < min_length:
            if is_dev:
                warnings.append(f"{var} is short ({len(value)} < {min_length} chars)")
            else:
                errors.append(f"{var} must be at least {min_length} characters")
        
        # Check for weak values
        weak_values = ["admin", "service", "dev-secret", "test", "demo"]
        if any(weak in value.lower() for weak in weak_values):
            if is_dev:
                warnings.append(f"{var} looks weak: {value[:10]}...")
            else:
                errors.append(f"{var} appears to be a weak/default value")
    
    # Optional variables with defaults
    env_config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    env_config["NOOGH_PORT"] = os.getenv("NOOGH_PORT", "8001")
    env_config["NOOGH_ENV"] = "development" if is_dev else os.getenv("NOOGH_ENV", "production")
    
    # Service tokens (optional but recommended)
    for token in ["NOOGH_SERVICE_TOKEN", "NOOGH_READONLY_TOKEN", "NOOGH_INTERNAL_TOKEN"]:
        value = os.getenv(token)
        if value:
            env_config[token] = value
        elif not is_dev:
            warnings.append(f"Optional token not set: {token}")
    
    # Print results
    if errors:
        print_error("Validation failed:")
        for error in errors:
            print(f"  • {error}")
        sys.exit(1)
    
    if warnings:
        for warning in warnings:
            print_warning(warning)
    
    # Validate paths exist
    data_dir = Path(env_config["NOOGH_DATA_DIR"])
    if not data_dir.exists():
        print_info(f"Creating data directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
        data_dir.chmod(0o700)
    
    # Check venv
    if not VENV_BIN.exists():
        print_error(f"Virtual environment not found at {VENV_BIN}")
        print_info("Run: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt")
        sys.exit(1)
    
    print_success("Environment validation passed")
    return env_config

# ============================================================================
# Service Startup Functions
# ============================================================================

def start_redis(manager: ProcessManager, args) -> bool:
    """Start Redis if needed"""
    if args.no_redis:
        print_info("Skipping Redis startup (--no-redis)")
        return True
    
    print_header("Redis Setup")
    
    # Check if Redis is already running
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
        print_success("Redis is already running")
        return True
    except Exception:
        pass
    
    # Try to start Redis via Docker
    print_info("Starting Redis via Docker...")
    
    # Remove old container if exists
    subprocess.run(
        ["docker", "rm", "-f", "noogh-redis"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        subprocess.run([
            "docker", "run", "-d",
            "--name", "noogh-redis",
            "-p", "6379:6379",
            "redis:7-alpine",
            "redis-server", "--appendonly", "yes"
        ], check=True)
        
        time.sleep(2)
        print_success("Redis started via Docker")
        return True
        
    except subprocess.CalledProcessError:
        print_error("Failed to start Redis via Docker")
        print_warning("Please start Redis manually or use --no-redis if it's already running")
        return False
    except FileNotFoundError:
        print_error("Docker not found")
        print_warning("Install Docker or start Redis manually")
        return False

def start_gateway(manager: ProcessManager, env_config: dict) -> bool:
    """Start Gateway service"""
    print_header("Starting Gateway")
    
    port = env_config["NOOGH_PORT"]
    
    # Check if port is already in use
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout.strip():
            pid = result.stdout.strip().split('\n')[0]
            print_error(f"Port {port} is already in use by PID {pid}")
            print_info("Options:")
            print(f"  1. Kill the process: kill {pid}")
            print(f"  2. Use a different port: ./start_noogh_system.py --port 8002")
            return False
    except FileNotFoundError:
        # lsof not available, continue anyway
        pass
    
    cmd = [
        str(VENV_BIN / "uvicorn"),
        "gateway.app.main:app",
        "--host", "127.0.0.1",
        "--port", port,
        "--workers", "1"
    ]
    
    process = manager.start_process(cmd, "Gateway", env_config)
    
    # Wait for readiness
    time.sleep(3)
    
    # Check if process is still alive
    if process.poll() is not None:
        print_error("Gateway process died immediately after start")
        print_info("Checking error output...")
        
        # Try to get error from stderr
        try:
            _, stderr = process.communicate(timeout=1)
            if stderr:
                print(f"\n{Colors.RED}Error output:{Colors.END}")
                print(stderr[:1000])  # First 1000 chars
        except Exception:
            pass
        
        return False
    
    return manager.wait_for_http(
        f"http://localhost:{port}/health",
        "Gateway",
        timeout=30
    )

def start_worker(manager: ProcessManager, env_config: dict) -> bool:
    """Start Worker service"""
    print_header("Starting Worker")
    
    cmd = [
        str(VENV_BIN / "python3"),
        "-m", "gateway.app.core.worker"
    ]
    
    manager.start_process(cmd, "Worker", env_config)
    
    # Wait for worker to write heartbeat
    time.sleep(5)
    
    # Check readiness via Gateway
    port = env_config["NOOGH_PORT"]
    try:
        response = requests.get(f"http://localhost:{port}/ready", timeout=2)
        ready_status = response.json()
        
        if ready_status.get("worker"):
            print_success("Worker is ready!")
            return True
        else:
            print_warning(f"Worker not ready: {ready_status.get('error_worker', 'Unknown')}")
            return True  # Continue anyway
            
    except Exception as e:
        print_warning(f"Couldn't verify worker status: {e}")
        return True  # Continue anyway

# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="NOOGH Complete System Startup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--gateway-only", action="store_true",
                       help="Start only Gateway (no Worker)")
    parser.add_argument("--worker-only", action="store_true",
                       help="Start only Worker (no Gateway)")
    parser.add_argument("--no-redis", action="store_true",
                       help="Don't start Redis (assume it's running)")
    parser.add_argument("--dev", action="store_true",
                       help="Development mode (relaxed validations)")
    parser.add_argument("--port", type=int,
                       help="Override Gateway port")
    
    args = parser.parse_args()
    
    # Print banner
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════╗")
    print("║   NOOGH Complete System Startup        ║")
    print("╚════════════════════════════════════════╝")
    print(Colors.END)
    
    # Validate environment
    env_config = validate_environment(args.dev)
    
    # Override port if specified
    if args.port:
        env_config["NOOGH_PORT"] = str(args.port)
    
    # Add PYTHONPATH
    env_config["PYTHONPATH"] = str(PROJECT_ROOT)
    
    # Create process manager
    manager = ProcessManager()
    
    try:
        # Start Redis
        if not start_redis(manager, args):
            print_error("Redis startup failed")
            sys.exit(1)
        
        # Start Gateway
        if not args.worker_only:
            if not start_gateway(manager, env_config):
                print_error("Gateway startup failed")
                manager.shutdown()
                sys.exit(1)
        
        # Start Worker
        if not args.gateway_only:
            if not start_worker(manager, env_config):
                print_warning("Worker startup had issues, but continuing...")
        
        # Final status
        print_header("System Status")
        print_success("All services started successfully!")
        print()
        print(f"{Colors.BOLD}Service Endpoints:{Colors.END}")
        print(f"  Gateway:  http://localhost:{env_config['NOOGH_PORT']}")
        print(f"  Health:   http://localhost:{env_config['NOOGH_PORT']}/health")
        print(f"  Ready:    http://localhost:{env_config['NOOGH_PORT']}/ready")
        print(f"  Redis:    {env_config['REDIS_URL']}")
        print()
        print(f"{Colors.BOLD}Dashboard Access:{Colors.END}")
        print(f"  URL:      http://localhost:{env_config['NOOGH_PORT']}/dashboard")
        print(f"  {Colors.YELLOW}Token:    {env_config['NOOGH_ADMIN_TOKEN']}{Colors.END}")
        print(f"  {Colors.YELLOW}(Copy this token and paste in Dashboard > Settings > API Token){Colors.END}")
        print()
        print(f"{Colors.BOLD}Data Directory:{Colors.END} {env_config['NOOGH_DATA_DIR']}")
        print(f"{Colors.BOLD}Environment:{Colors.END} {env_config['NOOGH_ENV']}")
        print()
        print_info("Press CTRL+C to stop all services")
        
        # Keep running
        while True:
            time.sleep(10)
            
            # Check if processes are still alive
            for proc in manager.processes:
                if proc.poll() is not None:
                    print_error(f"Process {proc.pid} died unexpectedly!")
                    manager.shutdown()
                    sys.exit(1)
    
    except KeyboardInterrupt:
        print()  # New line after ^C
        manager.shutdown()
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        manager.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()
