import pytest

from neural_engine.tools.tool_executor import ToolExecutor


def test_fix_arabic_paths_happy_path():
    executor = ToolExecutor()
    params = {
        "path": "/home/نووغ/projects",
        "user": "نووغ",
        "config": {
            "dataDir": "/home/نووغ/data"
        },
        "listOfPaths": ["/home/نووغ/projects", "/home/نووغ/config"]
    }
    expected = {
        "path": "/home/noogh/projects",
        "user": "noogh",
        "config": {
            "dataDir": "/home/noogh/data"
        },
        "listOfPaths": ["/home/noogh/projects", "/home/noogh/config"]
    }
    result = executor._fix_arabic_paths(params)
    assert result == expected


def test_fix_arabic_paths_empty_dict():
    executor = ToolExecutor()
    params = {}
    result = executor._fix_arabic_paths(params)
    assert result == {}


def test_fix_arabic_paths_none_input():
    executor = ToolExecutor()
    params = None
    result = executor._fix_arabic_paths(params)
    assert result is None


def test_fix_arabic_paths_invalid_type():
    executor = ToolExecutor()
    params = ["path", "/home/نووغ/projects"]
    result = executor._fix_arabic_paths(params)
    assert result == params


def test_fix_arabic_paths_nested_structure():
    executor = ToolExecutor()
    params = {
        "nested": {
            "path": "/home/نووغ/projects",
            "list": ["/home/نووغ/config", "/home/نووغ/data"]
        }
    }
    expected = {
        "nested": {
            "path": "/home/noogh/projects",
            "list": ["/home/noogh/config", "/home/noogh/data"]
        }
    }
    result = executor._fix_arabic_paths(params)
    assert result == expected