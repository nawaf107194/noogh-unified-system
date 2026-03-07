import pytest
from neural_engine.tools.system_tools import system_shell

def test_system_shell_happy_path():
    result = system_shell("echo 'Hello, World!'")
    assert result["success"] is True
    assert result["output"].strip() == "Hello, World!"
    assert result["error"] == ""
    assert result["returncode"] == 0
    assert result["summary_ar"] == "تم تنفيذ الأمر. الحالة: نجاح"

def test_system_shell_empty_command():
    result = system_shell("")
    assert result["success"] is False
    assert result["error"] == "يجب تحديد الأمر"
    assert result["output"] == ""
    assert result["returncode"] is None
    assert result["summary_ar"] == "لم يتم تحديد الأمر"

def test_system_shell_none_command():
    result = system_shell(None)
    assert result["success"] is False
    assert result["error"] == "يجب تحديد الأمر"
    assert result["output"] == ""
    assert result["returncode"] is None
    assert result["summary_ar"] == "لم يتم تحديد الأمر"

def test_system_shell_dangerous_command():
    dangerous_commands = [
        "rm -rf /",
        "mkfs /dev/sda1",
        "dd if=/dev/zero of=/dev/null bs=1G count=10",
        "> /dev/tty",
        "chmod 777 /root",
        ":(){ :|: & };:",
        "fork bomb"
    ]
    
    for cmd in dangerous_commands:
        result = system_shell(cmd)
        assert result["success"] is False
        assert f"أمر محظور: {cmd}" in result["error"]
        assert result["output"] == ""
        assert result["returncode"] is None
        assert "هذا الأمر محظور لأسباب أمنية" in result["summary_ar"]

def test_system_shell_timeout():
    result = system_shell("sleep 31")
    assert result["success"] is False
    assert result["error"] == "انتهى الوقت المسموح"
    assert result["output"] == ""
    assert result["returncode"] is None
    assert result["summary_ar"] == "انتهى وقت تنفيذ الأمر (30 ثانية)"

def test_system_shell_exception():
    try:
        import subprocess
        original_run = subprocess.run
        def mock_run(*args, **kwargs):
            raise Exception("Mocked exception")
        subprocess.run = mock_run
        
        result = system_shell("any_command")
    finally:
        subprocess.run = original_run
    
    assert result["success"] is False
    assert "خطأ في تنفيذ الأمر" in result["error"]
    assert result["output"] == ""
    assert result["returncode"] is None
    assert "خطأ في تنفيذ الأمر: Mocked exception" in result["summary_ar"]