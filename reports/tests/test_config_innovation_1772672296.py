import pytest

class TestGetSetting:
    def setup_method(self):
        self.settings = {
            'valid_key': 'value',
            'another_valid_key': 123
        }
        self.subject = SettingsManager(self.settings)

    def test_get_setting_with_existing_key(self):
        result = self.subject.get_setting('valid_key')
        assert result == 'value'

    def test_get_setting_with_non_existing_key(self):
        result = self.subject.get_setting('nonexistent_key')
        assert result is None

    def test_get_setting_with_empty_string_key(self):
        result = self.subject.get_setting('')
        assert result is None

    def test_get_setting_with_none_key(self):
        result = self.subject.get_setting(None)
        assert result is None

    def test_get_setting_with_long_key(self):
        long_key = 'test_key' * 100
        result = self.subject.get_setting(long_key)
        assert result is None