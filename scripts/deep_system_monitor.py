#!/usr/bin/env python3
"""
NOOGH Deep System Monitor
=========================
مراقبة عميقة وشاملة لجميع مكونات النظام
"""

import psutil
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import socket

class DeepSystemMonitor:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "system": {},
            "processes": {},
            "services": {},
            "network": {},
            "disk_io": {},
            "database": {},
            "logs": {},
            "alerts": []
        }

    def get_detailed_cpu_info(self) -> Dict[str, Any]:
        """معلومات CPU مفصلة"""
        cpu_freq = psutil.cpu_freq()
        cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)

        return {
            "total_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "current_freq_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
            "min_freq_mhz": round(cpu_freq.min, 2) if cpu_freq else None,
            "max_freq_mhz": round(cpu_freq.max, 2) if cpu_freq else None,
            "overall_percent": psutil.cpu_percent(interval=1),
            "per_core_percent": [round(p, 1) for p in cpu_percent_per_core],
            "load_average": [round(x, 2) for x in psutil.getloadavg()],
            "context_switches": psutil.cpu_stats().ctx_switches,
            "interrupts": psutil.cpu_stats().interrupts
        }

    def get_detailed_memory_info(self) -> Dict[str, Any]:
        """معلومات الذاكرة مفصلة"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "virtual": {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "free_gb": round(mem.free / (1024**3), 2),
                "percent": mem.percent,
                "cached_gb": round(mem.cached / (1024**3), 2) if hasattr(mem, 'cached') else None,
                "buffers_gb": round(mem.buffers / (1024**3), 2) if hasattr(mem, 'buffers') else None
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "free_gb": round(swap.free / (1024**3), 2),
                "percent": swap.percent
            }
        }

    def get_detailed_disk_info(self) -> Dict[str, Any]:
        """معلومات القرص مفصلة"""
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()

        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                })
            except PermissionError:
                pass

        return {
            "root": {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "percent": disk_usage.percent
            },
            "io_counters": {
                "read_mb": round(disk_io.read_bytes / (1024**2), 2),
                "write_mb": round(disk_io.write_bytes / (1024**2), 2),
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count
            } if disk_io else None,
            "partitions": partitions
        }

    def get_network_info(self) -> Dict[str, Any]:
        """معلومات الشبكة مفصلة"""
        net_io = psutil.net_io_counters()
        connections = psutil.net_connections(kind='inet')

        # Count connections by status
        conn_status = {}
        for conn in connections:
            status = conn.status
            conn_status[status] = conn_status.get(status, 0) + 1

        return {
            "io_counters": {
                "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout
            },
            "connections": {
                "total": len(connections),
                "by_status": conn_status
            }
        }

    def get_noogh_processes_detailed(self) -> List[Dict[str, Any]]:
        """معلومات مفصلة عن عمليات NOOGH"""
        noogh_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info',
                                         'cpu_percent', 'create_time', 'num_threads']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'noogh' in cmdline.lower() or any(keyword in cmdline.lower()
                    for keyword in ['agent', 'neural', 'gateway', 'redis']):

                    mem_info = proc.info['memory_info']
                    create_time = datetime.fromtimestamp(proc.info['create_time'])
                    uptime = datetime.now() - create_time

                    noogh_processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cmdline": cmdline[:150],
                        "memory_mb": round(mem_info.rss / (1024**2), 2),
                        "memory_percent": round(psutil.Process(proc.info['pid']).memory_percent(), 2),
                        "cpu_percent": round(proc.info['cpu_percent'], 2),
                        "num_threads": proc.info['num_threads'],
                        "uptime_hours": round(uptime.total_seconds() / 3600, 2),
                        "status": psutil.Process(proc.info['pid']).status()
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return sorted(noogh_processes, key=lambda x: x['memory_mb'], reverse=True)

    def check_services_detailed(self) -> Dict[str, Any]:
        """فحص مفصل للخدمات"""
        services = {
            "redis": {"port": 6379, "status": False, "response_time_ms": None},
            "gateway": {"port": 8001, "status": False, "response_time_ms": None},
            "neural_engine": {"port": 8002, "status": False, "response_time_ms": None},
            "ollama": {"port": 11434, "status": False, "response_time_ms": None}
        }

        for service, config in services.items():
            try:
                start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', config['port']))
                sock.close()

                if result == 0:
                    config['status'] = True
                    config['response_time_ms'] = round((time.time() - start) * 1000, 2)
            except:
                pass

        return services

    def check_database_status(self) -> Dict[str, Any]:
        """فحص حالة قواعد البيانات"""
        db_status = {
            "sqlite": {"status": False, "size_mb": 0, "path": None},
            "chroma": {"status": False, "size_mb": 0, "path": None}
        }

        # Check SQLite
        sqlite_files = list(self.project_root.glob("data/**/*.db")) + \
                       list(self.project_root.glob("data/**/*.sqlite"))
        if sqlite_files:
            db_status["sqlite"]["status"] = True
            db_status["sqlite"]["path"] = str(sqlite_files[0])
            db_status["sqlite"]["size_mb"] = round(sqlite_files[0].stat().st_size / (1024**2), 2)

        # Check ChromaDB
        chroma_path = self.project_root / "data" / "chroma"
        if chroma_path.exists():
            db_status["chroma"]["status"] = True
            db_status["chroma"]["path"] = str(chroma_path)
            total_size = sum(f.stat().st_size for f in chroma_path.rglob('*') if f.is_file())
            db_status["chroma"]["size_mb"] = round(total_size / (1024**2), 2)

        return db_status

    def analyze_recent_logs(self) -> Dict[str, Any]:
        """تحليل السجلات الأخيرة"""
        log_analysis = {
            "total_log_files": 0,
            "total_size_mb": 0,
            "recent_errors": [],
            "recent_warnings": []
        }

        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            log_analysis["total_log_files"] = len(log_files)
            log_analysis["total_size_mb"] = round(
                sum(f.stat().st_size for f in log_files) / (1024**2), 2
            )

            # Analyze recent logs (last 100 lines)
            for log_file in log_files[:3]:  # Check first 3 log files
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()[-100:]
                        for line in lines:
                            if 'ERROR' in line.upper():
                                log_analysis["recent_errors"].append({
                                    "file": log_file.name,
                                    "message": line.strip()[:200]
                                })
                            elif 'WARNING' in line.upper():
                                log_analysis["recent_warnings"].append({
                                    "file": log_file.name,
                                    "message": line.strip()[:200]
                                })
                except:
                    pass

        return log_analysis

    def generate_alerts(self):
        """توليد التنبيهات"""
        # CPU alerts
        if self.report["system"]["cpu"]["overall_percent"] > 80:
            self.report["alerts"].append({
                "level": "warning",
                "component": "CPU",
                "message": f"استخدام CPU مرتفع: {self.report['system']['cpu']['overall_percent']}%"
            })

        # Memory alerts
        mem_percent = self.report["system"]["memory"]["virtual"]["percent"]
        if mem_percent > 85:
            self.report["alerts"].append({
                "level": "critical",
                "component": "Memory",
                "message": f"الذاكرة ممتلئة: {mem_percent}%"
            })
        elif mem_percent > 75:
            self.report["alerts"].append({
                "level": "warning",
                "component": "Memory",
                "message": f"استخدام الذاكرة مرتفع: {mem_percent}%"
            })

        # Disk alerts
        disk_percent = self.report["system"]["disk"]["root"]["percent"]
        if disk_percent > 90:
            self.report["alerts"].append({
                "level": "critical",
                "component": "Disk",
                "message": f"القرص ممتلئ: {disk_percent}%"
            })
        elif disk_percent > 80:
            self.report["alerts"].append({
                "level": "warning",
                "component": "Disk",
                "message": f"مساحة القرص منخفضة: {disk_percent}%"
            })

        # Service alerts
        for service, config in self.report["services"].items():
            if not config["status"]:
                self.report["alerts"].append({
                    "level": "critical",
                    "component": service,
                    "message": f"الخدمة {service} متوقفة"
                })

        # Process alerts
        for proc in self.report["processes"][:5]:
            if proc["memory_percent"] > 10:
                self.report["alerts"].append({
                    "level": "info",
                    "component": "Process",
                    "message": f"العملية {proc['name']} (PID {proc['pid']}) تستخدم {proc['memory_percent']}% من الذاكرة"
                })

    def monitor_deep(self):
        """مراقبة عميقة شاملة"""
        print("🔍 NOOGH Deep System Monitor")
        print("=" * 80)

        print("\n📊 جمع البيانات...")

        # Collect all data
        self.report["system"]["cpu"] = self.get_detailed_cpu_info()
        self.report["system"]["memory"] = self.get_detailed_memory_info()
        self.report["system"]["disk"] = self.get_detailed_disk_info()
        self.report["system"]["network"] = self.get_network_info()

        self.report["processes"] = self.get_noogh_processes_detailed()
        self.report["services"] = self.check_services_detailed()
        self.report["database"] = self.check_database_status()
        self.report["logs"] = self.analyze_recent_logs()

        # Generate alerts
        self.generate_alerts()

        # Print detailed report
        self.print_detailed_report()

        # Save report
        self.save_report()

    def print_detailed_report(self):
        """طباعة تقرير مفصل"""
        print("\n" + "=" * 80)
        print("📊 تقرير المراقبة العميقة")
        print("=" * 80)

        # CPU
        cpu = self.report["system"]["cpu"]
        print(f"\n💻 المعالج (CPU):")
        print(f"  الأنوية: {cpu['total_cores']} فيزيائية، {cpu['logical_cores']} منطقية")
        print(f"  التردد: {cpu['current_freq_mhz']} MHz (Max: {cpu['max_freq_mhz']} MHz)")
        print(f"  الاستخدام الكلي: {cpu['overall_percent']}%")
        print(f"  Load Average: {cpu['load_average']}")

        # Memory
        mem = self.report["system"]["memory"]["virtual"]
        swap = self.report["system"]["memory"]["swap"]
        print(f"\n🧠 الذاكرة (RAM):")
        print(f"  المستخدم: {mem['used_gb']:.1f}GB / {mem['total_gb']:.1f}GB ({mem['percent']}%)")
        print(f"  المتاح: {mem['available_gb']:.1f}GB")
        print(f"  Swap: {swap['used_gb']:.1f}GB / {swap['total_gb']:.1f}GB ({swap['percent']}%)")

        # Disk
        disk = self.report["system"]["disk"]["root"]
        print(f"\n💾 القرص:")
        print(f"  المستخدم: {disk['used_gb']:.1f}GB / {disk['total_gb']:.1f}GB ({disk['percent']}%)")
        print(f"  المتاح: {disk['free_gb']:.1f}GB")

        if self.report["system"]["disk"]["io_counters"]:
            io = self.report["system"]["disk"]["io_counters"]
            print(f"  I/O: قراءة {io['read_mb']:.1f}MB، كتابة {io['write_mb']:.1f}MB")

        # Network
        net = self.report["system"]["network"]["io_counters"]
        print(f"\n🌐 الشبكة:")
        print(f"  مُرسل: {net['bytes_sent_mb']:.1f}MB")
        print(f"  مُستقبَل: {net['bytes_recv_mb']:.1f}MB")
        print(f"  الاتصالات: {self.report['system']['network']['connections']['total']}")

        # Services
        print(f"\n🔌 الخدمات:")
        for service, config in self.report["services"].items():
            status = "✅ نشط" if config["status"] else "❌ متوقف"
            response = f" ({config['response_time_ms']}ms)" if config["response_time_ms"] else ""
            print(f"  {status} {service}:{config['port']}{response}")

        # Processes
        print(f"\n🤖 عمليات NOOGH (أعلى 5 حسب الذاكرة):")
        for proc in self.report["processes"][:5]:
            print(f"  PID {proc['pid']:6} | {proc['name']:20} | "
                  f"RAM: {proc['memory_mb']:7.1f}MB ({proc['memory_percent']:4.1f}%) | "
                  f"CPU: {proc['cpu_percent']:4.1f}% | "
                  f"Uptime: {proc['uptime_hours']:.1f}h")

        # Database
        print(f"\n🗄️  قواعد البيانات:")
        for db_name, db_info in self.report["database"].items():
            status = "✅" if db_info["status"] else "❌"
            size = f"{db_info['size_mb']}MB" if db_info["status"] else "N/A"
            print(f"  {status} {db_name}: {size}")

        # Logs
        logs = self.report["logs"]
        print(f"\n📝 السجلات:")
        print(f"  عدد الملفات: {logs['total_log_files']}")
        print(f"  الحجم الكلي: {logs['total_size_mb']:.1f}MB")
        print(f"  أخطاء حديثة: {len(logs['recent_errors'])}")
        print(f"  تحذيرات حديثة: {len(logs['recent_warnings'])}")

        # Alerts
        if self.report["alerts"]:
            print(f"\n⚠️  التنبيهات ({len(self.report['alerts'])}):")
            for alert in self.report["alerts"]:
                emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert["level"], "⚪")
                print(f"  {emoji} [{alert['level'].upper()}] {alert['component']}: {alert['message']}")
        else:
            print(f"\n✅ لا توجد تنبيهات - النظام يعمل بشكل مثالي!")

        print("\n" + "=" * 80)

    def save_report(self):
        """حفظ التقرير"""
        report_dir = self.project_root / "reports" / "deep_monitoring"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f"deep_monitor_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        print(f"💾 التقرير الكامل محفوظ في: {report_file}")

def main():
    monitor = DeepSystemMonitor()
    monitor.monitor_deep()

if __name__ == "__main__":
    main()
