import pytest

class MockNeuralEngine:
    def __init__(self):
        self.patterns = {
            "pattern1": {"successes": 50, "occurrences": 100},
            "pattern2": {"successes": 30, "occurrences": 150},
        }
        self.insights = []

    def _generate_insight(self, pattern: str):
        """Generate learning insight from pattern"""
        stats = self.patterns[pattern]
        success_rate = (stats["successes"] / stats["occurrences"]) * 100

        # Generate recommendation
        if success_rate > 80:
            recommendation = f"Pattern '{pattern}' is highly successful - continue using"
        elif success_rate < 20:
            recommendation = f"Pattern '{pattern}' often fails - consider alternative approach"
        else:
            recommendation = f"Pattern '{pattern}' has mixed results - use with caution"

        insight = LearningInsight(
            pattern=pattern,
            confidence=min(stats["occurrences"] / 100, 1.0),
            occurrences=stats["occurrences"],
            success_rate=success_rate,
            recommendation=recommendation,
        )

        # Update or add insight
        existing = next((i for i in self.insights if i.pattern == pattern), None)
        if existing:
            self.insights.remove(existing)
        self.insights.append(insight)

class LearningInsight:
    def __init__(self, pattern, confidence, occurrences, success_rate, recommendation):
        self.pattern = pattern
        self.confidence = confidence
        self.occurrences = occurrences
        self.success_rate = success_rate
        self.recommendation = recommendation

# Test cases
def test_generate_insight_happy_path():
    engine = MockNeuralEngine()
    insight = engine._generate_insight("pattern1")
    assert insight.pattern == "pattern1"
    assert insight.confidence == 1.0
    assert insight.occurrences == 100
    assert insight.success_rate == 50.0
    assert insight.recommendation == "Pattern 'pattern1' is highly successful - continue using"

def test_generate_insight_edge_case_empty_pattern():
    engine = MockNeuralEngine()
    insight = engine._generate_insight("")
    assert insight is None

def test_generate_insight_edge_case_none_pattern():
    engine = MockNeuralEngine()
    insight = engine._generate_insight(None)
    assert insight is None

def test_generate_insight_error_case_invalid_pattern():
    engine = MockNeuralEngine()
    insight = engine._generate_insight("invalid_pattern")
    assert insight is None