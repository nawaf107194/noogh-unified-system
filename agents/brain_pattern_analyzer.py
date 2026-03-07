#!/usr/bin/env python3
"""
Brain Pattern Analyzer
يحلل الـ 607 setups لاكتشاف لماذا SHORT أفضل من LONG
ويولّد قواعد جديدة لتحسين الأداء

الهدف:
- فهم الفرق بين LONG الرابحة والخاسرة
- فهم الفرق بين SHORT الرابحة والخاسرة
- اكتشاف features مرتبطة بالنجاح
- توليد filters جديدة لتحسين LONG
"""
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import logging
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_core.neural_bridge import NeuralEngineClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


class BrainPatternAnalyzer:
    """محلل أنماط ذكي بقيادة العقل"""

    def __init__(self, neural_bridge):
        self.brain = neural_bridge
        self.setups = []
        self.insights = []

        logger.info("🧠 Brain Pattern Analyzer initialized")

    def load_backtest_data(self, file_path: str) -> pd.DataFrame:
        """تحميل بيانات الباكتست"""
        logger.info(f"📥 Loading backtest data from {file_path}...")

        setups = []
        with open(file_path, 'r') as f:
            for line in f:
                setups.append(json.loads(line))

        df = pd.DataFrame(setups)
        logger.info(f"✅ Loaded {len(df)} setups")

        # تحويل timestamp إلى datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def analyze_statistics(self, df: pd.DataFrame) -> Dict:
        """تحليل إحصائي أساسي"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 Statistical Analysis")
        logger.info(f"{'='*60}")

        stats = {}

        # Overall stats
        total = len(df)
        wins = len(df[df['outcome'] == 'WIN'])
        losses = len(df[df['outcome'] == 'LOSS'])
        timeouts = len(df[df['outcome'] == 'TIMEOUT'])

        stats['overall'] = {
            'total': total,
            'wins': wins,
            'losses': losses,
            'timeouts': timeouts,
            'win_rate': (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        }

        logger.info(f"\n📈 Overall:")
        logger.info(f"   Total: {total}")
        logger.info(f"   Wins: {wins} ({wins/total*100:.1f}%)")
        logger.info(f"   Losses: {losses} ({losses/total*100:.1f}%)")
        logger.info(f"   Timeouts: {timeouts} ({timeouts/total*100:.1f}%)")
        logger.info(f"   Win Rate: {stats['overall']['win_rate']:.1f}%")

        # By signal type
        for signal_type in ['LONG', 'SHORT']:
            subset = df[df['signal'] == signal_type]
            if len(subset) == 0:
                continue

            wins = len(subset[subset['outcome'] == 'WIN'])
            losses = len(subset[subset['outcome'] == 'LOSS'])
            wr = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

            stats[signal_type] = {
                'total': len(subset),
                'wins': wins,
                'losses': losses,
                'win_rate': wr,
                'avg_max_profit': subset['max_profit'].mean(),
                'avg_max_loss': subset['max_loss'].mean()
            }

            logger.info(f"\n📊 {signal_type}:")
            logger.info(f"   Total: {len(subset)}")
            logger.info(f"   Wins: {wins} / Losses: {losses}")
            logger.info(f"   Win Rate: {wr:.1f}%")
            logger.info(f"   Avg Max Profit: {subset['max_profit'].mean():.2f}%")
            logger.info(f"   Avg Max Loss: {subset['max_loss'].mean():.2f}%")

        return stats

    def compare_winning_vs_losing(self, df: pd.DataFrame, signal_type: str) -> Dict:
        """مقارنة الإعدادات الرابحة vs الخاسرة لنوع إشارة معين"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 Analyzing {signal_type} signals: Winners vs Losers")
        logger.info(f"{'='*60}")

        subset = df[df['signal'] == signal_type]
        winners = subset[subset['outcome'] == 'WIN']
        losers = subset[subset['outcome'] == 'LOSS']

        if len(winners) == 0 or len(losers) == 0:
            logger.warning(f"⚠️ Not enough data for {signal_type}")
            return {}

        comparison = {}

        # مقارنة features رقمية
        numeric_features = ['rsi', 'volume', 'taker_buy_ratio', 'atr',
                           'max_profit', 'max_loss']

        logger.info(f"\n📊 Feature Comparison:")
        logger.info(f"{'Feature':<20} | {'Winners Avg':<15} | {'Losers Avg':<15} | {'Difference'}")
        logger.info("-" * 70)

        for feature in numeric_features:
            if feature not in winners.columns:
                continue

            win_avg = winners[feature].mean()
            lose_avg = losers[feature].mean()
            diff = win_avg - lose_avg
            diff_pct = (diff / lose_avg * 100) if lose_avg != 0 else 0

            comparison[feature] = {
                'winners_avg': win_avg,
                'losers_avg': lose_avg,
                'difference': diff,
                'difference_pct': diff_pct
            }

            logger.info(f"{feature:<20} | {win_avg:<15.4f} | {lose_avg:<15.4f} | {diff:+.4f} ({diff_pct:+.1f}%)")

        return comparison

    async def ask_brain_for_insights(
        self,
        stats: Dict,
        long_comparison: Dict,
        short_comparison: Dict
    ) -> str:
        """اسأل العقل عن رؤيته للأنماط"""
        logger.info(f"\n{'='*60}")
        logger.info("🧠 Asking Brain for insights...")
        logger.info(f"{'='*60}")

        prompt = f"""أنت خبير في تداول العملات الرقمية. حلل البيانات التالية من 607 إعداد تداول تاريخي:

📊 النتائج الإجمالية:
- LONG signals: {stats['LONG']['win_rate']:.1f}% معدل نجاح ({stats['LONG']['wins']}W/{stats['LONG']['losses']}L)
- SHORT signals: {stats['SHORT']['win_rate']:.1f}% معدل نجاح ({stats['SHORT']['wins']}W/{stats['SHORT']['losses']}L)

🔍 الفرق الحاسم:
SHORT أفضل من LONG بمقدار {stats['SHORT']['win_rate'] - stats['LONG']['win_rate']:.1f}%

📈 مقارنة LONG (الرابحة vs الخاسرة):
{json.dumps(long_comparison, indent=2)}

📈 مقارنة SHORT (الرابحة vs الخاسرة):
{json.dumps(short_comparison, indent=2)}

المطلوب:
1. لماذا SHORT أفضل من LONG؟
2. ما الفرق الأساسي بين LONG الرابحة والخاسرة؟
3. ما الفرق الأساسي بين SHORT الرابحة والخاسرة؟
4. اقترح 3 قواعد (filters) محددة لتحسين أداء LONG
5. اقترح 2 قواعد لتحسين أداء SHORT أكثر

أجب بتنسيق JSON:
{{
  "why_short_better": "السبب الرئيسي...",
  "long_winners_pattern": "النمط المشترك في LONG الرابحة...",
  "long_losers_pattern": "النمط المشترك في LONG الخاسرة...",
  "short_winners_pattern": "النمط المشترك في SHORT الرابحة...",
  "long_improvement_rules": [
    {{"rule": "القاعدة 1", "reasoning": "السبب"}},
    {{"rule": "القاعدة 2", "reasoning": "السبب"}},
    {{"rule": "القاعدة 3", "reasoning": "السبب"}}
  ],
  "short_improvement_rules": [
    {{"rule": "القاعدة 1", "reasoning": "السبب"}},
    {{"rule": "القاعدة 2", "reasoning": "السبب"}}
  ]
}}"""

        try:
            response = await self.brain.complete(
                messages=[
                    {"role": "system", "content": "أنت خبير تحليل بيانات تداول. ركز على الأنماط الكمية والقواعد القابلة للتطبيق."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000
            )

            # استخراج النص من الرد
            response_text = response.get('content', '') if isinstance(response, dict) else str(response)

            logger.info("\n🧠 Brain Response:")
            logger.info(response_text)

            # محاولة استخراج JSON
            try:
                # البحث عن JSON في النص
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response_text[start:end]
                    insights = json.loads(json_str)
                    return insights
                else:
                    logger.warning("⚠️ No JSON found in response, using raw text")
                    return {'raw_response': response_text}
            except json.JSONDecodeError:
                logger.warning("⚠️ Failed to parse JSON, using raw text")
                return {'raw_response': response_text}

        except Exception as e:
            logger.error(f"❌ Error asking brain: {e}")
            return {}

    def generate_strategy_code(self, insights: Dict) -> str:
        """توليد كود Python للقواعد المقترحة"""
        logger.info(f"\n{'='*60}")
        logger.info("⚙️ Generating strategy improvement code...")
        logger.info(f"{'='*60}")

        if 'long_improvement_rules' not in insights:
            logger.warning("⚠️ No improvement rules found in insights")
            return ""

        code = """# Auto-generated strategy improvements from Brain analysis
# Based on 607 historical setups analysis

def improved_long_filter(setup: Dict) -> bool:
    \"\"\"
    تحسينات على إشارات LONG بناءً على تحليل العقل
    تطبق القواعد المكتشفة لتحسين معدل النجاح من 39.8% إلى هدف 50%+
    \"\"\"

"""

        for i, rule in enumerate(insights.get('long_improvement_rules', []), 1):
            rule_text = rule.get('rule', '')
            reasoning = rule.get('reasoning', '')

            code += f"    # Rule {i}: {rule_text}\n"
            code += f"    # Reasoning: {reasoning}\n"

            # محاولة تحويل القاعدة إلى كود
            if 'taker_buy_ratio' in rule_text.lower():
                if '>' in rule_text or 'أكبر' in rule_text or 'فوق' in rule_text:
                    code += f"    if setup.get('taker_buy_ratio', 0.5) <= 0.55:\n"
                    code += f"        return False  # Reject: weak buying pressure\n\n"
            elif 'rsi' in rule_text.lower():
                if 'oversold' in rule_text.lower() or 'تشبع بيع' in rule_text:
                    code += f"    if setup.get('rsi', 50) >= 45:\n"
                    code += f"        return False  # Reject: not oversold enough\n\n"
            elif 'volume' in rule_text.lower():
                if 'above average' in rule_text.lower() or 'أعلى من المتوسط' in rule_text:
                    code += f"    if setup.get('volume', 0) < setup.get('volume_avg', 0) * 1.2:\n"
                    code += f"        return False  # Reject: volume too low\n\n"

        code += "    return True  # Passed all filters\n\n"

        # SHORT improvements
        code += """
def improved_short_filter(setup: Dict) -> bool:
    \"\"\"
    تحسينات على إشارات SHORT لزيادة معدل النجاح من 58.1% إلى هدف 65%+
    \"\"\"

"""

        for i, rule in enumerate(insights.get('short_improvement_rules', []), 1):
            rule_text = rule.get('rule', '')
            reasoning = rule.get('reasoning', '')

            code += f"    # Rule {i}: {rule_text}\n"
            code += f"    # Reasoning: {reasoning}\n"

            if 'taker_buy_ratio' in rule_text.lower():
                if '<' in rule_text or 'أقل' in rule_text:
                    code += f"    if setup.get('taker_buy_ratio', 0.5) >= 0.45:\n"
                    code += f"        return False  # Reject: too much buying\n\n"

        code += "    return True  # Passed all filters\n"

        return code

    async def run_analysis(self):
        """تشغيل التحليل الكامل"""
        logger.info(f"\n{'='*70}")
        logger.info("🧠 BRAIN PATTERN ANALYSIS - START")
        logger.info(f"{'='*70}\n")

        # 1. تحميل البيانات
        data_file = Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')
        df = self.load_backtest_data(data_file)

        # 2. تحليل إحصائي
        stats = self.analyze_statistics(df)

        # 3. مقارنة Winners vs Losers
        long_comparison = self.compare_winning_vs_losing(df, 'LONG')
        short_comparison = self.compare_winning_vs_losing(df, 'SHORT')

        # 4. سؤال العقل
        brain_insights = await self.ask_brain_for_insights(
            stats,
            long_comparison,
            short_comparison
        )

        # 5. توليد كود التحسينات
        if brain_insights and 'raw_response' not in brain_insights:
            strategy_code = self.generate_strategy_code(brain_insights)

            # حفظ الكود
            code_file = Path('/home/noogh/projects/noogh_unified_system/src/strategies/brain_improved_filters.py')
            code_file.parent.mkdir(parents=True, exist_ok=True)

            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(strategy_code)

            logger.info(f"\n💾 Strategy code saved to: {code_file}")

        # 6. حفظ التحليل الكامل
        analysis_output = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'statistics': stats,
            'long_comparison': long_comparison,
            'short_comparison': short_comparison,
            'brain_insights': brain_insights
        }

        output_file = Path('/home/noogh/projects/noogh_unified_system/src/data/brain_analysis.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_output, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Full analysis saved to: {output_file}")

        logger.info(f"\n{'='*70}")
        logger.info("✅ BRAIN PATTERN ANALYSIS - COMPLETE")
        logger.info(f"{'='*70}\n")

        return analysis_output


async def main():
    """نقطة البداية"""

    # Initialize Neural Bridge
    neural_bridge = NeuralEngineClient(
        base_url="http://localhost:11434",
        mode="vllm"
    )

    # Initialize Analyzer
    analyzer = BrainPatternAnalyzer(neural_bridge=neural_bridge)

    # Run analysis
    await analyzer.run_analysis()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
