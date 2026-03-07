# Example usage
from runpod_teacher.architecture_initializer import ArchitectureInitializer
from runpod_teacher.architecture_base import ArchitectureBase

initializer = ArchitectureInitializer(ArchitectureBase)
architecture = initializer.configure(extra_param="value")