"""Tests for diff_parser module — NOOGH and unified diff parsing."""
import pytest
from unified_core.evolution.diff_parser import (
    extract_metadata_from_diff,
    _parse_noogh_format,
    _parse_unified_diff,
)


class TestNooghFormat:
    """Tests for NOOGH-style diff parsing."""

    SAMPLE_DIFF = (
        "# Refactoring: compute_score\n"
        "# Confidence: 85%\n"
        "--- ORIGINAL ---\n"
        "def compute_score(x):\n"
        "    return x * 2\n"
        "+++ REFACTORED +++\n"
        "def compute_score(x):\n"
        "    return x * 3\n"
    )

    def test_parses_noogh_format(self):
        result = extract_metadata_from_diff(self.SAMPLE_DIFF)
        assert result is not None
        assert "compute_score" in result["function"]
        assert result["confidence"] == 0.85
        assert "x * 2" in result["original_code"]
        assert "x * 3" in result["refactored_code"]

    def test_missing_markers_returns_none(self):
        assert _parse_noogh_format("just some text") is None

    def test_empty_original_returns_none(self):
        diff = "--- ORIGINAL ---\n+++ REFACTORED +++\ndef foo(): pass"
        assert _parse_noogh_format(diff) is None

    def test_no_function_header_defaults(self):
        diff = (
            "--- ORIGINAL ---\n"
            "old code\n"
            "+++ REFACTORED +++\n"
            "new code\n"
        )
        result = _parse_noogh_format(diff)
        assert result is not None
        assert result["function"] == "unknown"

    def test_no_confidence_header_defaults(self):
        diff = (
            "--- ORIGINAL ---\n"
            "old code\n"
            "+++ REFACTORED +++\n"
            "new code\n"
        )
        result = _parse_noogh_format(diff)
        assert result["confidence"] == 0.8


class TestUnifiedDiff:
    """Tests for standard unified diff parsing."""

    SAMPLE_UNIFIED = (
        "--- a/utils.py\n"
        "+++ b/utils.py\n"
        "@@ -10,3 +10,3 @@ def compute(x):\n"
        " def compute(x):\n"
        "-    return x * 2\n"
        "+    return x * 3\n"
    )

    def test_parses_unified_diff(self):
        result = _parse_unified_diff(self.SAMPLE_UNIFIED)
        assert result is not None
        assert "x * 2" in result["original_code"]
        assert "x * 3" in result["refactored_code"]

    def test_extracts_function_name_from_hunk_header(self):
        result = _parse_unified_diff(self.SAMPLE_UNIFIED)
        assert result is not None
        assert result["function"] == "compute"

    def test_no_headers_returns_none(self):
        assert _parse_unified_diff("just some text\nwith lines") is None

    def test_context_lines_in_both(self):
        diff = (
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "@@ -1,4 +1,4 @@\n"
            " import os\n"
            "-old_line\n"
            "+new_line\n"
            " more_context\n"
        )
        result = _parse_unified_diff(diff)
        assert result is not None
        assert "import os" in result["original_code"]
        assert "import os" in result["refactored_code"]
        assert "old_line" in result["original_code"]
        assert "new_line" in result["refactored_code"]

    def test_unified_lower_confidence(self):
        result = _parse_unified_diff(self.SAMPLE_UNIFIED)
        assert result is not None
        assert result["confidence"] == 0.7


class TestExtractMetadataFromDiff:
    """Tests for the top-level extraction function."""

    def test_none_input_returns_none(self):
        assert extract_metadata_from_diff(None) is None

    def test_empty_string_returns_none(self):
        assert extract_metadata_from_diff("") is None

    def test_noogh_format_preferred(self):
        """When both formats could match, NOOGH is tried first."""
        diff = (
            "--- ORIGINAL ---\n"
            "old\n"
            "+++ REFACTORED +++\n"
            "new\n"
        )
        result = extract_metadata_from_diff(diff)
        assert result is not None
        assert result["confidence"] == 0.8  # NOOGH default, not unified's 0.7

    def test_falls_back_to_unified(self):
        diff = (
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "@@ -1,2 +1,2 @@\n"
            "-old\n"
            "+new\n"
        )
        result = extract_metadata_from_diff(diff)
        assert result is not None
        assert result["confidence"] == 0.7

    def test_unparseable_returns_none(self):
        assert extract_metadata_from_diff("random garbage text") is None
