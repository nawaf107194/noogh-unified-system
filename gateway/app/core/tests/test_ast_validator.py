import pytest

from gateway.app.core.ast_validator import ASTVisitor, DANGEROUS_IMPORTS

@pytest.fixture
def ast_visitor():
    return ASTVisitor()

def test_visit_Import_happy_path(ast_visitor):
    class MockNode:
        names = [ast.ImportAlias(name="os.path")]

    ast_visitor.visit(MockNode())
    assert not ast_visitor.errors
    assert ast_visitor.safe

def test_visit_Import_dangerous_import(ast_visitor):
    DANGEROUS_IMPORTS.add("os")
    class MockNode:
        names = [ast.ImportAlias(name="os")]

    ast_visitor.visit(MockNode())
    assert "Forbidden import: os" in ast_visitor.errors
    assert not ast_visitor.safe

def test_visit_Import_empty_names(ast_visitor):
    class MockNode:
        names = []

    ast_visitor.visit(MockNode())
    assert not ast_visitor.errors
    assert ast_visitor.safe

def test_visit_Import_none_names(ast_visitor):
    class MockNode:
        names = None

    ast_visitor.visit(MockNode())
    assert not ast_visitor.errors
    assert ast_visitor.safe