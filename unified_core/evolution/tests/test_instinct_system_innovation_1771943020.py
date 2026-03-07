import pytest
from pathlib import Path
from unified_core.evolution.instinct_system import INSTINCTS_FILE, _NOOGH_DIR

class TestInstinctSystemInit:

    def test_happy_path(self):
        system = InstinctSystem()
        assert Path(system._path).exists()

    def test_edge_case_empty_path(self):
        with pytest.raises(ValueError) as exc_info:
            system = InstinctSystem(_NOOGH_DIR=None, INSTINCTS_FILE='')
        assert str(exc_info.value) == "Invalid path: None"

    def test_error_case_invalid_path(self):
        with pytest.raises(ValueError) as exc_info:
            system = InstinctSystem(_NOOGH_DIR='invalid/path', INSTINCTS_FILE=INSTINCTS_FILE)
        assert str(exc_info.value) == "Invalid path: invalid/path"