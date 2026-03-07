import pytest
import os

from shared.code_generator import CodeGenerator

def test_init_happy_path():
    cg = CodeGenerator(output_directory='test_dir')
    assert cg.output_directory == 'test_dir'
    assert os.path.exists('test_dir')

def test_init_edge_case_empty_output_directory():
    cg = CodeGenerator(output_directory='')
    assert cg.output_directory == '.'
    assert os.path.exists('.')

def test_init_edge_case_none_output_directory():
    cg = CodeGenerator(output_directory=None)
    assert cg.output_directory == '.'
    assert os.path.exists('.')

def test_init_error_case_invalid_output_directory_type():
    with pytest.raises(TypeError):
        cg = CodeGenerator(output_directory=123)

def test_init_error_case_nonexistent_parent_directory():
    parent_dir = 'non_existent_parent_dir/sub_dir'
    try:
        os.makedirs(parent_dir)
    except FileExistsError:
        pass

    with pytest.raises(FileNotFoundError):
        cg = CodeGenerator(output_directory='sub_dir')

    # Clean up
    os.rmdir('non_existent_parent_dir')