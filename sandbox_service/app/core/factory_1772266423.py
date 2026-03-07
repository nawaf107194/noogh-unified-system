# sandbox_service/app/core/sandbox_impl.py

from .factory import SandboxFactory

class SandboxImplementation:
    def __init__(self, sandbox_type, config):
        self.sandbox = SandboxFactory.create_sandbox(sandbox_type)
        self.config = config

    # Methods and properties for SandboxImplementation