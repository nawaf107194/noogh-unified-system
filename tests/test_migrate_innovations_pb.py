import pytest
from google.protobuf import timestamp_pb2
from datetime import datetime, timedelta

def create_test_json_inno(**overrides):
    defaults = {
        '_id': 'test_id',
        'timestamp': 1633072800.0,
        'innovation_type': 'optimize',
        'status': 'suggested',
        'priority': 'medium',
        'source_tags': ['tag1', 'tag2'],
        'target_files': ['file1.py', 'file2.py']
    }
    defaults.update(overrides)
    return defaults

def test_json_to_proto_happy_path():
    json_inno = create_test_json_inno()
    p = json_to_proto(json_inno)
    
    assert p.id == 'optimize_1633072800.0'
    assert p.description == ''
    assert p.reasoning == ''
    assert p.trigger_event == ''
    assert p.context['original_type'] == 'optimize'
    assert p.innovation_type == learning_pb2.INNOVATION_TYPE_PERFORMANCE
    assert p.status == learning_pb2.INNOVATION_STATUS_SUGGESTED
    assert p.priority == 5
    assert p.context['tags'] == 'tag1,tag2'
    assert p.suggested_at.seconds == 1633072800
    assert p.suggested_at.nanos == 0
    assert p.applied_at.seconds == 0
    assert p.applied_at.nanos == 0
    assert p.affected_files == ['file1.py', 'file2.py']

def test_json_to_proto_empty_input():
    json_inno = {}
    p = json_to_proto(json_inno)
    
    assert p.id.startswith('unknown_')
    assert p.description == ''
    assert p.reasoning == ''
    assert p.trigger_event == ''
    assert p.context['original_type'] == ''
    assert p.innovation_type == learning_pb2.INNOVATION_TYPE_UNSPECIFIED
    assert p.status == learning_pb2.INNOVATION_STATUS_UNSPECIFIED
    assert p.priority == 5
    assert 'tags' not in p.context
    assert p.suggested_at.seconds == 0
    assert p.suggested_at.nanos == 0
    assert p.applied_at.seconds == 0
    assert p.applied_at.nanos == 0
    assert len(p.affected_files) == 0

def test_json_to_proto_none_input():
    json_inno = None
    p = json_to_proto(json_inno)
    
    assert p is None

def test_json_to_proto_invalid_timestamp():
    json_inno = create_test_json_inno(timestamp='invalid')
    p = json_to_proto(json_inno)
    
    assert 'suggested_at' not in p

def test_json_to_proto_invalid_priority():
    json_inno = create_test_json_inno(priority='invalid')
    p = json_to_proto(json_inno)
    
    assert p.priority == 5