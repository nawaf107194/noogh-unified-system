import pytest

from unified_core.system.resource_governor_1772391658 import ResourceGovernor, LLMClient

class TestResourceGovernorInit:

    @pytest.fixture
    def llm_client(self):
        return LLMClient()

    @pytest.fixture
    def resource_governor(self):
        return ResourceGovernor()

    def test_happy_path(self, llm_client, resource_governor):
        governor = ResourceGovernor(llm_client=llm_client, resource_governor=resource_governor)
        assert governor.llm_client == llm_client
        assert governor.resource_governor == resource_governor

    def test_resource_governor_none(self, llm_client):
        governor = ResourceGovernor(llm_client=llm_client)
        assert governor.llm_client == llm_client
        assert isinstance(governor.resource_governor, ResourceGovernor)

    def test_llm_client_none(self, resource_governor):
        governor = ResourceGovernor(llm_client=None, resource_governor=resource_governor)
        assert governor.llm_client is None
        assert governor.resource_governor == resource_governor

    def test_both_none(self, llm_client, resource_governor):
        governor = ResourceGovernor(llm_client=None, resource_governor=None)
        assert governor.llm_client is None
        assert isinstance(governor.resource_governor, ResourceGovernor)

    def test_invalid_llm_client_type(self, resource_governor):
        with pytest.raises(TypeError) as exc_info:
            ResourceGovernor(llm_client="not a client", resource_governor=resource_governor)
        assert "llm_client" in str(exc_info.value)

    def test_invalid_resource_governor_type(self, llm_client):
        with pytest.raises(TypeError) as exc_info:
            ResourceGovernor(llm_client=llm_client, resource_governor="not a governor")
        assert "resource_governor" in str(exc_info.value)