# tools_endpoint_map.py
import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

ROUTE_RE = re.compile(r'@router\.(get|post|put|delete|patch)\(\s*"(?P<path>/[^"]*)"')
PREFIX_RE = re.compile(r'prefix\s*=\s*"(?P<prefix>/[^"]*)"')
INCLUDE_RE = re.compile(r'include_router\((?P<args>[^)]*)\)')
MOUNT_RE = re.compile(r'app\.mount\(\s*"(?P<path>/[^"]*)"')
HTTP_CALL_RE = re.compile(
    r'(httpx|requests|aiohttp)\.(get|post|put|delete|patch)\(|'
    r'client\.(get|post|put|delete|patch)\('
)
URL_LITERAL_RE = re.compile(r'("|\')(?P<url>/(api/[^"\']*|task|chat|process|execute)[^"\']*)\1')
HOST_RE = re.compile(r'(127\.0\.0\.1|localhost|:\d{2,5}/)')

def iter_py_files(roots: List[str]) -> List[Path]:
    files: List[Path] = []
    for r in roots:
        p = Path(r)
        if not p.exists():
            continue
        for f in p.rglob("*.py"):
            # skip venv-ish or cache
            if "__pycache__" in f.parts:
                continue
            files.append(f)
    return files

def scan_file(path: Path) -> Dict:
    text = path.read_text(errors="ignore")
    routes = []
    for m in ROUTE_RE.finditer(text):
        routes.append({
            "method": m.group(1).upper(),
            "path": m.group("path"),
            "lineno": text.count("\n", 0, m.start()) + 1
        })

    prefixes = []
    for m in PREFIX_RE.finditer(text):
        prefixes.append({
            "prefix": m.group("prefix"),
            "lineno": text.count("\n", 0, m.start()) + 1
        })

    includes = []
    for m in INCLUDE_RE.finditer(text):
        includes.append({
            "args": m.group("args").strip(),
            "lineno": text.count("\n", 0, m.start()) + 1
        })

    mounts = []
    for m in MOUNT_RE.finditer(text):
        mounts.append({
            "path": m.group("path"),
            "lineno": text.count("\n", 0, m.start()) + 1
        })

    http_calls = []
    if HTTP_CALL_RE.search(text) or HOST_RE.search(text):
        for m in URL_LITERAL_RE.finditer(text):
            http_calls.append({
                "path_like": m.group("url"),
                "lineno": text.count("\n", 0, m.start()) + 1
            })

    return {
        "file": str(path),
        "routes": routes,
        "prefixes": prefixes,
        "includes": includes,
        "mounts": mounts,
        "http_calls": http_calls
    }

def build_index(scans: List[Dict]) -> Tuple[Dict[str, List[Dict]], Dict[str, List[Dict]]]:
    endpoint_defs: Dict[str, List[Dict]] = {}
    endpoint_calls: Dict[str, List[Dict]] = {}

    for s in scans:
        f = s["file"]
        for r in s["routes"]:
            key = r["path"]
            endpoint_defs.setdefault(key, []).append({"file": f, **r})
        for c in s["http_calls"]:
            key = c["path_like"]
            endpoint_calls.setdefault(key, []).append({"file": f, **c})

    return endpoint_defs, endpoint_calls

def match_calls_to_defs(endpoint_defs: Dict[str, List[Dict]], endpoint_calls: Dict[str, List[Dict]]):
    # naive matching: exact path string appears in both
    matched = []
    for call_path, calls in endpoint_calls.items():
        if call_path in endpoint_defs:
            matched.append({
                "path": call_path,
                "defined_in": endpoint_defs[call_path],
                "called_from": calls
            })
    return matched

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--out", default="endpoint_report.json")
    args = ap.parse_args()

    files = iter_py_files(args.roots)
    scans = [scan_file(f) for f in files]

    endpoint_defs, endpoint_calls = build_index(scans)
    matched = match_calls_to_defs(endpoint_defs, endpoint_calls)

    report = {
        "roots": args.roots,
        "files_scanned": len(files),
        "endpoints_defined": {k: len(v) for k, v in endpoint_defs.items()},
        "endpoints_called_literals": {k: len(v) for k, v in endpoint_calls.items()},
        "matched_callgraph": matched,
        "raw_scans": scans,
    }

    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"✅ Wrote: {args.out}")
    print(f"   files_scanned={len(files)} endpoints_defined={len(endpoint_defs)} calls_literals={len(endpoint_calls)} matched={len(matched)}")

if __name__ == "__main__":
    main()
