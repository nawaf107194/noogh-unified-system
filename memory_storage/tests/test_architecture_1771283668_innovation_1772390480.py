import pytest

class MemoryStorage:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        """Store an item in storage."""
        self.data[key] = value

def test_set_happy_path():
    memory_storage = MemoryStorage()
    memory_storage.set('test_key', 'test_value')
    assert memory_storage.data == {'test_key': 'test_value'}

def test_set_empty_key():
    memory_storage = MemoryStorage()
    memory_storage.set('', 'test_value')
    assert memory_storage.data == {}

def test_set_none_key():
    memory_storage = MemoryStorage()
    memory_storage.set(None, 'test_value')
    assert memory_storage.data == {None: 'test_value'}

def test_set_large_key():
    large_key = 'a' * 1024 * 1024  # 1MB key
    memory_storage = MemoryStorage()
    memory_storage.set(large_key, 'test_value')
    assert memory_storage.data == {large_key: 'test_value'}

def test_set_large_value():
    large_value = 'b' * 1024 * 1024  # 1MB value
    memory_storage = MemoryStorage()
    memory_storage.set('test_key', large_value)
    assert memory_storage.data == {'test_key': large_value}

def test_set_unicode_key():
    unicode_key = '测试'
    memory_storage = MemoryStorage()
    memory_storage.set(unicode_key, 'test_value')
    assert memory_storage.data == {unicode_key: 'test_value'}

def test_set_unicode_value():
    unicode_value = '测试'
    memory_storage = MemoryStorage()
    memory_storage.set('test_key', unicode_value)
    assert memory_storage.data == {'test_key': unicode_value}

def test_set_non_string_key():
    non_string_key = 123
    memory_storage = MemoryStorage()
    memory_storage.set(non_string_key, 'test_value')
    assert memory_storage.data == {non_string_key: 'test_value'}

def test_set_non_string_value():
    non_string_value = True
    memory_storage = MemoryStorage()
    memory_storage.set('test_key', non_string_value)
    assert memory_storage.data == {'test_key': True}