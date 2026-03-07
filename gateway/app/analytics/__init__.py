"""
Analytics engine for NOOGH Autonomic Dashboard.
Calculates KPIs, detects insights, and generates intelligence.
"""

from .kpi_calculator import KPICalculator
from .insights_engine import InsightsEngine

__all__ = ["KPICalculator", "InsightsEngine"]
