import pytest

def test_update_config_happy_path():
    config_manager = ConfigManager.get_instance()
    old_value = config_manager.config_data['key']
    new_value = 'new_value'
    config_manager.update_config('key', new_value)
    updated_value = config_manager.get_config()['key']
    assert updated_value == new_value
    config_manager.update_config('key', old_value)  # Reset to original value

def test_update_config_empty_key():
    config_manager = ConfigManager.get_instance()
    new_value = 'new_value'
    with pytest.raises(KeyError):
        config_manager.update_config('', new_value)

def test_update_config_none_key():
    config_manager = ConfigManager.get_instance()
    new_value = 'new_value'
    with pytest.raises(KeyError):
        config_manager.update_config(None, new_value)

def test_update_config_nonexistent_key():
    config_manager = ConfigManager.get_instance()
    key = 'nonexistent_key'
    new_value = 'new_value'
    updated_value = config_manager.update_config(key, new_value)
    assert updated_value is None
    config_manager.config_data[key] = old_value  # Reset to original value

def test_update_config_boundary_values():
    config_manager = ConfigManager.get_instance()
    old_value = config_manager.config_data['key']
    boundary_value = 'boundary_value'
    config_manager.update_config('key', boundary_value)
    updated_value = config_manager.get_config()['key']
    assert updated_value == boundary_value
    config_manager.update_config('key', old_value)  # Reset to original value

def test_update_config_async_behavior(mocker):
    mock_get_instance = mocker.patch.object(ConfigManager, 'get_instance')
    mock_get_instance.return_value.config_data = {'key': 'old_value'}
    
    async def async_update_and_check():
        config_manager = ConfigManager.get_instance()
        key = 'key'
        new_value = 'new_value'
        await asyncio.sleep(0.1)  # Simulate async operation
        config_manager.update_config(key, new_value)
        updated_value = config_manager.get_config()[key]
        assert updated_value == new_value
        config_manager.update_config(key, old_value)  # Reset to original value
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(async_update_and_check())
    finally:
        loop.close()

# Run with pytest