import pytest

class MockCommand:
    def execute(self):
        return "Command executed"

class AsyncMockCommand:
    async def execute(self):
        return "Async command executed"

class TestRunCommand:
    def test_happy_path_command(self, noogh_instance):
        # Arrange
        noogh_instance.command = MockCommand()
        
        # Act
        result = noogh_instance.run_command()
        
        # Assert
        assert result == "Command executed"
    
    def test_happy_path_async_command(self, noogh_instance):
        # Arrange
        noogh_instance.command = AsyncMockCommand()

        # Act and Assert (using asyncio to handle the async execution)
        with pytest.raises(asyncio.TimeoutError):
            asyncio.run(noogh_instance.run_command(timeout=0.1))
    
    def test_edge_case_none_command(self, noogh_instance):
        # Arrange
        noogh_instance.command = None
        
        # Act
        result = noogh_instance.run_command()
        
        # Assert
        assert result is None
    
    def test_edge_case_empty_command(self, noogh_instance):
        # Arrange
        noogh_instance.command = ''
        
        # Act
        result = noogh_instance.run_command()
        
        # Assert
        assert result is None
    
    def test_error_case_invalid_command_type(self, noogh_instance):
        # Arrange
        noogh_instance.command = "not a command"
        
        # Act and Assert (no explicit exception handling in the code, so we check for None)
        result = noogh_instance.run_command()
        assert result is None

@pytest.fixture
def noogh_instance():
    class Noogh:
        def __init__(self):
            self.command = None
        
        def run_command(self, *args, **kwargs):
            if isinstance(self.command, AsyncCommand):
                asyncio.run(self.command.execute())
            else:
                return self.command.execute()
    
    return Noogh()