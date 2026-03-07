import pytest

def test_create_preamble_happy_path():
    tool_name = "test_tool"
    params = {"prompt": "test prompt", "file_path": "/path/to/test.txt", "command": "echo 'test'"}
    expected_output = "🔧 سأقوم الآن بإستخدام الأداة test_tool (الوصف: 'test prompt', ملف: /path/to/test.txt, الأمر: `echo 'test'`)...)"
    assert create_preamble(tool_name, params) == expected_output

def test_create_preamble_empty_params():
    tool_name = "test_tool"
    params = {}
    expected_output = "🔧 سأقوم الآن بإستخدام الأداة test_tool..."
    assert create_preamble(tool_name, params) == expected_output

def test_create_preamble_no_params():
    tool_name = "test_tool"
    expected_output = "🔧 سأقوم الآن بإستخدام الأداة test_tool..."
    assert create_preamble(tool_name) == expected_output

def test_create_preamble_invalid_tool_name():
    tool_name = "unknown_tool"
    params = {"prompt": "test prompt"}
    expected_output = "🔧 سأقوم الآن بإستخدام الأداة unknown_tool (الوصف: 'test prompt')..."
    assert create_preamble(tool_name, params) == expected_output

def test_create_preamble_async_behavior(mocker):
    from neural_engine.preamble_manager import PreambleManager
    mocker.patch.object(PreambleManager, "TOOL_DESCRIPTIONS_AR", {"test_tool": "async tool"})
    
    tool_name = "test_tool"
    params = {"prompt": "test prompt"}
    expected_output = "🔧 سأقوم الآن بإستخدام الأداة async tool (الوصف: 'test prompt')..."
    assert create_preamble(tool_name, params) == expected_output