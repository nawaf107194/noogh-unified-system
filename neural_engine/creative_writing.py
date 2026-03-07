"""
Creative Writing System for Noug Neural OS
Provides poetry generation, storytelling, and creative content creation
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PoetryStyle(Enum):
    """Poetry styles"""

    CLASSICAL_ARABIC = "classical_arabic"  # قصيدة عمودية
    FREE_VERSE = "free_verse"  # شعر حر
    HAIKU = "haiku"
    SONNET = "sonnet"
    MODERN = "modern"
    RHYMED = "rhymed"  # مقفى


class StoryGenre(Enum):
    """Story genres"""

    FANTASY = "fantasy"
    SCIFI = "scifi"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    ADVENTURE = "adventure"
    HORROR = "horror"
    DRAMA = "drama"


@dataclass
class Poem:
    """Represents a generated poem"""

    title: str
    content: str
    style: PoetryStyle
    language: str
    lines: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
            title = self.title
            content = self.content
            style_value = self.style.value
            language = self.language
            lines = self.lines
            metadata = self.metadata

            return {
                "title": title,
                "content": content,
                "style": style_value,
                "language": language,
                "lines": lines,
                "metadata": metadata,
            }


@dataclass
class Story:
    """Represents a generated story"""

    title: str
    content: str
    genre: StoryGenre
    language: str
    chapters: List[str]
    characters: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "genre": self.genre.value,
            "language": self.language,
            "chapters": self.chapters,
            "characters": self.characters,
            "metadata": self.metadata,
        }


class PoetryGenerator:
    """
    Generates poetry in various styles and languages
    Supports Arabic and English poetry
    """

    def __init__(self, reasoning_engine=None):
        self.reasoning_engine = reasoning_engine
        self.generated_poems: List[Poem] = []

        logger.info("PoetryGenerator initialized")

    async def generate_poem(
        self, theme: str, style: PoetryStyle = PoetryStyle.FREE_VERSE, language: str = "arabic", num_lines: int = 8
    ) -> Poem:
        """
        Generate a poem on given theme

        Args:
            theme: Theme/topic of the poem
            style: Poetry style
            language: Language (arabic/english)
            num_lines: Number of lines

        Returns:
            Generated Poem
        """

        # Build prompt based on style and language
        prompt = self._build_poetry_prompt(theme, style, language, num_lines)

        # Generate using reasoning engine if available
        if self.reasoning_engine:
            result = await self.reasoning_engine.reason(
                context={"intent": "creative_poetry", "language": language}, query=prompt
            )
            content = result.conclusion
        else:
            # Fallback: Generate mock poem
            content = self._generate_mock_poem(theme, style, language, num_lines)

        # Parse into lines
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        # Create title
        title = self._generate_title(theme, language)

        poem = Poem(
            title=title,
            content=content,
            style=style,
            language=language,
            lines=lines,
            metadata={"theme": theme, "num_lines": len(lines), "generated_at": "now"},
        )

        self.generated_poems.append(poem)

        return poem

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

    def _generate_mock_poem(self, theme: str, style: PoetryStyle, language: str, num_lines: int) -> str:
        """Generate a mock poem for testing"""

        if language == "arabic":
            if style == PoetryStyle.CLASSICAL_ARABIC:
                return """في عالم الذكاء نسير *** نحو المستقبل نطير
بالعلم والتقنية نبني *** حضارة للغد تضيء
الآلة تفكر وتعي *** والإنسان يبدع ويحيي
معاً نصنع الأحلام *** في زمن التكنولوجيا"""
            else:
                return f"""عن {theme} أكتب اليوم
في سطور من نور
أحلام تتحقق
وأفكار تنمو
في عالم جديد
مليء بالإبداع
والذكاء الاصطناعي
يرسم المستقبل"""
        else:
            return f"""About {theme} I write today
In lines of light and wonder
Dreams that come to life
Ideas that grow and bloom
In a world so new
Full of creativity
And artificial minds
Painting tomorrow"""

    def _generate_title(self, theme: str, language: str) -> str:
        """Generate poem title"""
        if language == "arabic":
            return f"قصيدة في {theme}"
        else:
            return f"Poem on {theme}"


class StoryTeller:
    """
    Generates stories and narratives
    Supports multiple genres and languages
    """

    def __init__(self, reasoning_engine=None):
        self.reasoning_engine = reasoning_engine
        self.generated_stories: List[Story] = []

        logger.info("StoryTeller initialized")

    async def generate_story(
        self,
        theme: str,
        genre: StoryGenre = StoryGenre.ADVENTURE,
        language: str = "arabic",
        length: str = "short",  # short, medium, long
    ) -> Story:
        """
        Generate a story

        Args:
            theme: Story theme
            genre: Story genre
            language: Language
            length: Story length

        Returns:
            Generated Story
        """

        # Build prompt
        prompt = self._build_story_prompt(theme, genre, language, length)

        # Generate using reasoning engine if available
        if self.reasoning_engine:
            result = await self.reasoning_engine.reason(
                context={"intent": "creative_story", "language": language}, query=prompt
            )
            content = result.conclusion
        else:
            # Fallback: Generate mock story
            content = self._generate_mock_story(theme, genre, language)

        # Parse chapters
        chapters = self._parse_chapters(content)

        # Extract characters
        characters = self._extract_characters(content)

        # Generate title
        title = self._generate_story_title(theme, genre, language)

        story = Story(
            title=title,
            content=content,
            genre=genre,
            language=language,
            chapters=chapters,
            characters=characters,
            metadata={"theme": theme, "length": length, "word_count": len(content.split()), "generated_at": "now"},
        )

        self.generated_stories.append(story)

        return story

    def _build_story_prompt(self, theme: str, genre: StoryGenre, language: str, length: str) -> str:
        """Build prompt for story generation"""

        length_map = {
            "short": "قصيرة" if language == "arabic" else "short",
            "medium": "متوسطة" if language == "arabic" else "medium",
            "long": "طويلة" if language == "arabic" else "long",
        }

        if language == "arabic":
            genre_ar = {
                StoryGenre.FANTASY: "خيالية",
                StoryGenre.SCIFI: "خيال علمي",
                StoryGenre.MYSTERY: "غموض",
                StoryGenre.ADVENTURE: "مغامرة",
                StoryGenre.HORROR: "رعب",
                StoryGenre.DRAMA: "دراما",
            }
            return f"اكتب قصة {genre_ar.get(genre, 'مغامرة')} {length_map[length]} عن {theme}"
        else:
            return f"Write a {length_map[length]} {genre.value} story about {theme}"

    def _generate_mock_story(self, theme: str, genre: StoryGenre, language: str) -> str:
        """Generate a mock story for testing"""

        if language == "arabic":
            return f"""# الفصل الأول: البداية

في عالم حيث يلتقي {theme} مع المستقبل، كانت هناك قصة تستحق أن تُروى.

بطلنا، أحمد، كان شاباً طموحاً يحلم بتغيير العالم. في أحد الأيام، اكتشف سراً عظيماً...

# الفصل الثاني: الاكتشاف

السر كان أعظم مما تخيل. تقنية جديدة قادرة على تحويل الأحلام إلى حقيقة.

# الفصل الثالث: النهاية

وهكذا، تعلم أحمد أن الأحلام الكبيرة تحتاج إلى شجاعة أكبر."""
        else:
            return f"""# Chapter 1: The Beginning

In a world where {theme} meets the future, there was a story worth telling.

Our hero, Alex, was an ambitious young person dreaming of changing the world. One day, they discovered a great secret...

# Chapter 2: The Discovery

The secret was greater than imagined. A new technology capable of turning dreams into reality.

# Chapter 3: The End

And so, Alex learned that big dreams require even bigger courage."""

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

    def _extract_characters(self, content: str) -> List[str]:
        """Extract character names from story"""
        # Simple extraction - look for capitalized names
        # In production, use NER
        characters = []

        # Arabic names
        arabic_names = ["أحمد", "فاطمة", "علي", "سارة", "محمد"]
        for name in arabic_names:
            if name in content:
                characters.append(name)

        # English names
        english_names = ["Alex", "Sarah", "John", "Emma", "David"]
        for name in english_names:
            if name in content:
                characters.append(name)

        return list(set(characters))

    def _generate_story_title(self, theme: str, genre: StoryGenre, language: str) -> str:
        """Generate story title"""
        if language == "arabic":
            return f"قصة {theme}"
        else:
            return f"The Story of {theme}"


class CreativeWritingEngine:
    """
    Unified creative writing engine
    Combines poetry and storytelling capabilities
    """

    def __init__(self, reasoning_engine=None):
        self.poetry_generator = PoetryGenerator(reasoning_engine)
        self.story_teller = StoryTeller(reasoning_engine)

        logger.info("CreativeWritingEngine initialized")

    async def create(
        self, content_type: str, theme: str, language: str = "arabic", **kwargs  # 'poem' or 'story'
    ) -> Dict[str, Any]:
        """
        Create creative content

        Args:
            content_type: Type of content ('poem' or 'story')
            theme: Content theme
            language: Language
            **kwargs: Additional parameters

        Returns:
            Generated content as dict
        """

        if content_type == "poem":
            style = kwargs.get("style", PoetryStyle.FREE_VERSE)
            if isinstance(style, str):
                style = PoetryStyle(style)

            poem = await self.poetry_generator.generate_poem(
                theme=theme, style=style, language=language, num_lines=kwargs.get("num_lines", 8)
            )
            return poem.to_dict()

        elif content_type == "story":
            genre = kwargs.get("genre", StoryGenre.ADVENTURE)
            if isinstance(genre, str):
                genre = StoryGenre(genre)

            story = await self.story_teller.generate_story(
                theme=theme, genre=genre, language=language, length=kwargs.get("length", "short")
            )
            return story.to_dict()

        else:
            raise ValueError(f"Unknown content type: {content_type}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get creative writing statistics"""
        return {
            "total_poems": len(self.poetry_generator.generated_poems),
            "total_stories": len(self.story_teller.generated_stories),
            "languages": ["arabic", "english"],
            "poetry_styles": [s.value for s in PoetryStyle],
            "story_genres": [g.value for g in StoryGenre],
        }
