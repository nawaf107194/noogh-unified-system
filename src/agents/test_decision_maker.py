#!/usr/bin/env python3
"""
اختبار نظام اتخاذ القرارات - DecisionScorer
يُظهر أن النظام يتخذ قرارات لكن لا يسجلها في قاعدة البيانات
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_core.core.gravity import DecisionScorer, DecisionContext

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


async def test_decision_making():
    """اختبار اتخاذ القرارات"""

    print(f"\n{CYAN}{BOLD}╔═══════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║              🧠 اختبار نظام اتخاذ القرارات 🧠                    ║{RESET}")
    print(f"{CYAN}{BOLD}╚═══════════════════════════════════════════════════════════════════╝{RESET}\n")

    # Initialize DecisionScorer
    print(f"{YELLOW}جاري تحميل DecisionScorer...{RESET}")
    scorer = DecisionScorer()
    print(f"{GREEN}✓ DecisionScorer محمّل بنجاح{RESET}\n")

    # Test questions
    questions = [
        "Should I enter a LONG trade on BTCUSDT?",
        "ماذا أفعل عندما تنخفض العملة 5%؟",
        "What is the best stop loss strategy?",
        "كيف أحسّن Win Rate؟",
        "Should I switch to live trading now?"
    ]

    print(f"{CYAN}{BOLD}طرح 5 أسئلة على النظام:{RESET}\n")

    decisions = []

    for i, question in enumerate(questions, 1):
        print(f"{YELLOW}Q{i}: {question}{RESET}")

        # Create decision context
        context = DecisionContext(
            query=question,
            urgency=0.7,
            constraints={}
        )

        # Ask for decision
        decision = await scorer.decide(context)

        # Show result
        print(f"{GREEN}✓ Decision ID: {decision.decision_id}{RESET}")
        print(f"{GREEN}✓ Type: {decision.decision_type.value}{RESET}")
        print(f"{GREEN}✓ Action: {decision.content.get('action_type', 'N/A')}{RESET}")
        print(f"{GREEN}✓ Based on {len(decision.based_on_beliefs)} beliefs{RESET}")
        print(f"{GREEN}✓ Cost: {decision.cost_paid:.3f}{RESET}\n")

        decisions.append(decision)

    # Summary
    print(f"\n{CYAN}{BOLD}النتيجة:{RESET}")
    print(f"{GREEN}✓ تم اتخاذ {len(decisions)} قرارات بنجاح{RESET}")
    print(f"{YELLOW}✓ القرارات مُخزَّنة في الذاكرة: {len(scorer._decision_history)}{RESET}")

    # Check database
    print(f"\n{CYAN}التحقق من قاعدة البيانات...{RESET}")

    import sqlite3
    db_path = Path(__file__).parent.parent / 'data' / 'shared_memory.sqlite'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if decisions table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='decisions'")
    decisions_table = cursor.fetchone()

    if decisions_table:
        cursor.execute("SELECT COUNT(*) FROM decisions")
        count = cursor.fetchone()[0]
        print(f"{YELLOW}✓ جدول 'decisions' موجود: {count} قرارات مُسجَّلة{RESET}")
    else:
        print(f"{RED}✗ جدول 'decisions' غير موجود في قاعدة البيانات!{RESET}")

    conn.close()

    # Explanation
    print(f"\n{CYAN}{BOLD}التفسير:{RESET}")
    print(f"{YELLOW}• DecisionScorer يعمل ويتخذ قرارات{RESET}")
    print(f"{YELLOW}• القرارات تُحفَظ في الذاكرة (memory) فقط{RESET}")
    print(f"{YELLOW}• لا يوجد تسجيل دائم في قاعدة البيانات{RESET}")
    print(f"{YELLOW}• عندما يُعاد تشغيل النظام، القرارات تُمحى{RESET}\n")

    print(f"{GREEN}{BOLD}الحل:{RESET}")
    print(f"{GREEN}1. إضافة جدول 'decisions' في قاعدة البيانات{RESET}")
    print(f"{GREEN}2. تعديل _commit_decision() للكتابة في DB{RESET}")
    print(f"{GREEN}3. ربط autonomous_trading_agent مع DecisionScorer{RESET}\n")


if __name__ == "__main__":
    asyncio.run(test_decision_making())
