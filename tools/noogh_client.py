#!/usr/bin/env python3
"""
NOOGH API Python Client

Client بسيط للتعامل مع:
- GET /health
- GET /tree
- GET /all-files
- GET /file/{path}
- POST /file/{path}
- DELETE /file/{path}
- POST /execute
- POST /search
"""

import os
import sys
from typing import Any, Dict, Optional, List

import requests  # pip install requests

DEFAULT_BASE_URL = os.environ.get("NOOGH_API_BASE", "http://localhost:8888")
DEFAULT_TOKEN = os.environ.get("NOOGH_API_TOKEN", "noogh-project-access-2026-x7k9m2p4")


class NooghClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        token: str = DEFAULT_TOKEN,
        timeout: int = 30,
    ) -> None:
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        )

    # ---- helpers ----
    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = self.session.get(
            self._url(path), params=params, timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    def _post(
        self, path: str, json_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        resp = self.session.post(
            self._url(path), json=json_data, timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str) -> Dict[str, Any]:
        resp = self.session.delete(self._url(path), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ---- public methods ----
    def health(self) -> Dict[str, Any]:
        # لا يحتاج توكن، لكن نستخدم نفس الجلسة
        resp = requests.get(self._url("/health"), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def tree(self) -> Dict[str, Any]:
        return self._get("/tree")

    def all_files(self, pattern: str = "*.py") -> Dict[str, Any]:
        return self._get("/all-files", params={"pattern": pattern})

    def read_file(self, path: str) -> Dict[str, Any]:
        return self._get(f"/file/{path}")

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        data = {"content": content, "encoding": encoding}
        return self._post(f"/file/{path}", json_data=data)

    def delete_path(self, path: str) -> Dict[str, Any]:
        return self._delete(f"/file/{path}")

    def execute(
        self, command: str, cwd: Optional[str] = None, timeout: int = 30
    ) -> Dict[str, Any]:
        data = {"command": command, "cwd": cwd, "timeout": timeout}
        return self._post("/execute", json_data=data)

    def search(
        self,
        query: str,
        path: str = ".",
        file_pattern: str = "*.py",
    ) -> Dict[str, Any]:
        data = {"query": query, "path": path, "file_pattern": file_pattern}
        return self._post("/search", json_data=data)

    # ==== high-level helpers ==================================

    def run_tests(
        self,
        test_command: str = "pytest",
        cwd: Optional[str] = None,
        timeout: int = 600,
    ) -> Dict[str, Any]:
        """
        يشغّل اختبارات المشروع (افتراضياً pytest في مجلد src).
        cwd: مسار العمل (يجب أن يكون داخل /home/noogh/projects/noogh_unified_system)
        """
        if cwd is None:
            cwd = "/home/noogh/projects/noogh_unified_system/src"
        return self.execute(command=test_command, cwd=cwd, timeout=timeout)

    def restart_bot(
        self,
        stop_pattern: str,
        start_command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """
        يوقف البوت الحالي ثم يشغّله من جديد.
        stop_pattern: نص يطابق عملية البوت في ps/grep (مثلاً TrapLiveTrader أو اسم الملف).
        start_command: أمر تشغيل البوت (مثلاً: python3 trading/trap_live_trader.py).
        cwd: مسار العمل (يجب أن يكون داخل /home/noogh/projects/noogh_unified_system)
        """
        if cwd is None:
            cwd = "/home/noogh/projects/noogh_unified_system"

        # 1) إيقاف البوت
        stop_cmd = f"pkill -f '{stop_pattern}' || true"
        stop_res = self.execute(stop_cmd, cwd=cwd, timeout=timeout)

        # 2) تشغيل البوت
        start_res = self.execute(
            f"{start_command} >/tmp/noogh_bot.log 2>&1 & echo $!",
            cwd=cwd,
            timeout=timeout,
        )

        return {
            "stop": stop_res,
            "start": start_res,
        }

    def read_log(
        self,
        log_path: str = "/tmp/noogh_bot.log",
        tail_lines: int = 200,
    ) -> Dict[str, Any]:
        """
        يقرأ آخر N سطر من لوق معيّن (افتراضياً /tmp/noogh_bot.log).
        ملاحظة: المسار يجب أن يكون ضمن مجلد المشروع.
        """
        # استخدام tail عن طريق execute مع cwd داخل المشروع
        project_cwd = "/home/noogh/projects/noogh_unified_system/src"
        cmd = f"tail -n {tail_lines} {log_path} 2>&1 || echo 'Log file not found: {log_path}'"
        res = self.execute(cmd, cwd=project_cwd, timeout=30)
        return {
            "log_path": log_path,
            "tail_lines": tail_lines,
            "output": res.get("stdout", "") or res.get("stderr", ""),
        }


def main(argv: List[str]) -> None:
    """
    أمثلة استخدام سريعة من الـ CLI:
      python noogh_client.py health
      python noogh_client.py tree
      python noogh_client.py read unified_core/core/world_model.py
      python noogh_client.py exec "ls -R" .
      python noogh_client.py search "TrapLiveTrader" trading
    """
    client = NooghClient()

    if len(argv) < 2:
        print(main.__doc__)
        return

    cmd = argv[1]

    if cmd == "health":
        print(client.health())

    elif cmd == "tree":
        print(client.tree())

    elif cmd == "all":
        pattern = argv[2] if len(argv) > 2 else "*.py"
        print(client.all_files(pattern))

    elif cmd == "read":
        if len(argv) < 3:
            print("usage: python noogh_client.py read <relative_path>")
            return
        path = argv[2]
        res = client.read_file(path)
        print(f"# {res['path']} ({res['lines']} lines)")
        print(res["content"])

    elif cmd == "exec":
        if len(argv) < 3:
            print("usage: python noogh_client.py exec <command> [cwd]")
            return
        command = argv[2]
        cwd = argv[3] if len(argv) > 3 else None
        res = client.execute(command, cwd=cwd)
        print("exit_code:", res["exit_code"])
        print("--- STDOUT ---")
        print(res["stdout"])
        print("--- STDERR ---")
        print(res["stderr"])

    elif cmd == "search":
        if len(argv) < 3:
            print("usage: python noogh_client.py search <query> [path] [pattern]")
            return
        query = argv[2]
        path = argv[3] if len(argv) > 3 else "."
        pattern = argv[4] if len(argv) > 4 else "*.py"
        res = client.search(query, path=path, file_pattern=pattern)
        print(f"files_matched: {res['files_matched']}")
        for f in res["results"]:
            print("==", f["file"], "==")
            for m in f["matches"]:
                print(f"{m['line_num']:4d}: {m['text']}")

    else:
        print("Unknown command:", cmd)
        print(main.__doc__)


if __name__ == "__main__":
    main(sys.argv)
