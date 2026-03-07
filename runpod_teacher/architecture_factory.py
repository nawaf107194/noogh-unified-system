# runpod_teacher/architecture_factory.py

class ArchitectureFactory:
    def __init__(self):
        self._architectures = {}

    def register_architecture(self, key, architecture_class):
        if key in self._architectures:
            raise ValueError(f"Architecture with key '{key}' already registered.")
        self._architectures[key] = architecture_class

    def create_architecture(self, key, *args, **kwargs):
        if key not in self._architectures:
            raise ValueError(f"No architecture found with key '{key}'.")
        return self._architectures[key](*args, **kwargs)

# Usage example in runpod_teacher/architecture_1772079125.py
from runpod_teacher.architecture_factory import ArchitectureFactory

factory = ArchitectureFactory()
factory.register_architecture('architecture_1772079125', Architecture_1772079125)

# Create an instance of the architecture
architecture = factory.create_architecture('architecture_1772079125')