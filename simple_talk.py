import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from unified_core.intelligence import ActiveQuestioner

print("\n🧠 NOOGH - المحادثة البسيطة 🧠\n" + "-"*30)

questioner = ActiveQuestioner(max_depth=3)
result = questioner.ask_why_chain("انخفض سعر الدوجكوين بنسبة 15% فجأة")

print(f"📊 الأسئلة التي سألها NOOGH لنفسه: {result['depth_reached']}")
print(f"🎯 السبب الجذري الذي توصل إليه: {result['root_cause']}")
print("-" * 30 + "\n")
