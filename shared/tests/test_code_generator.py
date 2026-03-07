import pytest
import os
from shared.code_generator import CodeGenerator

@pytest.fixture
def code_generator(tmp_path):
    return CodeGenerator(output_directory=tmp_path)

def test_write_to_file_happy_path(code_generator, tmp_path):
    file_name = "test.txt"
    content = "Hello, World!"
    code_generator._write_to_file(file_name, content)
    full_path = os.path.join(tmp_path, file_name)
    with open(full_path, 'r') as file:
        assert file.read() == content

def test_write_to_file_empty_content(code_generator, tmp_path):
    file_name = "test.txt"
    content = ""
    code_generator._write_to_file(file_name, content)
    full_path = os.path.join(tmp_path, file_name)
    with open(full_path, 'r') as file:
        assert file.read() == content

def test_write_to_file_none_content(code_generator, tmp_path):
    file_name = "test.txt"
    content = None
    result = code_generator._write_to_file(file_name, content)
    assert result is None
    full_path = os.path.join(tmp_path, file_name)
    assert not os.path.exists(full_path)

def test_write_to_file_invalid_filename(code_generator, tmp_path):
    file_name = None
    content = "Hello, World!"
    result = code_generator._write_to_file(file_name, content)
    assert result is None
    full_path = os.path.join(tmp_path, file_name) if file_name else None
    assert not os.path.exists(full_path)

def test_write_to_file_invalid_directory(code_generator):
    class MockCodeGenerator(CodeGenerator):
        def __init__(self, output_directory=None):
            super().__init__(output_directory=output_directory)
    
    code_generator = MockCodeGenerator(output_directory="/nonexistent/directory")
    file_name = "test.txt"
    content = "Hello, World!"
    result = code_generator._write_to_file(file_name, content)
    assert result is None
    full_path = os.path.join("/nonexistent/directory", file_name)
    assert not os.path.exists(full_path)