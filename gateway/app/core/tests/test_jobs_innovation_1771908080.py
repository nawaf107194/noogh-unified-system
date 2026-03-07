import pytest
from typing import List, Optional

from gateway.app.core.jobs import JobRecord, list_jobs

class MockJobGateway:
    def __init__(self):
        self.jobs = [
            JobRecord(id=1, name="Job 1"),
            JobRecord(id=2, name="Job 2"),
            JobRecord(id=3, name="Job 3"),
        ]

    def list_jobs(self, limit: int = 50) -> List[JobRecord]:
        return self.jobs[:limit]

@pytest.fixture
def job_gateway():
    return MockJobGateway()

def test_list_jobs_happy_path(job_gateway):
    result = job_gateway.list_jobs()
    assert len(result) == 3
    assert all(isinstance(job, JobRecord) for job in result)
    assert result[0].id == 1 and result[0].name == "Job 1"
    assert result[1].id == 2 and result[1].name == "Job 2"
    assert result[2].id == 3 and result[2].name == "Job 3"

def test_list_jobs_edge_case_empty(job_gateway):
    job_gateway.jobs = []
    result = job_gateway.list_jobs()
    assert len(result) == 0
    assert all(isinstance(job, JobRecord) for job in result)

def test_list_jobs_edge_case_none(job_gateway):
    job_gateway.jobs = None
    result = job_gateway.list_jobs()
    assert result is None

def test_list_jobs_edge_case_boundary_limit(job_gateway):
    result = job_gateway.list_jobs(limit=2)
    assert len(result) == 2
    assert all(isinstance(job, JobRecord) for job in result)

def test_list_jobs_error_case_invalid_input(job_gateway):
    with pytest.raises(ValueError):
        job_gateway.list_jobs(limit=-1)