import pytest

class TestMultiHypothesisReasoning:
    def setup_method(self):
        from unified_core.intelligence.multi_hypothesis_reasoning import MultiHypothesisReasoning
        self.mhr = MultiHypothesisReasoning()
        self.mhr.current_weights = {'h1': 0.5, 'h2': 0.3, 'h3': 0.2}

    def test_update_hypothesis_weights_happy_path(self):
        evidence = {'h1': 0.8, 'h2': 0.2}
        self.mhr.update_hypothesis_weights(evidence)
        assert pytest.approx(self.mhr.current_weights['h1'], abs=0.01) == 0.5 * (1 + 0.8)
        assert pytest.approx(self.mhr.current_weights['h2'], abs=0.01) == 0.3 * (1 + 0.2)
        assert pytest.approx(self.mhr.current_weights['h3'], abs=0.01) == 0.2

    def test_update_hypothesis_weights_empty_evidence(self):
        evidence = {}
        self.mhr.update_hypothesis_weights(evidence)
        for weight in self.mhr.current_weights.values():
            assert pytest.approx(weight, abs=0.01) == 0.5 * 0.95

    def test_update_hypothesis_weights_none_evidence(self):
        evidence = None
        self.mhr.update_hypothesis_weights(evidence)
        for weight in self.mhr.current_weights.values():
            assert pytest.approx(weight, abs=0.01) == 0.5 * 0.95

    def test_update_hypothesis_weights_invalid_evidence(self):
        evidence = 'not a dictionary'
        with pytest.raises(TypeError):
            self.mhr.update_hypothesis_weights(evidence)

    def test_update_hypothesis_weights_missing_evidence(self):
        evidence = {'h1': 0.8}
        self.mhr.update_hypothesis_weights(evidence)
        assert pytest.approx(self.mhr.current_weights['h2'], abs=0.01) == 0.3 * (1 + 0.2)
        assert pytest.approx(self.mhr.current_weights['h3'], abs=0.01) == 0.2