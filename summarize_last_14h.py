import json
import time

past_14h_ts = time.time() - (14 * 3600)

stats = {
    "proposals": 0,
    "approvals": 0,
    "rejections": 0,
    "trades_total": 0,
    "trades_wins": 0,
    "trades_losses": 0,
    "trades_pnl": 0.0,
    "best_trade": None,
    "worst_trade": None
}

try:
    with open('/home/noogh/projects/noogh_unified_system/src/data/trading/trade_history.json', 'r') as f:
        data = json.load(f)
        for t in data.get('history', []):
            if t.get('closed_at', 0) > past_14h_ts:
                stats["trades_total"] += 1
                pnl = t.get("pnl_percent", 0)
                if pnl > 0:
                    stats["trades_wins"] += 1
                else:
                    stats["trades_losses"] += 1
                stats["trades_pnl"] += pnl
                
                # track best/worst
                if not stats["best_trade"] or pnl > stats["best_trade"]["pnl_percent"]:
                    stats["best_trade"] = t
                if not stats["worst_trade"] or pnl < stats["worst_trade"]["pnl_percent"]:
                    stats["worst_trade"] = t
except Exception as e:
    print(f"Trade parse error: {e}")

try:
    with open('/home/noogh/.noogh/evolution/evolution_ledger.jsonl', 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                e = json.loads(line)
                ts = e.get('timestamp', 0)
                # handle proposal missing timestamp or being in data
                if ts == 0:
                    ts = e.get('data', {}).get('created_at', 0)
                
                if isinstance(ts, (int, float)) and ts > past_14h_ts:
                    t = e.get('type')
                    if t == 'proposal':
                        stats["proposals"] += 1
                    elif t == 'approval':
                        stats["approvals"] += 1
                    elif t in ['rejection', 'execution_error', 'rollback']:
                        stats["rejections"] += 1
            except Exception:
                pass
except Exception as e:
    print(f"Ledger parse error: {e}")

print("=== ⏰ ملخص نشاط NOOGH (آخر 14 ساعة) ===")
print(f"🔹 محاولات الابتكار (Proposals): {stats['proposals']}")
print(f"✅ الابتكارات الناجحة والمطبقة (Promoted): {stats['approvals']}")
print(f"🚫 الأكواد والابتكارات المرفوضة من Sandbox أو السياسات: {stats['rejections']}")

print("\n=== 💰 صفقات الكريبتو المستقلة المكتملة ===")
print(f"إجمالي الصفقات: {stats['trades_total']}")
print(f"🟢 ربح: {stats['trades_wins']} | 🔴 خسارة: {stats['trades_losses']}")
print(f"📊 إجمالي نسبة الربح في 14 ساعة: {stats['trades_pnl']:.2f}%")

if stats["best_trade"]:
    bt = stats["best_trade"]
    print(f"\n🏆 أفضل صفقة ({bt.get('symbol')} {bt.get('direction')}): ربح {bt.get('pnl_percent'):.2f}%")
    print(f"   السبب كما فكر به العقل: {bt.get('reasoning')}")

if stats["worst_trade"]:
    wt = stats["worst_trade"]
    print(f"\n☠️ أسوأ صفقة ({wt.get('symbol')} {wt.get('direction')}): خسارة {wt.get('pnl_percent'):.2f}%")
