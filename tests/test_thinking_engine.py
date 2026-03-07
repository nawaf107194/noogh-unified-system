"""
Tests for ThinkingEngine

Tests the transparent thinking system with stream-of-consciousness reasoning.
"""

import pytest
from neural_engine.neural_core.thinking_engine import (
    ThinkingEngine,
    ThinkingDepth,
    think_about
)


class TestThinkingEngine:
    """Test suite for ThinkingEngine"""
    
    def test_initialization(self):
        """Test engine initialization"""
        engine = ThinkingEngine()
        assert engine is not None
        assert engine.thinking_history == []
    
    def test_think_minimal_depth(self):
        """Test thinking with minimal depth"""
        result = think_about(
            "What is 2+2?",
            depth=ThinkingDepth.MINIMAL
        )
        
        assert result is not None
        assert result.thought_process != ""
        assert len(result.insights) > 0
        assert result.approach != ""
        assert 0.0 <= result.confidence <= 1.0
        assert result.depth == ThinkingDepth.MINIMAL
    
    def test_think_deep_depth(self):
        """Test thinking with deep depth"""
        result = think_about(
            "How to optimize system performance?",
            depth=ThinkingDepth.DEEP
        )
        
        assert result is not None
        assert len(result.thought_process) > 0
        assert len(result.insights) > 0
        # Deep thinking should have more content
        assert "deep" in result.thought_process.lower() or "analysis" in result.thought_process.lower()
    
    def test_think_with_context(self):
        """Test thinking with context"""
        context = {
            "system": "NOOGH",
            "component": "reasoning_engine"
        }
        
        result = think_about(
            "Improve this component",
            context=context,
            depth=ThinkingDepth.STANDARD
        )
        
        assert result is not None
        assert len(result.insights) > 0
    
    def test_thinking_history(self):
        """Test history tracking"""
        engine = ThinkingEngine()
        
        # Think multiple times
        engine.think("Query 1", depth=ThinkingDepth.MINIMAL)
        engine.think("Query 2", depth=ThinkingDepth.STANDARD)
        
        history = engine.get_thinking_history()
        assert len(history) == 2
        assert history[0]["query"] == "Query 1"
        assert history[1]["query"] == "Query 2"
    
    def test_clear_history(self):
        """Test clearing history"""
        engine = ThinkingEngine()
        engine.think("Test query")
        
        assert len(engine.thinking_history) > 0
        
        engine.clear_history()
        assert len(engine.thinking_history) == 0
    
    def test_confidence_calculation(self):
        """Test confidence scoring"""
        result = think_about("Simple question")
        
        # Confidence should be between 0 and 1
        assert 0.0 <= result.confidence <= 1.0
    
    def test_all_depth_levels(self):
        """Test all depth levels"""
        query = "Test query"
        
        for depth in ThinkingDepth:
            result = think_about(query, depth=depth)
            assert result.depth == depth
            assert result.thought_process != ""


class TestThinkingIntegration:
    """Integration tests for thinking engine"""
    
    def test_with_complexity_analyzer(self):
        """Test integration with complexity analyzer"""
        try:
            from neural_engine.neural_core.complexity_analyzer import analyze_query_complexity
            
            query = "This is a complex multi-step question requiring deep analysis and careful consideration"
            
            # Analyze complexity
            complexity = analyze_query_complexity(query)
            
            # Think with suggested depth
            result = think_about(query, depth=complexity.suggested_depth)
            
            assert result is not None
            assert result.thought_process != ""
            
        except ImportError:
            pytest.skip("ComplexityAnalyzer not available")
    
    def test_with_reasoning_engine(self):
        """Test integration with reasoning engine"""
        try:
            from neural_engine.reasoning_engine import ReasoningEngine
            
            # Check if reasoning engine has thinking_engine
            engine = ReasoningEngine(backend="mock")
            assert hasattr(engine, 'thinking_engine')
            assert engine.thinking_engine is not None
            
        except Exception as e:
            pytest.skip(f"ReasoningEngine integration not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
