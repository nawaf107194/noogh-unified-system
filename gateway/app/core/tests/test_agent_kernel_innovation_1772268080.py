import pytest

from gateway.app.core.agent_kernel import AgentKernel

@pytest.fixture
def agent_kernel():
    return AgentKernel()

@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        ("This is a normal text.", "This is a normal text."),
        ("sudo rm -rf /home/user", "[Sudo Blocked] [Deletion Blocked]"),
        ("/etc/passwd", "[System Path Blocked]"),
        (".env file", "[Secret Blocked]"),
        ("", ""),
        (None, None),
    ],
)
def test_sanitize_answer(agent_kernel, input_text, expected_output):
    result = agent_kernel._sanitize_answer(input_text)
    assert result == expected_output