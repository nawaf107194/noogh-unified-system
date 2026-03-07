#!/usr/bin/env python3
"""
NOOGH Agent Health Checker
==========================
فحص حالة جميع الوكلاء وإصلاح المعطلة تلقائياً
"""

import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

class AgentHealthChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.registry_path = self.project_root / "agents" / "agent_registry.json"
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": 0,
            "running": [],
            "stopped": [],
            "missing_files": [],
            "errors": []
        }

    def load_registry(self):
        """تحميل سجل الوكلاء"""
        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ خطأ في تحميل السجل: {e}")
            return []

    def check_process_running(self, agent_file):
        """فحص إذا كان الوكيل يعمل"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', agent_file],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except:
            return False

    def check_file_exists(self, agent_file):
        """فحص إذا كان ملف الوكيل موجود"""
        # Handle both relative and absolute paths
        if agent_file.startswith('/'):
            file_path = Path(agent_file)
        else:
            file_path = self.project_root / agent_file
        return file_path.exists()

    def check_all_agents(self):
        """فحص جميع الوكلاء"""
        agents = self.load_registry()
        self.report["total_agents"] = len(agents)

        print("🔍 فحص الوكلاء...")
        print("=" * 60)

        for agent in agents:
            name = agent.get("name", "Unknown")
            file = agent.get("file", "")
            role = agent.get("role", "")

            # Check if file exists
            file_exists = self.check_file_exists(file)
            if not file_exists:
                print(f"❌ {name}: ملف غير موجود ({file})")
                self.report["missing_files"].append({
                    "name": name,
                    "file": file
                })
                continue

            # Check if running
            is_running = self.check_process_running(file)

            if is_running:
                print(f"✅ {name}: يعمل")
                self.report["running"].append({
                    "name": name,
                    "role": role,
                    "file": file
                })
            else:
                print(f"⚠️  {name}: متوقف")
                self.report["stopped"].append({
                    "name": name,
                    "role": role,
                    "file": file
                })

        return self.report

    def print_summary(self):
        """طباعة ملخص الحالة"""
        print("\n" + "=" * 60)
        print("📊 ملخص الحالة:")
        print("=" * 60)
        print(f"إجمالي الوكلاء: {self.report['total_agents']}")
        print(f"✅ نشط: {len(self.report['running'])}")
        print(f"⚠️  متوقف: {len(self.report['stopped'])}")
        print(f"❌ ملفات مفقودة: {len(self.report['missing_files'])}")

        if self.report['stopped']:
            print("\n⚠️  الوكلاء المتوقفة:")
            for agent in self.report['stopped']:
                print(f"  - {agent['name']} ({agent['role']})")

        if self.report['missing_files']:
            print("\n❌ الملفات المفقودة:")
            for agent in self.report['missing_files']:
                print(f"  - {agent['name']}: {agent['file']}")

    def save_report(self):
        """حفظ التقرير"""
        report_file = self.project_root / "reports" / f"agent_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        print(f"\n💾 التقرير محفوظ في: {report_file}")

def main():
    print("🔧 NOOGH Agent Health Checker")
    print("=" * 60)

    checker = AgentHealthChecker()
    checker.check_all_agents()
    checker.print_summary()
    checker.save_report()

if __name__ == "__main__":
    main()
