# 🧠 NOOGH Learning System v3

نظام التعلم الموحد الذي يجمع جميع مكونات التعلم في NOOGH.

## المكونات

| المكوّن | الوظيفة |
|---------|----------|
| `LearningEngine` | المحرك الرئيسي — واجهة موحدة لكل شيء |
| `SharedMemoryStore` | قاعدة بيانات SQLite مع schema محسّن |
| `AdaptiveCurriculum` | يضبط أولويات التعلم بناءً على أداء التداول |
| `KnowledgeConsolidator` | dedup + decay + تعزيز المؤكد |

## مصادر التعلم

- **GitHub** — أحدث repos في AI/Trading/Quant
- **arXiv** — أوراق cs.AI + q-fin.TR
- **HackerNews** — أهم الأخبار التقنية
- **Heuristic** — دروس مستخلصة من نتائج التداول الفعلية

## الاستخدام

```python
# من الكود
from agents.learning import LearningEngine, LearningDomain

engine = LearningEngine()
await engine.run_cycle()           # دورة واحدة
await engine.run_continuous(1800)  # كل 30 دقيقة

# استعلام
top = engine.get_knowledge(domain=LearningDomain.TRADING, limit=10)
```

```bash
# من سطر الأوامر
python -m agents.learning.learning_engine --once
python -m agents.learning.learning_engine --interval 900  # كل 15 دقيقة
```

## Adaptive Curriculum

النظام يراقب win_rate من نتائج paper trading:
- إذا win_rate < 50% → يرفع وزن domain `trading` تلقائياً
- يُعطي الأولوية للمصادر المرتبطة بالخسائل الأخيرة

## Schema SQLite

```sql
-- beliefs: المعرفة المكتسبة
key TEXT PRIMARY KEY
value TEXT (JSON)
utility_score REAL  -- 0.0 → 1.0
domain TEXT
updated_at REAL

-- learning_cycles: سجل الدورات
cycle_id INTEGER PK
data TEXT (JSON)
created_at REAL
```
