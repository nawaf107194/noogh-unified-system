import pytest
from pathlib import Path
import tempfile

def test_build_tree_happy_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        # Create some structure
        (root / "file1.txt").touch()
        (root / "subdir" / "file2.txt").mkdir(parents=True).touch()
        (root / ".hidden" / "file3.txt").mkdir(parents=True).touch()

        tree = build_tree(root)
        assert f"{root}/" in tree
        assert f"{root / 'file1.txt'}" in tree
        assert f"{root / 'subdir' / 'file2.txt'}" in tree

def test_build_tree_edge_case_empty_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        tree = build_tree(root)
        assert f"{root}/" == tree.strip()

def test_build_tree_edge_case_none_input():
    tree = build_tree(None)
    assert tree is None

def test_build_tree_boundary_max_depth():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "subdir1" / "subdir2").mkdir(parents=True)
        tree = build_tree(root, max_depth=1)
        assert f"{root}/" in tree
        assert f"{root / 'subdir1'}" in tree
        assert f"{root / 'subdir1' / 'subdir2'}" not in tree

def test_build_tree_boundary_max_entries():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        for i in range(700):
            (root / f"file{i}.txt").touch()
        tree = build_tree(root, max_entries=600)
        assert f"{root}/" in tree
        assert "(tree truncated at 600 entries)" in tree

def test_build_tree_skip_hidden_dirs():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / ".git").mkdir()
        (root / "__pycache__").mkdir()
        (root / "file1.txt").touch()
        tree = build_tree(root)
        assert f"{root}/" in tree
        assert f"{root / 'file1.txt'}" in tree
        assert f"{root / '.git'}" not in tree
        assert f"{root / '__pycache__'}" not in tree

def test_build_tree_no_entries():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        tree = build_tree(root, max_entries=0)
        assert f"{root}/" == tree.strip()

def test_build_tree_invalid_input_non_pathlike():
    with pytest.raises(TypeError):
        build_tree("not a path")