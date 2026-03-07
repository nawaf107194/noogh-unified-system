import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from gateway.app.core.worker import Worker, JobRecord
from kernel.models import Kernel, Result

class TestWorker:

    @pytest.fixture
    def worker(self):
        return Worker()

    @pytest.fixture
    def job_record(self):
        job_request = JobRequest(
            task="echo hello",
            budgets=Budgets(max_steps=10)
        )
        return JobRecord(request=job_request)

    @patch('gateway.app.core.worker.Worker.get_kernel')
    @patch('kernel.models.Kernel.process')
    def test_happy_path(self, mock_process, worker, job_record):
        mock_result = Result(
            success=True,
            answer="hello",
            error=None,
            steps=1
        )
        mock_process.return_value = mock_result

        result = worker._execute_sync(job_record)

        assert result == {
            "success": True,
            "answer": "hello",
            "error": None,
            "steps": 1,
            "execution_time_ms": pytest.approx(0, abs=1)
        }
        assert mock_process.call_count == 1
        assert mock_process.call_args_list[0][0] == ("echo hello",)
        assert mock_process.call_args_list[0][1]['auth'] == AuthContext(token="worker", scopes={"*"})

    @patch('gateway.app.core.worker.Worker.get_kernel')
    def test_edge_case_empty_job_record(self, mock_get_kernel, worker):
        job_record = JobRecord(request=None)

        result = worker._execute_sync(job_record)

        assert result == {
            "success": False,
            "answer": None,
            "error": "Invalid job request",
            "steps": 0,
            "execution_time_ms": pytest.approx(0, abs=1)
        }
        assert mock_get_kernel.call_count == 0

    @patch('gateway.app.core.worker.Worker.get_kernel')
    def test_error_case_invalid_budgets(self, mock_get_kernel, worker):
        job_request = JobRequest(
            task="echo hello",
            budgets=None
        )
        job_record = JobRecord(request=job_request)

        result = worker._execute_sync(job_record)

        assert result == {
            "success": False,
            "answer": None,
            "error": "Invalid job request",
            "steps": 0,
            "execution_time_ms": pytest.approx(0, abs=1)
        }
        assert mock_get_kernel.call_count == 0