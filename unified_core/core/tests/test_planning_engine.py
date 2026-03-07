import pytest
from typing import List
from unittest.mock import Mock

class PlanningEngine:
    def _format_deliberation_prompt(self, briefs: List[str]) -> str:
        briefs_text = "\n".join([f"- {b}" for b in briefs])
        return f"""<identity>
أنت العقل الاستراتيجي لنظام NOOGH — تحلل رؤى المتخصصين وتحدد المسار الأمثل.
</identity>

<context>
Specialist Advisor Insights:
{briefs_text}
</context>

<methodology>
1. حلل كل رؤية متخصص بشكل مستقل
2. حدد التقاطعات والتناقضات بين الرؤى
3. رتب المسارات حسب: الأثر الأمني > الاستقرار > التطوير الذاتي
4. اختر المسار الذي يحقق أعلى عائد بأقل مخاطرة
</methodology>

<rules>
- لا تقترح مساراً لا يستند إلى بيانات من المتخصصين
- لا تختلق مقاييس أو أرقام — استند فقط إلى ما هو متاح
- إذا كانت البيانات غير كافية، اضبط الثقة تحت 0.5
- أخرج JSON فقط — بدون شرح أو نص إضافي
</rules>

<output_format>
{{ "path": "المجال التقني المحدد", "rationale": "لماذا هذا المسار", "eye": "المقياس الرئيسي للنجاح", "confidence": 0.0-1.0 }}
</output_format>

<reminder>
⚠️ JSON فقط. لا نص قبله أو بعده. الثقة يجب أن تعكس جودة البيانات المتاحة فعلاً.
</reminder>"""

@pytest.fixture
def planning_engine():
    return PlanningEngine()

def test_happy_path(planning_engine):
    briefs = ["Insight 1", "Insight 2", "Insight 3"]
    prompt = planning_engine._format_deliberation_prompt(briefs)
    assert "<context>\nSpecialist Advisor Insights:\n- Insight 1\n- Insight 2\n- Insight 3" in prompt

def test_empty_input(planning_engine):
    briefs = []
    prompt = planning_engine._format_deliberation_prompt(briefs)
    assert "<context>\nSpecialist Advisor Insights:" in prompt

def test_none_input(planning_engine):
    with pytest.raises(TypeError):
        planning_engine._format_deliberation_prompt(None)

def test_invalid_input_type(planning_engine):
    with pytest.raises(TypeError):
        planning_engine._format_deliberation_prompt("not a list")

def test_single_brief(planning_engine):
    briefs = ["Single Insight"]
    prompt = planning_engine._format_deliberation_prompt(briefs)
    assert "<context>\nSpecialist Advisor Insights:\n- Single Insight" in prompt

def test_large_number_of_briefs(planning_engine):
    briefs = [f"Insight {i}" for i in range(100)]
    prompt = planning_engine._format_deliberation_prompt(briefs)
    assert "<context>\nSpecialist Advisor Insights:" in prompt
    assert len(prompt.split("\n")) == 107  # 100 insights + 7 other lines

# No async behavior to test in this function