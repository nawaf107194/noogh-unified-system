#!/usr/bin/env python3
"""
NOOGH Complete System Launcher
==============================

Starts ALL system components:
1. Redis (via Docker)
2. Neural Engine (Port 8000) - LLM Backend
3. Gateway (Port 8001) - API + Dashboard + Chat
4. Agent Daemon - Autonomous AI (GPU)

Usage:
    python3 start_full_system.py
    python3 start_full_system.py --no-agent  # Without Agent Daemon
"""

import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

# Set environment
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.chdir("/home/noogh/projects/noogh_unified_system/src")
sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")


def print_banner():
    print(f"""
{BOLD}{BLUE}╔═══════════════════════════════════════════════════════════╗
║                                                             ║
║   ███╗   ██╗ ██████╗  ██████╗  ██████╗ ██╗  ██╗            ║
║   ████╗  ██║██╔═══██╗██╔═══██╗██╔════╝ ██║  ██║            ║
║   ██╔██╗ ██║██║   ██║██║   ██║██║  ███╗███████║            ║
║   ██║╚██╗██║██║   ██║██║   ██║██║   ██║██╔══██║            ║
║   ██║ ╚████║╚██████╔╝╚██████╔╝╚██████╔╝██║  ██║            ║
║   ╚═╝  ╚═══╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝            ║
║                                                             ║
║   GENUINE AI AGENT - AUTONOMOUS SYSTEM                     ║
║                                                             ║
╚═══════════════════════════════════════════════════════════╝{END}
""")


class SystemLauncher:
    def __init__(self):
        self.processes = {}
        self.agent_task = None
        self._shutdown = False
    
    def log(self, icon, msg, color=END):
        print(f"{color}{icon} {msg}{END}")
    
    def success(self, msg):
        self.log("✅", msg, GREEN)
    
    def error(self, msg):
        self.log("❌", msg, RED)
    
    def info(self, msg):
        self.log("ℹ️ ", msg, BLUE)
    
    def warn(self, msg):
        self.log("⚠️ ", msg, YELLOW)
    
    def header(self, msg):
        print(f"\n{BOLD}{BLUE}{'─'*50}{END}")
        print(f"{BOLD}  {msg}{END}")
        print(f"{BOLD}{BLUE}{'─'*50}{END}\n")
    
    def run_cmd(self, cmd, name, background=True):
        """Run command as background process."""
        log_file = open(f"{name.lower().replace(' ', '_')}.log", "w")
        
        if background:
            proc = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=log_file,
                cwd="/home/noogh/projects/noogh_unified_system/src"
            )
            self.processes[name] = proc
            self.success(f"{name} started (PID: {proc.pid})")
            return proc
        else:
            return subprocess.run(cmd, capture_output=True)
    
    def wait_http(self, url, name, timeout=120):
        """Wait for HTTP service."""
        import requests
        
        self.info(f"Waiting for {name}...")
        for i in range(timeout):
            try:
                r = requests.get(url, timeout=2)
                if r.status_code < 500:
                    self.success(f"{name} is ready!")
                    return True
            except Exception:
                pass
            time.sleep(1)
        
        self.error(f"{name} failed to start after {timeout}s")
        return False
    
    def start_redis(self):
        """Start Redis via Docker."""
        self.header("Starting Redis")
        
        # Check if port 6379 is already occupied
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', 6379)) == 0:
                self.success("Redis port 6379 already in use (assuming Redis is running)")
                return True

        # Check if running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=noogh-redis", "-q"],
            capture_output=True, text=True
        )
        
        if result.stdout.strip():
            self.success("Redis already running")
            return True
        
        # Start new container
        subprocess.run(["docker", "rm", "-f", "noogh-redis"], 
                      capture_output=True)
        
        result = subprocess.run([
            "docker", "run", "-d",
            "--name", "noogh-redis",
            "-p", "6379:6379",
            "redis:7-alpine"
        ], capture_output=True)
        
        if result.returncode == 0:
            self.success("Redis started")
            time.sleep(2)
            return True
        
        self.error("Failed to start Redis")
        return False
    
    def start_neural_engine(self):
        """Start Neural Engine on port 8000."""
        self.header("Starting Neural Engine")
        
        # Load .env
        from dotenv import load_dotenv
        load_dotenv()
        
        cmd = [
            sys.executable, "-m", "uvicorn",
            "neural_engine.api.main:app",
            "--host", "127.0.0.1",
            "--port", "8000"
        ]
        
        self.run_cmd(cmd, "Neural Engine")
        return self.wait_http("http://localhost:8000/health", "Neural Engine")
    
    def start_gateway(self):
        """Start Gateway on port 8001."""
        self.header("Starting Gateway")
        
        cmd = [
            sys.executable, "-m", "uvicorn",
            "gateway.app.main:app",
            "--host", "127.0.0.1",
            "--port", "8001"
        ]
        
        self.run_cmd(cmd, "Gateway")
        return self.wait_http("http://localhost:8001/health", "Gateway")
    
    async def start_agent_daemon(self):
        """Start Agent Daemon (autonomous GPU)."""
        self.header("Starting Agent Daemon (GPU)")
        
        from unified_core.agent_daemon import AgentDaemon
        
        daemon = AgentDaemon(loop_interval=3.0)
        
        if not await daemon.initialize():
            self.error("Agent Daemon initialization failed")
            return None
        
        self.success("Agent Daemon initialized")
        
        # Run in background task
        self.agent_task = asyncio.create_task(daemon.run_forever())
        return daemon
    
    def print_status(self, daemon=None):
        """Print system status."""
        self.header("System Status")
        
        print(f"{BOLD}Services:{END}")
        print(f"  Redis:         {'✅ Running' if 'redis' not in [p.poll() for p in self.processes.values() if p] else '⚠️  Check'}")
        print(f"  Neural Engine: http://localhost:8000")
        print(f"  Gateway:       http://localhost:8001")
        print(f"  Agent Daemon:  {'✅ Autonomous Mode' if daemon else '⚠️  Not started'}")
        
        print(f"\n{BOLD}Access Points:{END}")
        print(f"  🌐 Dashboard:    http://localhost:8001/")
        print(f"  💬 Chat:         http://localhost:8001/dashboard")
        print(f"  📊 API Docs:     http://localhost:8001/docs")
        print(f"  🔧 Neural API:   http://localhost:8000/docs")
        
        if daemon:
            status = daemon.get_status()
            print(f"\n{BOLD}Agent Status:{END}")
            print(f"  State:    {status['state'].upper()}")
            print(f"  Device:   {status.get('gpu', {}).get('device', 'cpu')}")
            if 'gpu_info' in status.get('gpu', {}):
                gpu = status['gpu']['gpu_info']
                print(f"  GPU:      {gpu['name']}")
        
        print(f"\n{YELLOW}Press Ctrl+C to stop all services{END}\n")
    
    async def shutdown(self, daemon=None):
        """Shutdown all services."""
        self._shutdown = True
        self.header("Shutting Down")
        
        # Stop agent daemon
        if daemon:
            self.info("Stopping Agent Daemon...")
            await daemon.shutdown()
            if self.agent_task:
                self.agent_task.cancel()
        
        # Stop processes
        for name, proc in self.processes.items():
            if proc and proc.poll() is None:
                self.info(f"Stopping {name}...")
                proc.terminate()
        
        time.sleep(2)
        
        # Force kill if needed
        for name, proc in self.processes.items():
            if proc and proc.poll() is None:
                proc.kill()
        
        self.success("All services stopped")
    
    async def run(self, with_agent=True):
        """Run complete system."""
        print_banner()
        
        # Start services
        if not self.start_redis():
            return
        
        if not self.start_neural_engine():
            return
        
        if not self.start_gateway():
            return
        
        # Start agent daemon
        daemon = None
        if with_agent:
            daemon = await self.start_agent_daemon()
        
        # Print status
        self.print_status(daemon)
        
        # Wait for shutdown
        try:
            while not self._shutdown:
                await asyncio.sleep(5)
                
                # Check processes
                for name, proc in self.processes.items():
                    if proc and proc.poll() is not None:
                        self.error(f"{name} died unexpectedly!")
        
        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown(daemon)


def main():
    launcher = SystemLauncher()
    
    # Parse args
    with_agent = "--no-agent" not in sys.argv
    
    # Setup signal handler
    def signal_handler(sig, frame):
        print("\n")
        asyncio.get_event_loop().stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    try:
        asyncio.run(launcher.run(with_agent=with_agent))
    except KeyboardInterrupt:
        asyncio.run(launcher.shutdown())


if __name__ == "__main__":
    main()
