import pytest
from unified_core.intelligence.explainer import Explainer

class TestExplainerFormat:

    def setup_method(self):
        self.explainer = Explainer()

    def test_happy_path_complete_explanation(self):
        explanation = {
            'summary': 'Decision summary',
            'reasoning': 'Reasoning chain details',
            'alternatives': 'Alternative options',
            'confidence': {'level': 0.85, 'interpretation': 'High', 'factors': ['Factor1', 'Factor2']},
            'risks': 'Known risks',
            'next_steps': 'Next steps to take',
            'details': 'Technical details'
        }
        audience = "User"
        expected_output = (
            f"=== DECISION EXPLANATION ({audience.upper()}) ===\n"
            "Summary: Decision summary\n"
            "Reasoning Chain:\n"
            "Reasoning chain details\n"
            "Alternatives Considered:\n"
            "Alternative options\n"
            "Confidence: 85.0% (High)\n"
            "Factors: Factor1, Factor2\n"
            "Known Risks:\n"
            "Known risks\n"
            "Next Steps:\n"
            "Next steps to take\n"
            "\nTechnical Details: Technical details"
        )
        assert self.explainer._format(explanation, audience) == expected_output

    def test_happy_path_minimum_explanation(self):
        explanation = {
            'summary': 'Decision summary'
        }
        audience = "System"
        expected_output = (
            f"=== DECISION EXPLANATION ({audience.upper()}) ===\n"
            "Summary: Decision summary\n"
        )
        assert self.explainer._format(explanation, audience) == expected_output

    def test_edge_case_empty_explanation(self):
        explanation = {}
        audience = ""
        expected_output = (
            f"=== DECISION EXPLANATION ({audience.upper()}) ===\n"
        )
        assert self.explainer._format(explanation, audience) == expected_output

    def test_edge_case_none_audience(self):
        explanation = {
            'summary': 'Decision summary'
        }
        audience = None
        with pytest.raises(TypeError) as excinfo:
            self.explainer._format(explanation, audience)
        assert "Can't convert 'NoneType' object to str" in str(excinfo.value)

    def test_edge_case_none_summary(self):
        explanation = {
            'summary': None
        }
        audience = "User"
        expected_output = (
            f"=== DECISION EXPLANATION ({audience.upper()}) ===\n"
            "Summary: None\n"
        )
        assert self.explainer._format(explanation, audience) == expected_output

    def test_edge_case_empty_string_summary(self):
        explanation = {
            'summary': ''
        }
        audience = "User"
        expected_output = (
            f"=== DECISION EXPLANATION ({audience.upper()}) ===\n"
            "Summary: \n"
        )
        assert self.explainer._format(explanation, audience) == expected_output