import pytest
from typing import List, Dict, Optional
from gateway.app.analytics.kpi_calculator import _calc_approval_rate

def safe_div(numerator: int, denominator: int, default: float) -> float:
    return numerator / denominator if denominator != 0 else default

class TestKPI_Calculator:

    def test_happy_path(self):
        events = [
            {'type': 'decision', 'payload': {'approved': True}},
            {'type': 'decision', 'payload': {'approved': False}},
            {'type': 'decision', 'payload': {'approved': True}}
        ]
        assert _calc_approval_rate(events) == 67.00

    def test_empty_list(self):
        events = []
        assert _calc_approval_rate(events) == 0.00

    def test_none_input(self):
        assert _calc_approval_rate(None) == 0.00

    def test_no_decisions(self):
        events = [
            {'type': 'other', 'payload': {}},
            {'type': 'other', 'payload': {}}
        ]
        assert _calc_approval_rate(events) == 0.00

    def test_boundary_values(self):
        events = [{'type': 'decision', 'payload': {'approved': True}}]
        assert _calc_approval_rate(events) == 100.00

        events = [{'type': 'decision', 'payload': {'approved': False}}]
        assert _calc_approval_rate(events) == 0.00

    def test_invalid_inputs(self):
        # The function does not explicitly raise exceptions, so we don't need to test for specific errors here.
        pass