#!/usr/bin/env python3
"""
NOOGH Dependency Audit Tool
===========================
فحص شامل للتبعيات وثغرات الأمان
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

class DependencyAuditor:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "total_packages": 0,
            "outdated": [],
            "security_issues": [],
            "conflicts": [],
            "recommendations": []
        }

    def get_installed_packages(self):
        """الحصول على قائمة الحزم المثبتة"""
        try:
            result = subprocess.run(
                ['pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                check=True
            )
            packages = json.loads(result.stdout)
            self.report["total_packages"] = len(packages)
            return packages
        except Exception as e:
            print(f"❌ خطأ في جلب الحزم: {e}")
            return []

    def check_outdated(self):
        """فحص الحزم القديمة"""
        try:
            result = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                self.report["outdated"] = [
                    {
                        "name": pkg["name"],
                        "current": pkg["version"],
                        "latest": pkg["latest_version"]
                    }
                    for pkg in outdated
                ]
                return len(outdated)
        except Exception as e:
            print(f"⚠️  تحذير: {e}")
            return 0

    def check_security(self):
        """فحص الثغرات الأمنية (يتطلب pip-audit)"""
        try:
            # Check if pip-audit is installed
            subprocess.run(['pip-audit', '--version'], capture_output=True, check=True)

            result = subprocess.run(
                ['pip-audit', '--format=json'],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                audit_data = json.loads(result.stdout)
                self.report["security_issues"] = audit_data.get("dependencies", [])
                return len(self.report["security_issues"])
        except subprocess.CalledProcessError:
            print("⚠️  pip-audit غير مثبت (اختياري)")
            self.report["recommendations"].append("تثبيت pip-audit: pip install pip-audit")
        except Exception as e:
            print(f"⚠️  تخطي فحص الأمان: {e}")
        return 0

    def check_conflicts(self):
        """فحص تعارضات التبعيات"""
        try:
            result = subprocess.run(
                ['pip', 'check'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                conflicts = result.stdout.strip().split('\n')
                self.report["conflicts"] = [c for c in conflicts if c]
                return len(self.report["conflicts"])
        except Exception as e:
            print(f"❌ خطأ في فحص التعارضات: {e}")
        return 0

    def generate_recommendations(self):
        """توليد التوصيات"""
        if self.report["outdated"]:
            # Group critical packages
            critical = ["fastapi", "uvicorn", "redis", "psutil", "transformers"]
            outdated_critical = [
                pkg for pkg in self.report["outdated"]
                if pkg["name"].lower() in critical
            ]

            if outdated_critical:
                self.report["recommendations"].append(
                    f"تحديث الحزم الحرجة ({len(outdated_critical)}): " +
                    ", ".join([p["name"] for p in outdated_critical[:5]])
                )

        if self.report["security_issues"]:
            self.report["recommendations"].append(
                f"إصلاح {len(self.report['security_issues'])} ثغرة أمنية"
            )

        if self.report["conflicts"]:
            self.report["recommendations"].append(
                "حل تعارضات التبعيات"
            )

    def print_summary(self):
        """طباعة الملخص"""
        print("\n" + "=" * 60)
        print("📊 ملخص التدقيق:")
        print("=" * 60)
        print(f"إجمالي الحزم: {self.report['total_packages']}")
        print(f"⚠️  قديمة: {len(self.report['outdated'])}")
        print(f"🔒 ثغرات أمنية: {len(self.report['security_issues'])}")
        print(f"⚔️  تعارضات: {len(self.report['conflicts'])}")

        if self.report["outdated"]:
            print("\n⚠️  أهم الحزم القديمة:")
            for pkg in self.report["outdated"][:10]:
                print(f"  - {pkg['name']}: {pkg['current']} → {pkg['latest']}")

        if self.report["security_issues"]:
            print("\n🔒 ثغرات أمنية:")
            for issue in self.report["security_issues"][:5]:
                print(f"  - {issue.get('name', 'Unknown')}: {issue.get('vulnerability', 'N/A')}")

        if self.report["recommendations"]:
            print("\n💡 التوصيات:")
            for rec in self.report["recommendations"]:
                print(f"  • {rec}")

    def save_report(self):
        """حفظ التقرير"""
        report_file = self.project_root / "reports" / f"dependency_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        print(f"\n💾 التقرير محفوظ في: {report_file}")

        # Save update commands
        if self.report["outdated"]:
            update_file = self.project_root / "scripts" / "update_dependencies.sh"
            with open(update_file, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# Auto-generated dependency update commands\n\n")
                for pkg in self.report["outdated"]:
                    f.write(f"pip install --upgrade {pkg['name']}\n")
            update_file.chmod(0o755)
            print(f"💾 أوامر التحديث في: {update_file}")

    def audit(self):
        """تنفيذ التدقيق الكامل"""
        print("🔍 NOOGH Dependency Audit")
        print("=" * 60)

        print("📦 فحص الحزم المثبتة...")
        self.get_installed_packages()

        print("⏫ فحص التحديثات...")
        self.check_outdated()

        print("🔒 فحص الأمان...")
        self.check_security()

        print("⚔️  فحص التعارضات...")
        self.check_conflicts()

        print("💡 توليد التوصيات...")
        self.generate_recommendations()

        self.print_summary()
        self.save_report()

def main():
    auditor = DependencyAuditor()
    auditor.audit()

if __name__ == "__main__":
    main()
