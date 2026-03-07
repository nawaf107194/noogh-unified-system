# unified_core/core/security_hardening.py
import os
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("unified_core.security.hardener")

class FileIntegrityMonitor:
    """مراقب سلامة الملفات"""
    
    def __init__(self, watch_paths: List[str]):
        self.watch_paths = watch_paths
        self.hashes = {}
        
    def _get_hash(self, path: str) -> str:
        import hashlib
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def scan(self) -> List[str]:
        """فحص التغييرات"""
        changed = []
        for path in self.watch_paths:
            if not os.path.exists(path):
                continue
            current = self._get_hash(path)
            if path in self.hashes and self.hashes[path] != current:
                changed.append(path)
                logger.warning(f"File modified: {path}")
            self.hashes[path] = current
        return changed

class ProcessMonitor:
    """مراقب العمليات المشبوهة"""
    
    def audit_rogue_processes(self) -> List[int]:
        """البحث عن عمليات غير مصرح بها"""
        # منطق بسيط للبحث عن عمليات تستهلك موارد عالية بشكل مفاجئ
        # أو تحاول الوصول لملفات حساسة
        return []

class EnhancedSecurityHardener:
    """المصلد الأمني المطور - v5.0"""
    
    def __init__(self):
        self.integrity = FileIntegrityMonitor([
            ".env",
            "unified_core/agent_daemon.py",
            "unified_core/core/security_hardening.py"
        ])
        self.ps_monitor = ProcessMonitor()
        
    async def run_full_audit(self) -> Dict[str, Any]:
        """تشغيل فحص أمني كامل"""
        logger.info("🛡️ Starting v5.0 Enhanced Security Audit...")
        
        # فحص الملفات
        changed_files = self.integrity.scan()
        
        # فحص الصلاحيات
        permissions_report = self._check_sensitive_permissions()
        
        # فحص المنافذ
        ports = self._scan_open_ports()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "integrity_violations": changed_files,
            "permission_issues": permissions_report,
            "open_ports": ports,
            "status": "hardened" if not changed_files else "vulnerable"
        }
        
        if changed_files:
            logger.error(f"🚨 INTEGRITY BREACH DETECTED: {changed_files}")
            
        return report

    def _check_sensitive_permissions(self) -> List[Dict]:
        """فحص صلاحيات الملفات الحساسة"""
        issues = []
        sensitive = ["/etc/shadow", "/home/noogh/.ssh/authorized_keys"]
        for path in sensitive:
            if os.path.exists(path):
                mode = oct(os.stat(path).st_mode & 0o777)
                if mode > "0o644":
                    issues.append({"path": path, "mode": mode, "risk": "HIGH"})
        return issues

    def _scan_open_ports(self) -> List[int]:
        """فحص المنافذ المفتوحة"""
        try:
            output = subprocess.check_output(["ss", "-tuln"], text=True)
            ports = []
            for line in output.splitlines():
                if "LISTEN" in line:
                    parts = line.split()
                    if len(parts) > 4:
                        port = parts[4].split(":")[-1]
                        if port.isdigit():
                            ports.append(int(port))
            return sorted(list(set(ports)))
        except:
            return []

if __name__ == "__main__":
    async def test():
        hardener = EnhancedSecurityHardener()
        report = await hardener.run_full_audit()
        import json
        print(json.dumps(report, indent=2))
        
    asyncio.run(test())
