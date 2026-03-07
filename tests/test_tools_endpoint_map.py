import pytest

from tools_endpoint_map import match_calls_to_defs

def test_match_calls_to_defs_happy_path():
    endpoint_defs = {
        "/api/v1/users": [{"method": "GET", "handler": "get_users"}],
        "/api/v1/posts": [{"method": "POST", "handler": "create_post"}]
    }
    
    endpoint_calls = {
        "/api/v1/users": [{"method": "GET", "path": "/api/v1/users", "data": {}}],
        "/api/v1/posts": [{"method": "POST", "path": "/api/v1/posts", "data": {}}]
    }
    
    expected_output = [
        {
            "path": "/api/v1/users",
            "defined_in": [{"method": "GET", "handler": "get_users"}],
            "called_from": [{"method": "GET", "path": "/api/v1/users", "data": {}}]
        },
        {
            "path": "/api/v1/posts",
            "defined_in": [{"method": "POST", "handler": "create_post"}],
            "called_from": [{"method": "POST", "path": "/api/v1/posts", "data": {}}]
        }
    ]
    
    assert match_calls_to_defs(endpoint_defs, endpoint_calls) == expected_output

def test_match_calls_to_defs_edge_case_empty_input():
    endpoint_defs = {}
    endpoint_calls = {}
    
    assert match_calls_to_defs(endpoint_defs, endpoint_calls) == []

def test_match_calls_to_defs_edge_case_none_input():
    endpoint_defs = None
    endpoint_calls = None
    
    assert match_calls_to_defs(endpoint_defs, endpoint_calls) == []

def test_match_calls_to_defs_error_case_invalid_input_types():
    endpoint_defs = "not a dict"
    endpoint_calls = {"path": [{"method": "GET", "path": "/api/v1/users"}]}
    
    with pytest.raises(TypeError):
        match_calls_to_defs(endpoint_defs, endpoint_calls)