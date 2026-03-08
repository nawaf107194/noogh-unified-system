#!/usr/bin/env python3
"""
NOOGH Rapid Prototyping Agent - FIXED VERSION
Replace SandboxService with safe subprocess directly (no external deps)
Simulates an AI-first IDE environment (inspired by Cursor/Bolt/VibeCode).
"""
import asyncio
import logging
import os
import time
import json
import subprocess
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("agents.rapid_prototyping")

_BASE_WORKSPACE = Path("/tmp/noogh_rapid_workspace")
_BASE_WORKSPACE.mkdir(parents=True, exist_ok=True)

_LANG_MAP = {
    "python": ".py",
    "javascript": ".js",
    "bash": ".sh",
    "html": ".html",
    "css": ".css",
    "json": ".json",
}

_CODE_TEMPLATES = {
    "python": '#!/usr/bin/env python3\n"""\n{description}\n"""\nimport json\nimport logging\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n\ndef main():\n    logger.info("Starting: {name}")\n    # TODO: Implement logic here\n    return {"status": "success", "message": "Prototype running"}\n\nif __name__ == "__main__":\n    print(json.dumps(main(), indent=2))\n',
    "javascript": "'use strict';\n/**\n * {description}\n */\nasync function main() {{\n    console.log('Starting: {name}');\n    return {{ status: 'success' }};\n}}\nmain().then(r => console.log(JSON.stringify(r, null, 2)));\n",
    "bash": "#!/bin/bash\n# {description}\nset -euo pipefail\necho \"Starting: {name}\"\n# TODO: Implement logic\necho \"Done\"\n",
    "html": "<!DOCTYPE html>\n<html lang=\"en\">\n<head><meta charset=\"UTF-8\"><title>{name}</title></head>\n<body><h1>{name}</h1><p>{description}</p></body>\n</html>\n",
    "default": "# {name}\n# {description}\n# TODO: Implement\n"
}


class SafeSubprocess:
    """Safe subprocess executor with timeout."""
    ALLOWED = {"python3", "python", "node", "bash", "sh"}
    MAX_TIMEOUT = 30

    @classmethod
    def run(cls, cmd: list, cwd: str = None, timeout: int = 10) -> Dict:
        if not cmd or cmd[0] not in cls.ALLOWED:
            return {"success": False, "error": f"Not allowed: {cmd[0] if cmd else ''}", "stdout": "", "stderr": ""}
        timeout = min(timeout, cls.MAX_TIMEOUT)
        try:
            r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
            return {"success": r.returncode == 0, "returncode": r.returncode,
                    "stdout": r.stdout[:50000], "stderr": r.stderr[:10000]}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout {timeout}s", "stdout": "", "stderr": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "stdout": "", "stderr": ""}


class RapidPrototypingAgent:
    """
    Rapid Prototyping IDE module to generate instant code workspaces.
    FIXED: Uses safe subprocess instead of SandboxService (no external deps).
    """

    def __init__(self):
        self.handlers = {
            "RAPID_PROTOTYPE": self._rapid_prototype,
            "RUN_CODE": self._run_code,
            "LIST_WORKSPACES": self._list_workspaces,
        }
        self._running = False
        logger.info("\u2705 RapidPrototypingAgent initialized (safe subprocess mode)")

    def _detect_language(self, prompt: str) -> str:
        p = prompt.lower()
        if any(w in p for w in ["html", "web page", "frontend"]):
            return "html"
        elif any(w in p for w in ["javascript", "node", "react"]):
            return "javascript"
        elif any(w in p for w in ["bash", "shell", "linux"]):
            return "bash"
        return "python"

    async def _rapid_prototype(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a complete code prototype.
        Args:
            prompt (str): Description of what to build.
            language (str): Optional language override.
            run (bool): Whether to execute the prototype.
        """
        prompt = task.get("prompt", task.get("input", ""))
        if not prompt:
            return {"success": False, "error": "No prompt provided for rapid generation."}

        language = task.get("language", self._detect_language(prompt))
        should_run = task.get("run", False)

        logger.info(f"\U0001f527 Generating Rapid Prototype: {prompt[:50]}")

        workspace_id = f"noogh_proto_{int(time.time())}"
        workspace_dir = _BASE_WORKSPACE / workspace_id
        workspace_dir.mkdir(parents=True, exist_ok=True)

        ext = _LANG_MAP.get(language.lower(), ".py")
        name = "_".join(prompt.split()[:3]).lower()[:30]
        template = _CODE_TEMPLATES.get(language.lower(), _CODE_TEMPLATES["default"])
        code = template.format(name=name, description=prompt)

        target_file = workspace_dir / f"app{ext}"
        target_file.write_text(code, encoding="utf-8")

        meta = {"workspace_id": workspace_id, "prompt": prompt,
                "language": language, "file": str(target_file),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        (workspace_dir / "meta.json").write_text(json.dumps(meta, indent=2))

        result = {"success": True, "workspace_id": workspace_id,
                  "workspace_dir": str(workspace_dir), "file": str(target_file),
                  "language": language, "lines": len(code.splitlines()), "prompt": prompt}

        if should_run and language in ("python", "javascript", "bash"):
            result["execution"] = await self._execute_file(str(target_file), language)

        logger.info(f"\u2705 Prototype created: {workspace_id}")
        return result

    async def _execute_file(self, file_path: str, language: str) -> Dict:
        cmd_map = {"python": ["python3", file_path], "javascript": ["node", file_path], "bash": ["bash", file_path]}
        cmd = cmd_map.get(language)
        if not cmd:
            return {"success": False, "error": f"Cannot execute: {language}"}
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: SafeSubprocess.run(cmd, cwd=str(Path(file_path).parent), timeout=15)
        )

    async def _run_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        code = task.get("code", "")
        language = task.get("language", "python")
        if not code:
            return {"success": False, "error": "No code provided"}
        ext = _LANG_MAP.get(language.lower(), ".py")
        with tempfile.NamedTemporaryFile(suffix=ext, mode="w", encoding="utf-8", delete=False) as f:
            f.write(code)
            tmp = f.name
        try:
            return {"success": True, "execution": await self._execute_file(tmp, language)}
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass

    async def _list_workspaces(self, task: Dict[str, Any]) -> Dict[str, Any]:
        workspaces = []
        for d in sorted(_BASE_WORKSPACE.iterdir(), reverse=True):
            if d.is_dir():
                meta_file = d / "meta.json"
                if meta_file.exists():
                    try:
                        workspaces.append(json.loads(meta_file.read_text()))
                    except Exception:
                        workspaces.append({"workspace_id": d.name})
        return {"success": True, "workspaces": workspaces[:20], "total": len(workspaces)}

    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", task.get("type", "")).upper()
        handler = self.handlers.get(action)
        if handler:
            return await handler(task)
        return await self._rapid_prototype(task)

    def start(self):
        self._running = True
        logger.info("\U0001f7e2 RapidPrototypingAgent started")

    def stop(self):
        self._running = False
        logger.info("\U0001f534 RapidPrototypingAgent stopped")


if __name__ == "__main__":
    async def main():
        logging.basicConfig(level=logging.INFO)
        agent = RapidPrototypingAgent()
        agent.start()
        result = await agent.handle_task({
            "action": "RAPID_PROTOTYPE",
            "prompt": "Create a data scraper that reads URLs and saves results",
            "language": "python",
            "run": False
        })
        print(json.dumps(result, indent=2, ensure_ascii=False))
    asyncio.run(main())
