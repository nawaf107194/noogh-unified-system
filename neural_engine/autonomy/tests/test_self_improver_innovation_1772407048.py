import pytest

from neural_engine.autonomy.self_improver import _get_improvement_guidance, FileCategory

class TestGetImprovementGuidance:

    @pytest.mark.parametrize("category, expected", [
        (FileCategory.AUTHORITY, """
🟢 **ملف Authority - محمي**
- ✅ يمكن تحليله وفهمه
- ✅ يمكن تشخيص مشاكله
- ❌ لا يمكن اقتراح تعديلات تلقائية
- 💡 للتعديل: اطلب من المستخدم بشكل صريح مع diff
"""),
        (FileCategory.SENSITIVE, """
🟣 **ملف Sensitive - مغلق**
- ⚠️ تحليل محدود فقط
- ❌ لا يمكن اقتراح تعديلات
- 🔒 أي تغيير يحتاج مراجعة أمنية
"""),
        (FileCategory.PATTERN, """
🔵 **ملف Pattern - قابل للتحسين**
- ✅ يمكن تحليله بالكامل
- ✅ يمكن اقتراح تحسينات
- ⚠️ التنفيذ يحتاج موافقة
"""),
        (FileCategory.HISTORICAL, """
🔴 **ملف Historical - بحذر**
- ✅ يمكن تحليله
- ⚠️ اقتراحات تحتاج تبرير قوي
- 💡 غالباً الأفضل تركه كمرجع تاريخي
"""),
        (FileCategory.GENERATED, """
⬜ **ملف Generated - حر**
- ✅ يمكن تحليله وتعديله
- ✅ يمكن اقتراح تحسينات
- ✅ التنفيذ أسهل (لكن لا يزال يحتاج موافقة)
""")
    ])
    def test_happy_path(self, category, expected):
        result = _get_improvement_guidance(category)
        assert result == expected

    def test_edge_case_none_category(self):
        result = _get_improvement_guidance(None)
        assert result == "❓ صنف غير معروف"

    @pytest.mark.parametrize("category, expected", [
        (None, "❓ صنف غير معروف"),
        ("invalid_category", "❓ صنف غير معروف")
    ])
    def test_error_cases(self, category, expected):
        result = _get_improvement_guidance(category)
        assert result == expected