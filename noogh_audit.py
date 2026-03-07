#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NOOGH Read-Only Audit Script
- Generates a detailed markdown report about:
  - Project tree (limited depth)
  - File counts / sizes
  - Key components discovery (AgentKernel / ReAct / ToolRegistry / Governance flags)
  - Duplicate/parallel implementations hints
  - Backup/old files detection
  - TODO/FIXME markers
  - Basic security keyword scan (informational, not enforcement)
Safe: READ-ONLY (no writes except report output).
"""

from __future__ import annotations
import os
import re
import sys
import json
import time
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

TEXT_EXT = {
    ".py", ".md", ".txt", ".yml", ".yaml", ".json", ".toml", ".ini",
    ".env", ".cfg", ".conf", ".sh", ".service", ".html", ".css", ".js"
}

BACKUP_PATTERNS = [
    r"\.bak$", r"\.backup$", r"\.old$", r"\.orig$", r"~$",
    r"_backup\.py$", r"\.backup_", r"\.swp$", r"\.tmp$",
]

KEY_FILES_HINTS = [
    "gateway/app/core/agent_kernel.py",
    "gateway/app/core/react_engine.py",
    "gateway/app/core/protocol.py",
    "neural_engine/reasoning/react_loop.py",
    "neural_engine/tools/tool_executor.py",
    "neural_engine/tools/tool_registry.py",
    "unified_core/core/actuators.py",
    "unified_core/governance/feature_flags.py",
]

KEY_SYMBOLS = {
    "AgentKernel": re.compile(r"\bclass\s+AgentKernel\b"),
    "ReActEngine": re.compile(r"\bclass\s+ReActEngine\b"),
    "SecureReActParser": re.compile(r"\bclass\s+SecureReActParser\b"),
    "ToolRegistry": re.compile(r"\bclass\s+ToolRegistry\b"),
    "ToolExecutor": re.compile(r"\bclass\s+ToolExecutor\b"),
    "GovernanceFlags": re.compile(r"NOOGH_GOVERNANCE_ENABLED|GOVERNANCE_ENABLED"),
    "NetworkActuator": re.compile(r"NetworkActuator"),
}

TODO_RE = re.compile(r"\b(TODO|FIXME|HACK)\b", re.IGNORECASE)

SECURITY_KEYWORDS = [
    "subprocess", "os.system", "eval(", "exec(", "__import__", "socket",
    "requests", "pty.spawn", "pexpect", "rm -rf", "curl ", "wget "
]

@dataclass
class FileHit:
    path: str
    line: int
    snippet: str

def is_text_file(p: Path) -> bool:
    return p.suffix.lower() in TEXT_EXT

def safe_read_text(p: Path, max_bytes: int = 2_000_000) -> str:
    # read up to max_bytes to avoid huge files
    with p.open("rb") as f:
        b = f.read(max_bytes)
    try:
        return b.decode("utf-8", errors="replace")
    except Exception:
        return b.decode(errors="replace")

def sha256_file(p: Path, max_bytes: int = 5_000_000) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        remaining = max_bytes
        while remaining > 0:
            chunk = f.read(min(65536, remaining))
            if not chunk:
                break
            h.update(chunk)
            remaining -= len(chunk)
    return h.hexdigest()

def build_tree(root: Path, max_depth: int = 4, max_entries: int = 600) -> str:
    lines = []
    count = 0
    root = root.resolve()

    def walk(dir_path: Path, depth: int):
        nonlocal count
        if depth > max_depth or count >= max_entries:
            return
        try:
            entries = sorted(dir_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except Exception:
            return
        for e in entries:
            if count >= max_entries:
                return
            # skip heavy/hidden dirs
            if e.name in {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache", ".pytest_cache"}:
                continue
            prefix = "  " * depth + ("- " if depth else "")
            if e.is_dir():
                lines.append(f"{prefix}{e.name}/")
                count += 1
                walk(e, depth + 1)
            else:
                lines.append(f"{prefix}{e.name}")
                count += 1

    lines.append(f"{root}/")
    walk(root, 1)
    if count >= max_entries:
        lines.append(f"... (tree truncated at {max_entries} entries)")
    return "\n".join(lines)

def find_hits_in_text(text: str, regex: re.Pattern, path: str, max_hits: int = 50) -> List[FileHit]:
    hits: List[FileHit] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if regex.search(line):
            snippet = line.strip()
            hits.append(FileHit(path=path, line=i, snippet=snippet[:200]))
            if len(hits) >= max_hits:
                break
    return hits

def scan_project(root: Path) -> Dict:
    root = root.resolve()
    report: Dict = {
        "meta": {
            "root": str(root),
            "generated_at": datetime.now().isoformat(),
        },
        "counts": {
            "total_files": 0,
            "total_dirs": 0,
            "text_files": 0,
            "python_files": 0,
            "bytes_total": 0,
        },
        "largest_files": [],
        "backup_files": [],
        "key_files_presence": {},
        "symbols": {k: [] for k in KEY_SYMBOLS.keys()},
        "todos": [],
        "security_keywords": [],
        "duplicates_by_hash": {},
        "toolregistry_candidates": [],
        "reactengine_candidates": [],
        "governance_flags": [],
    }

    # Collect files
    all_files: List[Path] = []
    all_dirs: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune heavy dirs
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache", ".pytest_cache"}]
        dpath = Path(dirpath)
        all_dirs.append(dpath)
        for fn in filenames:
            p = dpath / fn
            all_files.append(p)

    report["counts"]["total_files"] = len(all_files)
    report["counts"]["total_dirs"] = len(all_dirs)

    # Stats + largest files
    largest: List[Tuple[int, str]] = []
    text_files: List[Path] = []
    py_files: List[Path] = []
    backup_files: List[str] = []

    for p in all_files:
        try:
            st = p.stat()
            size = int(st.st_size)
            report["counts"]["bytes_total"] += size
            largest.append((size, str(p.relative_to(root))))
        except Exception:
            continue

        if any(re.search(bp, p.name, re.IGNORECASE) for bp in BACKUP_PATTERNS):
            backup_files.append(str(p.relative_to(root)))

        if is_text_file(p):
            text_files.append(p)
        if p.suffix.lower() == ".py":
            py_files.append(p)

    report["counts"]["text_files"] = len(text_files)
    report["counts"]["python_files"] = len(py_files)

    largest.sort(reverse=True, key=lambda x: x[0])
    report["largest_files"] = [{"path": path, "size_bytes": size} for size, path in largest[:25]]
    report["backup_files"] = sorted(backup_files)[:200]

    # Key files presence
    for k in KEY_FILES_HINTS:
        report["key_files_presence"][k] = (root / k).exists()

    # Duplicate detection by sha (only small/medium files to avoid cost)
    # limit to <= 5MB
    hashes: Dict[str, List[str]] = {}
    for p in all_files:
        try:
            if p.is_file():
                size = p.stat().st_size
                if size <= 5_000_000:
                    h = sha256_file(p)
                    rel = str(p.relative_to(root))
                    hashes.setdefault(h, []).append(rel)
        except Exception:
            pass
    dups = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    # keep only top 50 groups
    report["duplicates_by_hash"] = dict(list(sorted(dups.items(), key=lambda kv: len(kv[1]), reverse=True))[:50])

    # Scan text files for key symbols, todos, governance, ToolRegistry/ReActEngine candidates, security keywords
    sec_hits: List[FileHit] = []
    todo_hits: List[FileHit] = []
    gov_hits: List[FileHit] = []

    for p in text_files:
        rel = str(p.relative_to(root))
        try:
            text = safe_read_text(p)
        except Exception:
            continue

        # Symbols
        for sym, rx in KEY_SYMBOLS.items():
            hits = find_hits_in_text(text, rx, rel, max_hits=10)
            if hits:
                report["symbols"][sym].extend([{"path": h.path, "line": h.line, "snippet": h.snippet} for h in hits])

        # TODO/FIXME
        for i, line in enumerate(text.splitlines(), start=1):
            if TODO_RE.search(line):
                todo_hits.append(FileHit(rel, i, line.strip()))
                if len(todo_hits) >= 250:
                    break

        # Governance flags
        if "GOVERNANCE" in text or "NOOGH_GOVERNANCE" in text:
            for i, line in enumerate(text.splitlines(), start=1):
                if re.search(r"NOOGH_GOVERNANCE_ENABLED|GOVERNANCE_ENABLED|NOOGH_GOVERNANCE_DRY_RUN|DRY_RUN", line):
                    gov_hits.append(FileHit(rel, i, line.strip()))
                    if len(gov_hits) >= 80:
                        break

        # Candidates by filename patterns
        if rel.endswith("tool_registry.py") or "tool_registry" in rel:
            report["toolregistry_candidates"].append(rel)
        if rel.endswith("react_engine.py") or rel.endswith("react_loop.py") or "react_engine" in rel or "react_loop" in rel:
            report["reactengine_candidates"].append(rel)

        # Security keyword scan (informational)
        low = text.lower()
        if any(k.lower() in low for k in SECURITY_KEYWORDS):
            for i, line in enumerate(text.splitlines(), start=1):
                l = line.lower()
                if any(k.lower() in l for k in SECURITY_KEYWORDS):
                    sec_hits.append(FileHit(rel, i, line.strip()))
                    if len(sec_hits) >= 250:
                        break

    report["todos"] = [{"path": h.path, "line": h.line, "snippet": h.snippet[:200]} for h in todo_hits[:250]]
    report["governance_flags"] = [{"path": h.path, "line": h.line, "snippet": h.snippet[:200]} for h in gov_hits[:80]]
    report["security_keywords"] = [{"path": h.path, "line": h.line, "snippet": h.snippet[:200]} for h in sec_hits[:250]]

    # Sort candidates unique
    report["toolregistry_candidates"] = sorted(set(report["toolregistry_candidates"]))[:200]
    report["reactengine_candidates"] = sorted(set(report["reactengine_candidates"]))[:200]

    return report

def bytes_human(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024.0:
            return f"{x:.2f} {u}"
        x /= 1024.0
    return f"{x:.2f} PB"

def render_markdown(r: Dict) -> str:
    meta = r["meta"]
    c = r["counts"]

    lines: List[str] = []
    lines.append("# 📋 NOOGH Project Audit Report (Read-Only)")
    lines.append("")
    lines.append(f"- **Root:** `{meta['root']}`")
    lines.append(f"- **Generated:** `{meta['generated_at']}`")
    lines.append("")
    lines.append("## 1) Project Stats")
    lines.append("")
    lines.append(f"- Total dirs: **{c['total_dirs']}**")
    lines.append(f"- Total files: **{c['total_files']}**")
    lines.append(f"- Text files: **{c['text_files']}**")
    lines.append(f"- Python files: **{c['python_files']}**")
    lines.append(f"- Total size: **{bytes_human(c['bytes_total'])}**")
    lines.append("")

    lines.append("## 2) Key Files Presence")
    lines.append("")
    for k, ok in r["key_files_presence"].items():
        lines.append(f"- `{k}`: {'✅' if ok else '❌'}")
    lines.append("")

    lines.append("## 3) Largest Files (Top 25)")
    lines.append("")
    for it in r["largest_files"]:
        lines.append(f"- `{it['path']}` — {bytes_human(it['size_bytes'])}")
    lines.append("")

    lines.append("## 4) Backup/Old Files (Sample up to 200)")
    lines.append("")
    if r["backup_files"]:
        for p in r["backup_files"][:200]:
            lines.append(f"- `{p}`")
    else:
        lines.append("- (none detected)")
    lines.append("")

    lines.append("## 5) Duplicates by Hash (Top groups)")
    lines.append("")
    if r["duplicates_by_hash"]:
        for h, paths in list(r["duplicates_by_hash"].items())[:20]:
            lines.append(f"- **{len(paths)} files** share hash `{h[:12]}...`")
            for p in paths[:10]:
                lines.append(f"  - `{p}`")
            if len(paths) > 10:
                lines.append("  - ...")
    else:
        lines.append("- (no duplicates detected within scanned limits)")
    lines.append("")

    lines.append("## 6) Detected Core Symbols (Where classes/flags exist)")
    lines.append("")
    for sym, hits in r["symbols"].items():
        lines.append(f"### {sym}")
        if hits:
            for h in hits[:30]:
                lines.append(f"- `{h['path']}:{h['line']}` — {h['snippet']}")
            if len(hits) > 30:
                lines.append("- ...")
        else:
            lines.append("- (not found)")
        lines.append("")

    lines.append("## 7) ReAct / ToolRegistry Candidates")
    lines.append("")
    lines.append("### ReAct-related files")
    for p in r["reactengine_candidates"][:80]:
        lines.append(f"- `{p}`")
    if len(r["reactengine_candidates"]) > 80:
        lines.append("- ...")
    lines.append("")
    lines.append("### ToolRegistry-related files")
    for p in r["toolregistry_candidates"][:80]:
        lines.append(f"- `{p}`")
    if len(r["toolregistry_candidates"]) > 80:
        lines.append("- ...")
    lines.append("")

    lines.append("## 8) Governance Flags (Matches)")
    lines.append("")
    if r["governance_flags"]:
        for h in r["governance_flags"][:80]:
            lines.append(f"- `{h['path']}:{h['line']}` — {h['snippet']}")
    else:
        lines.append("- (no governance flag references found)")
    lines.append("")

    lines.append("## 9) TODO / FIXME / HACK (Sample)")
    lines.append("")
    if r["todos"]:
        for h in r["todos"][:120]:
            lines.append(f"- `{h['path']}:{h['line']}` — {h['snippet']}")
        if len(r["todos"]) > 120:
            lines.append("- ...")
    else:
        lines.append("- (none found)")
    lines.append("")

    lines.append("## 10) Security Keyword Scan (Informational)")
    lines.append("")
    if r["security_keywords"]:
        for h in r["security_keywords"][:120]:
            lines.append(f"- `{h['path']}:{h['line']}` — {h['snippet']}")
        if len(r["security_keywords"]) > 120:
            lines.append("- ...")
    else:
        lines.append("- (no hits)")
    lines.append("")

    lines.append("## 11) Project Tree (Depth-limited)")
    lines.append("")
    lines.append("```")
    lines.append(build_tree(Path(meta["root"]), max_depth=4, max_entries=600))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)

def main():
    import argparse

    ap = argparse.ArgumentParser(description="NOOGH Read-Only Audit Script -> Markdown report")
    ap.add_argument("root", nargs="?", default=".", help="Project root directory (default: current dir)")
    ap.add_argument("--out", default="NOOGH_AUDIT_REPORT.md", help="Output markdown file")
    ap.add_argument("--json-out", default="", help="Optional JSON output path (for automation)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: root not found or not a directory: {root}")
        sys.exit(2)

    start = time.time()
    r = scan_project(root)
    md = render_markdown(r)

    out_path = Path(args.out).resolve()
    out_path.write_text(md, encoding="utf-8")

    if args.json_out:
        jpath = Path(args.json_out).resolve()
        jpath.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")

    elapsed = (time.time() - start) * 1000
    print(f"✅ Report written: {out_path}")
    if args.json_out:
        print(f"✅ JSON written: {Path(args.json_out).resolve()}")
    print(f"⏱️ Done in {elapsed:.0f} ms")

if __name__ == "__main__":
    main()
