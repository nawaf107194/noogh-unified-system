"""
Progress Checkpoint Manager - نظام نقاط التحقق

مستوحى من GPT-5 progress checkpoints pattern.
يوفر تقارير دورية كل 3-5 أدوات.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ActionSummary:
    """ملخص إجراء واحد"""
    tool_name: str
    success: bool
    timestamp: str
    summary: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class Checkpoint:
    """نقطة تحقق"""
    checkpoint_number: int
    actions_count: int
    actions: List[ActionSummary]
    created_at: str
    overall_progress: str


class ProgressCheckpointManager:
    """
    مدير نقاط التحقق التقدمية
    
    يوفر:
    - تقارير كل 3-5 أدوات
    - ملخصات دورية
    - تتبع التقدم
    
    مستوحى من GPT-5.
    """
    
    def __init__(self, checkpoint_interval: int = 4):
        """
        Initialize checkpoint manager
        
        Args:
            checkpoint_interval: عدد الإجراءات بين كل checkpoint
        """
        self.checkpoint_interval = checkpoint_interval
        self.actions: List[ActionSummary] = []
        self.checkpoints: List[Checkpoint] = []
        self.checkpoint_counter = 0
        
        logger.info(f"ProgressCheckpointManager initialized (interval={checkpoint_interval})")
    
    def record_action(
        self,
        tool_name: str,
        success: bool,
        summary: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[Checkpoint]:
        """
        تسجيل إجراء
        
        Args:
            tool_name: اسم الأداة
            success: نجح أم لا
            summary: ملخص النتيجة
            details: تفاصيل إضافية
            
        Returns:
            Checkpoint إذا حان وقت التقرير، None otherwise
        """
        action = ActionSummary(
            tool_name=tool_name,
            success=success,
            timestamp=datetime.now().isoformat(),
            summary=summary,
            details=details
        )
        
        self.actions.append(action)
        
        # Check if we should create checkpoint
        if len(self.actions) >= self.checkpoint_interval:
            return self._create_checkpoint()
        
        return None
    
    def _create_checkpoint(self) -> Checkpoint:
        """إنشاء نقطة تحقق"""
        self.checkpoint_counter += 1
        
        # Calculate overall progress
        successful = sum(1 for a in self.actions if a.success)
        total = len(self.actions)
        
        overall_progress = self._generate_progress_summary(successful, total)
        
        checkpoint = Checkpoint(
            checkpoint_number=self.checkpoint_counter,
            actions_count=total,
            actions=self.actions.copy(),
            created_at=datetime.now().isoformat(),
            overall_progress=overall_progress
        )
        
        self.checkpoints.append(checkpoint)
        
        # Clear actions for next checkpoint
        self.actions = []
        
        logger.info(f"Checkpoint #{self.checkpoint_counter} created")
        
        return checkpoint
    
    def _generate_progress_summary(self, successful: int, total: int) -> str:
        """توليد ملخص التقدم"""
        success_rate = (successful / total * 100) if total > 0 else 0
        
        if success_rate == 100:
            return f"✅ التقدم ممتاز: جميع الـ {total} إجراءات نجحت"
        elif success_rate >= 80:
            return f"✅ التقدم جيد: {successful}/{total} إجراءات نجحت ({success_rate:.0f}%)"
        elif success_rate >= 50:
            return f"⚠️ التقدم متوسط: {successful}/{total} إجراءات نجحت ({success_rate:.0f}%)"
        else:
            return f"❌ التقدم ضعيف: {successful}/{total} فقط نجحت ({success_rate:.0f}%)"
    
    def format_checkpoint_report(self, checkpoint: Checkpoint) -> str:
        """تنسيق تقرير نقطة التحقق"""
        report = []
        
        report.append(f"\n{'='*60}")
        report.append(f"📊 نقطة التحقق #{checkpoint.checkpoint_number}")
        report.append(f"{'='*60}")
        report.append(f"\n{checkpoint.overall_progress}\n")
        
        report.append("الإجراءات المنفذة:")
        for i, action in enumerate(checkpoint.actions, 1):
            status = "✅" if action.success else "❌"
            report.append(f"  {i}. {status} {action.tool_name}: {action.summary}")
        
        report.append(f"\n{'='*60}\n")
        
        return "\n".join(report)
    
    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """الحصول على آخر نقطة تحقق"""
        return self.checkpoints[-1] if self.checkpoints else None
    
    def get_all_checkpoints(self) -> List[Checkpoint]:
        """الحصول على جميع نقاط التحقق"""
        return self.checkpoints.copy()
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """إحصائيات شاملة"""
        total_actions = sum(c.actions_count for c in self.checkpoints)
        total_actions += len(self.actions)  # Include pending
        
        successful = sum(
            sum(1 for a in c.actions if a.success)
            for c in self.checkpoints
        )
        successful += sum(1 for a in self.actions if a.success)
        
        return {
            "total_checkpoints": len(self.checkpoints),
            "total_actions": total_actions,
            "successful_actions": successful,
            "success_rate": (successful / total_actions * 100) if total_actions > 0 else 0,
            "pending_actions": len(self.actions)
        }
    
    def force_checkpoint(self) -> Optional[Checkpoint]:
        """إجبار إنشاء checkpoint حتى لو لم يكتمل العدد"""
        if self.actions:
            return self._create_checkpoint()
        return None


# Global instance
_global_checkpoint_manager = None

def __init__(self, interval: int):
        self.interval = interval

_global_checkpoint_manager: Optional[ProgressCheckpointManager] = None

def get_checkpoint_manager(interval: int = 4) -> ProgressCheckpointManager:
    """الحصول على checkpoint manager عام"""
    global _global_checkpoint_manager
    
    if not isinstance(interval, int):
        raise TypeError(f"Interval must be an integer, got {type(interval)}")
    
    if interval <= 0:
        raise ValueError("Interval must be a positive integer")
    
    if _global_checkpoint_manager is None:
        logger.info(f"Creating new ProgressCheckpointManager with interval={interval}")
        _global_checkpoint_manager = ProgressCheckpointManager(interval)
    else:
        logger.info(f"Returning existing ProgressCheckpointManager with interval={_global_checkpoint_manager.interval}")
    
    return _global_checkpoint_manager


# مثال على الاستخدام
if __name__ == "__main__":
    manager = ProgressCheckpointManager(checkpoint_interval=3)
    
    # محاكاة إجراءات
    checkpoint = manager.record_action("read_file", True, "قراءة ملف config.py")
    checkpoint = manager.record_action("analyze_code", True, "تحليل الكود")
    checkpoint = manager.record_action("generate_image", True, "توليد صورة")
    
    # الآن سينشئ checkpoint
    if checkpoint:
        print(manager.format_checkpoint_report(checkpoint))
    
    # المزيد من الإجراءات
    manager.record_action("write_file", False, "فشل كتابة الملف")
    manager.record_action("execute_command", True, "تنفيذ أمر بنجاح")
    checkpoint = manager.record_action("verify_code", True, "التحقق من الكود")
    
    if checkpoint:
        print(manager.format_checkpoint_report(checkpoint))
    
    # إحصائيات شاملة
    print("\n📈 الإحصائيات الشاملة:")
    stats = manager.get_overall_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
