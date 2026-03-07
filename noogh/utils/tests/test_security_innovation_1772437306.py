import pytest
from noogh.utils.security import secure_command
from subprocess import TimeoutExpired

@pytest.mark.parametrize("command_parts, expected_output", [
    (["echo", "hello"], True),
    (["ls", "-l"], False),  # Assuming 'ls' is not allowed in the test environment
])
def test_secure_command_happy_path(command_parts, expected_output):
    assert secure_command(command_parts) == expected_output

@pytest.mark.parametrize("command_parts", [
    [],
    None,
    "echo hello",
    ["echo"],
], ids=["empty_list", "none", "string", "single_element"])
def test_secure_command_edge_cases(command_parts):
    assert not secure_command(command_parts)[0]

def test_secure_command_allowed_commands():
    allowed_commands = {"echo"}
    assert secure_command(["echo"], allowed_commands=allowed_commands)[0]
    assert not secure_command(["ls"], allowed_commands=allowed_commands)[0]

def test_secure_command_timeout():
    with pytest.raises(TimeoutExpired):
        secure_command(["sleep", "10"], timeout=5)

def test_secure_command_error_cases():
    base_cmd = os.path.basename("unknown_command")
    logger.warning(f"SECURITY: Command not whitelisted: {base_cmd}")
    assert not secure_command(["unknown_command"])[0]

async def test_secure_command_async_behavior(mocker):
    mock_run = mocker.patch('noogh.utils.security.subprocess.run')
    mock_run.return_value.stdout = "Async output"
    
    result = await secure_command(["echo", "hello"], timeout=10, shell=True)
    assert result[0]
    assert result[1] == "Async output"