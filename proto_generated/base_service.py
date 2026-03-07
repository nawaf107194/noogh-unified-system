# proto_generated/base_service.py
import abc
import grpc
from typing import Type, Any

class BaseGrpcService(abc.ABC):
    def __init__(self, service_name: str, host: str = 'localhost', port: int = 50051):
        self.service_name = service_name
        self.host = host
        self.port = port
        self.channel = None
        self.stub = None
        self.server = None

    @abc.abstractmethod
    def get_service_class(self) -> Type[Any]:
        """Return the generated service class"""
        pass

    @abc.abstractmethod
    def get_stub_class(self) -> Type[Any]:
        """Return the generated stub class"""
        pass

    def initialize_channel(self):
        """Initialize gRPC channel"""
        self.channel = grpc.insecure_channel(f"{self.host}:{self.port}")

    def initialize_stub(self):
        """Initialize gRPC stub"""
        if not self.channel:
            self.initialize_channel()
        self.stub = self.get_stub_class()(self.channel)

    def start_server(self):
        """Start gRPC server"""
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.get_service_class().add_to_server(self, self.server)
        self.server.add_insecure_port(f"{self.host}:{self.port}")
        self.server.start()

    def stop_server(self):
        """Stop gRPC server"""
        if self.server:
            self.server.stop(0)

    def __enter__(self):
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_server()