from unified_core.initialization import mark_ready, ComponentState

class TestMarkReady:

    @pytest.fixture(autouse=True)
    def setup(self):
        from unified_core.initialization import _components, _lock
        self._original_components = _components.copy()
        self._original_lock_state = _lock.locked()
        _components.clear()
        if self._original_lock_state:
            _lock.release()

    @pytest.fixture(autouse=True)
    def teardown(self):
        from unified_core.initialization import _components, _lock
        _components.update(self._original_components)
        if self._original_lock_state:
            _lock.acquire()

    def test_happy_path(self):
        mark_ready("test_component")
        assert "test_component" in mark_ready._components
        assert mark_ready._components["test_component"] == ComponentState.READY

    def test_empty_name(self):
        with pytest.raises(RuntimeError, match="Component None not registered"):
            mark_ready(None)

    def test_none_name(self):
        with pytest.raises(RuntimeError, match="Component None not registered"):
            mark_ready("")

    def test_unregistered_component(self):
        with pytest.raises(RuntimeError, match="Component fake_component not registered"):
            mark_ready("fake_component")