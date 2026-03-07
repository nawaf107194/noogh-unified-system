import pytest

class TestWebSearcher:

    @pytest.fixture
    def web_searcher(self):
        from neural_engine.specialized_systems.web_searcher import WebSearcher
        return WebSearcher()

    def test_is_technical_query_happy_path(self, web_searcher):
        assert web_searcher._is_technical_query("What is an algorithm?")
        assert web_searcher._is_technical_query("Neural networks are fascinating.")
        assert web_searcher._is_technical_query("How to optimize a machine learning model?")
        assert not web_searcher._is_technical_query("Where can I find good coffee?")
        
    def test_is_technical_query_edge_cases(self, web_searcher):
        assert not web_searcher._is_technical_query("")
        assert not web_searcher._is_technical_query(" ")
        assert not web_searcher._is_technical_query(None)

    def test_is_technical_query_error_cases(self, web_searcher):
        with pytest.raises(TypeError):
            web_searcher._is_technical_query(123)
        with pytest.raises(TypeError):
            web_searcher._is_technical_query(True)
        with pytest.raises(TypeError):
            web_searcher._is_technical_query(["invalid", "input"])
    
    # Since the function does not have any async behavior, we skip this part.
    # def test_is_technical_query_async_behavior(self, web_searcher):
    #     pass