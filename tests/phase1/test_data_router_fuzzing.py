"""
DataRouter Fuzz Testing

Property-based and fuzz testing for the DataRouter classification logic.
Tests cover:
- Type confusion attacks
- Malformed input handling
- Unicode edge cases
- Resource exhaustion prevention
- Boundary condition validation

Uses Hypothesis library for property-based testing where available.
"""
import pytest
import asyncio
import random
import string
import sys
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import json

# Import the module under test
from unified_core.db.router import DataRouter, DataType, RoutingDecision, RoutingStrategy

# Try to import Hypothesis for property-based testing
try:
    from hypothesis import given, strategies as st, settings, assume, HealthCheck
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    # Create dummy decorators
    def given(*args, **kwargs):
        def decorator(f):
            return pytest.mark.skip(reason="Hypothesis not installed")(f)
        return decorator
    class st:
        @staticmethod
        def text(*args, **kwargs): pass
        @staticmethod
        def dictionaries(*args, **kwargs): pass
        @staticmethod
        def lists(*args, **kwargs): pass
        @staticmethod
        def floats(*args, **kwargs): pass
        @staticmethod
        def integers(*args, **kwargs): pass
        @staticmethod
        def binary(*args, **kwargs): pass
        @staticmethod
        def none(): pass
        @staticmethod
        def booleans(): pass
        @staticmethod
        def one_of(*args): pass
    def settings(*args, **kwargs):
        def decorator(f): return f
        return decorator
    def assume(x): return x
    class HealthCheck:
        function_scoped_fixture = None


@dataclass
class FuzzResult:
    """Result of fuzz testing."""
    input_value: Any
    input_type: str
    success: bool
    error: Optional[str] = None
    result: Optional[RoutingDecision] = None
    execution_time_ms: float = 0.0


# =============================================================================
# FUZZ DATA GENERATORS
# =============================================================================

def generate_random_string(length: int = 100) -> str:
    """Generate random ASCII string."""
    return ''.join(random.choices(string.printable, k=length))


def generate_random_bytes(length: int = 100) -> bytes:
    """Generate random bytes."""
    return bytes(random.randint(0, 255) for _ in range(length))


def generate_malformed_json() -> str:
    """Generate malformed JSON strings."""
    malformed = [
        '{"unclosed": "value',
        '{key: "no quotes"}',
        '{"nested": {"too": {"deep": ',
        '["array", "without", "close"',
        '{"trailing": comma,}',
        '{null: "as key"}',
        '{"unicode": "\uFFFF\uFFFE"}',
    ]
    return random.choice(malformed)


def generate_unicode_edge_cases() -> str:
    """Generate Unicode edge case strings."""
    cases = [
        "\u0000",  # Null
        "\u200B",  # Zero-width space
        "\uFEFF",  # BOM
        "\u202E",  # Right-to-left override
        "\uFFFF",  # Non-character
        "مرحبا",  # Arabic
        "こんにちは",  # Japanese
        "🔥💻🚀",  # Emoji
        "\u0027",  # Unicode apostrophe
        "A" + "\u0308",  # Combining character
        "\uD800",  # Lone surrogate (invalid)
    ]
    return random.choice(cases)


def generate_type_confusion_inputs() -> List[Any]:
    """Generate inputs that might cause type confusion."""
    return [
        None,
        True,
        False,
        float('inf'),
        float('-inf'),
        float('nan'),
        complex(1, 2),
        frozenset([1, 2, 3]),
        set([1, 2, 3]),
        (1, 2, 3),
        range(10),
        b"bytes",
        bytearray(b"bytearray"),
        memoryview(b"memory"),
        lambda x: x,
        type,
        object(),
    ]


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def router():
    """Create DataRouter for testing."""
    return DataRouter()


@pytest.fixture
def fuzz_iterations():
    """Number of fuzz iterations."""
    return 100


# =============================================================================
# BASIC FUZZ TESTS
# =============================================================================

class TestBasicFuzzing:
    """Basic fuzz testing for DataRouter."""
    
    def test_fuzz_random_strings(self, router, fuzz_iterations):
        """Fuzz with random printable strings."""
        failures = []
        
        for i in range(fuzz_iterations):
            input_val = generate_random_string(random.randint(1, 1000))
            start = datetime.now()
            
            try:
                result = router.classify(input_val)
                assert isinstance(result, RoutingDecision)
            except Exception as e:
                failures.append(FuzzResult(
                    input_value=input_val[:100] + "..." if len(input_val) > 100 else input_val,
                    input_type="random_string",
                    success=False,
                    error=str(e),
                    execution_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
        
        # Report failures
        if failures:
            print(f"\n{len(failures)} failures out of {fuzz_iterations} iterations:")
            for f in failures[:5]:
                print(f"  - {f.error}")
        
        assert len(failures) < fuzz_iterations * 0.05, f"Too many failures: {len(failures)}/{fuzz_iterations}"
    
    def test_fuzz_unicode_strings(self, router, fuzz_iterations):
        """Fuzz with Unicode edge cases."""
        failures = []
        
        for i in range(fuzz_iterations):
            input_val = generate_unicode_edge_cases()
            
            try:
                result = router.classify(input_val)
                assert isinstance(result, RoutingDecision)
            except (UnicodeError, UnicodeDecodeError, UnicodeEncodeError) as e:
                failures.append(FuzzResult(
                    input_value=repr(input_val),
                    input_type="unicode",
                    success=False,
                    error=str(e)
                ))
        
        # Accept higher failure rate for unicode edge cases (surrogates, etc.)
        assert len(failures) < fuzz_iterations * 0.25, f"Too many Unicode failures: {len(failures)}"
    
    def test_fuzz_empty_inputs(self, router):
        """Test various empty input types."""
        empty_inputs = [
            "",
            [],
            {},
            None,
            0,
            0.0,
            False,
        ]
        
        for input_val in empty_inputs:
            try:
                result = router.classify(input_val)
                # Should handle gracefully (return default or error cleanly)
                if result is not None:
                    assert isinstance(result, RoutingDecision)
            except (ValueError, TypeError):
                pass  # Graceful rejection is acceptable
    
    def test_fuzz_deeply_nested_structures(self, router):
        """Test deeply nested data structures."""
        depths = [10, 50, 100, 500]
        
        for depth in depths:
            # Nested dict
            nested_dict = {}
            current = nested_dict
            for i in range(depth):
                current["nested"] = {}
                current = current["nested"]
            
            try:
                result = router.classify(nested_dict)
                if result is not None:
                    assert isinstance(result, RoutingDecision)
            except (RecursionError, ValueError):
                pass  # Depth limit rejection is acceptable
            
            # Nested list
            nested_list = []
            current = nested_list
            for i in range(depth):
                current.append([])
                current = current[0]
            
            try:
                result = router.classify(nested_list)
                if result is not None:
                    assert isinstance(result, RoutingDecision)
            except (RecursionError, ValueError):
                pass


class TestTypeConfusionFuzzing:
    """Test type confusion attack prevention."""
    
    def test_type_confusion_inputs(self, router):
        """Test handling of unexpected types."""
        for input_val in generate_type_confusion_inputs():
            try:
                result = router.classify(input_val)
                # Should either handle or reject gracefully
                if result is not None:
                    assert isinstance(result, RoutingDecision)
            except (TypeError, ValueError, AttributeError):
                pass  # Type rejection is acceptable
    
    def test_dict_with_callable_values(self, router):
        """Test dict with callable values that could be exploited."""
        dangerous_dicts = [
            {"__class__": "malicious"},
            {"__init__": lambda: None},
            {"__del__": "cleanup"},
            {"__getattr__": "override"},
            {"eval": "code"},
            {"exec": "command"},
        ]
        
        for d in dangerous_dicts:
            try:
                result = router.classify(d)
                assert isinstance(result, RoutingDecision)
                # Should not execute any callables
            except (TypeError, ValueError):
                pass
    
    def test_list_with_mixed_types(self, router):
        """Test list with mixed, unusual types."""
        mixed_lists = [
            [1, "two", 3.0, None, True, {"nested": "dict"}],
            [lambda x: x, type, object()],
            [float('inf'), float('nan'), complex(1, 2)],
            [b"bytes", bytearray(b"arr"), memoryview(b"mem")],
        ]
        
        for lst in mixed_lists:
            try:
                result = router.classify(lst)
                if result is not None:
                    assert isinstance(result, RoutingDecision)
            except (TypeError, ValueError):
                pass


class TestResourceExhaustionPrevention:
    """Test protection against resource exhaustion attacks."""
    
    def test_extremely_long_string(self, router):
        """Test handling of very long strings."""
        sizes = [10_000, 100_000, 1_000_000]
        
        for size in sizes:
            long_string = "A" * size
            start = datetime.now()
            
            try:
                result = router.classify(long_string)
                elapsed = (datetime.now() - start).total_seconds()
                
                # Should complete in reasonable time
                assert elapsed < 5.0, f"Classification took too long: {elapsed}s for {size} chars"
                
                if result is not None:
                    assert isinstance(result, RoutingDecision)
            except (ValueError, MemoryError):
                pass  # Rejection is acceptable for very large inputs
    
    def test_extremely_large_list(self, router):
        """Test handling of very large lists."""
        sizes = [1_000, 10_000, 100_000]
        
        for size in sizes:
            large_list = list(range(size))
            start = datetime.now()
            
            try:
                result = router.classify(large_list)
                elapsed = (datetime.now() - start).total_seconds()
                
                assert elapsed < 5.0, f"Classification took too long: {elapsed}s for {size} elements"
            except (ValueError, MemoryError):
                pass
    
    def test_extremely_large_dict(self, router):
        """Test handling of very large dictionaries."""
        sizes = [1_000, 10_000]
        
        for size in sizes:
            large_dict = {str(i): i for i in range(size)}
            start = datetime.now()
            
            try:
                result = router.classify(large_dict)
                elapsed = (datetime.now() - start).total_seconds()
                
                assert elapsed < 5.0, f"Classification took too long: {elapsed}s for {size} keys"
            except (ValueError, MemoryError):
                pass
    
    def test_repeated_classification_no_memory_leak(self, router):
        """Test that repeated classifications don't leak memory."""
        import gc
        
        # Get baseline memory (if psutil available)
        try:
            import psutil
            process = psutil.Process()
            baseline_memory = process.memory_info().rss
        except ImportError:
            baseline_memory = None
        
        # Run many classifications
        for i in range(1000):
            router.classify(f"test input {i}")
        
        gc.collect()
        
        if baseline_memory:
            current_memory = process.memory_info().rss
            memory_increase = current_memory - baseline_memory
            
            # Should not increase by more than 50MB
            assert memory_increase < 50 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.2f}MB"


# =============================================================================
# PROPERTY-BASED TESTS (Hypothesis)
# =============================================================================

class TestPropertyBasedFuzzing:
    """Property-based testing using Hypothesis."""
    
    @given(st.text(min_size=0, max_size=1000)) if HYPOTHESIS_AVAILABLE else given()
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture]) if HYPOTHESIS_AVAILABLE else settings()
    def test_classify_never_crashes_on_text(self, router, text):
        """Property: classify should never crash on any text input."""
        try:
            result = router.classify(text)
            if result is not None:
                assert isinstance(result, RoutingDecision)
                assert result.data_type is not None
                assert result.primary_target in ["postgres", "vector", "graph", None, ""]
        except (ValueError, TypeError):
            pass  # Controlled rejection is acceptable
    
    @given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=0, max_size=1000)) if HYPOTHESIS_AVAILABLE else given()
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture]) if HYPOTHESIS_AVAILABLE else settings()
    def test_classify_handles_float_lists(self, router, floats):
        """Property: float lists (embeddings) should be handled."""
        try:
            result = router.classify(floats)
            if result is not None:
                assert isinstance(result, RoutingDecision)
        except (ValueError, TypeError):
            pass
    
    @given(st.dictionaries(st.text(min_size=1, max_size=50), st.text(min_size=0, max_size=100), min_size=0, max_size=50)) if HYPOTHESIS_AVAILABLE else given()
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture]) if HYPOTHESIS_AVAILABLE else settings()
    def test_classify_handles_arbitrary_dicts(self, router, d):
        """Property: arbitrary dictionaries should be handled."""
        try:
            result = router.classify(d)
            if result is not None:
                assert isinstance(result, RoutingDecision)
        except (ValueError, TypeError):
            pass


# =============================================================================
# BOUNDARY CONDITION TESTS
# =============================================================================

class TestBoundaryConditions:
    """Test boundary conditions in classification."""
    
    def test_single_character_inputs(self, router):
        """Test single character inputs."""
        single_chars = [
            "a", "1", ".", " ", "\n", "\t", "\0",
            "+", "-", "*", "/", "=", "<", ">",
            "'", '"', "`", "\\", "/", "|",
        ]
        
        for char in single_chars:
            try:
                result = router.classify(char)
                if result is not None:
                    assert isinstance(result, RoutingDecision)
            except ValueError:
                pass
    
    def test_numeric_edge_cases(self, router):
        """Test numeric edge cases."""
        numbers = [
            0, -0, 1, -1,
            sys.maxsize, -sys.maxsize,
            sys.float_info.max, sys.float_info.min,
            sys.float_info.epsilon,
            1e308, 1e-308,
        ]
        
        for num in numbers:
            try:
                result = router.classify(num)
                if result is not None:
                    assert isinstance(result, RoutingDecision)
            except (ValueError, TypeError):
                pass
    
    def test_special_string_patterns(self, router):
        """Test strings that might confuse parsers."""
        patterns = [
            # SQL-like
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE",
            # Math-like
            "sin", "cos", "log", "sqrt", "pi", "e",
            # Logic-like
            "if", "then", "else", "and", "or", "not",
            # Relationship-like
            "is a", "has a", "relates to", "connects",
            # Mixed
            "SELECT * FROM users WHERE sin(x) > 0 AND is_admin",
        ]
        
        for pattern in patterns:
            result = router.classify(pattern)
            assert isinstance(result, RoutingDecision)
            # Verify classification is reasonable
            assert result.confidence > 0


# =============================================================================
# FUZZ TEST REPORT GENERATOR
# =============================================================================

class TestFuzzReportGenerator:
    """Generate comprehensive fuzz test report."""
    
    def test_generate_fuzz_report(self, router):
        """Run comprehensive fuzzing and generate report."""
        report = {
            "random_string_tests": 0,
            "random_string_passes": 0,
            "unicode_tests": 0,
            "unicode_passes": 0,
            "type_confusion_tests": 0,
            "type_confusion_passes": 0,
            "resource_tests": 0,
            "resource_passes": 0,
            "total_tests": 0,
            "total_passes": 0,
        }
        
        # Random string tests
        for _ in range(100):
            report["random_string_tests"] += 1
            report["total_tests"] += 1
            try:
                result = router.classify(generate_random_string(100))
                if result is not None:
                    report["random_string_passes"] += 1
                    report["total_passes"] += 1
            except Exception:
                pass
        
        # Unicode tests
        for _ in range(50):
            report["unicode_tests"] += 1
            report["total_tests"] += 1
            try:
                result = router.classify(generate_unicode_edge_cases())
                if result is not None:
                    report["unicode_passes"] += 1
                    report["total_passes"] += 1
            except Exception:
                pass
        
        # Type confusion tests
        for val in generate_type_confusion_inputs():
            report["type_confusion_tests"] += 1
            report["total_tests"] += 1
            try:
                result = router.classify(val)
                report["type_confusion_passes"] += 1
                report["total_passes"] += 1
            except Exception:
                pass
        
        # Resource tests
        for size in [100, 1000, 10000]:
            report["resource_tests"] += 1
            report["total_tests"] += 1
            try:
                result = router.classify("A" * size)
                if result is not None:
                    report["resource_passes"] += 1
                    report["total_passes"] += 1
            except Exception:
                pass
        
        # Print report
        print(f"\n{'='*60}")
        print("FUZZ TESTING REPORT")
        print(f"{'='*60}")
        print(f"Total Tests: {report['total_tests']}")
        print(f"Total Passes: {report['total_passes']}")
        print(f"Pass Rate: {report['total_passes']/report['total_tests']*100:.1f}%")
        print(f"\nBreakdown:")
        print(f"  Random Strings: {report['random_string_passes']}/{report['random_string_tests']}")
        print(f"  Unicode: {report['unicode_passes']}/{report['unicode_tests']}")
        print(f"  Type Confusion: {report['type_confusion_passes']}/{report['type_confusion_tests']}")
        print(f"  Resource: {report['resource_passes']}/{report['resource_tests']}")
        print(f"{'='*60}\n")
        
        # Assert reasonable pass rate
        pass_rate = report["total_passes"] / report["total_tests"] * 100
        assert pass_rate >= 80, f"Pass rate too low: {pass_rate:.1f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
