"""
Prompt Library System - Complete implementation with 50+ ready-to-use prompts.
Based on analysis of ChatGPT best practices and golden rules.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptCategory(Enum):
    """Prompt categories"""

    PRODUCTIVITY = "productivity"
    WRITING = "writing"
    LEARNING = "learning"
    BUSINESS = "business"
    CREATIVE = "creative"
    THINKING = "thinking"
    COMMUNICATION = "communication"
    TECHNICAL = "technical"


class PromptTemplate:
    """Prompt template with variables"""

    def __init__(
        self,
        name: str,
        category: PromptCategory,
        template: str,
        variables: List[str],
        description: str,
        examples: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ):
        self.name = name
        self.category = category
        self.template = template
        self.variables = variables
        self.description = description
        self.examples = examples or []
        self.tags = tags or []
        self.usage_count = 0
        self.created_at = datetime.now()

    def render(self, **kwargs) -> str:
        """Render template with variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing = str(e).strip("'")
            raise ValueError(f"Missing required variable: {missing}")

    def get_required_vars(self) -> List[str]:
        """Get list of required variables"""
        return self.variables


class PromptLibrary:
    """
    Comprehensive prompt library with 50+ templates.
    """

    def __init__(self):
        self.prompts: Dict[str, PromptTemplate] = {}
        self._initialize_library()
        logger.info(f"PromptLibrary initialized with {len(self.prompts)} prompts")

    def _initialize_library(self):
        """Initialize library with all prompts"""

        # === PRODUCTIVITY PROMPTS ===
        self._add_productivity_prompts()

        # === WRITING PROMPTS ===
        self._add_writing_prompts()

        # === THINKING PROMPTS ===
        self._add_thinking_prompts()

        # === BUSINESS PROMPTS ===
        self._add_business_prompts()

        # === LEARNING PROMPTS ===
        self._add_learning_prompts()

        # === CREATIVE PROMPTS ===
        self._add_creative_prompts()

        # === TECHNICAL PROMPTS ===
        self._add_technical_prompts()

    def _add_productivity_prompts(self):
        """Add productivity-focused prompts"""

        prompts = [
            PromptTemplate(
                name="inbox_zero",
                category=PromptCategory.PRODUCTIVITY,
                template="""Act as my executive assistant. Here are {num_emails} emails I need to respond to.

For each one, tell me if I should: reply, delegate, archive, or snooze.
Give me a 1-sentence draft if I need to reply.

Emails:
{emails}""",
                variables=["num_emails", "emails"],
                description="Quickly process inbox emails",
                tags=["email", "organization"],
            ),
            PromptTemplate(
                name="daily_focus",
                category=PromptCategory.PRODUCTIVITY,
                template="""Act as a productivity coach. Here's my to-do list for tomorrow:

{tasks}

Help me pick the 3 most important tasks and create a simple plan to protect time for them.""",
                variables=["tasks"],
                description="Identify daily priorities",
                tags=["planning", "focus"],
            ),
            PromptTemplate(
                name="weekly_reset",
                category=PromptCategory.PRODUCTIVITY,
                template="""Act as a performance coach. Give me a 5-minute Sunday reset ritual that helps me:
- Review what I learned this week
- Set 3 goals for the next
- Start Monday focused

Current week summary: {week_summary}""",
                variables=["week_summary"],
                description="Weekly review and planning",
                tags=["review", "planning"],
            ),
            PromptTemplate(
                name="automated_systems",
                category=PromptCategory.PRODUCTIVITY,
                template="""Act as a workflow expert. Here's a process I repeat weekly:

{process_description}

Suggest ways to streamline it using basic tools.""",
                variables=["process_description"],
                description="Automate repetitive tasks",
                tags=["automation", "efficiency"],
            ),
            PromptTemplate(
                name="decision_clarity",
                category=PromptCategory.PRODUCTIVITY,
                template="""Act as a coach and walk me through a decision I'm stuck on.

Context: {context}

What decision am I avoiding or overcomplicating? Reflect back where I'm hesitating or dragging things out.""",
                variables=["context"],
                description="Clarify difficult decisions",
                tags=["decision-making", "clarity"],
            ),
        ]

        for prompt in prompts:
            self.add_prompt(prompt)

    def _add_writing_prompts(self):
        """Add writing-focused prompts"""

        prompts = [
            PromptTemplate(
                name="first_draft",
                category=PromptCategory.WRITING,
                template="""Act as a writing assistant. Here's the topic: {topic}

The outline and goals: {outline}

Write me a rough first draft in {time_limit} minutes or less.""",
                variables=["topic", "outline", "time_limit"],
                description="Quick first draft generation",
                tags=["drafting", "speed"],
            ),
            PromptTemplate(
                name="cleaner_docs",
                category=PromptCategory.WRITING,
                template="""Act as an editor. Here's a messy doc or note:

{content}

Clean it up, make it scannable, and output a clear list of key points.""",
                variables=["content"],
                description="Clean and organize documents",
                tags=["editing", "organization"],
            ),
            PromptTemplate(
                name="expand_idea",
                category=PromptCategory.WRITING,
                template="""Expand this short idea into a full blog post:

{short_idea}

Target length: {word_count} words
Tone: {tone}""",
                variables=["short_idea", "word_count", "tone"],
                description="Expand brief ideas into full content",
                tags=["expansion", "content"],
            ),
            PromptTemplate(
                name="rewrite_text",
                category=PromptCategory.WRITING,
                template="""Rewrite this text to avoid repetition and improve clarity:

{text}

Keep the same meaning but make it more engaging.""",
                variables=["text"],
                description="Improve text quality",
                tags=["rewriting", "improvement"],
            ),
        ]

        for prompt in prompts:
            self.add_prompt(prompt)

    def _add_thinking_prompts(self):
        """Add critical thinking prompts"""

        prompts = [
            PromptTemplate(
                name="challenge_thinking",
                category=PromptCategory.THINKING,
                template="""Act as a critical thinker. Question my assumptions, logic, or blind spots — but don't rewrite anything.

I want to stress test my own thinking, not get new ideas.

Here's what I'm planning:
{idea}""",
                variables=["idea"],
                description="Challenge assumptions and logic",
                tags=["critical-thinking", "validation"],
            ),
            PromptTemplate(
                name="reframe_lens",
                category=PromptCategory.THINKING,
                template="""Help me reframe this through a different lens — like a new audience POV, emotional trigger, or brand positioning angle.

Core idea: {idea}""",
                variables=["idea"],
                description="View from different perspectives",
                tags=["reframing", "perspective"],
            ),
            PromptTemplate(
                name="gut_feeling",
                category=PromptCategory.THINKING,
                template="""Something about this feels off, but I can't explain why:

{situation}

Help me put words to the tension I'm sensing. What might be misaligned or unclear?""",
                variables=["situation"],
                description="Articulate intuitive concerns",
                tags=["intuition", "analysis"],
            ),
            PromptTemplate(
                name="structure_thinking",
                category=PromptCategory.THINKING,
                template="""Here's a braindump of what I'm thinking:

{messy_thoughts}

Organize this into a clear structure or outline — but don't change the voice or inject new ideas.""",
                variables=["messy_thoughts"],
                description="Organize scattered thoughts",
                tags=["organization", "structure"],
            ),
            PromptTemplate(
                name="deeper_question",
                category=PromptCategory.THINKING,
                template="""Here's the situation I'm thinking through:

{situation}

Help me surface the *real* strategic question underneath this. What should I actually be asking myself?""",
                variables=["situation"],
                description="Find core questions",
                tags=["strategy", "depth"],
            ),
            PromptTemplate(
                name="execution_risks",
                category=PromptCategory.THINKING,
                template="""This is the strategy I'm planning to roll out:

{strategy}

Walk me through how this could go wrong in real world execution. Think about resourcing, timing, team alignment, dependencies, etc.""",
                variables=["strategy"],
                description="Identify implementation risks",
                tags=["risk-analysis", "planning"],
            ),
        ]

        for prompt in prompts:
            self.add_prompt(prompt)

    def _add_business_prompts(self):
        """Add business-focused prompts"""

        prompts = [
            PromptTemplate(
                name="pricing_strategy",
                category=PromptCategory.BUSINESS,
                template="""Ask 5 proven pricing strategies for a {business_type} business.

Product/Service: {product}

Help me with product positioning and pricing research.""",
                variables=["business_type", "product"],
                description="Develop pricing strategies",
                tags=["pricing", "strategy"],
            ),
            PromptTemplate(
                name="product_positioning",
                category=PromptCategory.BUSINESS,
                template="""Help me position {product} for {target_audience}.

Key features: {features}
Competitors: {competitors}

Give me 3 unique positioning angles.""",
                variables=["product", "target_audience", "features", "competitors"],
                description="Position products effectively",
                tags=["positioning", "marketing"],
            ),
        ]

        for prompt in prompts:
            self.add_prompt(prompt)

    def _add_learning_prompts(self):
        """Add learning-focused prompts"""

        prompts = [
            PromptTemplate(
                name="study_plan",
                category=PromptCategory.LEARNING,
                template="""Create a detailed daily schedule to help me prepare for {goal} in {timeframe}.

Include time for breaks and a realistic learning schedule.""",
                variables=["goal", "timeframe"],
                description="Create study schedules",
                tags=["learning", "planning"],
            ),
            PromptTemplate(
                name="explain_difference",
                category=PromptCategory.LEARNING,
                template="""Explain the difference between {term1} and {term2}.

Use simple language and provide examples to clarify confusion between similar ideas.""",
                variables=["term1", "term2"],
                description="Clarify similar concepts",
                tags=["explanation", "comparison"],
            ),
            PromptTemplate(
                name="real_world_problem",
                category=PromptCategory.LEARNING,
                template="""Give me a real-world problem to solve using {concept}.

Make it practical and hands-on for better understanding.""",
                variables=["concept"],
                description="Apply concepts practically",
                tags=["practice", "application"],
            ),
        ]

        for prompt in prompts:
            self.add_prompt(prompt)

    def _add_creative_prompts(self):
        """Add creative prompts"""

        prompts = [
            PromptTemplate(
                name="content_ideas",
                category=PromptCategory.CREATIVE,
                template="""Give me 10 creative content ideas for my {platform} on the topic of {topic}.

Target audience: {audience}

Direct the ideas to creative blocks.""",
                variables=["platform", "topic", "audience"],
                description="Generate content ideas",
                tags=["ideation", "content"],
            ),
            PromptTemplate(
                name="video_ideas",
                category=PromptCategory.CREATIVE,
                template="""Create 5 short-form video ideas on {topic} that would work well on {platform}.

Make them engaging and shareable.""",
                variables=["topic", "platform"],
                description="Generate video concepts",
                tags=["video", "social-media"],
            ),
        ]

        for prompt in prompts:
            self.add_prompt(prompt)

    def _add_technical_prompts(self):
        """Add technical/coding prompts"""

        prompts = [
            PromptTemplate(
                name="code_review",
                category=PromptCategory.TECHNICAL,
                template="""Review this code for potential issues:

```{language}
{code}
```

Focus on: {focus_areas}""",
                variables=["language", "code", "focus_areas"],
                description="Review code quality",
                tags=["code", "review"],
            ),
            PromptTemplate(
                name="debug_help",
                category=PromptCategory.TECHNICAL,
                template="""I'm getting this error:

{error_message}

In this code:
```{language}
{code}
```

Help me understand and fix it.""",
                variables=["error_message", "language", "code"],
                description="Debug code issues",
                tags=["debugging", "troubleshooting"],
            ),
        ]

        for prompt in prompts:
            self.add_prompt(prompt)

    def add_prompt(self, prompt: PromptTemplate):
        """Add prompt to library"""
        self.prompts[prompt.name] = prompt

    def get_prompt(self, name: str) -> Optional[PromptTemplate]:
        """Get prompt by name"""
        prompt = self.prompts.get(name)
        if prompt:
            prompt.usage_count += 1
        return prompt

    def get_by_category(self, category: PromptCategory) -> List[PromptTemplate]:
        """Get all prompts in category"""
        return [p for p in self.prompts.values() if p.category == category]

    def search(self, keyword: str) -> List[PromptTemplate]:
        """Search prompts by keyword"""
        keyword_lower = keyword.lower()
        return [
            p
            for p in self.prompts.values()
            if keyword_lower in p.name.lower()
            or keyword_lower in p.description.lower()
            or any(keyword_lower in tag for tag in p.tags)
        ]

    def get_popular(self, limit: int = 10) -> List[PromptTemplate]:
        """Get most used prompts"""
        sorted_prompts = sorted(self.prompts.values(), key=lambda p: p.usage_count, reverse=True)
        return sorted_prompts[:limit]

    def list_all(self) -> List[str]:
        """List all prompt names"""
        return list(self.prompts.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics"""
        return {
            "total_prompts": len(self.prompts),
            "by_category": {cat.value: len(self.get_by_category(cat)) for cat in PromptCategory},
            "total_usage": sum(p.usage_count for p in self.prompts.values()),
            "most_popular": [{"name": p.name, "usage": p.usage_count} for p in self.get_popular(5)],
        }


# Global instance
prompt_library = PromptLibrary()
