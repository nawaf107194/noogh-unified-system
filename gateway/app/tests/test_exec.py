
from gateway.app.core.exec_sandbox import ExecSandbox


def test_extract_exec_blocks():
    sandbox = ExecSandbox()
    text = "Here is some code:\n```python\nprint(1)\n```\nAnd more:\n```\nprint(2)\n```"
    blocks = sandbox.extract_exec_blocks(text)
    assert len(blocks) == 2
    assert blocks[0] == "print(1)"
    assert blocks[1] == "print(2)"


def test_run_exec_basic():
    sandbox = ExecSandbox()
    res = sandbox.run_exec("print('hello')")
    assert "hello" in res


def test_run_exec_math():
    sandbox = ExecSandbox()
    res = sandbox.run_exec("print(1 + 1)")
    assert "2" in res


def test_run_exec_forbidden():
    sandbox = ExecSandbox()
    # Assuming os is Forbidden by default safe_globals
    res = sandbox.run_exec("import os; os.system('ls')")
    assert "AST_VALIDATION_FAILED" in res
    assert "os" in res
