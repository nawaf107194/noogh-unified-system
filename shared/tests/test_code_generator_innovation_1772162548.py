import pytest
import os

from shared.code_generator import CodeGenerator

def test_happy_path():
    generator = CodeGenerator(output_directory='/tmp/test_output')
    assert generator.output_directory == '/tmp/test_output'
    assert os.path.exists(generator.output_directory)

def test_edge_case_empty_string():
    generator = CodeGenerator(output_directory='')
    assert generator.output_directory == '.'
    assert os.path.exists(generator.output_directory)

def test_edge_case_none():
    generator = CodeGenerator(output_directory=None)
    assert generator.output_directory == '.'
    assert os.path.exists(generator.output_directory)

def test_error_case_invalid_path():
    with pytest.raises(FileNotFoundError):
        generator = CodeGenerator(output_directory='/nonexistent/path')