# 📊 دليل المراقبة - Autonomous Trading Agent

## ✅ ما تم إنجازه اليوم

### 1. دمج Trap Strategy + AI Brain
- ✅ استبدال SignalEngineV2 (خاسر) بـ Trap Hybrid Engine (ربحي)
- ✅ دمج مع qwen2.5-coder:7b للتحليل الذكي
- ✅ Hybrid Mode (حقيقي عند 100% فقط)

### 2. إصلاح Precision Error
- ✅ إضافة `get_symbol_info()` + `round_quantity()`
- ✅ تقريب صحيح لكل symbol

### 3. التشغيل والمراقبة
- ✅ إنشاء `run_autonomous_agent_continuous.py` (تشغيل مستمر)
- ✅ إنشاء `monitor_live.py` (مراقبة real-time)

---

## 🚀 التشغيل المستمر

### Option 1: Foreground (موصى به للاختبار)

**Terminal 1 - تشغيل Agent:**
```bash
cd /home/noogh/projects/noogh_unified_system
python3 -m src.agents.run_autonomous_agent_continuous
```

**Terminal 2 - مراقبة حية:**
```bash
cd /home/noogh/projects/noogh_unified_system
python3 -m src.agents.monitor_live
```

**الإيقاف:** `Ctrl+C` في terminal Agent

---

### Option 2: Background (للتشغيل الطويل)

**تشغيل في الخلفية:**
```bash
cd /home/noogh/projects/noogh_unified_system
nohup python3 -m src.agents.run_autonomous_agent_continuous > agent_continuous.log 2>&1 &
```

**مراقبة Log:**
```bash
# Real-time
tail -f src/logs/autonomous_trading_agent.log | grep -v FutureWarning

# آخر 50 سطر
tail -50 src/logs/autonomous_trading_agent.log | grep -v FutureWarning | grep -v fillna

# فلترة الإشارات فقط
tail -f src/logs/autonomous_trading_agent.log | grep -E "Signal|Brain|Position|Executed|Cycle"
```

**الإيقاف:**
```bash
pkill -f run_autonomous_agent_continuous
```

**فحص الحالة:**
```bash
ps aux | grep run_autonomous_agent_continuous | grep -v grep
```

---

## 📊 المراقبة

### 1. Monitor Script (Real-time Dashboard)

```bash
python3 -m src.agents.monitor_live
```

**يعرض:**
- ✅ Status (RUNNING/STOPPED)
- ✅ Last Update
- ✅ Current Cycle
- ✅ Mode (HYBRID/PAPER/LIVE)
- ✅ Balance
- ✅ Open Positions
- ✅ Recent Signals
- ✅ Recent Trades

**التحديث:** كل 5 ثواني

---

### 2. Log Monitoring (Manual)

**آخر نشاط:**
```bash
tail -30 src/logs/autonomous_trading_agent.log | grep -v FutureWarning
```

**مراقبة مستمرة:**
```bash
tail -f src/logs/autonomous_trading_agent.log | grep -v FutureWarning
```

**فلترة الإشارات:**
```bash
tail -f src/logs/autonomous_trading_agent.log | grep "Trap Signal"
```

**Brain Decisions:**
```bash
tail -f src/logs/autonomous_trading_agent.log | grep "Brain Decision"
```

**Trades:**
```bash
tail -f src/logs/autonomous_trading_agent.log | grep "Paper Position"
```

---

## 📈 كيف يعمل Agent

### Cycle Flow (كل 5 دقائق)

```
1. فحص 500 عملة
   ↓
2. Trap Engine: كشف liquidity traps
   ↓
3. AI Brain: تحليل الإشارة (0-100% ثقة)
   ↓
4. Decision:
   - < 70%: REJECT
   - 70-99%: Paper Trade
   - 100%: Live Trade (في Hybrid mode)
   ↓
5. Position Management: مراقبة الصفقات المفتوحة
   ↓
6. Learning: التعلم من النتائج
```

---

## 🎯 متى ينفذ صفقة حقيقية؟

**في Hybrid Mode:**
- ✅ Trap Signal detected
- ✅ Brain Confidence = **100%**
- ✅ DailyTracker allows trade
- ✅ Risk management OK

**في Paper Mode:**
- ❌ لن ينفذ أبداً (وهمي فقط)

**في Live Mode:**
- ⚠️ ينفذ كل الإشارات (خطير!)

---

## 📊 مثال على Cycle

```
19:17:34 | INFO | === Trading Cycle 1 ===
19:17:34 | INFO | 🔍 Analyzing 500 markets...

19:19:25 | INFO | 📊 [Trap Signal] SANTOSUSDT: SHORT @ $1.42
19:19:25 | INFO |    ↳ Stop Loss: $1.44
19:19:25 | INFO |    ↳ Quick TP: $1.39
19:19:25 | INFO |    ↳ Reasons: Bearish Sweep + Buy Exhaustion

19:19:32 | INFO | 🧠 [Brain Decision] SANTOSUSDT: SKIP | Confidence: 70%
19:19:32 | INFO |    ↳ Reason: الاتجاه العام BEARISH + لا يوجد تأكيد قوي
19:19:32 | INFO |    ↳ ❌ Brain rejected the setup

---

19:21:06 | INFO | 📊 [Trap Signal] BASUSDT: LONG @ $0.01
19:21:06 | INFO |    ↳ Stop Loss: $0.01
19:21:06 | INFO |    ↳ Quick TP: $0.01

19:21:10 | INFO | 🧠 [Brain Decision] BASUSDT: LONG | Confidence: 85%
19:21:10 | INFO |    ↳ Reason: سحب سيولة + فراغ سعري + اندفاع شرائي

19:21:33 | INFO | 📝 Paper Position Opened: BASUSDT LONG @ $0.005129
19:21:33 | INFO | 📝 Paper trade: BASUSDT (85% < 100%)
19:21:33 | INFO | ✅ Found 1 potential setups
```

---

## ⚙️ التخصيص

### تغيير Cycle Interval

في `run_autonomous_agent_continuous.py` (line ~76):
```python
await asyncio.sleep(300)  # 5 minutes
```

### تغيير Hybrid Threshold

في `autonomous_trading_agent.py` (line ~153):
```python
self.live_trading_threshold = 100  # 100% للأمان
```

### تغيير عدد العملات

في `autonomous_trading_agent.py` (line ~210):
```python
await self._fetch_top_symbols(limit=500)  # 100, 200, 500
```

---

## 📁 الملفات

| الملف | الوصف |
|------|-------|
| `run_autonomous_agent_continuous.py` | تشغيل مستمر (loop) |
| `monitor_live.py` | مراقبة real-time |
| `autonomous_trading_agent.py` | Agent الرئيسي |
| `trap_hybrid_engine.py` | محرك Trap |
| `binance_futures.py` | Binance API (مع precision fix) |

---

## 🎉 الخلاصة

✅ **Agent جاهز للعمل المستمر!**

**الخطوات:**
1. شغّل `run_autonomous_agent_continuous.py`
2. راقب باستخدام `monitor_live.py`
3. دعه يعمل 24-48 ساعة
4. راجع النتائج (WR, PF)
5. إذا النتائج جيدة → Hybrid Mode سيبدأ Live عند 100%!

---

**التاريخ:** 2026-02-27
**الإصدار:** 3.0 (Continuous + Monitoring)
**الحالة:** ✅ Production Ready
