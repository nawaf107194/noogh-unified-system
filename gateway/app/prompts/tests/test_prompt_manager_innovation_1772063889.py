import pytest

class PromptTemplate:
    def __init__(self, template, variables):
        self.template = template
        self.variables = variables

def render(self, **kwargs) -> str:
    """Render template with provided variables."""
    rendered = self.template
    placeholder_format = "{{{}}}"
    missing_value_format = "{{MISSING:{}}}"

    for var in self.variables:
        value = kwargs.get(var, missing_value_format.format(var))
        rendered = rendered.replace(placeholder_format.format(var), str(value))
    return rendered

class TestPromptTemplateRender:

    @pytest.mark.parametrize("template, variables, kwargs, expected", [
        ("Hello, {{name}}!", ["name"], {"name": "Alice"}, "Hello, Alice!"),
        ("Default value: {{{default}}}", ["default"], {}, "Default value: MISSING:default"),
        ("Multiple {{vars}} here", ["var1", "var2"], {"var1": "A", "var2": "B"}, "Multiple A here"),
    ])
    def test_happy_path(self, template, variables, kwargs, expected):
        prompt = PromptTemplate(template, variables)
        assert render(prompt, **kwargs) == expected

    @pytest.mark.parametrize("template, variables, kwargs", [
        ("Hello, {{name}}!", ["name"], {}),
        ("Default value: {{{default}}}", ["default"], {"default": None}),
        ("Multiple {{vars}} here", ["var1", "var2"], {}),
    ])
    def test_edge_cases(self, template, variables, kwargs):
        prompt = PromptTemplate(template, variables)
        assert render(prompt, **kwargs) == f"Default value: {template[template.find('MISSING:') + 8 : -1]}"

    @pytest.mark.parametrize("template, variables, kwargs", [
        ("{{invalid}}", ["invalid"], {}),
        ("Missing {{variable}}", ["variable"], {"variable": ""}),
    ])
    def test_error_cases(self, template, variables, kwargs):
        prompt = PromptTemplate(template, variables)
        result = render(prompt, **kwargs)
        assert isinstance(result, str) and "MISSING:" in result

# Uncomment the following line to run tests
# pytest /path/to/test_prompt_manager.py::TestPromptTemplateRender