import pytest

from gateway.app.core.local_brain_bridge import LocalBrainBridge, ModuleMetadata

class TestLocalBrainBridge:

    @pytest.fixture
    def local_brain_bridge(self):
        return LocalBrainBridge()

    def test_get_metadata_happy_path(self, local_brain_bridge):
        # Arrange
        expected_metadata = ModuleMetadata()
        local_brain_bridge._metadata = expected_metadata

        # Act
        result = local_brain_bridge.get_metadata()

        # Assert
        assert result == expected_metadata

    def test_get_metadata_edge_case_none(self, local_brain_bridge):
        # Arrange
        local_brain_bridge._metadata = None

        # Act
        result = local_brain_bridge.get_metadata()

        # Assert
        assert result is None

    def test_get_metadata_edge_case_empty(self, local_brain_bridge):
        # Arrange
        local_brain_bridge._metadata = ModuleMetadata()

        # Act
        result = local_brain_bridge.get_metadata()

        # Assert
        assert result == local_brain_bridge._metadata  # Assuming empty metadata is valid

    def test_get_metadata_error_case_invalid_input(self, local_brain_bridge):
        # Arrange
        invalid_input = "not a ModuleMetadata instance"

        # Act & Assert
        with pytest.raises(TypeError):
            local_brain_bridge._metadata = invalid_input
            local_brain_bridge.get_metadata()