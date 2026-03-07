import pytest
from pathlib import Path
import os
from unified_core.evolution.architecture_model import ArchitectureModel, ComponentNode, DependencyEdge, ClassInfo

def test_happy_path():
    model = ArchitectureModel("test_root")
    assert isinstance(model.src_root, Path)
    assert model.src_root == Path("test_root")
    assert model.nodes == {}
    assert model.edges == []
    assert model.classes == {}

def test_default_src_root():
    model = ArchitectureModel()
    expected_path = str(Path(__file__).resolve().parents[2])
    assert isinstance(model.src_root, Path)
    assert model.src_root == Path(expected_path)
    assert model.nodes == {}
    assert model.edges == []
    assert model.classes == {}

def test_empty_src_root():
    with pytest.raises(ValueError):
        ArchitectureModel("")

def test_none_src_root():
    with pytest.raises(ValueError):
        ArchitectureModel(None)

def test_boundary_cases():
    model = ArchitectureModel(src_root="/")
    assert isinstance(model.src_root, Path)
    assert model.src_root == Path("/")
    assert model.nodes == {}
    assert model.edges == []
    assert model.classes == {}

def test_invalid_src_root_type():
    with pytest.raises(TypeError):
        ArchitectureModel(123)