import pytest
from unified_core.storage.protobuf_storage import ProtobufInnovationStorage

def test_happy_path(tmpdir):
    storage_path = str(tmpdir.join("innovations.pb"))
    storage = ProtobufInnovationStorage(storage_path)
    assert storage.storage_path == storage_path
    assert storage._ensure_directory.call_count == 1
    logger.info.assert_called_once_with(f"📦 ProtobufInnovationStorage initialized: {storage_path}")

def test_edge_case_empty_path():
    with pytest.raises(ValueError):
        storage = ProtobufInnovationStorage("")

def test_edge_case_none_path():
    with pytest.raises(ValueError):
        storage = ProtobufInnovationStorage(None)

def test_error_case_invalid_path(tmpdir):
    invalid_path = str(tmpdir.join("invalid_dir", "innovations.pb"))
    storage = ProtobufInnovationStorage(invalid_path)
    assert storage.storage_path == invalid_path
    assert storage._ensure_directory.call_count == 1
    logger.info.assert_called_once_with(f"📦 ProtobufInnovationStorage initialized: {storage.storage_path}")