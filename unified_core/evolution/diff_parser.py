"""
Diff Parser — Extract metadata from evolution proposal diffs.

Extracted from EvolutionController v1.3 for modularity.
Enhanced with support for multiple diff formats.
"""
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("unified_core.evolution.diff_parser")


def extract_metadata_from_diff(diff: str) -> Optional[Dict[str, Any]]:
    """Extract original_code and refactored_code from a proposal diff.

    Supports two formats:

    1. NOOGH format:
        # Refactoring: <function_name>
        # Confidence: <N>%
        --- ORIGINAL ---
        <original code>
        +++ REFACTORED +++
        <refactored code>

    2. Unified diff format:
        --- a/path/to/file
        +++ b/path/to/file
        @@ -N,M +N,M @@
        <context and changes>
    """
    if not diff:
        return None

    # Try NOOGH format first
    result = _parse_noogh_format(diff)
    if result:
        return result

    # Try unified diff format
    result = _parse_unified_diff(diff)
    if result:
        return result

    return None


def _parse_noogh_format(diff: str) -> Optional[Dict[str, Any]]:
    """Parse NOOGH-style diff with ORIGINAL/REFACTORED markers."""
    orig_marker = "--- ORIGINAL ---"
    refac_marker = "+++ REFACTORED +++"

    if orig_marker not in diff or refac_marker not in diff:
        return None

    try:
        # Extract original code (between ORIGINAL and REFACTORED markers)
        after_orig = diff.split(orig_marker, 1)[1]
        original_code = after_orig.split(refac_marker, 1)[0].strip()

        # Extract refactored code (after REFACTORED marker)
        refactored_code = diff.split(refac_marker, 1)[1].strip()

        if not original_code or not refactored_code:
            return None

        # Extract function name from header
        function = "unknown"
        for line in diff.split('\n')[:5]:
            if line.startswith("# Refactoring:"):
                function = line.split(":", 1)[1].strip()
                break

        # Extract confidence from header
        confidence = 0.8
        for line in diff.split('\n')[:5]:
            if line.startswith("# Confidence:"):
                try:
                    confidence = float(line.split(":")[1].strip().rstrip('%')) / 100
                except (ValueError, IndexError):
                    pass
                break

        return {
            "original_code": original_code,
            "refactored_code": refactored_code,
            "function": function,
            "confidence": confidence,
        }
    except Exception as e:
        logger.debug(f"Failed to parse NOOGH diff: {e}")
        return None


def _parse_unified_diff(diff: str) -> Optional[Dict[str, Any]]:
    """Parse standard unified diff format.

    Extracts removed lines (original) and added lines (refactored).
    """
    lines = diff.split('\n')

    # Must have --- and +++ headers
    has_headers = any(l.startswith('--- ') for l in lines) and any(l.startswith('+++ ') for l in lines)
    if not has_headers:
        return None

    try:
        original_lines = []
        refactored_lines = []
        in_hunk = False

        for line in lines:
            if line.startswith('@@'):
                in_hunk = True
                continue
            if not in_hunk:
                continue

            if line.startswith('-') and not line.startswith('---'):
                original_lines.append(line[1:])  # Remove leading -
            elif line.startswith('+') and not line.startswith('+++'):
                refactored_lines.append(line[1:])  # Remove leading +
            elif line.startswith(' '):
                # Context line — part of both
                original_lines.append(line[1:])
                refactored_lines.append(line[1:])

        if not original_lines and not refactored_lines:
            return None

        # Try to detect function name from the hunk header or content
        function = "unknown"
        for line in lines:
            match = re.search(r'@@.*@@\s+(def |async def )(\w+)', line)
            if match:
                function = match.group(2)
                break

        return {
            "original_code": '\n'.join(original_lines),
            "refactored_code": '\n'.join(refactored_lines),
            "function": function,
            "confidence": 0.7,  # Lower confidence for unified diffs
        }
    except Exception as e:
        logger.debug(f"Failed to parse unified diff: {e}")
        return None
