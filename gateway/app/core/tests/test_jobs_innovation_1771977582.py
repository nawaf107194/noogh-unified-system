import pytest

from gateway.app.core.jobs import JobRecord, get_job

class MockJobRepository:
    def __init__(self):
        self.jobs = {
            "1": JobRecord(id="1", name="Test Job 1", status="Pending"),
            "2": JobRecord(id="2", name="Test Job 2", status="Completed")
        }

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        return self.jobs.get(job_id)

@pytest.fixture
def job_repository():
    return MockJobRepository()

def test_get_job_happy_path(job_repository):
    # Arrange
    job_id = "1"
    expected_result = JobRecord(id="1", name="Test Job 1", status="Pending")
    
    # Act
    result = get_job(job_id, job_repository)
    
    # Assert
    assert result == expected_result

def test_get_job_empty_job_id(job_repository):
    # Arrange
    job_id = ""
    expected_result = None
    
    # Act
    result = get_job(job_id, job_repository)
    
    # Assert
    assert result == expected_result

def test_get_job_none_job_id(job_repository):
    # Arrange
    job_id = None
    expected_result = None
    
    # Act
    result = get_job(job_id, job_repository)
    
    # Assert
    assert result == expected_result

def test_get_job_non_existent_job_id(job_repository):
    # Arrange
    job_id = "3"
    expected_result = None
    
    # Act
    result = get_job(job_id, job_repository)
    
    # Assert
    assert result == expected_result

def test_get_job_boundary_values(job_repository):
    # Arrange
    min_id = "0"
    max_id = "9999999999"
    expected_min_result = None
    expected_max_result = None
    
    # Act
    result_min = get_job(min_id, job_repository)
    result_max = get_job(max_id, job_repository)
    
    # Assert
    assert result_min == expected_min_result
    assert result_max == expected_max_result

def test_get_job_async_behavior(job_repository):
    # This test is not applicable as the function does not have async behavior
    pass