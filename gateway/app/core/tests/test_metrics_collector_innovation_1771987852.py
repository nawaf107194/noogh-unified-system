import pytest
from unittest.mock import patch
from datetime import datetime
import json

from gateway.app.core.metrics_collector import MetricsCollector

class TestMetricsCollector:

    @pytest.fixture
    def metrics_collector(self):
        return MetricsCollector()

    @pytest.fixture
    def mock_open_file(self, monkeypatch):
        mock_file = MagicMock()
        mock_file.write.return_value = None
        mock_file.close.return_value = None
        monkeypatch.setattr("builtins.open", lambda *args, **kwargs: mock_file)
        return mock_file

    def test_log_interaction_happy_path(self, metrics_collector, mock_open_file):
        query = "test_query"
        response = "test_response"
        success = True
        metadata = {"key": "value"}

        metrics_collector.log_interaction(query, response, success, metadata)

        expected_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "success": success,
            "metadata": metadata,
        }

        mock_open_file.assert_called_once_with(metrics_collector.current_log_file, "a", encoding="utf-8")
        mock_open_file.return_value.write.assert_called_once_with(json.dumps(expected_entry) + "\n")

    def test_log_interaction_edge_cases(self, metrics_collector, mock_open_file):
        query = ""
        response = None
        success = False
        metadata = {}

        metrics_collector.log_interaction(query, response, success, metadata)

        expected_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "success": success,
            "metadata": {},
        }

        mock_open_file.assert_called_once_with(metrics_collector.current_log_file, "a", encoding="utf-8")
        mock_open_file.return_value.write.assert_called_once_with(json.dumps(expected_entry) + "\n")

    def test_log_interaction_error_cases(self, metrics_collector):
        query = 123
        response = None
        success = False
        metadata = {}

        with pytest.raises(TypeError):
            metrics_collector.log_interaction(query, response, success, metadata)

    @patch.object(MetricsCollector, "_update_topic_stats")
    @patch.object(MetricsCollector, "_update_failure_stats")
    def test_log_interaction_update_stats(self, mock_update_topic_stats, mock_update_failure_stats, metrics_collector):
        query = "test_query"
        response = "test_response"
        success = True
        metadata = {"key": "value"}

        metrics_collector.log_interaction(query, response, success, metadata)

        if not success:
            mock_update_failure_stats.assert_called_once_with(query)
        else:
            mock_update_topic_stats.assert_called_once_with(query)