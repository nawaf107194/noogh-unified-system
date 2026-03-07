import pytest
import os
from unittest.mock import patch
from gateway.app.core.policy_store import PolicyStore, PolicySnapshot, DEFAULT_POLICY

def test_load_happy_path(tmpdir):
    store = PolicyStore(Path(str(tmpdir / "policy.json")))
    assert isinstance(store.load(), PolicySnapshot)
    assert store._policy == DEFAULT_POLICY
    with open(store.path, "r") as f:
        loaded_policy = json.load(f)
    assert loaded_policy == DEFAULT_POLICY

def test_load_empty_file(tmpdir):
    store = PolicyStore(Path(str(tmpdir / "policy.json")))
    with patch.object(store, "_read_nolock", return_value={}):
        snapshot = store.load()
        assert isinstance(snapshot, PolicySnapshot)
        assert store._policy == {}
        assert snapshot.policy == {}

def test_load_nonexistent_file(tmpdir):
    store = PolicyStore(Path(str(tmpdir / "nonexistent_policy.json")))
    with patch.object(os.path, "exists", return_value=False):
        snapshot = store.load()
        assert isinstance(snapshot, PolicySnapshot)
        assert store._policy == DEFAULT_POLICY
        assert snapshot.policy == DEFAULT_POLICY

def test_load_invalid_json(tmpdir):
    store = PolicyStore(Path(str(tmpdir / "invalid_policy.json")))
    with open(store.path, "w") as f:
        f.write("invalid json")
    with patch.object(os.path, "exists", return_value=True):
        snapshot = store.load()
        assert isinstance(snapshot, PolicySnapshot)
        assert store._policy == {}
        assert snapshot.policy == {}

def test_load_with_defaults(tmpdir):
    store = PolicyStore(Path(str(tmpdir / "policy.json")))
    custom_policy = {"key": "value"}
    with patch.object(store, "_read_nolock", return_value=custom_policy):
        snapshot = store.load()
        assert isinstance(snapshot, PolicySnapshot)
        assert store._policy == {**DEFAULT_POLICY, **custom_policy}
        assert snapshot.policy == {**DEFAULT_POLICY, **custom_policy}