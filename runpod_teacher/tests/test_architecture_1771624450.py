import pytest

def save_data(data, file_path):
    """Save data to a file."""
    with open(file_path, 'w') as output_file:
        output_file.write(data)

def test_save_data_happy_path():
    """Test normal inputs"""
    data = "Hello, world!"
    file_path = "/tmp/test_happy_path.txt"
    save_data(data, file_path)
    with open(file_path, 'r') as input_file:
        content = input_file.read()
    assert content == data

def test_save_data_edge_case_empty_string():
    """Test empty string"""
    data = ""
    file_path = "/tmp/test_edge_case_empty.txt"
    save_data(data, file_path)
    with open(file_path, 'r') as input_file:
        content = input_file.read()
    assert content == data

def test_save_data_edge_case_none_input():
    """Test None input"""
    data = None
    file_path = "/tmp/test_edge_case_none.txt"
    save_data(data, file_path)
    with open(file_path, 'r') as input_file:
        content = input_file.read()
    assert content == str(data)

def test_save_data_error_case_invalid_file_path():
    """Test invalid file path"""
    data = "Hello, world!"
    file_path = "/invalid/path/test_error_case.txt"
    try:
        save_data(data, file_path)
        assert False, "Expected an exception to be raised"
    except IOError as e:
        assert str(e) == f"[Errno 2] No such file or directory: '{file_path}'"

def test_save_data_async_behavior():
    """Test async behavior"""
    import asyncio
    
    async def async_test():
        data = "Hello, world!"
        file_path = "/tmp/test_async_behavior.txt"
        await save_data(data, file_path)
        with open(file_path, 'r') as input_file:
            content = input_file.read()
        assert content == data

    asyncio.run(async_test())