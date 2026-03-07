import pytest

class TestOnStartup:
    def setup_method(self):
        class MockOrchestration:
            def __init__(self):
                self._on_startup = []
                
            def on_startup(self, func: callable):
                self._on_startup.append(func)
                return func
                
        self.orchestration = MockOrchestration()
        
    def test_happy_path(self):
        @self.orchestration.on_startup
        def test_func():
            pass
        
        assert len(self.orchestration._on_startup) == 1
        assert self.orchestration._on_startup[0] is test_func
    
    def test_empty_list(self):
        assert len(self.orchestration._on_startup) == 0
    
    def test_none_function(self):
        with pytest.raises(TypeError):
            self.orchestration.on_startup(None)
    
    def test_invalid_input(self):
        with pytest.raises(TypeError):
            self.orchestration.on_startup(123)
            
    def test_multiple_functions(self):
        @self.orchestration.on_startup
        def func1():
            pass
            
        @self.orchestration.on_startup
        def func2():
            pass
            
        assert len(self.orchestration._on_startup) == 2
        assert self.orchestration._on_startup[0] is func1
        assert self.orchestration._on_startup[1] is func2
    
    def test_async_function(self):
        async def async_test_func():
            pass
        
        @self.orchestration.on_startup
        def sync_test_func():
            pass
        
        assert len(self.orchestration._on_startup) == 2
        assert self.orchestration._on_startup[0] is async_test_func
        assert self.orchestration._on_startup[1] is sync_test_func