import pytest
from unified_core.evolution.code_validator import get_class_methods
import ast

def create_ast_with_class(class_name, method_names):
    class_def = ast.ClassDef(name=class_name)
    for method_name in method_names:
        method = ast.FunctionDef(name=method_name, body=[])
        class_def.body.append(method)
    return ast.Module(body=[class_def])

def test_get_class_methods_happy_path():
    class_ast = create_ast_with_class('MyClass', ['method1', 'method2'])
    expected_result = {'MyClass': {'method1', 'method2'}}
    assert get_class_methods(class_ast) == expected_result

def test_get_class_methods_empty_class():
    empty_class_ast = create_ast_with_class('EmptyClass', [])
    expected_result = {'EmptyClass': set()}
    assert get_class_methods(empty_class_ast) == expected_result

def test_get_class_methods_no_classes():
    module_ast = ast.Module(body=[])
    expected_result = {}
    assert get_class_methods(module_ast) == expected_result

def test_get_class_methods_async_method():
    async_method_ast = create_ast_with_class('AsyncClass', ['async_method'])
    expected_result = {'AsyncClass': {'async_method'}}
    assert get_class_methods(async_method_ast) == expected_result

def test_get_class_methods_mixed_methods():
    mixed_methods_ast = create_ast_with_class('MixedClass', ['method1', 'async_method2'])
    expected_result = {'MixedClass': {'method1', 'async_method2'}}
    assert get_class_methods(mixed_methods_ast) == expected_result