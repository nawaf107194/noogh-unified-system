# docs/__init__.py
"""
Architecture Documentation Package

This package provides comprehensive documentation and definitions for the system architecture.
It is organized into subpackages for different aspects of the architecture.

Modules:
    architecture: Core architecture definitions
    config: Configuration management documentation
    tests: Test cases for architecture components

Subpackages:
    patterns: Common design patterns used in the architecture
    components: Individual architectural components documentation
"""

# Initialize package structure
__all__ = [
    'architecture',
    'config',
    'tests',
    'patterns',
    'components'
]

# Initialize submodules
from . import architecture
from . import config
from . import tests
from . import patterns
from . import components