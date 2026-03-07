import pytest
from google.protobuf import timestamp_pb2
from src.migrate_innovations_pb import json_to_proto, learning_pb2

def test_happy_path():
    json_input = {
        "_id": "12345",
        "rationale": "Test rationale",
        "triggered_by": "User1",
        "innovation_type": "optimize",
        "status": "suggested",
        "priority": "high",
        "source_tags": ["tag1", "tag2"],
        "timestamp": 1633072800,
        "applied_at": 1633072900,
        "target_files": ["file1.txt", "file2.txt"]
    }
    
    p = json_to_proto(json_input)
    
    assert p.id == "12345"
    assert p.description == "Test rationale"
    assert p.reasoning == "Test rationale"
    assert p.trigger_event == "User1"
    assert p.context['original_type'] == "optimize"
    assert p.innovation_type == learning_pb2.INNOVATION_TYPE_PERFORMANCE
    assert p.status == learning_pb2.INNOVATION_STATUS_SUGGESTED
    assert p.priority == 1
    assert p.context['tags'] == "tag1,tag2"
    assert p.suggested_at.seconds == 1633072800
    assert p.applied_at.seconds == 1633072900
    assert p.affected_files == ["file1.txt", "file2.txt"]

def test_edge_case_none_input():
    json_input = None
    
    p = json_to_proto(json_input)
    
    assert p is None

def test_edge_case_empty_dict():
    json_input = {}
    
    p = json_to_proto(json_input)
    
    assert p.id == ""
    assert p.description == ""
    assert p.reasoning == ""
    assert p.trigger_event == ""
    assert p.context['original_type'] == ""
    assert p.innovation_type == learning_pb2.INNOVATION_TYPE_UNSPECIFIED
    assert p.status == learning_pb2.INNOVATION_STATUS_UNSPECIFIED
    assert p.priority == 5
    assert p.context.get('tags') is None
    assert p.suggested_at.seconds == 0
    assert p.applied_at.seconds == 0
    assert not p.affected_files

def test_edge_case_invalid_priority():
    json_input = {
        "_id": "12345",
        "priority": "very_high"
    }
    
    p = json_to_proto(json_input)
    
    assert p.priority == 5

def test_error_case_missing_required_field():
    with pytest.raises(KeyError):
        json_to_proto({})
        
if __name__ == "__main__":
    pytest.main()