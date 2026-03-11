"""
Tests for SelfDevAgent.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from agents.self_dev_agent import CodeAnalyzer, DuplicateDetector, PerformanceMonitor


class TestCodeAnalyzer:
    def setup_method(self):
        self.analyzer = CodeAnalyzer()

    def test_analyze_clean_file(self, tmp_path):
        code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''
        f = tmp_path / "clean.py"
        f.write_text(code)
        result = self.analyzer.analyze_file(f)
        assert result["score"] > 80
        assert result["file"] == "clean.py"

    def test_analyze_bare_except(self, tmp_path):
        code = '''
def risky():
    try:
        pass
    except:
        pass
'''
        f = tmp_path / "risky.py"
        f.write_text(code)
        result = self.analyzer.analyze_file(f)
        bare = [i for i in result["issues"] if i["type"] == "bare_except"]
        assert len(bare) > 0
        assert result["score"] < 100

    def test_analyze_invalid_file(self, tmp_path):
        f = tmp_path / "bad.py"
        f.write_text("def broken(")
        result = self.analyzer.analyze_file(f)
        assert "error" in result
        assert result["score"] == 0


class TestDuplicateDetector:
    def setup_method(self):
        self.detector = DuplicateDetector()

    def test_detect_timestamp_files(self, tmp_path):
        (tmp_path / "base_agent_1771673767.py").write_text("# old")
        results = self.detector.scan(tmp_path)
        names = [r["file"] for r in results]
        assert "base_agent_1771673767.py" in names

    def test_no_duplicates(self, tmp_path):
        (tmp_path / "clean_agent.py").write_text("# clean")
        results = self.detector.scan(tmp_path)
        assert len(results) == 0


class TestPerformanceMonitor:
    def setup_method(self):
        self.monitor = PerformanceMonitor()

    def test_evaluate_no_data(self):
        result = self.monitor.evaluate()
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

    def test_evaluate_low_winrate(self, tmp_path):
        stats = {"win_rate": 0.3, "max_drawdown": 0.05}
        stats_file = tmp_path / "trading_stats.json"
        stats_file.write_text(json.dumps(stats))
        self.monitor.data_dir = tmp_path
        result = self.monitor.evaluate()
        assert any("Win rate" in r for r in result["recommendations"])
