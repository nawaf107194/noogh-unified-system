import pytest

class MockCreativeWriting:
    def _parse_chapters(self, content: str) -> List[str]:
        """Parse story into chapters"""
        chapters = []
        current_chapter = []

        for line in content.split("\n"):
            if line.startswith("#"):
                if current_chapter:
                    chapters.append("\n".join(current_chapter))
                current_chapter = [line]
            else:
                current_chapter.append(line)

        if current_chapter:
            chapters.append("\n".join(current_chapter))

        return chapters if chapters else [content]

@pytest.fixture
def creative_writing():
    return MockCreativeWriting()

def test_parse_chapters_happy_path(creative_writing):
    content = "# Chapter 1\nOnce upon a time\n\n# Chapter 2\nIn a galaxy far, far away"
    expected = ["Chapter 1\nOnce upon a time", "Chapter 2\nIn a galaxy far, far away"]
    assert creative_writing._parse_chapters(content) == expected

def test_parse_chapters_empty_content(creative_writing):
    content = ""
    expected = [""]
    assert creative_writing._parse_chapters(content) == expected

def test_parse_chapters_none_content(creative_writing):
    content = None
    expected = [None]
    assert creative_writing._parse_chapters(content) == expected

def test_parse_chapters_no_headers(creative_writing):
    content = "Once upon a time\nIn a galaxy far, far away"
    expected = ["Once upon a time\nIn a galaxy far, far away"]
    assert creative_writing._parse_chapters(content) == expected

def test_parse_chapters_single_header(creative_writing):
    content = "# Chapter 1\nOnce upon a time"
    expected = ["Chapter 1\nOnce upon a time"]
    assert creative_writing._parse_chapters(content) == expected