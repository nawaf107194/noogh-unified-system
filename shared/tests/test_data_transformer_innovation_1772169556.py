import pytest
import pandas as pd

def load_data(file_path):
    """Loads data from a CSV file into a DataFrame."""
    return pd.read_csv(file_path)

@pytest.mark.parametrize("file_path, expected", [
    ("data/test.csv", pd.DataFrame),  # Happy path: normal input
    (None, None),                     # Edge case: None input
    ("", None),                       # Edge case: empty string input
    ("nonexistent_file.csv", None),   # Error case: invalid file_path
])
def test_load_data(file_path, expected):
    result = load_data(file_path)
    
    if expected is None:
        assert result is None
    elif expected == pd.DataFrame:
        assert isinstance(result, pd.DataFrame) and not result.empty
    else:
        raise ValueError("Unexpected expected value")

# Test async behavior (if applicable)
# Note: Since the function does not support async behavior, this test will be skipped.
# @pytest.mark.asyncio
# async def test_load_data_async():
#     # Implement if necessary
#     pass