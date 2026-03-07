import pytest
from pathlib import Path

# Assuming ROUTE_RE, PREFIX_RE, INCLUDE_RE, MOUNT_RE, and URL_LITERAL_RE are defined in tools_endpoint_map.py
from .tools_endpoint_map import scan_file

def test_scan_file_happy_path():
    content = """
@route('/test', method='GET')
@prefix('/api/v1')
@include('module.submodule.include')
@mount('/static')

http://example.com/api/test
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write(content)
        file_path = Path(temp.name)

    result = scan_file(file_path)
    
    assert result == {
        "file": str(file_path),
        "routes": [
            {
                "method": "GET",
                "path": "/test",
                "lineno": 2
            }
        ],
        "prefixes": [
            {
                "prefix": "/api/v1",
                "lineno": 3
            }
        ],
        "includes": [
            {
                "args": "module.submodule.include",
                "lineno": 4
            }
        ],
        "mounts": [
            {
                "path": "/static",
                "lineno": 5
            }
        ],
        "http_calls": [
            {
                "path_like": "http://example.com/api/test",
                "lineno": 6
            }
        ]
    }

def test_scan_file_empty_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        file_path = Path(temp.name)

    result = scan_file(file_path)
    
    assert result == {
        "file": str(file_path),
        "routes": [],
        "prefixes": [],
        "includes": [],
        "mounts": [],
        "http_calls": []
    }

def test_scan_file_none_input():
    with pytest.raises(TypeError):
        scan_file(None)

def test_scan_file_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        scan_file(Path("/nonexistent/file.py"))

def test_scan_file_invalid_route_syntax():
    content = """
@route('/test', method='INVALID')
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write(content)
        file_path = Path(temp.name)

    result = scan_file(file_path)
    
    assert result == {
        "file": str(file_path),
        "routes": [],
        "prefixes": [],
        "includes": [],
        "mounts": [],
        "http_calls": []
    }

def test_scan_file_invalid_prefix_syntax():
    content = """
@prefix('/api/v1/'
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write(content)
        file_path = Path(temp.name)

    result = scan_file(file_path)
    
    assert result == {
        "file": str(file_path),
        "routes": [],
        "prefixes": [],
        "includes": [],
        "mounts": [],
        "http_calls": []
    }

def test_scan_file_invalid_include_syntax():
    content = """
@include('module.submodule.include'
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write(content)
        file_path = Path(temp.name)

    result = scan_file(file_path)
    
    assert result == {
        "file": str(file_path),
        "routes": [],
        "prefixes": [],
        "includes": [],
        "mounts": [],
        "http_calls": []
    }

def test_scan_file_invalid_mount_syntax():
    content = """
@mount('/static/'
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write(content)
        file_path = Path(temp.name)

    result = scan_file(file_path)
    
    assert result == {
        "file": str(file_path),
        "routes": [],
        "prefixes": [],
        "includes": [],
        "mounts": [],
        "http_calls": []
    }