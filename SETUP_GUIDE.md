# 🚀 NOOGH Trading System - Setup Guide

## 📚 الملفات الجديدة

### **1. Data Layer** ✅
```
src/data/
├── database.py                  # قاعدة البيانات (SQLite/PostgreSQL)
├── models.py                    # نماذج ORM
├── trade_repository.py          # CRUD للصفقات
├── market_data_repository.py    # CRUD للبيانات التاريخية
└── __init__.py                  # Package init
```

### **2. Signal Engine V3** ✅
```
src/trading/signal_engine_v3.py   # محرك إشارات متكامل
```

### **3. Database Init** ✅
```
src/trading/init_database.py      # إنشاء قاعدة البيانات
```

---

## 🛠️ خطوات التثبيت

### **Step 1: سحب التحديثات**
```bash
cd /home/noogh/noogh-unified-system
git pull origin main
```

### **Step 2: تثبيت المكتبات**
```bash
pip install sqlalchemy pandas numpy python-binance
```

### **Step 3: نسخ الملفات**
```bash
# نسخ كل شيء
cp -r src/data /home/noogh/projects/noogh_unified_system/src/
cp src/trading/signal_engine_v3.py /home/noogh/projects/noogh_unified_system/src/trading/
cp src/trading/init_database.py /home/noogh/projects/noogh_unified_system/src/trading/
cp src/trading/technical_analyzer.py /home/noogh/projects/noogh_unified_system/src/trading/
cp src/trading/smart_strategy_v2.py /home/noogh/projects/noogh_unified_system/src/trading/
```

### **Step 4: إنشاء قاعدة البيانات**
```bash
cd /home/noogh/projects/noogh_unified_system/src/trading
python3 init_database.py
```

**المتوقع:**
```
🔧 Initializing database...
🔌 Connecting to database: data/noogh_trading.db
✅ Database configured
✅ All tables created
✅ Database initialized successfully!

Tables created:
  - trades
  - market_data
  - signals
  - performance_metrics
  - strategy_configs

🔍 Testing database connection...
✅ Connection OK - Total trades: 0
```

### **Step 5: اختبار Signal Engine V3**
```bash
python3 signal_engine_v3.py
```

**المتوقع:**
```
🚀 Signal Engine V3 initialized (v3.0.0)
🔍 Analyzing BTCUSDT...

================================================================================
📡 SIGNAL: BTCUSDT
================================================================================
Direction: LONG
Confidence: 90
Technical Score: 75/100
Entry: 59500.00
SL: 57715.00
TP: 63962.50
Action: READY
================================================================================
```

---

## 🎯 الاستخدام

### **1. استخدام Signal Engine**

```python
from trading.signal_engine_v3 import SignalEngineV3
from binance.client import Client

# Initialize
client = Client()
engine = SignalEngineV3(client=client)

# تحليل عملة واحدة
signal = engine.analyze('BTCUSDT')

if signal and signal['action'] == 'READY':
    print(f"Entry: {signal['entry_price']}")
    print(f"SL: {signal['sl_price']}")
    print(f"TP: {signal['tp_price']}")

# مسح السوق وإيجاد أفضل 10 فرص
ready_signals = engine.scan_and_analyze(top_n=10)
print(f"Found {len(ready_signals)} ready signals")
```

### **2. حفظ صفقة**

```python
from data import TradeRepository

repo = TradeRepository()

# إنشاء صفقة
trade = repo.create({
    'symbol': 'BTCUSDT',
    'side': 'LONG',
    'entry_price': 59500.0,
    'sl_price': 57715.0,
    'tp_price': 63962.5,
    'position_size': 100.0,
    'strategy_name': 'SmartStrategyV2',
    'strategy_version': '2.0',
    'technical_score': 75,
    'confidence': 'HIGH'
})

print(f"Trade created: {trade.id}")

# إغلاق صفقة
trade = repo.close_trade(
    trade_id=trade.id,
    exit_price=63000.0,
    exit_reason='TP'
)

print(f"P&L: {trade.pnl_pct:+.2f}%")
```

### **3. جلب إحصائيات**

```python
from data import TradeRepository
from datetime import datetime, timedelta

repo = TradeRepository()

# إحصائيات آخر 30 يوم
stats = repo.get_statistics(
    start_date=datetime.now() - timedelta(days=30)
)

print(f"Total Trades: {stats['total_trades']}")
print(f"Win Rate: {stats['win_rate']:.2%}")
print(f"Profit Factor: {stats['profit_factor']:.2f}")
print(f"Total P&L: ${stats['total_pnl']:.2f}")
```

---

## 🔄 تحديث Smart Strategy V2

الآن Smart Strategy V2 متكامل مع:
- ✅ Market Scanner
- ✅ Technical Analyzer
- ✅ Signal Engine V3
- ✅ Database

**تشغيل:**
```bash
cd /home/noogh/projects/noogh_unified_system/src/trading
python3 smart_strategy_v2.py
```

**سيقوم ب:**
1. مسح السوق (557 عملة)
2. اختيار أفضل 10
3. تحليل فني لكل واحدة
4. حفظ الإشارات في قاعدة البيانات
5. فتح صفقات إذا Score >= 70

---

## 📊 عرض البيانات

```python
# عرض آخر 10 صفقات
from data import TradeRepository

repo = TradeRepository()
trades = repo.get_trades(limit=10)

for trade in trades:
    print(f"{trade.id} | {trade.symbol} | {trade.side} | {trade.pnl_pct:+.2f}% | {trade.status}")
```

```python
# عرض آخر 10 إشارات
from data.database import get_db
from data.models import Signal

db = get_db()
with db.session() as session:
    signals = session.query(Signal).order_by(Signal.timestamp.desc()).limit(10).all()
    
    for sig in signals:
        print(f"{sig.symbol} | {sig.direction} | Score: {sig.technical_score} | {sig.action_taken}")
```

---

## 🔧 الصيانة

### **حذف بيانات قديمة**
```python
from data import MarketDataRepository

repo = MarketDataRepository()
deleted = repo.cleanup_old_data(days_to_keep=90)
print(f"Deleted {deleted} old candles")
```

### **إعادة بناء قاعدة البيانات**
```bash
python3 init_database.py --drop
```
⚠️ سيحذف كل البيانات!

---

## ⚙️ الإعدادات

### **استخدام PostgreSQL بدلاً من SQLite**

```bash
# متغيرات البيئة
export DB_TYPE=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=noogh
export DB_PASSWORD=your_password
export DB_NAME=noogh_trading

# إنشاء قاعدة البيانات
python3 init_database.py
```

---

## ✅ الخلاصة

الآن لديك:
1. ✅ **Data Pipeline** - تخزين دائم للصفقات والإشارات
2. ✅ **Signal Engine V3** - تحليل شامل متكامل
3. ✅ **Smart Strategy V2** - متكامل مع كل شيء
4. ✅ **Repository Pattern** - CRUD نظيف
5. ✅ **SQLite/PostgreSQL** - دعم قواعد بيانات متعددة

**الخطوة التالية: Backtesting Engine** 🚀
