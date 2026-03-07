import json
from pathlib import Path
import re

ledger_file = Path('/home/noogh/.noogh/evolution/evolution_ledger.jsonl')
if not ledger_file.exists():
    print("Ledger not found.")
    exit()

promoted = []
rejected = []

with open(ledger_file, 'r') as f:
    for line in f:
        if not line.strip(): continue
        try:
            event = json.loads(line)
            data = event.get('data', {})
            
            # Check for explicitly promoted innovations
            if event.get('type') == 'approval' and data.get('proposal_type') == 'code':
                desc = data.get('description', '')
                if 'innovation' in desc.lower() or 'feature' in desc.lower() or 'reasoning' in desc.lower() or 'architecture' in desc.lower():
                    promoted.append((data.get('proposal_id', 'Unknown'), desc))
            
            # Check for rejections/errors
            if event.get('type') in ['rejection', 'execution_error', 'rollback']:
                desc = data.get('description', '')
                reason = data.get('error', data.get('reason', 'Unknown reason'))
                if 'innovation' in desc.lower() or 'feature' in desc.lower():
                    rejected.append((data.get('proposal_id', 'Unknown'), desc, reason))
                    
        except json.JSONDecodeError:
            continue

print("=== 🚀 أحدث الابتكارات الناجحة (Promoted Innovations) ===")
# Show last 5 successful
for pid, desc in promoted[-5:]:
    print(f"✅ {desc} (ID: {pid[:8]}...)")

print("\n=== 🛡️ أحدث الأفكار المرفوضة (Rejected/Blocked) ===")
# Show last 5 rejected
for pid, desc, reason in rejected[-5:]:
    # Clean up long reasons
    short_reason = reason.split('\n')[0][:100]
    print(f"❌ {desc[:60]}... | قوبلت بالرفض بسبب: {short_reason}")

