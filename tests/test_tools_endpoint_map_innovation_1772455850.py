import pytest
from pathlib import Path

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

# Import the actual function to test its real outputs
from tools_endpoint_map import scan_file

def test_scan_file_happy_path():
    content = """
@route('/api/users', methods=['GET'])
@prefix('/v1')
@include('module.include')
@mount('/static')

http_call("https://example.com")
"""
    with open("test_file.py", "w") as f:
        f.write(content)
    
    result = scan_file(Path("test_file.py"))
    
    assert result == {
        "file": "test_file.py",
        "routes": [
            {"method": "GET", "path": "/api/users", "lineno": 2}
        ],
        "prefixes": [
            {"prefix": "/v1", "lineno": 3}
        ],
        "includes": [
            {"args": "module.include", "lineno": 4}
        ],
        "mounts": [
            {"path": "/static", "lineno": 5}
        ],
        "http_calls": [
            {"path_like": "https://example.com", "lineno": 6}
        ]
    }
    
    Path("test_file.py").unlink()

def test_scan_file_empty():
    with open("test_file.py", "w") as f:
        pass
    
    result = scan_file(Path("test_file.py"))
    
    assert result == {
        "file": "test_file.py",
        "routes": [],
        "prefixes": [],
        "includes": [],
        "mounts": [],
        "http_calls": []
    }
    
    Path("test_file.py").unlink()

def test_scan_file_none():
    with pytest.raises(TypeError):
        scan_file(None)

def test_scan_file_invalid_input():
    with pytest.raises(FileNotFoundError):
        scan_file(Path("/nonexistent/file"))