"""
Preamble Manager - نظام المقدمات التفسيرية

مستوحى من Codex CLI preamble pattern.
يوفر شرح للإجراءات قبل تنفيذها.
"""

from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class PreambleManager:
    """
    مدير المقدمات التفسيرية
    
    يوفر شرح واضح للإجراءات قبل تنفيذها:
    "سأقوم الآن بـ..."
    
    مستوحى من Codex CLI.
    """
    
    TOOL_DESCRIPTIONS_AR = {
        # System tools
        "get_system_status": "الحصول على حالة النظام",
        "get_time": "الحصول على الوقت الحالي",
        "list_directory": "عرض محتويات المجلد",
        "read_file": "قراءة الملف",
        
        # Media tools
        "generate_image": "توليد صورة",
        "generate_audio": "توليد صوت",
        "generate_video": "توليد فيديو",
        
        # Execution tools
        "execute_command": "تنفيذ أمر",
        "write_file": "كتابة ملف",
        "edit_file": "تعديل ملف",
        
        # Memory tools
        "search_memory": "البحث في الذاكرة",
        "update_memory": "تحديث الذاكرة",
        
        # Agent tools
        "check_agent_status": "فحص حالة الوكلاء",
        "spawn_agent": "إنشاء وكيل جديد",
        "think_together": "التفكير الجماعي"
    }
    
    @staticmethod
    def create_preamble(tool_name: str, params: Optional[dict] = None) -> str:
        """
        إنشاء مقدمة لأداة
        
        Args:
            tool_name: اسم الأداة
            params: المعاملات (اختياري)
            
        Returns:
            نص المقدمة بالعربية
        """
        description = PreambleManager.TOOL_DESCRIPTIONS_AR.get(
            tool_name,
            f"استخدام الأداة {tool_name}"
        )
        
        preamble = f"🔧 سأقوم الآن بـ{description}"
        
        # إضافة تفاصيل المعاملات إذا وجدت
        if params:
            details = []
            if "prompt" in params:
                details.append(f"الوصف: '{params['prompt']}'")
            if "file_path" in params:
                details.append(f"الملف: {params['file_path']}")
            if "command" in params:
                details.append(f"الأمر: `{params['command']}`")
            
            if details:
                preamble += f" ({', '.join(details)})"
        
        preamble += "..."
        
        return preamble
    
    @staticmethod
    def create_batch_preamble(tool_calls: List[tuple]) -> str:
        """
        إنشاء مقدمة لمجموعة أدوات
        
        Args:
            tool_calls: قائمة (tool_name, params)
            
        Returns:
            نص المقدمة
        """
        if not tool_calls:
            return ""
        
        if len(tool_calls) == 1:
            return PreambleManager.create_preamble(tool_calls[0][0], tool_calls[0][1])
        
        # Multiple tools
        tool_names = [call[0] for call in tool_calls]
        descriptions = [
            PreambleManager.TOOL_DESCRIPTIONS_AR.get(name, name)
            for name in tool_names
        ]
        
        preamble = f"🔧 سأقوم الآن بتنفيذ {len(tool_calls)} إجراءات:\n"
        for i, desc in enumerate(descriptions, 1):
            preamble += f"  {i}. {desc}\n"
        
        return preamble.strip()
    
    @staticmethod
    def create_completion_message(tool_name: str, success: bool = True) -> str:
            """
            رسالة الاكتمال بعد التنفيذ
        
            Args:
                tool_name: اسم الأداة
                success: نجح أم لا
            
            Returns:
                رسالة الاكتمال
            """
            description = PreambleManager.TOOL_DESCRIPTIONS_AR.get(tool_name, tool_name)

            if not description:
                logger.warning(f"No description found for tool: {tool_name}")
                description = tool_name

            if success:
                return f"✅ تم {description} بنجاح"
            else:
                return f"❌ فشل {description}"


# دالة مساعدة
def add_preamble(response: str, tool_calls: List[tuple]) -> str:
    """
    إضافة مقدمة للرد
    
    Args:
        response: الرد الأصلي
        tool_calls: قائمة استدعاءات الأدوات
        
    Returns:
        الرد مع المقدمة
    """
    if not tool_calls:
        return response
    
    preamble = PreambleManager.create_batch_preamble(tool_calls)
    return f"{preamble}\n\n{response}"


# مثال على الاستخدام
if __name__ == "__main__":
    # مثال واحد
    preamble = PreambleManager.create_preamble(
        "generate_image",
        {"prompt": "قطة جميلة"}
    )
    print(preamble)
    # Output: 🔧 سأقوم الآن بتوليد صورة (الوصف: 'قطة جميلة')...
    
    # مثال متعدد
    calls = [
        ("read_file", {"file_path": "config.py"}),
        ("get_system_status", {}),
        ("generate_image", {"prompt": "منظر طبيعي"})
    ]
    
    batch_preamble = PreambleManager.create_batch_preamble(calls)
    print("\n" + batch_preamble)
