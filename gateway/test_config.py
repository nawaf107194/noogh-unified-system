# gateway/test_config.py
class TestConfig:
    BASE_URL = "http://localhost"
    DEFAULT_PORT = 8000
    SECURE_PORT = 8443
    API_VERSION = "v1"
    
    def get_base_url(self, secure=False):
        protocol = "https" if secure else "http"
        port = self.SECURE_PORT if secure else self.DEFAULT_PORT
        return f"{protocol}://{self.BASE_URL}:{port}/{self.API_VERSION}"