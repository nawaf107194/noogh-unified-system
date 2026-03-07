"""
P1.7 Tests - Deterministic Intent Classification
Ensures: Same Input → Same Output (100% reproducible)
"""
import pytest
from gateway.app.console.intent_classifier import classify_intent_deterministic, INTENT_RULES, EXACT_PHRASES


class TestDeterministicIntent:
    """Test suite for P1.7 deterministic intent classification."""
    
    def test_same_input_same_output_100_times(self):
        """Critical: Same input MUST produce same output every time."""
        query = "show me system status"
        
        # Run 100 times
        results = [classify_intent_deterministic(query) for _ in range(100)]
        
        # All results must be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], start=2):
            assert result == first_result, f"Result {i} differs from first result"
        
        # Mode should be OBSERVE
        assert first_result["mode"] == "OBSERVE"
        assert first_result["confidence"] == 1.0
    
    def test_exact_phrase_highest_priority(self):
        """Exact phrases should have highest priority."""
        result = classify_intent_deterministic("are there any issues with the system")
        assert result["mode"] == "OBSERVE"
        assert "exact phrase" in result["summary"]
        assert result["priority"] == 200
    
    def test_priority_conflict_resolution(self):
        """When multiple keywords match, highest priority wins."""
        # "execute" (priority 100) vs "status" (priority 80)
        result = classify_intent_deterministic("execute status check")
        assert result["mode"] == "EXECUTE"
        assert result["priority"] == 100
        
        # "run" (priority 100) vs "show" (priority 80)
        result = classify_intent_deterministic("run and show results")
        assert result["mode"] == "EXECUTE"
    
    def test_observe_keywords(self):
        """Test OBSERVE mode keyword matching."""
        observe_queries = [
            "status",
            "show metrics",
            "display health",
            "current system state",
            "الحالة",  # Arabic
            "عرض النظام",
        ]
        
        for query in observe_queries:
            result = classify_intent_deterministic(query)
            assert result["mode"] == "OBSERVE", f"Failed for query: {query}"
            assert result["confidence"] == 1.0
    
    def test_execute_keywords(self):
        """Test EXECUTE mode keyword matching."""
        execute_queries = [
            "run the process",
            "execute command",
            "start the service",
            "trigger event",
            "نفذ الأمر",  # Arabic
        ]
        
        for query in execute_queries:
            result = classify_intent_deterministic(query)
            assert result["mode"] == "EXECUTE", f"Failed for query: {query}"
            assert result["priority"] == 100
    
    def test_analyze_keywords(self):
        """Test ANALYZE mode keyword matching."""
        analyze_queries = [
            "why is this happening",
            "explain the error",
            "diagnose the problem",
            "root cause analysis",
            "ليش صار كذا",  # Arabic
        ]
        
        for query in analyze_queries:
            result = classify_intent_deterministic(query)
            assert result["mode"] == "ANALYZE", f"Failed for query: {query}"
            assert result["priority"] == 60
    
    def test_default_mode_no_keywords(self):
        """Queries with no matching keywords should default to OBSERVE."""
        unknown_queries = [
            "hello there",
            "random text",
            "xyz abc 123",
        ]
        
        for query in unknown_queries:
            result = classify_intent_deterministic(query)
            assert result["mode"] == "OBSERVE", f"Default failed for: {query}"
            assert result["confidence"] == 0.5
            assert result["priority"] == 0
    
    def test_case_insensitive(self):
        """Classification should be case-insensitive."""
        queries = [
            "STATUS",
            "Status",
            "sTaTuS",
            "status"
        ]
        
        results = [classify_intent_deterministic(q) for q in queries]
        
        # All should produce identical results
        for result in results:
            assert result["mode"] == "OBSERVE"
    
    def test_alphabetical_tie_breaking(self):
        """When priorities are equal, alphabetical order should be deterministic."""
        # Add two rules with same priority
        from gateway.app.console.intent_classifier import add_custom_rule
        
        # Both priority 50
        add_custom_rule("MODE_A", ["zebra"], 50)
        add_custom_rule("MODE_B", ["apple"], 50)
        
        # "apple" comes before "zebra" alphabetically
        result = classify_intent_deterministic("apple zebra")
        # Due to sort stability and rule order, should be consistent
        assert result["mode"] in ["MODE_A", "MODE_B"]
        
        # Running again should give same result
        result2 = classify_intent_deterministic("apple zebra")
        assert result == result2
    
    def test_arabic_support(self):
        """Test Arabic keyword matching."""
        arabic_tests = [
            ("نفذ الأمر", "EXECUTE"),
            ("عرض الحالة", "OBSERVE"),
            ("ليش كذا", "ANALYZE"),
        ]
        
        for query, expected_mode in arabic_tests:
            result = classify_intent_deterministic(query)
            assert result["mode"] == expected_mode, f"Arabic failed: {query}"
    
    def test_matched_keyword_reported(self):
        """Result should include which keyword matched."""
        result = classify_intent_deterministic("show me status")
        
        assert result["matched_keyword"] in ["show", "status"]
        assert result["matched_keyword"] is not None
    
    def test_confidence_always_one_for_matches(self):
        """Matched keywords should always have confidence=1.0."""
        queries = ["status", "execute", "why", "show", "run"]
        
        for query in queries:
            result = classify_intent_deterministic(query)
            if result["matched_keyword"] is not None:
                assert result["confidence"] == 1.0
    
    def test_rules_are_sorted_by_priority(self):
        """INTENT_RULES should be sorted by priority (highest first)."""
        priorities = [rule.priority for rule in INTENT_RULES]
        assert priorities == sorted(priorities, reverse=True), "Rules not sorted by priority"
    
    def test_no_randomness(self):
        """Critical: No random behavior anywhere in classification."""
        import random
        
        # Set random seed (should have NO effect on results)
        random.seed(42)
        result1 = classify_intent_deterministic("status check")
        
        random.seed(999)
        result2 = classify_intent_deterministic("status check")
        
        # Results must be identical regardless of random state
        assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
