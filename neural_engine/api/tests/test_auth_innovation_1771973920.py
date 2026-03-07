import os
from fastapi import HTTPException, Header, FastAPI
from unittest.mock import patch
import pytest

app = FastAPI()

@app.get("/")
@patch.dict(os.environ, {"NOOGH_INTERNAL_TOKEN": "expected_token"}, clear=True)
def root(x_internal_token: Optional[str] = Header(default=None)):
    require_internal_token(x_internal_token)
    return {"message": "Success"}

def test_require_internal_token_happy_path():
    response = app.test_client().get("/", headers={"X-Internal-Token": "expected_token"})
    assert response.status_code == 200
    assert response.json() == {"message": "Success"}

def test_require_internal_token_empty_token():
    with pytest.raises(HTTPException) as exc_info:
        app.test_client().get("/", headers={"X-Internal-Token": ""})
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Missing internal token"

def test_require_internal_token_none_token():
    with pytest.raises(HTTPException) as exc_info:
        app.test_client().get("/", headers={})
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Missing internal token"

def test_require_internal_token_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        app.test_client().get("/", headers={"X-Internal-Token": "wrong_token"})
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Invalid internal token"

def test_require_internal_token_no_configured_token():
    with patch.dict(os.environ, {"NOOGH_INTERNAL_TOKEN": ""}, clear=True):
        with pytest.raises(HTTPException) as exc_info:
            app.test_client().get("/", headers={"X-Internal-Token": "expected_token"})
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal token not configured"