import json
import os
import glob
from pathlib import Path

SRC_DIR = "/home/noogh/projects/noogh_unified_system/src"
TRADING_FILES = [
    f"{SRC_DIR}/alpha_signals.py",
    f"{SRC_DIR}/backtest_engine.py",
    f"{SRC_DIR}/market_maker.py",
    f"{SRC_DIR}/portfolio_optimizer.py",
    f"{SRC_DIR}/execution_engine.py",
    f"{SRC_DIR}/stat_arb.py",
    f"{SRC_DIR}/ml_signals.py",
    f"{SRC_DIR}/data_pipeline.py",
    f"{SRC_DIR}/macro_engine.py",
]

def generate_report():
    report = ["# مراجعة شاملة لنظام التداول في NOOGH 📈🏦\n", "**تاريخ المراجعة**: 2026-03-06\n", "---\n\n"]
    report.append("## 🏗️ نظرة عامة على البنية المعمارية\n\nنظام التداول في NOOGH هو نظام تداول كمّي (Quantitative Trading System) متقدم للعملات الرقمية (Binance Futures)، مبني على أسس مؤسساتية (Institutional Grade).\n\n")
    
    report.append("### المكونات الرئيسية:\n")
    
    components = {
        "alpha_signals.py": "مختبر إشارات الألفا (Alpha Signals Lab)",
        "backtest_engine.py": "محرك الاختبار التاريخي (Backtesting Engine)",
        "market_maker.py": "نظام صناعة السوق (Market Making System)",
        "portfolio_optimizer.py": "نظام تحسين المحفظة (Portfolio Optimizer)",
        "execution_engine.py": "محرك التنفيذ الخوارزمي (Execution Algorithms - TWAP/VWAP)",
        "stat_arb.py": "نظام المراجحة الإحصائية (Statistical Arbitrage - Pairs Trading)",
        "ml_signals.py": "نماذج تعلم الآلة (Machine Learning Models)",
        "data_pipeline.py": "خط أنابيب البيانات (Data Pipeline / Feature Engineering)",
        "macro_engine.py": "محرك تحليل الاقتصاد الكلي (Macro Analysis - BTC.D, TOTAL3)",
        "agents/autonomous_trading_agent.py": "وكيل التداول الذاتي الرئيسي (Live Trading Agent)",
    }
    
    total_lines = 0
    for f_path in TRADING_FILES:
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                total_lines += len(lines)
                name = os.path.basename(f_path)
                desc = components.get(name, "مكون تداول")
                report.append(f"- **{name}**: {desc} ({len(lines):,} سطر كود)")
                
                # Extract some class names
                classes = [l.strip().split(' ')[1].split('(')[0].split(':')[0] for l in lines if l.startswith('class ')]
                if classes:
                    report.append(f"  - *أهم الكلاسات*: {', '.join(classes[:3])}{'...' if len(classes)>3 else ''}")
        except FileNotFoundError:
            report.append(f"- ⚠️ 파일 미발견: {f_path}")

    try:
        with open(f"{SRC_DIR}/agents/autonomous_trading_agent.py", "r") as f:
            lines = f.readlines()
            total_lines += len(lines)
            report.append(f"- **autonomous_trading_agent.py**: وكيل التداول الذاتي الرئيسي ({len(lines):,} سطر كود)")
    except Exception:
        pass

    report.append("\n\n---\n## 🎯 مميزات النظام (Institutional Features)\n")
    
    features = [
        "1. **Execution Algorithms**: تنفيذ الأوامر الكبيرة تدريجياً لتقليل الانزلاق (Slippage) باستخدام خوارزميات TWAP و VWAP و Iceberg.",
        "2. **Statistical Arbitrage**: القدرة على كشف أزواج العملات المترابطة (Cointegration) وتنفيذ صفقات مراجحة (Pairs Trading) عند انحرافها عن مسارها الطبيعي.",
        "3. **Machine Learning Pipeline**: تدريب نماذج XGBoost و Random Forest للتنبؤ باتجاه السوق (Classification) ووضع النطاقات (Regression) مع Validation و Feature Importance.",
        "4. **Portfolio Optimization**: توزيع رأس المال الذكي بين الأزواج باستخدام نماذج ماركويتز (Mean-Variance) وحساب (Kelly Criterion) للمخاطرة القصوى.",
        "5. **Market Making**: استراتيجية توفير سيولة (Liquidity Provision) مزدوجة (Bid/Ask) للاستفادة من الفروقات (Spread).",
        "6. **Tiered Take Profits**: جني الأرباح على دفعات (مثال: 50% عند الهدف الأول، 30% الهدف الثاني) لضمان الأرباح وتقليل المخاطرة المبكرة.",
        "7. **Macro Analysis**: ربط قرارات التداول بمؤشرات السوق الكلية مثل هيمنة البيتكوين (BTC Dominance) وسيولة العملات البديلة (TOTAL3).",
    ]
    report.extend([f"{f}\n" for f in features])

    report.append("\n---\n## 🔄 تدفق التداول الحي (Live Trading Flow)\n")
    flow = """
```text
[1. جمع البيانات]  ← Data Pipeline (OHLCV, Orderbook, Trades) + Macro Data
       ↓
[2. بناء الميزات]  ← Alpha Signals (Indicators) + ML Predictions + StatArb Z-Scores
       ↓
[3. توليد القرار]  ← Autonomous Agent (يجمع الإشارات ويطلب رأي الدماغ/LLM للقرار النهائي)
       ↓
[4. تحسين المحفظة] ← Portfolio Optimizer (يحدد الجانب المالي للقرار - Kelly Size, VaR)
       ↓
[5. إدارة التنفيذ] ← Execution Engine (إذا كان الحجم كبيراً يقسمه لـ VWAP/TWAP)
       ↓
[6. إدارة المخاطرة] ← تحديد الوقف المتحرك (Trailing SL) وجني الأرباح المتدرج (Tiered TP)
       ↓
[7. التعلم المستمر] ← حفظ نتيجة الصفقة في Memory Store لإعادة التدريب.
```
"""
    report.append(flow)
    
    report.append(f"\n\n**إجمالي الحجم**: ما يقارب {total_lines:,} سطر برمجي مخصص لبيئة التداول فقط.\n")
    
    with open('/home/noogh/projects/noogh_unified_system/src/trading_system_analysis.md', 'w', encoding='utf-8') as out:
        out.write('\n'.join(report))
        
generate_report()
