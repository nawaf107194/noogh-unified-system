import pytest
from unittest.mock import patch, Mock
from gateway.app.llm.brain_factory import create_brain, settings, logger

class TestBrainFactory:

    @pytest.fixture
    def mock_settings(self):
        with patch('gateway.app.llm.brain_factory.settings.ROUTING_MODE', return_value='cloud'):
            yield

    @pytest.fixture
    def mock_logger_info(self):
        with patch.object(logger, 'info') as mock_info:
            yield mock_info

    @pytest.fixture
    def mock_secrets(self):
        return {
            "CLOUD_API_KEY": "api_key",
            "CLOUD_PROVIDER": "provider"
        }

    @pytest.mark.usefixtures('mock_settings', 'mock_logger_info')
    def test_happy_path_cloud_mode(self, mock_secrets):
        service = create_brain(mock_secrets)
        assert isinstance(service, CloudClient)
        mock_logger_info.assert_called_once_with("BrainFactory: Initializing CloudClient (provider)")

    @pytest.mark.usefixtures('mock_settings', 'mock_logger_info')
    def test_happy_path_local_mode(self, mock_secrets):
        with patch.dict(settings.__dict__, {'ROUTING_MODE': 'auto'}), \
             patch.dict(mock_secrets, {'CLOUD_API_KEY': None}):
            service = create_brain(mock_secrets)
            assert isinstance(service, LocalBrainService)
            mock_logger_info.assert_called_once_with("BrainFactory: Initializing LocalBrainService")

    @pytest.mark.usefixtures('mock_settings', 'mock_logger_info')
    def test_edge_case_empty_secrets(self):
        with patch.dict(settings.__dict__, {'ROUTING_MODE': 'cloud'}), \
             patch.dict(mock_secrets, {'CLOUD_API_KEY': None}):
            service = create_brain({})
            assert isinstance(service, LocalBrainService)
            mock_logger_info.assert_called_once_with("BrainFactory: Initializing LocalBrainService")

    @pytest.mark.usefixtures('mock_settings', 'mock_logger_info')
    def test_edge_case_none_secrets(self):
        with patch.dict(settings.__dict__, {'ROUTING_MODE': 'cloud'}), \
             patch.dict(mock_secrets, {'CLOUD_API_KEY': None}):
            service = create_brain(None)
            assert isinstance(service, LocalBrainService)
            mock_logger_info.assert_called_once_with("BrainFactory: Initializing LocalBrainService")

    @pytest.mark.usefixtures('mock_settings', 'mock_logger_info')
    def test_error_case_invalid_mode(self, mock_secrets):
        with patch.dict(settings.__dict__, {'ROUTING_MODE': 'invalid'}):
            service = create_brain(mock_secrets)
            assert isinstance(service, LocalBrainService)
            mock_logger_info.assert_called_once_with("BrainFactory: Initializing LocalBrainService")

    @pytest.mark.usefixtures('mock_settings', 'mock_logger_info')
    def test_error_case_no_api_key(self, mock_secrets):
        with patch.dict(settings.__dict__, {'ROUTING_MODE': 'auto'}), \
             patch.dict(mock_secrets, {'CLOUD_API_KEY': None}):
            service = create_brain(mock_secrets)
            assert isinstance(service, LocalBrainService)
            mock_logger_info.assert_called_once_with("BrainFactory: Initializing LocalBrainService")

    @pytest.mark.usefixtures('mock_settings', 'mock_logger_info')
    def test_error_case_no_provider(self, mock_secrets):
        with patch.dict(settings.__dict__, {'ROUTING_MODE': 'cloud'}), \
             patch.dict(mock_secrets, {'CLOUD_API_KEY': "api_key", 'CLOUD_PROVIDER': None}):
            service = create_brain(mock_secrets)
            assert isinstance(service, CloudClient)
            mock_logger_info.assert_called_once_with("BrainFactory: Initializing CloudClient (None)")