"""
Memory Manager - نظام إدارة الذاكرة المصنف

مستوحى من Qoder memory system.
يوفر ذاكرة منظمة في 4 فئات رئيسية.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryCategory(Enum):
    """فئات الذاكرة"""
    USER_PREFER = "user_prefer"              # تفضيلات المستخدم
    PROJECT_INFO = "project_info"            # معلومات المشروع
    PROJECT_SPEC = "project_specification"   # مواصفات المشروع
    EXPERIENCE = "experience_lessons"        # دروس مستفادة


class MemoryScope(Enum):
    """نطاق الذاكرة"""
    WORKSPACE = "workspace"  # خاص بالمشروع
    GLOBAL = "global"        # عام عبر جميع المشاريع


@dataclass
class MemoryItem:
    """عنصر ذاكرة"""
    category: MemoryCategory
    scope: MemoryScope
    key: str
    value: Any
    metadata: Dict[str, Any]


class MemoryManager:
    """
    مدير الذاكرة المصنف
    
    يوفر 4 فئات:
    1. user_prefer: معلومات شخصية، تفضيلات
    2. project_info: تقنيات، إعدادات، بيئة
    3. project_specification: معايير التطوير، العمارة
    4. experience_lessons: دروس، best practices
    
    مستوحى من Qoder.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize memory manager
        
        Args:
            storage_path: مسار التخزين (اختياري)
        """
        self.storage_path = storage_path or "./memory_storage"
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        
        self.memories: Dict[MemoryCategory, Dict[str, MemoryItem]] = {
            category: {} for category in MemoryCategory
        }
        
        self._load_memories()
        logger.info(f"MemoryManager initialized with storage: {self.storage_path}")
    
    def store(
        self,
        category: MemoryCategory,
        key: str,
        value: Any,
        scope: MemoryScope = MemoryScope.WORKSPACE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryItem:
        """
        تخزين عنصر في الذاكرة
        
        Args:
            category: الفئة
            key: المفتاح
            value: القيمة
            scope: النطاق
            metadata: بيانات إضافية
            
        Returns:
            MemoryItem المخزن
        """
        item = MemoryItem(
            category=category,
            scope=scope,
            key=key,
            value=value,
            metadata=metadata or {}
        )
        
        self.memories[category][key] = item
        self._save_category(category)
        
        logger.info(f"Stored memory: {category.value}/{key}")
        return item
    
    def retrieve(
            self,
            category: MemoryCategory,
            key: str
        ) -> Optional[MemoryItem]:
            """
            استرجاع عنصر من الذاكرة
        
            Args:
                category: الفئة
                key: المفتاح
            
            Returns:
                MemoryItem أو None
            """
            if not isinstance(category, MemoryCategory):
                raise TypeError("Category must be an instance of MemoryCategory")
            if not isinstance(key, str):
                raise TypeError("Key must be a string")

            if category not in self.memories:
                self.logger.warning(f"Category {category} not found in memories.")
                return None

            memory_item = self.memories[category].get(key)
            if memory_item is None:
                self.logger.warning(f"Key {key} not found in category {category}.")
            return memory_item
    
    def search(
        self,
        query: str,
        category: Optional[MemoryCategory] = None
    ) -> List[MemoryItem]:
        """
        البحث في الذاكرة
        
        Args:
            query: نص البحث
            category: فئة محددة (اختياري)
            
        Returns:
            قائمة MemoryItems
        """
        results = []
        categories = [category] if category else list(MemoryCategory)
        
        for cat in categories:
            for item in self.memories[cat].values():
                # بحث بسيط في المفتاح والقيمة
                if (query.lower() in item.key.lower() or 
                    query.lower() in str(item.value).lower()):
                    results.append(item)
        
        return results
    
    def delete(self, category: MemoryCategory, key: str) -> bool:
        """
        حذف عنصر من الذاكرة
        
        Args:
            category: الفئة
            key: المفتاح
            
        Returns:
            True إذا تم الحذف
        """
        if not isinstance(category, MemoryCategory):
            raise TypeError("Category must be of type MemoryCategory")
        if not isinstance(key, str):
            raise TypeError("Key must be of type str")
        
        bucket = self.memories.get(category)
        if not bucket:
            return False
        
        if key in bucket:
            del bucket[key]
            self._save_category(category)
            logger.info(f"Deleted memory: {category.value}/{key}")
            return True
        
        return False
    
    def get_category_summary(self, category: MemoryCategory) -> Dict[str, Any]:
        """ملخص فئة معينة"""
        items = self.memories[category]
        return {
            "category": category.value,
            "count": len(items),
            "keys": list(items.keys())
        }
    
    def get_all_summaries(self) -> Dict[str, Any]:
        """ملخص جميع الفئات"""
        return {
            cat.value: self.get_category_summary(cat)
            for cat in MemoryCategory
        }
    
    def _save_category(self, category: MemoryCategory):
            """حفظ فئة إلى ملف"""
            if not isinstance(category, MemoryCategory):
                raise TypeError("The 'category' argument must be an instance of MemoryCategory")

            try:
                file_path = Path(self.storage_path) / f"{category.value}.json"
                if not isinstance(self.memories.get(category), dict):
                    raise ValueError(f"No memories found for category {category.value}")

                data = {
                    key: {
                        "category": item.category.value,
                        "scope": item.scope.value,
                        "key": item.key,
                        "value": item.value,
                        "metadata": item.metadata
                    }
                    for key, item in self.memories[category].items()
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                logger.info(f"Successfully saved category {category.value} to {file_path}")

            except FileNotFoundError as e:
                logger.error(f"Failed to save category {category.value}: File not found at {self.storage_path}. Error: {e}")
            except PermissionError as e:
                logger.error(f"Failed to save category {category.value}: Permission denied at {self.storage_path}. Error: {e}")
            except Exception as e:
                logger.error(f"Failed to save category {category.value}: An unexpected error occurred. Error: {e}")
    
    def _load_memories(self):
            """تحميل الذاكرة من الملفات"""
            if not isinstance(self.storage_path, str):
                raise ValueError("storage_path must be a string")

            for category in MemoryCategory:
                try:
                    file_path = Path(self.storage_path) / f"{category.value}.json"
                    if file_path.exists():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if not isinstance(data, dict):
                            logger.error(f"Data loaded from {file_path} is not a dictionary")
                            continue

                        for key, item_data in data.items():
                            if not isinstance(item_data, dict):
                                logger.error(f"Invalid item data format for key '{key}' in {category.value}")
                                continue

                            try:
                                item = MemoryItem(
                                    category=MemoryCategory(item_data["category"]),
                                    scope=MemoryScope(item_data["scope"]),
                                    key=item_data["key"],
                                    value=item_data["value"],
                                    metadata=item_data.get("metadata", {})
                                )
                                self.memories[category][key] = item
                            except KeyError as ke:
                                logger.error(f"Missing key '{ke}' in item data for key '{key}' in {category.value}")
                            except ValueError as ve:
                                logger.error(f"Value error when creating MemoryItem for key '{key}' in {category.value}: {ve}")

                        logger.info(f"Loaded {len(data)} items from {category.value}")
                    else:
                        logger.warning(f"No memory file found for category {category.value}")
                except FileNotFoundError as fnfe:
                    logger.error(f"File not found while loading memories for category {category.value}: {fnfe}")
                except json.JSONDecodeError as jde:
                    logger.error(f"JSON decode error while loading memories for category {category.value}: {jde}")
                except Exception as e:
                    logger.error(f"Unexpected error while loading memories for category {category.value}: {e}")
    
    # دوال مساعدة سريعة
    def remember_user_preference(self, key: str, value: Any):
        """تذكر تفضيل مستخدم"""
        return self.store(MemoryCategory.USER_PREFER, key, value, MemoryScope.GLOBAL)
    
    def remember_project_info(self, key: str, value: Any):
        """تذكر معلومة مشروع"""
        return self.store(MemoryCategory.PROJECT_INFO, key, value, MemoryScope.WORKSPACE)
    
    def remember_lesson(self, key: str, value: Any):
        """تذكر درس مستفاد"""
        return self.store(MemoryCategory.EXPERIENCE, key, value, MemoryScope.GLOBAL)


# دوال مساعدة
_global_memory_manager = None

def get_memory_manager(storage_path: Optional[str] = None) -> MemoryManager:
    """الحصول على memory manager عام"""
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager(storage_path)
    return _global_memory_manager


# مثال على الاستخدام
if __name__ == "__main__":
    # اختبار
    manager = MemoryManager("./test_memory")
    
    # تخزين
    manager.remember_user_preference("preferred_language", "Arabic")
    manager.remember_project_info("tech_stack", "Python, FastAPI, PyTorch")
    manager.remember_lesson("avoid_blocking_io", "Always use async for I/O operations")
    
    # استرجاع
    lang = manager.retrieve(MemoryCategory.USER_PREFER, "preferred_language")
    print(f"Preferred language: {lang.value if lang else 'None'}")
    
    # بحث
    results = manager.search("python")
    print(f"\nSearch results for 'python': {len(results)} items")
    
    # ملخص
    print("\nSummaries:")
    print(json.dumps(manager.get_all_summaries(), indent=2))
