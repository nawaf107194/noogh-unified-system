# اختبارات المرحلة 5 - NOOGH Wisdom

## نظرة عامة

ملف `test_noogh_wisdom_phase5.py` يحتوي على **23 اختباراً شاملاً** للميزات الجديدة في المرحلة 5:

### الميزات المختبرة

1. **نظام Kelly Criterion لتحجيم المراكز** (8 اختبارات)
2. **نظام أهداف الربح المتدرجة - Tiered Take Profits** (9 اختبارات)
3. **اختبارات التكامل** (2 اختبارات)
4. **الحالات الحدية والأخطاء** (4 اختبارات)

---

## 1. اختبارات Kelly Criterion (8 اختبارات)

### الوصف
يختبر نظام Kelly Criterion لتحديد الحجم الأمثل للصفقات بناءً على:
- **W**: معدل الفوز (Win Rate)
- **R**: نسبة متوسط الربح / متوسط الخسارة (Risk-Reward Ratio)
- **الصيغة**: `f* = W - ((1 - W) / R)`
- **Half-Kelly**: استخدام نصف قيمة Kelly لتقليل التقلبات

### الاختبارات

#### ✅ `test_kelly_calculation_with_positive_edge`
- **الهدف**: اختبار حساب Kelly مع ميزة إيجابية (Win Rate = 60%, R = 1.5)
- **النتيجة المتوقعة**: Kelly ≈ 33.3%, Half-Kelly ≈ 16.7%

#### ✅ `test_kelly_calculation_with_no_edge`
- **الهدف**: اختبار Kelly عندما لا توجد ميزة (Win Rate = 50%, R = 1.0)
- **النتيجة المتوقعة**: Kelly = 0 (لا يجب التداول)

#### ✅ `test_kelly_calculation_with_negative_edge`
- **الهدف**: اختبار Kelly مع ميزة سلبية (Win Rate = 40%, R = 1.0)
- **النتيجة المتوقعة**: Kelly < 0 (نظام غير مربح)

#### ✅ `test_dynamic_trade_usdt_with_insufficient_data`
- **الهدف**: اختبار السلوك مع بيانات غير كافية (< 5 صفقات)
- **النتيجة المتوقعة**: استخدام الحجم الافتراضي 2% من الرصيد

#### ✅ `test_dynamic_trade_usdt_during_drawdown`
- **الهدف**: اختبار التراجع (2+ خسائر متتالية)
- **النتيجة المتوقعة**: تقليل الحجم إلى 1% (anti-martingale)

#### ✅ `test_kelly_position_sizing_with_good_performance`
- **الهدف**: اختبار تحجيم Kelly مع أداء جيد (60% WR, 2.0 R:R)
- **النتيجة المتوقعة**: Kelly = 40%, Half-Kelly = 20%, محدود بـ 10% كحد أقصى

#### ✅ `test_kelly_position_sizing_bounds`
- **الهدف**: اختبار الحدود (1% minimum, 10% maximum)
- **النتيجة المتوقعة**:
  - Kelly عالي → محدود بـ 10%
  - Kelly سالب → محدود بـ 1%

#### ✅ `test_rolling_window_size`
- **الهدف**: التحقق من استخدام آخر 50 صفقة فقط
- **النتيجة المتوقعة**: تحليل آخر 50 صفقة حتى لو كان هناك 100+

---

## 2. اختبارات Tiered Take Profits (9 اختبارات)

### الوصف
يختبر نظام أهداف الربح المتدرجة:
- **TP1**: 1.5x مسافة SL (خروج 50% + نقل SL إلى Entry)
- **TP2**: 2.0x مسافة SL (خروج 30%)
- **TP3**: 3.0x مسافة SL (خروج 20% - إغلاق كامل)

### الاختبارات

#### ✅ `test_tp_calculation_for_long_position`
- **الهدف**: اختبار حساب TPs لصفقة LONG
- **مثال**:
  - Entry: $50,000
  - SL: $49,250 (750 نقطة)
  - TP1: $51,125 (750 × 1.5)
  - TP2: $51,500 (750 × 2.0)
  - TP3: $52,250 (750 × 3.0)

#### ✅ `test_tp_calculation_for_short_position`
- **الهدف**: اختبار حساب TPs لصفقة SHORT
- **مثال**:
  - Entry: $50,000
  - SL: $50,750 (750 نقطة)
  - TP1: $48,875 (750 × 1.5)
  - TP2: $48,500 (750 × 2.0)
  - TP3: $47,750 (750 × 3.0)

#### ✅ `test_tp1_hit_behavior`
- **الهدف**: اختبار سلوك النظام عند ضرب TP1
- **النتيجة المتوقعة**:
  - حذف TP1 من القائمة
  - نقل SL إلى سعر الدخول (Entry)
  - بقاء TP2 و TP3

#### ✅ `test_tp2_hit_behavior`
- **الهدف**: اختبار ضرب TP2
- **النتيجة المتوقعة**: حذف TP2، بقاء TP3 فقط

#### ✅ `test_tp3_hit_behavior`
- **الهدف**: اختبار ضرب TP3 (الهدف الأخير)
- **النتيجة المتوقعة**: إغلاق كامل للصفقة (قائمة TPs فارغة)

#### ✅ `test_tp_not_hit_when_price_below`
- **الهدف**: التحقق من عدم ضرب TP إذا كان السعر أدنى
- **النتيجة المتوقعة**: لا تغيير في قائمة TPs

#### ✅ `test_tp_for_short_position_hit_logic`
- **الهدف**: اختبار منطق ضرب TP للصفقات SHORT (السعر <= TP)
- **النتيجة المتوقعة**: ضرب TP1 عندما السعر يهبط إلى أو أقل من TP1

#### ✅ `test_risk_reward_calculation_with_tiered_tps`
- **الهدف**: اختبار حساب R:R باستخدام TP1 (conservative)
- **النتيجة المتوقعة**: R:R = 1.5 (TP1 basis)

#### ✅ `test_empty_take_profits_list`
- **الهدف**: اختبار حالة قائمة TPs فارغة
- **النتيجة المتوقعة**: R:R = 0

---

## 3. اختبارات التكامل (2 اختبارات)

#### ✅ `test_full_trade_lifecycle_with_all_tps_hit`
- **الهدف**: محاكاة دورة حياة كاملة لصفقة ناجحة
- **السيناريو**:
  1. فتح صفقة LONG مع 3 TPs
  2. ضرب TP1 → نقل SL إلى Entry
  3. ضرب TP2 → بقاء TP3
  4. ضرب TP3 → إغلاق كامل

#### ✅ `test_kelly_sizing_adapts_to_performance`
- **الهدف**: اختبار تكيف Kelly مع تغير الأداء
- **السيناريو**:
  - أداء جيد (70% WR, 2:1 R:R) → حجم أكبر
  - أداء ضعيف (40% WR, 1:1 R:R) → حجم أصغر (1%)

---

## 4. اختبارات الحالات الحدية (4 اختبارات)

#### ✅ `test_division_by_zero_in_kelly`
- **الهدف**: حماية من القسمة على صفر (كل الصفقات رابحة، لا خسائر)
- **النتيجة المتوقعة**: استخدام avg_loss = 1.0 كقيمة افتراضية

#### ✅ `test_zero_risk_reward_ratio`
- **الهدف**: اختبار R = 0
- **النتيجة المتوقعة**: Kelly = 0

#### ✅ `test_minimum_trade_size_enforcement`
- **الهدف**: فرض الحد الأدنى ($11)
- **مثال**: رصيد $100، 1% = $1 → يستخدم $11

#### ✅ `test_negative_kelly_fraction_handling`
- **الهدف**: معالجة Kelly السالب
- **النتيجة المتوقعة**: استخدام 1% كحد أدنى

---

## تشغيل الاختبارات

### جميع الاختبارات
```bash
cd /home/noogh/projects/noogh_unified_system/src/unified_core
python3 -m pytest tests/test_noogh_wisdom_phase5.py -v
```

### اختبارات Kelly فقط
```bash
python3 -m pytest tests/test_noogh_wisdom_phase5.py::TestKellyCriterionPositionSizing -v
```

### اختبارات TPs فقط
```bash
python3 -m pytest tests/test_noogh_wisdom_phase5.py::TestTieredTakeProfits -v
```

### اختبار محدد
```bash
python3 -m pytest tests/test_noogh_wisdom_phase5.py::TestKellyCriterionPositionSizing::test_kelly_calculation_with_positive_edge -v
```

### مع تفاصيل الأخطاء
```bash
python3 -m pytest tests/test_noogh_wisdom_phase5.py -v --tb=long
```

---

## النتائج المتوقعة

عند تشغيل جميع الاختبارات:
```
============================== 23 passed in 0.10s ==============================
```

### توزيع الاختبارات
- ✅ Kelly Criterion: 8/8 نجحت
- ✅ Tiered TPs: 9/9 نجحت
- ✅ Integration: 2/2 نجحت
- ✅ Edge Cases: 4/4 نجحت

---

## معايير النجاح

### Kelly Criterion
- ✓ حساب صحيح لـ Kelly fraction
- ✓ تطبيق Half-Kelly
- ✓ الالتزام بالحدود (1%-10%)
- ✓ معالجة حالات الخطأ (division by zero, negative Kelly)
- ✓ استخدام نافذة متحركة (50 صفقة)
- ✓ آلية anti-martingale خلال التراجع

### Tiered Take Profits
- ✓ حساب صحيح لـ TP1, TP2, TP3
- ✓ منطق صحيح للـ LONG و SHORT
- ✓ إدارة قائمة TPs (pop on hit)
- ✓ نقل SL عند TP1
- ✓ إغلاق كامل عند TP3
- ✓ حساب R:R بناءً على TP1

---

## Integration مع النظام الحالي

هذه الاختبارات تتحقق من:
1. التوافق مع `TradeDecision` dataclass
2. التوافق مع `ActiveTrade` dataclass
3. منطق `_get_dynamic_trade_usdt()`
4. منطق `update_prices()` لإدارة TPs

---

## الصيانة

عند تعديل الكود:
1. **تغيير في Kelly formula** → تحديث اختبارات Kelly
2. **تغيير في TP levels** → تحديث اختبارات TPs
3. **تغيير في الحدود** → تحديث `test_kelly_position_sizing_bounds`
4. **إضافة ميزة جديدة** → إضافة اختبارات جديدة

---

## ملاحظات مهمة

### Kelly Criterion
- يستخدم **Half-Kelly** لتقليل التقلبات
- الحدود: **1% min, 10% max**
- نافذة تحليل: **آخر 50 صفقة**
- آلية anti-martingale: **1% بعد خسارتين متتاليتين**

### Tiered TPs
- **TP1** (50% exit): 1.5x SL distance, SL → Entry
- **TP2** (30% exit): 2.0x SL distance
- **TP3** (20% exit): 3.0x SL distance, full close
- R:R يُحسب بناءً على **TP1** (conservative)

---

## الإصدار
- **التاريخ**: 2026-03-04
- **المرحلة**: Phase 5
- **الإصدار**: v1.0
- **الحالة**: ✅ جميع الاختبارات تعمل (23/23)
