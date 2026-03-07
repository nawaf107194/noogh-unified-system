import pytest

class PoetryStyle:
    CLASSICAL_ARABIC = "Classical Arabic"
    FREE_VERSE = "Free Verse"
    RHYMED = "Rhymed"

class CreativeWritingEngine:
    def _build_poetry_prompt(self, theme: str, style: PoetryStyle, language: str, num_lines: int) -> str:
        """Build prompt for poetry generation"""
        
        if language == "arabic":
            if style == PoetryStyle.CLASSICAL_ARABIC:
                return f"اكتب قصيدة عمودية عن {theme} من {num_lines} بيت شعري"
            elif style == PoetryStyle.FREE_VERSE:
                return f"اكتب قصيدة شعر حر عن {theme} من {num_lines} سطر"
            elif style == PoetryStyle.RHYMED:
                return f"اكتب قصيدة مقفاة عن {theme} من {num_lines} سطر"
            else:
                return f"اكتب قصيدة عن {theme} من {num_lines} سطر"
        else:
            return f"Write a {style.value} poem about {theme} with {num_lines} lines"

# Test case for happy path
def test_happy_path():
    engine = CreativeWritingEngine()
    prompt = engine._build_poetry_prompt("love", PoetryStyle.CLASSICAL_ARABIC, "arabic", 5)
    assert prompt == "اكتب قصيدة عمودية عن love من 5 بيت شعري"

# Test case for edge cases
def test_edge_cases():
    engine = CreativeWritingEngine()
    prompt = engine._build_poetry_prompt("", PoetryStyle.FREE_VERSE, "english", 10)
    assert prompt == "Write a Free Verse poem about  with 10 lines"
    
    prompt = engine._build_poetry_prompt("love", None, "arabic", 5)
    assert prompt == "اكتب قصيدة عن love من 5 سطر"

# Test case for error cases
def test_error_cases():
    engine = CreativeWritingEngine()
    with pytest.raises(NotImplementedError):
        engine._build_poetry_prompt("love", PoetryStyle.MODERN, "arabic", 5)

# Test case for async behavior (not applicable)