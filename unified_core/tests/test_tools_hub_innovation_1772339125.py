import pytest

class MockSmolagents:
    def tool_example(self):
        pass
    
    def ToolAnotherExample(self):
        pass
    
    def other_method(self):
        pass

def get_available_tools(smolagents) -> List[str]:
    """قائمة الأدوات المتاحة في smolagents"""
    if not smolagents:
        return []
    try:
        return [name for name in dir(smolagents) 
                if 'tool' in name.lower() or 'Tool' in name]
    except Exception:
        return []

def test_get_available_tools_happy_path():
    smolagents = MockSmolagents()
    assert get_available_tools(smolagents) == ['tool_example', 'ToolAnotherExample']

def test_get_available_tools_empty_input():
    assert get_available_tools(None) == []
    assert get_available_tools([]) == []

def test_get_available_tools_no_tools():
    class EmptySmolagents:
        pass
    smolagents = EmptySmolagents()
    assert get_available_tools(smolagents) == []

def test_get_available_tools_with_exception():
    class ErroringSmolagents:
        def tool_example(self):
            raise Exception("An error occurred")
    
    smolagents = ErroringSmolagents()
    assert get_available_tools(smolagents) == []