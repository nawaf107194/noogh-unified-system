import pytest

from unified_core.intelligence.critical_thinking import _reverse_causation

def test_reverse_causation_happy_path():
    claim = "The rain caused the road to be wet."
    expected_result = "Reverse causation: The assumed effect actually caused the assumed cause"
    assert _reverse_causation(claim) == expected_result

def test_reverse_causation_empty_input():
    claim = ""
    expected_result = "Reverse causation: The assumed effect actually caused the assumed cause"
    assert _reverse_causation(claim) == expected_result

def test_reverse_causation_none_input():
    claim = None
    expected_result = "Reverse causation: The assumed effect actually caused the assumed cause"
    assert _reverse_causation(claim) == expected_result

def test_reverse_causation_boundary_case():
    claim = "The sun sets in the west."
    expected_result = "Reverse causation: The assumed effect actually caused the assumed cause"
    assert _reverse_causation(claim) == expected_result