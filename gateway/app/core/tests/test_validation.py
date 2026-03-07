import pytest
from unittest.mock import Mock, patch
from gateway.app.core.validation import ValidationError
from gateway.app.core.agent_kernel import AgentResult

# Mocking the external dependencies
@pytest.fixture
def mock_validate_task():
    with patch('gateway.app.core.validation.validate_task', autospec=True) as mock:
        yield mock

@pytest.fixture
def mock_validate_auth_context():
    with patch('gateway.app.core.validation.validate_auth_context', autospec=True) as mock:
        yield mock

@pytest.fixture
def mock_logger():
    with patch('gateway.app.core.validation.logger', autospec=True) as mock:
        yield mock

@pytest.fixture
def mock_func():
    with patch('gateway.app.core.validation.func', autospec=True) as mock:
        mock.return_value = AgentResult(success=True, answer="Success", steps=1, error=None, metadata={})
        yield mock

class TestWrapperFunction:

    def test_happy_path(self, mock_validate_task, mock_validate_auth_context, mock_logger, mock_func):
        task = "valid_task"
        auth = Mock()
        
        result = self.wrapper(task, auth)
        
        assert result.success is True
        assert result.answer == "Success"
        assert result.steps == 1
        assert result.error is None
        assert result.metadata == {}
        mock_validate_task.assert_called_once_with(task)
        mock_validate_auth_context.assert_called_once_with(auth)
        mock_logger.error.assert_not_called()
        mock_func.assert_called_once()

    def test_edge_case_empty_task(self, mock_validate_task, mock_validate_auth_context, mock_logger, mock_func):
        task = ""
        auth = Mock()
        
        result = self.wrapper(task, auth)
        
        assert result.success is False
        assert "Invalid input" in result.answer
        assert result.steps == 0
        assert result.error != ""
        assert result.metadata["error_type"] == "VALIDATION_ERROR"
        mock_validate_task.assert_called_once_with(task)
        mock_logger.error.assert_called_once()
        mock_func.assert_not_called()

    def test_edge_case_none_task(self, mock_validate_task, mock_validate_auth_context, mock_logger, mock_func):
        task = None
        auth = Mock()
        
        result = self.wrapper(task, auth)
        
        assert result.success is False
        assert "Invalid input" in result.answer
        assert result.steps == 0
        assert result.error != ""
        assert result.metadata["error_type"] == "VALIDATION_ERROR"
        mock_validate_task.assert_called_once_with(task)
        mock_logger.error.assert_called_once()
        mock_func.assert_not_called()

    def test_error_case_invalid_task(self, mock_validate_task, mock_validate_auth_context, mock_logger, mock_func):
        task = "invalid_task"
        auth = Mock()
        mock_validate_task.side_effect = ValidationError("Task is invalid")
        
        result = self.wrapper(task, auth)
        
        assert result.success is False
        assert "Invalid input: Task is invalid" in result.answer
        assert result.steps == 0
        assert result.error == "Task is invalid"
        assert result.metadata["error_type"] == "VALIDATION_ERROR"
        mock_validate_task.assert_called_once_with(task)
        mock_logger.error.assert_called_once()
        mock_func.assert_not_called()

    def test_async_behavior(self, mock_validate_task, mock_validate_auth_context, mock_logger, mock_func):
        task = "async_task"
        auth = Mock()
        mock_func.return_value = AgentResult(success=True, answer="Async Success", steps=1, error=None, metadata={})
        
        async def async_wrapper(task, auth, *args, **kwargs):
            return await self.wrapper(task, auth, *args, **kwargs)
        
        import asyncio
        result = asyncio.run(async_wrapper(task, auth))
        
        assert result.success is True
        assert result.answer == "Async Success"
        assert result.steps == 1
        assert result.error is None
        assert result.metadata == {}
        mock_validate_task.assert_called_once_with(task)
        mock_validate_auth_context.assert_called_once_with(auth)
        mock_logger.error.assert_not_called()
        mock_func.assert_called_once()