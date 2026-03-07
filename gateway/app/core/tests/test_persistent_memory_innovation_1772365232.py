import json
import os
from pathlib import Path
import tempfile

from gateway.app.core.persistent_memory import _atomic_write_json

def test_atomic_write_json_happy_path():
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "test.json")
        data = {"key": "value"}
        _atomic_write_json(path, data)
        assert os.path.exists(path)
        with open(path, 'r') as f:
            content = json.load(f)
            assert content == data

def test_atomic_write_json_empty_data():
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "test.json")
        data = {}
        _atomic_write_json(path, data)
        assert os.path.exists(path)
        with open(path, 'r') as f:
            content = json.load(f)
            assert content == data

def test_atomic_write_json_none_data():
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "test.json")
        data = None
        _atomic_write_json(path, data)
        assert os.path.exists(path)
        with open(path, 'r') as f:
            content = json.load(f)
            assert content is None

def test_atomic_write_json_boundary_data():
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "test.json")
        data = {
            "int": 10**9,
            "float": 3.141592653589793,
            "bool": True,
            "string": "a" * 1000,
            "list": [i for i in range(10)],
            "dict": {"key": "value"}
        }
        _atomic_write_json(path, data)
        assert os.path.exists(path)
        with open(path, 'r') as f:
            content = json.load(f)
            assert content == data

def test_atomic_write_json_invalid_data():
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "test.json")
        data = {"key": ["value", None]}
        with pytest.raises(TypeError):
            _atomic_write_json(path, data)

def test_atomic_write_json_file_lock_error(mocker):
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "test.json")
        data = {"key": "value"}
        mock_os_replace = mocker.patch("os.replace", side_effect=OSError)
        with pytest.raises(OSError):
            _atomic_write_json(path, data)
        assert not os.path.exists(path)
        mock_os_replace.assert_called_once()

def test_atomic_write_json_tempfile_error(mocker):
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "test.json")
        data = {"key": "value"}
        mock_temfile_mkstemp = mocker.patch("tempfile.mkstemp", side_effect=OSError)
        with pytest.raises(OSError):
            _atomic_write_json(path, data)
        assert not os.path.exists(path)
        mock_temfile_mkstemp.assert_called_once()

def test_atomic_write_json_file_lock_race_condition(mocker):
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "test.json")
        data = {"key": "value"}
        mock_os_replace = mocker.patch("os.replace", side_effect=OSError)
        mock_os_unlink = mocker.patch("os.unlink", side_effect=None)
        with pytest.raises(OSError):
            _atomic_write_json(path, data)
        assert not os.path.exists(path)
        mock_os_replace.assert_called_once()
        mock_os_unlink.assert_called_once()

def test_atomic_write_json_file_lock_race_condition_no_tmp(mocker):
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "test.json")
        data = {"key": "value"}
        mock_os_replace = mocker.patch("os.replace", side_effect=OSError)
        mock_os_unlink = mocker.patch("os.unlink", side_effect=None)
        mock_os_remove = mocker.patch("os.remove", side_effect=None)
        with pytest.raises(OSError):
            _atomic_write_json(path, data)
        assert not os.path.exists(path)
        mock_os_replace.assert_called_once()
        mock_os_unlink.assert_called_once()
        mock_os_remove.assert_called_once()