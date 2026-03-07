import pytest
from unittest.mock import MagicMock

from unified_core.multimodal import Multimodal, GenerationType

@pytest.fixture
def multimodal_instance():
    instance = Multimodal()
    instance.generators = {
        'text': MagicMock(_initialized=True),
        'image': MagicMock(_initialized=False),
        'audio': MagicMock(_initialized=None),
    }
    return instance

def test_get_available_modalities_happy_path(multimodal_instance):
    available_mods = multimodal_instance.get_available_modalities()
    assert len(available_mods) == 1
    assert 'text' in available_mods

def test_get_available_modalities_empty_generators():
    instance = Multimodal()
    instance.generators = {}
    available_mods = instance.get_available_modalities()
    assert not available_mods

def test_get_available_modalities_all_uninitialized(multimodal_instance):
    for gen in multimodal_instance.generators.values():
        gen._initialized = False
    available_mods = multimodal_instance.get_available_modalities()
    assert not available_mods

def test_get_available_modalities_mixed_initialization(multimodal_instance):
    multimodal_instance.generators['audio']._initialized = True
    available_mods = multimodal_instance.get_available_modalities()
    assert len(available_mods) == 2
    assert 'text' in available_mods
    assert 'audio' in available_mods

def test_get_available_modalities_none_initialized(multimodal_instance):
    for gen in multimodal_instance.generators.values():
        gen._initialized = None
    available_mods = multimodal_instance.get_available_modalities()
    assert not available_mods