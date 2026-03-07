#!/usr/bin/env python3
"""
NOOGH Performance Monitor
=========================
نظام مراقبة الأداء الشامل للنظام
"""

import psutil
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class PerformanceMonitor:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "performance"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_system_metrics(self) -> Dict[str, Any]:
        """جمع مقاييس النظام"""
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
                "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                "percent": psutil.disk_usage('/').percent
            },
            "network": {
                "bytes_sent_mb": round(psutil.net_io_counters().bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(psutil.net_io_counters().bytes_recv / (1024**2), 2)
            }
        }

    def get_noogh_processes(self) -> list:
        """جمع معلومات عمليات NOOGH"""
        noogh_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_percent', 'cpu_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'noogh' in cmdline.lower() or 'agent' in cmdline.lower():
                    noogh_processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "memory_percent": round(proc.info['memory_percent'], 2),
                        "cpu_percent": round(proc.info['cpu_percent'], 2),
                        "cmdline": cmdline[:100]  # First 100 chars
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return noogh_processes

    def get_service_status(self) -> Dict[str, bool]:
        """فحص حالة الخدمات"""
        import subprocess

        services = {
            "redis": 6379,
            "gateway": 8001,
            "neural_engine": 8002,
            "ollama": 11434
        }

        status = {}
        for service, port in services.items():
            try:
                result = subprocess.run(
                    ['nc', '-z', 'localhost', str(port)],
                    capture_output=True,
                    timeout=2
                )
                status[service] = result.returncode == 0
            except:
                status[service] = False

        return status

    def collect_metrics(self) -> Dict[str, Any]:
        """جمع جميع المقاييس"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.get_system_metrics(),
            "noogh_processes": self.get_noogh_processes(),
            "services": self.get_service_status()
        }

    def save_metrics(self, metrics: Dict[str, Any]):
        """حفظ المقاييس"""
        # Save to daily file
        date_str = datetime.now().strftime('%Y%m%d')
        metrics_file = self.data_dir / f"metrics_{date_str}.jsonl"

        with open(metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metrics, ensure_ascii=False) + '\n')

    def print_current_status(self, metrics: Dict[str, Any]):
        """طباعة الحالة الحالية"""
        print("🔍 حالة النظام:")
        print("=" * 60)

        # System
        sys = metrics['system']
        print(f"💻 CPU: {sys['cpu']['percent']}% ({sys['cpu']['count']} cores)")
        print(f"🧠 RAM: {sys['memory']['used_gb']:.1f}GB / {sys['memory']['total_gb']:.1f}GB ({sys['memory']['percent']}%)")
        print(f"💾 Disk: {sys['disk']['used_gb']:.1f}GB / {sys['disk']['total_gb']:.1f}GB ({sys['disk']['percent']}%)")

        # Services
        print("\n🌐 الخدمات:")
        for service, status in metrics['services'].items():
            emoji = "✅" if status else "❌"
            print(f"  {emoji} {service}: {'نشط' if status else 'متوقف'}")

        # Processes
        print(f"\n🤖 عمليات NOOGH: {len(metrics['noogh_processes'])}")
        for proc in metrics['noogh_processes'][:5]:  # Top 5
            print(f"  - PID {proc['pid']}: RAM {proc['memory_percent']}%, CPU {proc['cpu_percent']}%")

        print("=" * 60)

    def monitor(self, interval: int = 60, duration: int = None):
        """مراقبة مستمرة"""
        print("🚀 بدء المراقبة...")
        start_time = time.time()

        try:
            while True:
                metrics = self.collect_metrics()
                self.save_metrics(metrics)
                self.print_current_status(metrics)

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break

                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n⏹️  توقف المراقبة")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='NOOGH Performance Monitor')
    parser.add_argument('--interval', type=int, default=60, help='فترة القياس بالثواني (default: 60)')
    parser.add_argument('--duration', type=int, help='مدة المراقبة بالثواني (optional)')
    parser.add_argument('--once', action='store_true', help='قياس واحد فقط')

    args = parser.parse_args()

    monitor = PerformanceMonitor()

    if args.once:
        metrics = monitor.collect_metrics()
        monitor.print_current_status(metrics)
        monitor.save_metrics(metrics)
    else:
        monitor.monitor(interval=args.interval, duration=args.duration)

if __name__ == "__main__":
    main()
