import json
from pathlib import Path

ledger_file = Path('/home/noogh/.noogh/evolution/evolution_ledger.jsonl')
if ledger_file.exists():
    with open(ledger_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
        # Fetch last 300 to get a good window
        events = [json.loads(line) for line in lines[-300:]]
        proposals = [e for e in events if e.get('type') == 'proposal']
        rejections = [e for e in events if e.get('type') in ('rejection', 'execution_error', 'rollback')]
        approvals = [e for e in events if e.get('type') == 'approval']
        
        print(f"Total events inspected: {len(events)}")
        print(f"Proposals: {len(proposals)}")
        print(f"Approvals: {len(approvals)}")
        print(f"Rejections: {len(rejections)}")
        
        print('\n=== 💡 أحدث المقترحات التي فكر فيها النظام ===')
        for p in proposals[-5:]:
            print(f"[PROPOSAL] ID: {p['data'].get('proposal_id')}")
            print(f"           Description: {p['data'].get('description')}")
            print(f"           Risk: {p['data'].get('risk_score')}")
            
        print('\n=== 🛡️ عمليات الحظر والرفض النخبوية ===')
        for r in rejections[-5:]:
            reason = r['data'].get('error', r['data'].get('reason', 'N/A'))
            print(f"[{r['type'].upper()}] ID: {r['data'].get('proposal_id')}")
            print(f"           Reason: {reason}")
