import pytest
from pathlib import Path
from noogh_system_diagnostic import check_endpoints, DiagResult

# Mocking the ENGINE_ROOT and its contents for testing
def mock_routes_file_content():
    return """
@router.post("/login")
def login():
    pass

@router.get("/public-data")
def public_data():
    pass

@router.post("/secure-data", Depends(verify_internal_token))
def secure_data():
    pass
"""

# Test fixtures to setup the test environment
@pytest.fixture
def mock_routes_file(tmp_path):
    routes_file = tmp_path / "api" / "routes.py"
    routes_file.parent.mkdir(parents=True, exist_ok=True)
    routes_file.write_text(mock_routes_file_content())
    return routes_file

@pytest.fixture
def mock_empty_routes_file(tmp_path):
    routes_file = tmp_path / "api" / "routes.py"
    routes_file.parent.mkdir(parents=True, exist_ok=True)
    routes_file.write_text("")
    return routes_file

@pytest.fixture
def non_existent_routes_file():
    routes_file = Path("/nonexistent/api/routes.py")
    return routes_file

# Test cases
def test_check_endpoints_happy_path(mock_routes_file):
    result = check_endpoints()
    assert result.status == "ok"
    assert result.message.startswith("Total endpoints: 3")
    assert "Authenticated: 1" in result.message
    assert "Unauthenticated: 2" in result.message

def test_check_endpoints_empty_routes_file(mock_empty_routes_file):
    result = check_endpoints()
    assert result.status == "ok"
    assert result.message.startswith("Total endpoints: 0")
    assert "Authenticated: 0" in result.message
    assert "Unauthenticated: 0" in result.message

def test_check_endpoints_non_existent_routes_file(non_existent_routes_file):
    result = check_endpoints()
    assert result.status == "error"
    assert result.message == "routes.py not found"

# Note: There are no error cases or async behavior in the provided function, so additional tests for those scenarios would be needed if they were part of the original code.