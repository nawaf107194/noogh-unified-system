import os

import pytest

# Set environment variables IMMEDIATELY for import-time config validation
# Must match SecretsManager requirements
os.environ["NOOGH_ADMIN_TOKEN"] = "test-admin-token"
os.environ["NOOGH_SERVICE_TOKEN"] = "test-service-token"
os.environ["NOOGH_READONLY_TOKEN"] = "test-readonly-token"
os.environ["NOOGH_INTERNAL_TOKEN"] = "test-internal-token"
os.environ["NOOGH_JOB_SIGNING_SECRET"] = "test-secret-min-32-chars-long-12345"
os.environ["NOOGH_PLUGIN_SIGNING_KEY"] = "test-plugin-key-12345"
os.environ["NOOGH_HOST"] = "127.0.0.1"
os.environ["NOOGH_PORT"] = "8000"
os.environ["NOOGH_SANDBOX_URL"] = "http://localhost:8000"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["NOOGH_ENV"] = "test"
os.environ["CLOUD_API_KEY"] = "test-cloud-key"
os.environ["CLOUD_PROVIDER"] = "openai"
os.environ["CLOUD_API_URL"] = "https://api.openai.com/v1"
os.environ["CLOUD_MODEL"] = "gpt-4"

if "NOOGH_DATA_DIR" not in os.environ:
    os.environ["NOOGH_DATA_DIR"] = "/tmp/noogh_test_default"


@pytest.fixture(scope="session", autouse=True)
def global_env_setup(tmp_path_factory):
    """Set up global environment variables for all tests"""
    data_dir = tmp_path_factory.mktemp("noogh_data")
    os.environ["NOOGH_DATA_DIR"] = str(data_dir)

    (data_dir / ".noogh_memory").mkdir(exist_ok=True)
    (data_dir / ".noogh_memory" / "sessions").mkdir(exist_ok=True)
    (data_dir / ".noogh_audit").mkdir(exist_ok=True)

    yield


@pytest.fixture
def admin_auth():
    """Admin auth context fixture"""
    from gateway.app.core.auth import AuthContext

    return AuthContext(token="test-admin-token", scopes={"*"})


@pytest.fixture(autouse=True)
def patch_agent_skills(global_env_setup):
    """Ensure AgentSkills uses the test data dir - NO-OP for new instance-based skills but kept for compat if needed"""
    yield
