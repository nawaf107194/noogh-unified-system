# docs/architecture.py

from .architecture_1771676467 import Architecture as Architecture_1771676467
from .architecture_1771280944 import Architecture as Architecture_1771280944

class Architecture:
    def __init__(self):
        self.architectures = {
            '1771676467': Architecture_1771676467(),
            '1771280944': Architecture_1771280944()
        }

    def get_architecture(self, version):
        return self.architectures.get(version)