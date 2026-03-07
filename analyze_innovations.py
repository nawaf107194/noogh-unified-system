import json
import time
from pathlib import Path

past_14h_ts = time.time() - (14 * 3600)

proposals = {}
promoted_ids = set()

# Parse the ledger
try:
    with open('/home/noogh/.noogh/evolution/evolution_ledger.jsonl', 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                event = json.loads(line)
                ts = event.get('timestamp', 0)
                if not isinstance(ts, (int, float)):
                    ts = event.get('data', {}).get('created_at', 0)
                    
                if isinstance(ts, (int, float)) and ts > past_14h_ts:
                    if event.get('type') == 'proposal':
                        pid = event.get('data', {}).get('proposal_id')
                        if pid:
                            proposals[pid] = event.get('data', {})
                    elif event.get('type') == 'approval':
                        pid = event.get('data', {}).get('proposal_id')
                        if pid:
                            promoted_ids.add(pid)
            except Exception:
                pass
except Exception as e:
    print(f"Error reading ledger: {e}")

print(f"📦 تم رصد {len(promoted_ids)} ابتكاراً ناجحاً ومطبقاً (Promoted) في آخر 14 ساعة.")
print("-" * 60)

for i, pid in enumerate(promoted_ids):
    data = proposals.get(pid, {})
    desc = data.get('description', 'غير معروف')
    targets = data.get('targets', [])
    rationale = data.get('rationale', 'لا يوجد تبرير مسجل')
    
    # Just get the file name
    target_names = [Path(t).name for t in targets] if targets else []
    
    print(f"\n{i+1}. 💡 {desc}")
    if target_names:
        print(f"   📂 الملفات المعدلة/المنشأة: {', '.join(target_names)}")
    if rationale:
        print(f"   🧠 سبب الابتكار: {rationale[:200]}...")
