import pytest

class TestGetAllFunction:
    @pytest.fixture
    def storage_instance(self):
        from memory_storage.architecture_1771283668 import MemoryStorage
        instance = MemoryStorage()
        instance.data = {'key1': 'value1', 'key2': 'value2'}
        return instance
    
    @pytest.fixture
    def empty_storage_instance(self):
        from memory_storage.architecture_1771283668 import MemoryStorage
        instance = MemoryStorage()
        instance.data = {}
        return instance
    
    def test_get_all_happy_path(self, storage_instance):
        """Test that get_all returns a copy of the data dictionary."""
        result = storage_instance.get_all()
        assert result == {'key1': 'value1', 'key2': 'value2'}
        # Ensure that the returned object is a copy and not the original reference
        assert result is not storage_instance.data
    
    def test_get_all_empty_data(self, empty_storage_instance):
        """Test that get_all works correctly with an empty dictionary."""
        result = empty_storage_instance.get_all()
        assert result == {}
    
    def test_get_all_immutable(self, storage_instance):
        """Test that modifying the returned copy does not affect the original data."""
        result = storage_instance.get_all()
        result['key1'] = 'changed_value'
        assert storage_instance.data['key1'] == 'value1'
    
    def test_get_all_invalid_input(self):
        """Test that an error is raised if the class is instantiated without proper setup."""
        from memory_storage.architecture_1771283668 import MemoryStorage
        instance = MemoryStorage()
        with pytest.raises(AttributeError):
            instance.get_all()
    
    def test_get_all_async_behavior(self, monkeypatch):
        """Test that the function behaves synchronously as expected."""
        from memory_storage.architecture_1771283668 import MemoryStorage
        instance = MemoryStorage()
        instance.data = {'key1': 'value1'}
        
        # Mocking to ensure synchronous behavior
        def mock_copy():
            return instance.data
        
        monkeypatch.setattr(instance, 'get_all', mock_copy)
        result = instance.get_all()
        assert result == {'key1': 'value1'}
        assert result is not instance.data