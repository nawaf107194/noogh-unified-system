import pytest
from unified_core.dev_agent import DevAgent, CodeLanguage

@pytest.fixture
def dev_agent():
    return DevAgent()

def test_extract_tests_happy_path_python(dev_agent):
    response = """
def test_example1():
    assert 1 + 1 == 2

class MyClass:
    def test_example2(self):
        assert self.value == 42
"""
    language = CodeLanguage.PYTHON
    expected_output = """def test_example1():
    assert 1 + 1 == 2


class MyClass:
    def test_example2(self):
        assert self.value == 42"""
    assert dev_agent._extract_tests(response, language) == expected_output

def test_extract_tests_happy_path_rust(dev_agent):
    response = """
#[test]
fn test_example1() {
    assert_eq!(1 + 1, 2);
}

struct MyClass;

impl MyClass {
    #[test]
    fn test_example2(&self) {
        assert_eq!(self.value, 42);
    }
}
"""
    language = CodeLanguage.RUST
    expected_output = """#[test]
fn test_example1() {
    assert_eq!(1 + 1, 2);

}

struct MyClass;

impl MyClass {
    #[test]
    fn test_example2(&self) {
        assert_eq!(self.value, 42);
    }
}"""
    assert dev_agent._extract_tests(response, language) == expected_output

def test_extract_tests_empty_input(dev_agent):
    response = ""
    language = CodeLanguage.PYTHON
    assert dev_agent._extract_tests(response, language) is None

def test_extract_tests_none_input(dev_agent):
    response = None
    language = CodeLanguage.RUST
    assert dev_agent._extract_tests(response, language) is None

def test_extract_tests_invalid_language(dev_agent):
    response = "Some invalid text"
    language = CodeLanguage.GO
    assert dev_agent._extract_tests(response, language) is None