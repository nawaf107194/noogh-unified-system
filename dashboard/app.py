import os
import sqlite3
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel
import urllib.request

# Load environment variables from .env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

app = FastAPI(title="NOOGH Sovereign Dashboard")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SRC_DIR = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC_DIR}/data/shared_memory.sqlite"

# تأكد من وجود المجلدات (إنشاء وهمي إذا لم تكن موجودة لمنع أخطاء FastAPI)
Path(f"{SRC_DIR}/dashboard/templates").mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=f"{SRC_DIR}/dashboard/templates")

def _query_db(query: str, params: tuple = ()):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        return []

@app.get("/")
def get_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/state")
def get_system_state():
    """يجلب الحالة الحية لنظام NOOGH (الأهداف، الدورة الأخيرة، الذاكرة، والأفعال)"""
    
    # 1. جلب الأهداف
    goals_row = _query_db("SELECT value FROM beliefs WHERE key='system:strategic_goals'")
    goals = json.loads(goals_row[0]['value']) if goals_row else {"short_term": [], "long_term": []}
    
    # 2. جلب ملخص الدورة الأخيرة
    last_cycle_row = _query_db(
        "SELECT value, updated_at FROM beliefs WHERE key='orchestrator:last_cycle'"
    )
    last_cycle = json.loads(last_cycle_row[0]['value']) if last_cycle_row else {}
    last_cycle_time = last_cycle_row[0]['updated_at'] if last_cycle_row else 0
    
    # 3. إحصائيات الذاكرة
    mem_stats_row = _query_db("SELECT COUNT(*) as c FROM beliefs")
    total_beliefs = mem_stats_row[0]['c'] if mem_stats_row else 0
    
    # 4. آخر أفعال محرك القرار (Action Layer)
    actions = _query_db(
        "SELECT value, updated_at FROM beliefs WHERE key LIKE 'action_taken:%' ORDER BY updated_at DESC LIMIT 4"
    )
    latest_actions = [json.loads(a['value']) for a in actions]
    
    return {
        "status": "online",
        "total_beliefs": total_beliefs,
        "last_cycle_time": last_cycle_time,
        "goals": goals,
        "cycle_data": last_cycle,
        "recent_actions": latest_actions
    }

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
def chat_with_brain(req: ChatRequest):
    """منفذ الدردشة مع الدماغ المركزي - مع دعم كامل للأوامر والتنفيذ"""

    # --- AGENT INTENT DETECTION & INTERCEPT ---
    import re, subprocess
    msg = req.message.strip()
    intercepted = False
    cmd_to_run = None
    
    # Intent: list directory - check FIRST to avoid conflict with file reading
    m = re.search(r'(?:اعرض|عرض|شوف|اظهر|أظهر|ls)\s+(?:محتويات|المجلد|المسار|الدليل)\s+([/][\w/\.\-]+)', msg)
    if m:
        cmd_to_run = f"ls -la {m.group(1).strip()}"
        intercepted = True

    # Intent: read file - requires "ملف" or "محتوى" keyword, or direct path with cat/اقرأ
    if not intercepted:
        m = re.search(r'(?:اقرأ|اقرا|ارني|أرني|افتح|cat)\s+(?:لي\s+)?(?:ملف\s+)?([/][\w/\.\-]+)', msg)
        if m:
            cmd_to_run = f"cat {m.group(1).strip()}"
            intercepted = True

    # Intent: execute command - improved to handle "نفذ: command" format
    if not intercepted:
        # First try: look for commands after colon (e.g., "نفذ: ps aux" or "نفذ أمر: ps aux")
        m = re.search(r'(?:نفذ|شغل|شغّل|execute|run)(?:\s+(?:الأمر|الامر|أمر|امر))?\s*:\s*(.+)', msg, re.IGNORECASE)
        if not m:
            # Fallback: standard pattern (starts with command-like word)
            m = re.search(r'(?:نفذ|شغل|شغّل|execute|run)\s+([a-z][\w\s\-\|\.\"\'\/\=\%]+)', msg, re.IGNORECASE)
        if m:
            raw_cmd = m.group(1).strip()  # Only strip whitespace, preserve quotes in command syntax
            # Only allow somewhat safe/read-only commands by checking prefix
            safe_prefixes = ("ls", "cat", "tail", "head", "df", "free", "uptime", "date", "whoami", "pwd", "echo", "ps", "grep", "find", "systemctl status", "journalctl", "nvidia-smi", "ping", "python3 -c", "du", "wc")
            if any(raw_cmd.startswith(p) for p in safe_prefixes):
                cmd_to_run = raw_cmd
                intercepted = True
            else:
                # Execute anyway (user responsibility)
                cmd_to_run = raw_cmd
                intercepted = True

    if intercepted and cmd_to_run:
        try:
            cwd = "/home/noogh/projects/noogh_unified_system/src"
            proc = subprocess.run(cmd_to_run, shell=True, capture_output=True, text=True, timeout=10, cwd=cwd)
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            res = out if out else err
            if not res:
                res = "تم التنفيذ (لا يوجد مخرجات)."
            elif len(res) > 3000:
                res = res[:3000] + "\n...[مقتطع]..."

            return {
                "reply": f"💻 **تنفيذ أداة النظام:** `{cmd_to_run}`\n\n```text\n{res}\n```"
            }
        except subprocess.TimeoutExpired:
            return {"reply": f"⚠️ انتهى وقت تنفيذ الأمر (Timeout): `{cmd_to_run}`"}
        except Exception as ex:
            return {"reply": f"⚠️ خطأ أثناء تنفيذ الأداة: {str(ex)}"}

    # --- SYSTEM QUERIES: Goals, Evolution, Health, Beliefs ---

    # Intent: Query system goals
    if re.search(r'(?:ما|اعرض|شوف|اظهر|أظهر|show|what).*(?:الأهداف|اهداف|الاهداف|goals?)', msg, re.IGNORECASE):
        try:
            state = get_system_state()
            goals = state.get("goals", {})
            short_term = goals.get("short_term", [])
            long_term = goals.get("long_term", [])

            reply = "🎯 **الأهداف الاستراتيجية لنظام NOOGH**\n\n"

            if short_term:
                reply += "**📋 قصيرة المدى:**\n"
                for i, g in enumerate(short_term, 1):
                    reply += f"{i}. {g}\n"
                reply += "\n"

            if long_term:
                reply += "**🚀 طويلة المدى:**\n"
                for i, g in enumerate(long_term, 1):
                    reply += f"{i}. {g}\n"

            if not short_term and not long_term:
                reply += "لم يتم تعيين أهداف بعد."

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب الأهداف: {str(e)}"}

    # Intent: Query evolution statistics
    if re.search(r'(?:ما|كم|اعرض|شوف|إحصائيات|احصائيات|stats?).*(?:التطور|التطورات|تطور|evolution)', msg, re.IGNORECASE):
        try:
            stats = get_evolution_stats()
            if "error" in stats:
                return {"reply": f"⚠️ {stats['error']}"}

            reply = "🧬 **إحصائيات نظام التطور الذاتي**\n\n"
            reply += f"📊 **الاقتراحات:** {stats['proposals']}\n"
            reply += f"✅ **المُطبقة:** {stats['promoted']}\n"
            reply += f"✓ **الموافقات:** {stats['approvals']}\n"
            reply += f"❌ **المرفوضة:** {stats['rejections']}\n"
            reply += f"🧪 **Canary ناجحة:** {stats['canary_success']}\n"
            reply += f"🧪 **Canary فاشلة:** {stats['canary_failed']}\n"

            recent = stats.get("recent_events", [])
            if recent:
                reply += f"\n**📜 آخر الأحداث (آخر 30 دقيقة):**\n"
                for evt in recent[:5]:
                    event_type = evt.get('type', 'unknown')
                    timestamp = evt.get('timestamp', 0)
                    reply += f"• {event_type} - {timestamp}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب إحصائيات التطور: {str(e)}"}

    # Intent: Full system state overview - CHECK BEFORE health (more specific)
    if re.search(r'(?:اعرض|شوف|اظهر|show).*(?:حالة|state).*(?:كاملة|شاملة|full|complete)', msg, re.IGNORECASE):
        try:
            state = get_system_state()

            reply = "📊 **الحالة الكاملة لنظام NOOGH**\n\n"
            reply += f"**الحالة:** {state.get('status', 'unknown')}\n"
            reply += f"**إجمالي المعتقدات:** {state.get('total_beliefs', 0)}\n"
            reply += f"**آخر دورة:** {state.get('last_cycle_time', 0)}\n\n"

            # Goals
            goals = state.get("goals", {})
            short_term = goals.get("short_term", [])
            long_term = goals.get("long_term", [])
            reply += f"**🎯 الأهداف:** {len(short_term)} قصيرة، {len(long_term)} طويلة\n\n"

            # Recent actions
            actions = state.get("recent_actions", [])
            if actions:
                reply += f"**🎬 آخر الأفعال ({len(actions)}):**\n"
                for act in actions[:3]:
                    act_str = str(act)[:80]
                    reply += f"• {act_str}...\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب الحالة الكاملة: {str(e)}"}

    # Intent: Query system health (checked AFTER full state)
    if re.search(r'(?:ما|اعرض|شوف|كيف).*(?:حالة|صحة|health|status).*(?:النظام|المنظومة|system)', msg, re.IGNORECASE):
        try:
            health = get_system_health()

            reply = "❤️ **صحة النظام**\n\n"
            reply += f"🖥️ **CPU:** {health['cpu_percent']}%\n"

            mem = health['memory']
            reply += f"💾 **الذاكرة:** {mem['percent']}% ({mem['available_gb']}GB / {mem['total_gb']}GB متاحة)\n"

            disk = health['disk']
            reply += f"💿 **القرص:** {disk['percent']}% ({disk['free_gb']}GB / {disk['total_gb']}GB متاحة)\n"

            reply += f"\n**⚙️ العمليات:**\n"
            procs = health['processes']
            reply += f"• Gateway: {'✅ يعمل' if procs['gateway'] else '❌ متوقف'}\n"
            reply += f"• Neural Engine: {'✅ يعمل' if procs['neural_engine'] else '❌ متوقف'}\n"
            reply += f"• Task Worker: {'✅ يعمل' if procs['task_worker'] else '❌ متوقف'}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب صحة النظام: {str(e)}"}

    # Intent: Search beliefs
    if re.search(r'(?:ابحث|بحث|search|find).*(?:في|عن|about|for|المعتقدات|beliefs?)', msg, re.IGNORECASE):
        try:
            # Extract search query - prioritize "عن <term>"
            query_match = re.search(r'(?:عن|for|about)\s+([^\s]+)', msg, re.IGNORECASE)
            search_q = query_match.group(1).strip() if query_match else ""

            if not search_q:
                # Try alternative pattern: "ابحث <query>"
                query_match = re.search(r'(?:ابحث|بحث|search)\s+(.+)', msg, re.IGNORECASE)
                search_q = query_match.group(1).strip() if query_match else ""

            # Always remove trailing phrases like "في المعتقدات"
            search_q = re.sub(r'\s+(?:في|عن)\s+(?:المعتقدات|beliefs?).*$', '', search_q, flags=re.IGNORECASE).strip()

            results = search_beliefs(q=search_q, limit=10)
            beliefs = results.get("beliefs", [])
            count = results.get("count", 0)

            reply = f"🔍 **نتائج البحث في المعتقدات**\n\n"
            reply += f"**الاستعلام:** `{search_q}`\n"
            reply += f"**النتائج:** {count}\n\n"

            if beliefs:
                for b in beliefs[:10]:
                    key = b.get('key', 'unknown')
                    value = b.get('value', '')
                    # Truncate long values
                    if len(value) > 100:
                        value = value[:100] + "..."
                    reply += f"**{key}:**\n```\n{value}\n```\n\n"
            else:
                reply += "لم يتم العثور على نتائج."

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في البحث: {str(e)}"}

    # --- BINANCE TRADING INTEGRATION ---

    # Intent: Get crypto price
    if re.search(r'(?:كم|ما|اعرض|show|what).*(?:سعر|price|قيمة).*(?:BTC|ETH|SOL|USDT|bitcoin|ethereum)', msg, re.IGNORECASE):
        try:
            # Import Binance manager
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_integration import get_binance_manager

            binance = get_binance_manager(testnet=False, read_only=True)

            # Extract symbol
            symbol_match = re.search(r'(BTC|ETH|SOL|BNB|ADA|DOT|LINK|UNI|AVAX|MATIC)', msg, re.IGNORECASE)
            symbol = f"{symbol_match.group(1).upper()}USDT" if symbol_match else "BTCUSDT"

            price = binance.get_price(symbol)
            ticker = binance.get_24h_ticker(symbol)

            reply = f"💰 **{symbol} - السعر الحالي**\n\n"
            reply += f"**السعر:** ${price:,.2f}\n"

            if ticker:
                change_emoji = "📈" if ticker['change'] > 0 else "📉"
                reply += f"**التغير 24h:** {change_emoji} {ticker['change_percent']:.2f}%\n"
                reply += f"**الأعلى 24h:** ${ticker['high']:,.2f}\n"
                reply += f"**الأدنى 24h:** ${ticker['low']:,.2f}\n"
                reply += f"**الحجم 24h:** {ticker['volume']:,.2f} {symbol[:3]}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب السعر: {str(e)}"}

    # Intent: Get account balance
    if re.search(r'(?:ما|كم|اعرض|show).*(?:رصيد|رصيدي|balance|محفظت)', msg, re.IGNORECASE):
        try:
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_integration import get_binance_manager

            # Check which keys are configured
            testnet_key = os.getenv('BINANCE_TESTNET_API_KEY', '')
            prod_key = os.getenv('BINANCE_API_KEY', '')

            use_testnet = testnet_key and testnet_key != 'your_testnet_api_key_here'
            use_prod = prod_key and prod_key != 'your_production_api_key_here'

            if use_prod:
                binance = get_binance_manager(testnet=False, read_only=True)
            elif use_testnet:
                binance = get_binance_manager(testnet=True, read_only=True)
            else:
                return {"reply": "⚠️ لم يتم تكوين مفاتيح API\n\nأضف المفاتيح في .env وأعد تشغيل Dashboard"}

            account = binance.get_account_info()

            if 'error' in account:
                return {"reply": f"⚠️ {account['error']}\n\nتأكد من إضافة API keys في .env"}

            reply = "💼 **رصيد الحساب**\n\n"

            balances = account.get('balances', [])
            if not balances:
                reply += "لا توجد أرصدة متاحة."
            else:
                for bal in balances[:10]:  # Show top 10
                    asset = bal['asset']
                    total = bal['total']
                    free = bal['free']
                    locked = bal['locked']

                    reply += f"**{asset}:** {total:.8f}\n"
                    if locked > 0:
                        reply += f"  └─ حر: {free:.8f} | مقفل: {locked:.8f}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب الرصيد: {str(e)}"}

    # Intent: Get 24h ticker statistics
    if re.search(r'(?:إحصائيات|احصائيات|stats|ticker).*(?:BTC|ETH|SOL|bitcoin)', msg, re.IGNORECASE):
        try:
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_integration import get_binance_manager

            binance = get_binance_manager(testnet=False, read_only=True)

            # Extract symbol
            symbol_match = re.search(r'(BTC|ETH|SOL|BNB|ADA)', msg, re.IGNORECASE)
            symbol = f"{symbol_match.group(1).upper()}USDT" if symbol_match else "BTCUSDT"

            ticker = binance.get_24h_ticker(symbol)

            if not ticker:
                return {"reply": f"⚠️ لم أتمكن من جلب إحصائيات {symbol}"}

            change_emoji = "📈" if ticker['change'] > 0 else "📉"

            reply = f"📊 **إحصائيات {symbol} - آخر 24 ساعة**\n\n"
            reply += f"**السعر الحالي:** ${ticker['price']:,.2f}\n"
            reply += f"**التغير:** {change_emoji} ${ticker['change']:,.2f} ({ticker['change_percent']:.2f}%)\n"
            reply += f"**الأعلى:** ${ticker['high']:,.2f}\n"
            reply += f"**الأدنى:** ${ticker['low']:,.2f}\n"
            reply += f"**الحجم:** {ticker['volume']:,.2f} {symbol[:3]}\n"
            reply += f"**حجم التداول:** ${ticker['quote_volume']:,.0f}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب الإحصائيات: {str(e)}"}

    # Intent: Get order book depth
    if re.search(r'(?:عمق|عروض|orderbook|depth|bids|asks).*(?:السوق|market)', msg, re.IGNORECASE):
        try:
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_integration import get_binance_manager

            binance = get_binance_manager(testnet=False, read_only=True)

            # Extract symbol
            symbol_match = re.search(r'(BTC|ETH|SOL|BNB)', msg, re.IGNORECASE)
            symbol = f"{symbol_match.group(1).upper()}USDT" if symbol_match else "BTCUSDT"

            orderbook = binance.get_orderbook(symbol, limit=5)

            reply = f"📚 **عمق السوق - {symbol}**\n\n"

            reply += "**🔴 عروض البيع (Asks):**\n"
            for price, qty in orderbook['asks'][:5]:
                reply += f"  ${price:,.2f} - {qty:.4f}\n"

            reply += "\n**🟢 عروض الشراء (Bids):**\n"
            for price, qty in orderbook['bids'][:5]:
                reply += f"  ${price:,.2f} - {qty:.4f}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب عمق السوق: {str(e)}"}

    # Intent: Get open orders
    if re.search(r'(?:الأوامر|اوامر|orders).*(?:المفتوحة|open|active)', msg, re.IGNORECASE):
        try:
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_integration import get_binance_manager

            # Check which keys are configured
            testnet_key = os.getenv('BINANCE_TESTNET_API_KEY', '')
            prod_key = os.getenv('BINANCE_API_KEY', '')

            use_testnet = testnet_key and testnet_key != 'your_testnet_api_key_here'
            use_prod = prod_key and prod_key != 'your_production_api_key_here'

            if use_prod:
                binance = get_binance_manager(testnet=False, read_only=True)
            elif use_testnet:
                binance = get_binance_manager(testnet=True, read_only=True)
            else:
                return {"reply": "⚠️ لم يتم تكوين مفاتيح API"}

            orders = binance.get_open_orders()

            if not orders:
                return {"reply": "✅ لا توجد أوامر مفتوحة"}

            reply = f"📝 **الأوامر المفتوحة ({len(orders)})**\n\n"

            for order in orders[:10]:
                side_emoji = "🟢" if order['side'] == 'BUY' else "🔴"
                reply += f"{side_emoji} **{order['symbol']}** - {order['type']}\n"
                reply += f"  السعر: ${order['price']:,.2f}\n"
                reply += f"  الكمية: {order['quantity']:.4f}\n"
                reply += f"  المنفذ: {order['executed_qty']:.4f}\n"
                reply += f"  الحالة: {order['status']}\n\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب الأوامر: {str(e)}"}

    # Intent: Get top coins by volume
    if re.search(r'(?:أفضل|افضل|top|best).*(?:العملات|coins|crypto)', msg, re.IGNORECASE):
        try:
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_integration import get_binance_manager

            binance = get_binance_manager(testnet=False, read_only=True)

            # Get top coins
            top_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']

            reply = "🏆 **أفضل العملات الرقمية**\n\n"

            for symbol in top_symbols:
                ticker = binance.get_24h_ticker(symbol)
                if ticker:
                    change_emoji = "📈" if ticker['change'] > 0 else "📉"
                    reply += f"**{symbol[:3]}:** ${ticker['price']:,.2f} "
                    reply += f"{change_emoji} {ticker['change_percent']:+.2f}%\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ في جلب العملات: {str(e)}"}

    # --- FUTURES TRADING INTEGRATION ---

    # Intent: Get futures account balance
    if re.search(r'(?:رصيد|balance).*(?:فيوتشر|futures?|العقود)', msg, re.IGNORECASE):
        try:
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_futures import get_futures_manager

            # Check which keys are configured
            testnet_key = os.getenv('BINANCE_TESTNET_API_KEY', '')
            prod_key = os.getenv('BINANCE_API_KEY', '')

            use_testnet = testnet_key and testnet_key != 'your_testnet_api_key_here'
            use_prod = prod_key and prod_key != 'your_production_api_key_here'

            if use_prod:
                futures = get_futures_manager(testnet=False, read_only=True)
            elif use_testnet:
                futures = get_futures_manager(testnet=True, read_only=True)
            else:
                return {"reply": "⚠️ لم يتم تكوين مفاتيح API"}

            account = futures.get_futures_account()

            if 'error' in account:
                return {"reply": f"⚠️ {account['error']}"}

            reply = "💼 **حساب Futures**\n\n"
            reply += f"**إجمالي الرصيد:** ${account['total_wallet_balance']:,.2f}\n"
            reply += f"**الربح/الخسارة غير المحققة:** ${account['total_unrealized_pnl']:+,.2f}\n"
            reply += f"**الرصيد المتاح:** ${account['available_balance']:,.2f}\n"
            reply += f"**الهامش الكلي:** ${account['total_margin_balance']:,.2f}\n"

            assets = account.get('assets', [])
            if assets:
                reply += "\n**الأصول:**\n"
                for asset in assets[:5]:
                    reply += f"• **{asset['asset']}:** {asset['wallet_balance']:.2f}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Intent: Get futures positions
    if re.search(r'(?:صفقات|صفقاتي|positions?|مراكز).*(?:فيوتشر|futures?|المفتوحة|open)', msg, re.IGNORECASE):
        try:
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_futures import get_futures_manager

            testnet_key = os.getenv('BINANCE_TESTNET_API_KEY', '')
            prod_key = os.getenv('BINANCE_API_KEY', '')

            use_testnet = testnet_key and testnet_key != 'your_testnet_api_key_here'
            use_prod = prod_key and prod_key != 'your_production_api_key_here'

            if use_prod:
                futures = get_futures_manager(testnet=False, read_only=True)
            elif use_testnet:
                futures = get_futures_manager(testnet=True, read_only=True)
            else:
                return {"reply": "⚠️ لم يتم تكوين مفاتيح API"}

            positions = futures.get_positions()

            if not positions:
                return {"reply": "✅ لا توجد صفقات مفتوحة"}

            reply = f"📊 **صفقات Futures المفتوحة ({len(positions)})**\n\n"

            for pos in positions:
                side_emoji = "🟢" if float(pos['position_amount']) > 0 else "🔴"
                pnl_emoji = "💚" if float(pos['unrealized_pnl']) > 0 else "❤️"

                reply += f"{side_emoji} **{pos['symbol']}** - {pos['position_side']}\n"
                reply += f"  الكمية: {abs(float(pos['position_amount'])):.4f}\n"
                reply += f"  سعر الدخول: ${pos['entry_price']:,.2f}\n"
                reply += f"  السعر الحالي: ${pos['mark_price']:,.2f}\n"
                reply += f"  {pnl_emoji} الربح/الخسارة: ${pos['unrealized_pnl']:+,.2f}\n"
                reply += f"  الرافعة: {pos['leverage']}x\n"
                reply += f"  سعر التصفية: ${pos['liquidation_price']:,.2f}\n\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Intent: Get funding rate
    if re.search(r'(?:معدل|نسبة|rate).*(?:التمويل|funding)', msg, re.IGNORECASE):
        try:
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_futures import get_futures_manager

            futures = get_futures_manager(testnet=False, read_only=True)

            # Extract symbol
            symbol_match = re.search(r'(BTC|ETH|SOL|BNB)', msg, re.IGNORECASE)
            symbol = f"{symbol_match.group(1).upper()}USDT" if symbol_match else "BTCUSDT"

            funding = futures.get_funding_rate(symbol)

            if not funding:
                return {"reply": f"⚠️ لم أتمكن من جلب معدل التمويل لـ {symbol}"}

            rate = funding['funding_rate'] * 100  # Convert to percentage
            rate_emoji = "💰" if rate > 0 else "💸"

            reply = f"📊 **معدل التمويل - {symbol}**\n\n"
            reply += f"{rate_emoji} **المعدل الحالي:** {rate:+.4f}%\n"
            reply += f"**السعر المرجعي:** ${funding.get('mark_price', 0):,.2f}\n\n"

            if rate > 0.01:
                reply += "⚠️ معدل تمويل مرتفع (Long positions تدفع)\n"
            elif rate < -0.01:
                reply += "⚠️ معدل تمويل سالب (Short positions تدفع)\n"
            else:
                reply += "✅ معدل تمويل طبيعي\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Intent: Get futures mark price
    if re.search(r'(?:سعر|price).*(?:فيوتشر|futures?).*(?:BTC|ETH|SOL)', msg, re.IGNORECASE):
        try:
            import sys
            sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')
            from trading.binance_futures import get_futures_manager

            futures = get_futures_manager(testnet=False, read_only=True)

            # Extract symbol
            symbol_match = re.search(r'(BTC|ETH|SOL|BNB)', msg, re.IGNORECASE)
            symbol = f"{symbol_match.group(1).upper()}USDT" if symbol_match else "BTCUSDT"

            mark_price = futures.get_mark_price(symbol)

            if not mark_price:
                return {"reply": f"⚠️ لم أتمكن من جلب السعر"}

            funding_rate = mark_price['funding_rate'] * 100

            reply = f"💰 **{symbol} Futures**\n\n"
            reply += f"**السعر المرجعي:** ${mark_price['mark_price']:,.2f}\n"
            reply += f"**سعر المؤشر:** ${mark_price['index_price']:,.2f}\n"
            reply += f"**معدل التمويل:** {funding_rate:+.4f}%\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # ---------------------------------------------
    # TRADING ENGINE - AI-POWERED ANALYSIS
    # ---------------------------------------------

    # Analyze Symbol (Arabic & English)
    if re.search(r'(حلل|تحليل)\s+(العملة\s+)?([A-Z]{3,10}USDT?)', msg, re.IGNORECASE) or \
       re.search(r'analyze\s+([A-Z]{3,10}USDT?)', msg, re.IGNORECASE):
        try:
            from trading import get_trading_engine

            # Extract symbol
            match = re.search(r'([A-Z]{3,10}USDT?)', msg, re.IGNORECASE)
            if match:
                symbol = match.group(1).upper()
                if not symbol.endswith('USDT'):
                    symbol += 'USDT'

                engine = get_trading_engine(testnet=False, read_only=True)
                analysis = engine.analyze_symbol(symbol)

                if 'error' in analysis:
                    return {"reply": f"⚠️ خطأ: {analysis['error']}"}

                signal_emoji = {
                    'BULLISH': '🟢',
                    'BEARISH': '🔴',
                    'NEUTRAL': '⚪'
                }.get(analysis['overall_signal'], '⚪')

                reply = f"📊 **تحليل {symbol}**\n\n"
                reply += f"**السعر:** ${analysis['price']:,.4f}\n"
                reply += f"**التغير 24 ساعة:** {analysis['24h_change']:+.2f}%\n"
                reply += f"**الحجم:** ${analysis['24h_volume']:,.0f}\n"
                reply += f"**ارتباط BTC:** {analysis['btc_correlation']:.2%}\n\n"

                # Funding rate signal
                funding = analysis.get('funding_rate_signal', {})
                if funding and 'signal' in funding:
                    funding_emoji = {
                        'BULLISH': '🟢',
                        'BEARISH': '🔴',
                        'NEUTRAL': '⚪'
                    }.get(funding.get('signal'), '⚪')
                    reply += f"**معدل التمويل:** {funding.get('funding_rate_pct', 0):+.4f}% {funding_emoji}\n"
                    reply += f"*{funding.get('reason', '')}*\n\n"

                # Warning if high correlation
                if 'warning' in analysis:
                    reply += f"⚠️ **تحذير:** {analysis['warning']}\n\n"

                reply += f"**الإشارة الإجمالية:** {signal_emoji} **{analysis['overall_signal']}**"

                return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Funding Rate Signal (Arabic & English)
    if re.search(r'(إشارة|معدل)\s+(التمويل|funding)', msg, re.IGNORECASE) or \
       re.search(r'funding\s+(rate\s+)?(signal|analysis)', msg, re.IGNORECASE):
        try:
            from trading import get_trading_engine

            # Extract symbol if provided, default to BTC
            match = re.search(r'([A-Z]{3,10}USDT?)', msg, re.IGNORECASE)
            symbol = 'BTCUSDT'
            if match:
                symbol = match.group(1).upper()
                if not symbol.endswith('USDT'):
                    symbol += 'USDT'

            engine = get_trading_engine(testnet=False, read_only=True)
            signal = engine.get_funding_rate_signal(symbol)

            if 'error' in signal:
                return {"reply": f"⚠️ خطأ: {signal['error']}"}

            signal_emoji = {
                'BULLISH': '🟢',
                'BEARISH': '🔴',
                'NEUTRAL': '⚪'
            }.get(signal['signal'], '⚪')

            reply = f"💰 **إشارة معدل التمويل - {symbol}**\n\n"
            reply += f"**معدل التمويل:** {signal['funding_rate_pct']:+.4f}%\n"
            reply += f"**الإشارة:** {signal_emoji} **{signal['signal']}**\n"
            reply += f"**السبب:** {signal['reason']}\n\n"

            if signal['signal'] == 'BEARISH':
                reply += "📉 معدل تمويل مرتفع - كثير من اللونجات (فكر في الشورت)\n"
            elif signal['signal'] == 'BULLISH':
                reply += "📈 معدل تمويل سلبي - كثير من الشورتات (فكر في اللونج)\n"
            else:
                reply += "⚖️ معدل تمويل طبيعي - لا إشارة واضحة\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # BTC Dominance Analysis (Arabic & English)
    if re.search(r'(تحليل|هيمنة)\s+BTC', msg, re.IGNORECASE) or \
       re.search(r'BTC\s+(dominance|analysis)', msg, re.IGNORECASE) or \
       re.search(r'(أمان|سلامة)\s+(الالتكوينات|altcoins?)', msg, re.IGNORECASE):
        try:
            from trading import get_trading_engine

            engine = get_trading_engine(testnet=False, read_only=True)
            signal = engine.get_btc_dominance_signal()

            if 'error' in signal:
                return {"reply": f"⚠️ خطأ: {signal['error']}"}

            signal_emoji = {
                'AVOID_ALTS': '🔴',
                'SAFE_FOR_ALTS': '🟢',
                'FOLLOW_BTC': '🟡',
                'NEUTRAL': '⚪'
            }.get(signal['signal'], '⚪')

            reply = f"📊 **تحليل هيمنة BTC**\n\n"
            reply += f"**تغير BTC (24 ساعة):** {signal['btc_24h_change']:+.2f}%\n"
            reply += f"**متوسط الارتباط:** {signal['avg_altcoin_correlation']:.2%}\n\n"

            reply += "**الارتباطات:**\n"
            for alt, corr in signal['correlations'].items():
                reply += f"- {alt}: {corr:.2%}\n"

            reply += f"\n**الإشارة:** {signal_emoji} **{signal['signal']}**\n"
            reply += f"**السبب:** {signal['reason']}\n\n"

            if signal['signal'] == 'AVOID_ALTS':
                reply += "⚠️ **تحذير:** تجنب تداول الالتكوينات الآن - BTC ينخفض بشدة مع ارتباط عالٍ\n"
            elif signal['signal'] == 'SAFE_FOR_ALTS':
                reply += "✅ **آمن:** ارتباط منخفض - يمكن تداول الالتكوينات بأمان\n"
            elif signal['signal'] == 'FOLLOW_BTC':
                reply += "📈 **فرصة:** الالتكوينات قد تتبع ارتفاع BTC\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Portfolio Summary (Arabic & English)
    if re.search(r'(ملخص|نظرة)\s+(المحفظة|البورتفوليو|portfolio)', msg, re.IGNORECASE) or \
       re.search(r'portfolio\s+summary', msg, re.IGNORECASE) or \
       re.search(r'(إجمالي|total)\s+(الرصيد|balance)', msg, re.IGNORECASE):
        try:
            from trading import get_trading_engine

            engine = get_trading_engine(testnet=False, read_only=True)
            summary = engine.get_portfolio_summary()

            if 'error' in summary:
                return {"reply": f"⚠️ خطأ: {summary['error']}"}

            spot = summary.get('spot', {})
            futures = summary.get('futures', {})
            grand_total = summary.get('grand_total', 0)

            reply = f"💼 **ملخص المحفظة**\n\n"

            reply += f"**📊 Spot Trading:**\n"
            reply += f"- إجمالي القيمة: ${spot.get('total_value_usdt', 0):,.2f}\n"
            reply += f"- عدد الأصول: {spot.get('assets_count', 0)}\n\n"

            reply += f"**⚡ Futures Trading:**\n"
            reply += f"- الرصيد الكلي: ${futures.get('total_balance', 0):,.2f}\n"
            reply += f"- الربح/الخسارة غير المحققة: ${futures.get('unrealized_pnl', 0):+,.2f}\n"
            reply += f"- الصفقات المفتوحة: {futures.get('open_positions', 0)}\n\n"

            reply += f"**💰 الإجمالي الكلي:** ${grand_total:,.2f}"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # ---------------------------------------------
    # ADVANCED STRATEGY - 30-DAY COMPOUNDING
    # ---------------------------------------------

    # Strategy Status (Arabic & English)
    if re.search(r'(استراتيجية|strategy)\s+(متقدمة|advanced|status|حالة)', msg, re.IGNORECASE):
        try:
            from trading import get_advanced_strategy

            strategy = get_advanced_strategy(testnet=False, read_only=True)
            status = strategy.get_strategy_status()

            capital = status['capital']
            today = status['today']
            thirty_day = status['thirty_day']
            trading_status = status['trading_status']

            reply = f"🎯 **Advanced 30-Day Strategy Status**\n\n"

            reply += f"**💰 Capital:**\n"
            reply += f"- Total: ${capital['total']:.2f}\n"
            reply += f"- Active: ${capital['active']:.2f}\n"
            reply += f"- Reserve: ${capital['reserve']:.2f}"
            if capital['reserve_protected']:
                reply += " ✅\n"
            else:
                reply += " 🚨\n"

            reply += f"\n**📊 Today:**\n"
            reply += f"- Trades: {today['wins']}W / {today['losses']}L / {today['open_trades']} Open\n"
            reply += f"- Win Rate: {today['win_rate']:.1f}%\n"
            reply += f"- P&L: ${today['total_pnl']:+.2f}\n"

            reply += f"\n**📈 30-Day Performance:**\n"
            reply += f"- Total Trades: {thirty_day['total_trades']}\n"
            reply += f"- Win Rate: {thirty_day['win_rate']:.1f}%\n"
            reply += f"- Total P&L: ${thirty_day['total_pnl']:+.2f}\n"
            reply += f"- ROI: {thirty_day['roi']:+.1f}%\n"

            reply += f"\n**🎮 Trading Status:**\n"
            if trading_status['allowed']:
                reply += f"✅ {trading_status['reason']}\n"
            else:
                reply += f"❌ {trading_status['reason']}\n"

            if status['trailing_stop_mode']:
                reply += "\n📈 **SCENARIO A:** Trailing stop mode active!"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Analyze Advanced Setup (Arabic & English)
    if re.search(r'(تحليل|analyze)\s+(متقدم|advanced)\s+([A-Z]{3,10})', msg, re.IGNORECASE):
        try:
            match = re.search(r'([A-Z]{3,10}USDT?)', msg, re.IGNORECASE)
            asset = match.group(1).upper()
            symbol = asset if asset.endswith('USDT') else f"{asset}USDT"

            from trading import get_advanced_strategy

            strategy = get_advanced_strategy(testnet=False, read_only=True)
            analysis = strategy.analyze_setup(symbol)

            if not analysis.get('signal'):
                return {"reply": f"⚠️ {analysis.get('reason', 'No signal')}"}

            signal = analysis['signal']
            signal_emoji = '🟢' if signal == 'LONG' else '🔴'

            reply = f"{signal_emoji} **Advanced Analysis: {symbol}**\n\n"
            reply += f"**Signal:** {signal} ({analysis['strength']:.0f}/100)\n"
            reply += f"**Macro Trend:** {analysis['macro_trend']}\n"
            reply += f"**Liquidity:** {analysis['liquidity_score']:.0f}/100\n\n"

            reply += f"**Entry Setup:**\n"
            reply += f"- Entry: ${analysis['entry_price']:,.2f}\n"
            reply += f"- Stop Loss: ${analysis['stop_loss']:,.2f}\n"
            reply += f"- TP1: ${analysis['take_profit']['tp1']:,.2f} (1:2)\n"
            reply += f"- TP2: ${analysis['take_profit']['tp2']:,.2f} (1:3)\n"
            reply += f"- TP3: ${analysis['take_profit']['tp3']:,.2f} (1:4)\n\n"

            reply += f"**Position:**\n"
            reply += f"- Size: ${analysis['position_size_usdt']:.2f}\n"
            reply += f"- Quantity: {analysis['quantity']:.4f} {asset}\n"
            reply += f"- Risk: ${analysis['take_profit']['risk']:.2f} (1% active balance)\n\n"

            reply += f"**Reasons:**\n"
            for reason in analysis['reasons']:
                reply += f"✓ {reason}\n"

            if analysis['trailing_stop_mode']:
                reply += f"\n📈 **SCENARIO A Active:** Will use trailing stop if TP1 hit!"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Execute Advanced Strategy (Arabic & English)
    if re.search(r'(نفذ|execute)\s+(الاستراتيجية|strategy)\s+([A-Z]{3,10})', msg, re.IGNORECASE):
        try:
            match = re.search(r'([A-Z]{3,10}USDT?)', msg, re.IGNORECASE)
            asset = match.group(1).upper()
            symbol = asset if asset.endswith('USDT') else f"{asset}USDT"

            from trading import get_advanced_strategy

            strategy = get_advanced_strategy(testnet=False, read_only=False)

            # 1. Analyze
            analysis = strategy.analyze_setup(symbol)

            if not analysis.get('signal'):
                return {"reply": f"⚠️ Cannot execute: {analysis.get('reason', 'No signal')}"}

            signal = analysis['signal']
            signal_emoji = '🟢' if signal == 'LONG' else '🔴'

            # 2. Confirmation
            reply = f"{signal_emoji} **Confirm Advanced Strategy Execution**\n\n"
            reply += f"**Signal:** {signal} {symbol} ({analysis['strength']:.0f}/100)\n"
            reply += f"**Entry:** ${analysis['entry_price']:,.2f}\n"
            reply += f"**Stop Loss:** ${analysis['stop_loss']:,.2f}\n"
            reply += f"**TP1:** ${analysis['take_profit']['tp1']:,.2f}\n"
            reply += f"**Position Size:** ${analysis['position_size_usdt']:.2f}\n"
            reply += f"**Risk:** ${analysis['take_profit']['risk']:.2f}\n\n"

            if analysis['trailing_stop_mode']:
                reply += f"📈 **Scenario A:** Trailing stop will activate at TP1\n\n"

            reply += f"⚠️ **This is a REAL futures trade with {analysis['position_size_usdt']:.2f} USDT!**\n\n"
            reply += f"To confirm: **نعم نفذ الاستراتيجية {asset}**"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Confirm Execute Strategy
    if re.search(r'(نعم|تأكيد|confirm|yes)\s+(نفذ|execute)\s+(الاستراتيجية|strategy)\s+([A-Z]{3,10})', msg, re.IGNORECASE):
        try:
            match = re.search(r'([A-Z]{3,10}USDT?)', msg, re.IGNORECASE)
            asset = match.group(1).upper()
            symbol = asset if asset.endswith('USDT') else f"{asset}USDT"

            from trading import get_advanced_strategy

            strategy = get_advanced_strategy(testnet=False, read_only=False)

            # Analyze + Execute
            analysis = strategy.analyze_setup(symbol)

            if not analysis.get('signal'):
                return {"reply": f"❌ Cannot execute: {analysis.get('reason')}"}

            result = strategy.execute_trade(analysis)

            if not result['success']:
                return {"reply": f"❌ Execution failed: {result['message']}"}

            trade = result['trade']
            signal_emoji = '🟢' if trade.side == 'LONG' else '🔴'

            reply = f"✅ **Strategy Executed!**\n\n"
            reply += f"{signal_emoji} **{trade.side} {trade.symbol}**\n"
            reply += f"- Entry: ${trade.entry_price:,.2f}\n"
            reply += f"- Quantity: {trade.quantity:.4f}\n"
            reply += f"- Stop Loss: ${trade.stop_loss:,.2f}\n"
            reply += f"- TP1: ${trade.take_profit['tp1']:,.2f}\n"
            reply += f"- Trade ID: {trade.trade_id}\n\n"

            if result.get('trailing_stop_mode'):
                reply += f"📈 **Trailing stop mode active!**\n\n"

            reply += f"💡 System will monitor and apply scenarios automatically."

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"❌ Execution error: {str(e)}"}

    # Monitor Active Trades (Arabic & English)
    if re.search(r'(راقب|monitor|check)\s+(الصفقات|trades|positions)', msg, re.IGNORECASE):
        try:
            from trading import get_advanced_strategy

            strategy = get_advanced_strategy(testnet=False, read_only=False)
            updates = strategy.monitor_active_trades()

            if not updates:
                return {"reply": "✅ No active trades or no updates needed"}

            reply = "📊 **Trade Monitoring Updates:**\n\n"

            for update in updates:
                action = update['action']
                trade_id = update['trade_id']
                message = update['message']

                if action == 'TRAILING_STOP_ACTIVATED':
                    reply += f"📈 {trade_id}\n{message}\n\n"
                elif action == 'SL_WIDENED':
                    reply += f"⏸️ {trade_id}\n{message}\n\n"
                elif action == 'CLOSED_SL':
                    pnl = update.get('pnl', 0)
                    pnl_emoji = '📈' if pnl > 0 else '📉'
                    reply += f"❌ {trade_id}\n{message}\nP&L: ${pnl:+.2f} {pnl_emoji}\n\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Today's Trades (Arabic & English)
    if re.search(r'(صفقات|trades)\s+(اليوم|today)', msg, re.IGNORECASE):
        try:
            from trading import get_trade_tracker

            tracker = get_trade_tracker()
            stats = tracker.get_today_stats()
            today_trades = tracker.get_today_trades()

            reply = f"📅 **Today's Trades ({stats['date']})**\n\n"
            reply += f"**Summary:**\n"
            reply += f"- Total: {stats['total_trades']}/3\n"
            reply += f"- Wins: {stats['wins']} 🟢\n"
            reply += f"- Losses: {stats['losses']} 🔴\n"
            reply += f"- Open: {stats['open_trades']} ⚪\n"
            reply += f"- Win Rate: {stats['win_rate']:.1f}%\n"
            reply += f"- Total P&L: ${stats['total_pnl']:+.2f}\n\n"

            if today_trades:
                reply += "**Trades:**\n"
                for trade in today_trades[-5:]:  # Last 5
                    status_emoji = {
                        'WIN': '🟢',
                        'LOSS': '🔴',
                        'OPEN': '⚪'
                    }.get(trade.status, '⚪')

                    reply += f"{status_emoji} {trade.side} {trade.symbol}"
                    if trade.pnl:
                        reply += f" → ${trade.pnl:+.2f}"
                    reply += "\n"

            can_trade = tracker.can_trade_today()
            if can_trade['allowed']:
                reply += f"\n✅ {can_trade['reason']}"
            else:
                reply += f"\n❌ {can_trade['reason']}"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # 30-Day Performance (Arabic & English)
    if re.search(r'(أداء|performance)\s+(30|ثلاثين)\s+(يوم|day)', msg, re.IGNORECASE):
        try:
            from trading import get_trade_tracker

            tracker = get_trade_tracker()
            perf = tracker.get_30day_performance()

            reply = f"📈 **30-Day Performance**\n\n"
            reply += f"**Trading Stats:**\n"
            reply += f"- Total Trades: {perf['total_trades']}\n"
            reply += f"- Wins: {perf['wins']} 🟢\n"
            reply += f"- Losses: {perf['losses']} 🔴\n"
            reply += f"- Win Rate: {perf['win_rate']:.1f}%\n"
            reply += f"- Days Active: {perf['days_trading']}\n\n"

            reply += f"**Financial Performance:**\n"
            reply += f"- Starting Balance: ${perf['starting_balance']:.2f}\n"
            reply += f"- Current Balance: ${perf['current_balance']:.2f}\n"
            reply += f"- Total P&L: ${perf['total_pnl']:+.2f}\n"
            reply += f"- Daily Avg P&L: ${perf['daily_avg_pnl']:+.2f}\n"
            reply += f"- ROI: {perf['roi']:+.1f}%\n\n"

            # Progress to goal
            goal = 100.0  # 100% ROI (double)
            progress = (perf['roi'] / goal) * 100
            reply += f"**Goal Progress:**\n"
            reply += f"Target: Double in 30 days (100% ROI)\n"
            reply += f"Current: {perf['roi']:+.1f}% ({progress:.0f}% of goal)\n"

            if perf['roi'] >= 100:
                reply += "\n🎉 **GOAL ACHIEVED!** Balance doubled!"
            elif progress >= 50:
                reply += "\n💪 **On track!** Keep going!"
            else:
                reply += "\n📊 Building momentum..."

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # ---------------------------------------------
    # TRADING EXECUTION (REAL MONEY - BE CAREFUL!)
    # ---------------------------------------------

    # BUY Spot Market Order (Arabic & English)
    if re.search(r'(اشتري|شراء|buy)\s+(\d+\.?\d*)\s+([A-Z]{3,10})', msg, re.IGNORECASE):
        try:
            match = re.search(r'(اشتري|شراء|buy)\s+(\d+\.?\d*)\s+([A-Z]{3,10})', msg, re.IGNORECASE)
            quantity = float(match.group(2))
            asset = match.group(3).upper()
            symbol = f"{asset}USDT"

            # Get current price for confirmation
            from trading import get_binance_manager
            binance = get_binance_manager(testnet=False, read_only=False)

            price = binance.get_price(symbol)
            estimated_cost = quantity * price

            # Safety confirmation
            reply = f"⚠️ **تأكيد الشراء**\n\n"
            reply += f"**العملة:** {symbol}\n"
            reply += f"**الكمية:** {quantity} {asset}\n"
            reply += f"**السعر الحالي:** ${price:,.4f}\n"
            reply += f"**التكلفة المتوقعة:** ${estimated_cost:,.2f} USDT\n\n"
            reply += f"⚠️ **هذا أمر حقيقي سيتم تنفيذه فوراً!**\n\n"
            reply += f"للتأكيد، أرسل: **نعم اشتري {quantity} {asset}**"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Confirm BUY (Arabic & English)
    if re.search(r'(نعم|تأكيد|confirm|yes)\s+(اشتري|شراء|buy)\s+(\d+\.?\d*)\s+([A-Z]{3,10})', msg, re.IGNORECASE):
        try:
            match = re.search(r'(نعم|تأكيد|confirm|yes)\s+(اشتري|شراء|buy)\s+(\d+\.?\d*)\s+([A-Z]{3,10})', msg, re.IGNORECASE)
            quantity = float(match.group(3))
            asset = match.group(4).upper()
            symbol = f"{asset}USDT"

            from trading import get_binance_manager
            binance = get_binance_manager(testnet=False, read_only=False)

            result = binance.create_market_order(symbol, 'BUY', quantity)

            if 'error' in result:
                return {"reply": f"❌ فشل الشراء: {result['error']}"}

            reply = f"✅ **تم الشراء بنجاح!**\n\n"
            reply += f"**رقم الأمر:** {result.get('order_id')}\n"
            reply += f"**العملة:** {result.get('symbol')}\n"
            reply += f"**الكمية المنفذة:** {result.get('executed_qty')}\n"
            reply += f"**الحالة:** {result.get('status')}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"❌ خطأ في التنفيذ: {str(e)}"}

    # SELL Spot Market Order (Arabic & English)
    if re.search(r'(بيع|sell)\s+(\d+\.?\d*)\s+([A-Z]{3,10})', msg, re.IGNORECASE):
        try:
            match = re.search(r'(بيع|sell)\s+(\d+\.?\d*)\s+([A-Z]{3,10})', msg, re.IGNORECASE)
            quantity = float(match.group(2))
            asset = match.group(3).upper()
            symbol = f"{asset}USDT"

            from trading import get_binance_manager
            binance = get_binance_manager(testnet=False, read_only=False)

            price = binance.get_price(symbol)
            estimated_value = quantity * price

            # Safety confirmation
            reply = f"⚠️ **تأكيد البيع**\n\n"
            reply += f"**العملة:** {symbol}\n"
            reply += f"**الكمية:** {quantity} {asset}\n"
            reply += f"**السعر الحالي:** ${price:,.4f}\n"
            reply += f"**القيمة المتوقعة:** ${estimated_value:,.2f} USDT\n\n"
            reply += f"⚠️ **هذا أمر حقيقي سيتم تنفيذه فوراً!**\n\n"
            reply += f"للتأكيد، أرسل: **نعم بيع {quantity} {asset}**"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Confirm SELL (Arabic & English)
    if re.search(r'(نعم|تأكيد|confirm|yes)\s+(بيع|sell)\s+(\d+\.?\d*)\s+([A-Z]{3,10})', msg, re.IGNORECASE):
        try:
            match = re.search(r'(نعم|تأكيد|confirm|yes)\s+(بيع|sell)\s+(\d+\.?\d*)\s+([A-Z]{3,10})', msg, re.IGNORECASE)
            quantity = float(match.group(3))
            asset = match.group(4).upper()
            symbol = f"{asset}USDT"

            from trading import get_binance_manager
            binance = get_binance_manager(testnet=False, read_only=False)

            result = binance.create_market_order(symbol, 'SELL', quantity)

            if 'error' in result:
                return {"reply": f"❌ فشل البيع: {result['error']}"}

            reply = f"✅ **تم البيع بنجاح!**\n\n"
            reply += f"**رقم الأمر:** {result.get('order_id')}\n"
            reply += f"**العملة:** {result.get('symbol')}\n"
            reply += f"**الكمية المنفذة:** {result.get('executed_qty')}\n"
            reply += f"**الحالة:** {result.get('status')}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"❌ خطأ في التنفيذ: {str(e)}"}

    # FUTURES: Open LONG Position (Arabic & English)
    if re.search(r'(افتح|open)\s+(لونج|long)\s+([A-Z]{3,10})\s+(\d+\.?\d*)', msg, re.IGNORECASE):
        try:
            match = re.search(r'(افتح|open)\s+(لونج|long)\s+([A-Z]{3,10})\s+(\d+\.?\d*)', msg, re.IGNORECASE)
            asset = match.group(3).upper()
            quantity = float(match.group(4))
            symbol = f"{asset}USDT"

            # Extract leverage if provided
            lev_match = re.search(r'(رافعة|leverage|x)\s*(\d+)', msg, re.IGNORECASE)
            leverage = int(lev_match.group(2)) if lev_match else 5

            # Extract stop loss if provided
            sl_match = re.search(r'(ستوب|stop)\s*(\d+\.?\d*)', msg, re.IGNORECASE)
            stop_loss = float(sl_match.group(2)) if sl_match else None

            from trading import get_futures_manager
            futures = get_futures_manager(testnet=False, read_only=False, max_leverage=10)

            price = futures.get_futures_price(symbol)
            position_value = quantity * price * leverage

            # Safety confirmation
            reply = f"⚠️ **تأكيد فتح صفقة LONG**\n\n"
            reply += f"**العملة:** {symbol}\n"
            reply += f"**الكمية:** {quantity}\n"
            reply += f"**السعر الحالي:** ${price:,.4f}\n"
            reply += f"**الرافعة:** {leverage}x\n"
            reply += f"**قيمة الصفقة:** ${position_value:,.2f}\n"
            if stop_loss:
                reply += f"**Stop Loss:** ${stop_loss:,.2f}\n"
            reply += f"\n🚨 **تحذير: Futures شديد الخطورة!**\n"
            reply += f"⚠️ **يمكن أن تخسر أكثر من رأس المال!**\n\n"
            reply += f"للتأكيد، أرسل: **نعم افتح long {asset} {quantity}**"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Confirm LONG Position (Arabic & English)
    if re.search(r'(نعم|تأكيد|confirm|yes)\s+(افتح|open)\s+(لونج|long)\s+([A-Z]{3,10})\s+(\d+\.?\d*)', msg, re.IGNORECASE):
        try:
            match = re.search(r'(نعم|تأكيد|confirm|yes)\s+(افتح|open)\s+(لونج|long)\s+([A-Z]{3,10})\s+(\d+\.?\d*)', msg, re.IGNORECASE)
            asset = match.group(4).upper()
            quantity = float(match.group(5))
            symbol = f"{asset}USDT"

            # Extract leverage and stop loss from original message
            lev_match = re.search(r'(رافعة|leverage|x)\s*(\d+)', msg, re.IGNORECASE)
            leverage = int(lev_match.group(2)) if lev_match else 5

            sl_match = re.search(r'(ستوب|stop)\s*(\d+\.?\d*)', msg, re.IGNORECASE)
            stop_loss = float(sl_match.group(2)) if sl_match else None

            from trading import get_futures_manager
            futures = get_futures_manager(testnet=False, read_only=False, max_leverage=10)

            result = futures.open_position(symbol, 'BUY', quantity, leverage=leverage, stop_loss=stop_loss)

            if 'error' in result:
                return {"reply": f"❌ فشل فتح الصفقة: {result['error']}"}

            reply = f"✅ **تم فتح صفقة LONG!**\n\n"
            reply += f"**رقم الأمر:** {result.get('order_id')}\n"
            reply += f"**العملة:** {result.get('symbol')}\n"
            reply += f"**الكمية:** {result.get('quantity')}\n"
            reply += f"**الحالة:** {result.get('status')}\n"
            if 'stop_loss' in result:
                reply += f"**Stop Loss:** ${result['stop_loss']['price']:,.2f}\n"
            reply += f"\n⚠️ **راقب الصفقة عن كثب!**"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"❌ خطأ في التنفيذ: {str(e)}"}

    # FUTURES: Open SHORT Position (Arabic & English)
    if re.search(r'(افتح|open)\s+(شورت|short)\s+([A-Z]{3,10})\s+(\d+\.?\d*)', msg, re.IGNORECASE):
        try:
            match = re.search(r'(افتح|open)\s+(شورت|short)\s+([A-Z]{3,10})\s+(\d+\.?\d*)', msg, re.IGNORECASE)
            asset = match.group(3).upper()
            quantity = float(match.group(4))
            symbol = f"{asset}USDT"

            lev_match = re.search(r'(رافعة|leverage|x)\s*(\d+)', msg, re.IGNORECASE)
            leverage = int(lev_match.group(2)) if lev_match else 5

            sl_match = re.search(r'(ستوب|stop)\s*(\d+\.?\d*)', msg, re.IGNORECASE)
            stop_loss = float(sl_match.group(2)) if sl_match else None

            from trading import get_futures_manager
            futures = get_futures_manager(testnet=False, read_only=False, max_leverage=10)

            price = futures.get_futures_price(symbol)
            position_value = quantity * price * leverage

            reply = f"⚠️ **تأكيد فتح صفقة SHORT**\n\n"
            reply += f"**العملة:** {symbol}\n"
            reply += f"**الكمية:** {quantity}\n"
            reply += f"**السعر الحالي:** ${price:,.4f}\n"
            reply += f"**الرافعة:** {leverage}x\n"
            reply += f"**قيمة الصفقة:** ${position_value:,.2f}\n"
            if stop_loss:
                reply += f"**Stop Loss:** ${stop_loss:,.2f}\n"
            reply += f"\n🚨 **تحذير: SHORT شديد الخطورة!**\n"
            reply += f"⚠️ **خسائر غير محدودة إذا ارتفع السعر!**\n\n"
            reply += f"للتأكيد، أرسل: **نعم افتح short {asset} {quantity}**"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Confirm SHORT Position
    if re.search(r'(نعم|تأكيد|confirm|yes)\s+(افتح|open)\s+(شورت|short)\s+([A-Z]{3,10})\s+(\d+\.?\d*)', msg, re.IGNORECASE):
        try:
            match = re.search(r'(نعم|تأكيد|confirm|yes)\s+(افتح|open)\s+(شورت|short)\s+([A-Z]{3,10})\s+(\d+\.?\d*)', msg, re.IGNORECASE)
            asset = match.group(4).upper()
            quantity = float(match.group(5))
            symbol = f"{asset}USDT"

            lev_match = re.search(r'(رافعة|leverage|x)\s*(\d+)', msg, re.IGNORECASE)
            leverage = int(lev_match.group(2)) if lev_match else 5

            sl_match = re.search(r'(ستوب|stop)\s*(\d+\.?\d*)', msg, re.IGNORECASE)
            stop_loss = float(sl_match.group(2)) if sl_match else None

            from trading import get_futures_manager
            futures = get_futures_manager(testnet=False, read_only=False, max_leverage=10)

            result = futures.open_position(symbol, 'SELL', quantity, leverage=leverage, stop_loss=stop_loss)

            if 'error' in result:
                return {"reply": f"❌ فشل فتح الصفقة: {result['error']}"}

            reply = f"✅ **تم فتح صفقة SHORT!**\n\n"
            reply += f"**رقم الأمر:** {result.get('order_id')}\n"
            reply += f"**العملة:** {result.get('symbol')}\n"
            reply += f"**الكمية:** {result.get('quantity')}\n"
            reply += f"**الحالة:** {result.get('status')}\n"
            if 'stop_loss' in result:
                reply += f"**Stop Loss:** ${result['stop_loss']['price']:,.2f}\n"
            reply += f"\n⚠️ **راقب الصفقة عن كثب!**"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"❌ خطأ في التنفيذ: {str(e)}"}

    # FUTURES: Close Position (Arabic & English)
    if re.search(r'(أغلق|close|إغلاق)\s+(صفقة|position)\s+([A-Z]{3,10})', msg, re.IGNORECASE):
        try:
            match = re.search(r'(أغلق|close|إغلاق)\s+(صفقة|position)\s+([A-Z]{3,10})', msg, re.IGNORECASE)
            asset = match.group(3).upper()
            symbol = f"{asset}USDT"

            from trading import get_futures_manager
            futures = get_futures_manager(testnet=False, read_only=False, max_leverage=10)

            # Get position info
            positions = futures.get_positions(symbol)
            if not positions:
                return {"reply": f"⚠️ لا توجد صفقة مفتوحة لـ {symbol}"}

            pos = positions[0]

            reply = f"⚠️ **تأكيد إغلاق الصفقة**\n\n"
            reply += f"**العملة:** {symbol}\n"
            reply += f"**الكمية:** {abs(pos['position_amount'])}\n"
            reply += f"**سعر الدخول:** ${pos['entry_price']:,.4f}\n"
            reply += f"**السعر الحالي:** ${pos['mark_price']:,.4f}\n"
            reply += f"**الربح/الخسارة:** ${pos['unrealized_pnl']:+,.2f}\n\n"
            reply += f"للتأكيد، أرسل: **نعم أغلق صفقة {asset}**"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"⚠️ خطأ: {str(e)}"}

    # Confirm Close Position
    if re.search(r'(نعم|تأكيد|confirm|yes)\s+(أغلق|close|إغلاق)\s+(صفقة|position)\s+([A-Z]{3,10})', msg, re.IGNORECASE):
        try:
            match = re.search(r'(نعم|تأكيد|confirm|yes)\s+(أغلق|close|إغلاق)\s+(صفقة|position)\s+([A-Z]{3,10})', msg, re.IGNORECASE)
            asset = match.group(4).upper()
            symbol = f"{asset}USDT"

            from trading import get_futures_manager
            futures = get_futures_manager(testnet=False, read_only=False, max_leverage=10)

            result = futures.close_position(symbol)

            if 'error' in result:
                return {"reply": f"❌ فشل إغلاق الصفقة: {result['error']}"}

            pnl_emoji = "📈" if result.get('pnl', 0) >= 0 else "📉"

            reply = f"✅ **تم إغلاق الصفقة!**\n\n"
            reply += f"**العملة:** {result.get('symbol')}\n"
            reply += f"**الكمية:** {result.get('quantity')}\n"
            reply += f"**الربح/الخسارة:** ${result.get('pnl', 0):+,.2f} {pnl_emoji}\n"
            reply += f"**الحالة:** {result.get('status')}\n"

            return {"reply": reply}
        except Exception as e:
            return {"reply": f"❌ خطأ في التنفيذ: {str(e)}"}

    # ---------------------------------------------

    # Try direct Neural Engine first (simpler and faster)
    NEURAL_URL = "http://127.0.0.1:8002/api/v1/process"

    try:
        payload = {"text": req.message, "use_react": True}
        body = json.dumps(payload).encode()

        r_req = urllib.request.Request(
            NEURAL_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Internal-Token": os.getenv("NOOGH_INTERNAL_TOKEN", "")
            },
            method="POST"
        )
        with urllib.request.urlopen(r_req, timeout=120) as r:
            resp_data = json.loads(r.read())
            reply = resp_data.get("response") or resp_data.get("message") or resp_data.get("answer") or str(resp_data)
            return {"reply": reply}

    except Exception as neural_err:
        # Fallback 1: Gateway chat/proxy
        try:
            GATEWAY_URL = "http://127.0.0.1:8001/api/v1/chat/proxy"

            payload = {"message": req.message, "stream": False}
            body = json.dumps(payload).encode()

            r_req = urllib.request.Request(
                GATEWAY_URL,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Internal-Token": os.getenv("NOOGH_INTERNAL_TOKEN", "")
                },
                method="POST"
            )
            with urllib.request.urlopen(r_req, timeout=120) as r:
                resp_data = json.loads(r.read())
                reply = resp_data.get("response") or resp_data.get("message") or resp_data.get("answer") or str(resp_data)
                return {"reply": reply}

        except Exception as gw_err:
            # Fallback 2: ollama direct with LIVE system context
            try:
                import subprocess, time as _time, sqlite3

                # ── Gather live system context ──
                ctx_parts = []

                # 1. Evolution stats from ledger
                try:
                    ledger_file = "/home/noogh/.noogh/evolution/evolution_ledger.jsonl"
                    if os.path.exists(ledger_file):
                        proposals = promoted = rejected = 0
                        proposal_descs = {}  # proposal_id -> description
                        promoted_ids = []
                        with open(ledger_file) as f:
                            for line in f:
                                try:
                                    e = json.loads(line)
                                    t = e.get("type", "")
                                    d = e.get("data", {})
                                    if t == "proposal":
                                        proposals += 1
                                        pid = d.get("proposal_id", "")
                                        desc = d.get("description", "")[:60]
                                        if pid and desc:
                                            proposal_descs[pid] = desc
                                    elif t == "promoted":
                                        promoted += 1
                                        promoted_ids.append(d.get("proposal_id", ""))
                                    elif t == "rejection":
                                        rejected += 1
                                except: pass
                        ctx_parts.append(f"التطور الذاتي: {proposals} اقتراح، {promoted} مُطبّق، {rejected} مرفوض")
                        # Get descriptions for promoted items
                        recent_names = []
                        for pid in promoted_ids[-5:]:
                            desc = proposal_descs.get(pid, pid)
                            recent_names.append(desc.replace("[INNOVATION] ", ""))
                        if recent_names:
                            ctx_parts.append("آخر التطورات المُطبقة: " + " | ".join(recent_names))
                except: pass

                # 2. System health
                try:
                    import psutil
                    cpu = psutil.cpu_percent(interval=0.1)
                    mem = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    ctx_parts.append(f"المعالج: {cpu}% | الذاكرة: {mem.percent}% ({mem.available // (1024**3)}GB حرة) | القرص: {disk.percent}%")
                except: pass

                # 3. GPU status
                try:
                    gpu_out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
                                           capture_output=True, text=True, timeout=3).stdout.strip()
                    if gpu_out:
                        parts = gpu_out.split(", ")
                        ctx_parts.append(f"GPU: {parts[0]}MB/{parts[1]}MB مستخدم، حرارة {parts[2]}°C")
                except: pass

                # 4. Services status
                try:
                    services_status = []
                    for svc in ["noogh-agent", "noogh-gateway", "noogh-neural"]:
                        r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True, timeout=3)
                        status = "✅" if r.stdout.strip() == "active" else "❌"
                        services_status.append(f"{svc}: {status}")
                    ctx_parts.append("الخدمات: " + " | ".join(services_status))
                except: pass

                # 5. Strategic goals from DB
                try:
                    db_path = os.path.join(os.getenv("NOOGH_DATA_DIR", "/home/noogh/.noogh"), "shared_memory.sqlite")
                    if os.path.exists(db_path):
                        conn = sqlite3.connect(db_path)
                        cursor = conn.execute("SELECT value FROM beliefs WHERE key LIKE '%strategic%' OR key LIKE '%goal%' LIMIT 3")
                        goals = [row[0][:80] for row in cursor.fetchall()]
                        conn.close()
                        if goals:
                            ctx_parts.append("الأهداف الاستراتيجية: " + " | ".join(goals))
                except: pass

                system_context = "\n".join(ctx_parts) if ctx_parts else "لا توجد بيانات منظومة متاحة"

                # FIX: Embed context directly in prompt instead of system (better model compliance)
                enhanced_prompt = f"""أنا الدماغ المركزي لنظام NOOGH (نظام ذكاء اصطناعي سيادي مستقل).

📊 **بيانات النظام الحية الآن:**
{system_context}

❓ **سؤال المستخدم:** {req.message}

✅ **تعليمات:** أجب بناءً على البيانات الحية أعلاه فقط. لا تقل "ليس لدي معلومات" - استخدم البيانات المتوفرة. كن دقيقاً ومباشراً."""

                OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
                ollama_payload = {
                    "model": "qwen2.5-coder:7b",
                    "prompt": enhanced_prompt,
                    "stream": False,
                    "options": {"temperature": 0.6, "num_predict": 512}
                }
                body = json.dumps(ollama_payload).encode()
                r_req = urllib.request.Request(
                    OLLAMA_URL,
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(r_req, timeout=120) as r:
                    resp_data = json.loads(r.read())
                    reply = resp_data.get("response", "")
                    if reply:
                        return {"reply": reply}
            except Exception as ollama_err:
                pass
            
            return {"reply": f"⚠️ الاتصال فشل. تأكد من تشغيل Neural Engine أو Gateway أو Ollama.\n\nالخطأ: {str(gw_err)}"}

@app.get("/api/evolution/stats")
def get_evolution_stats():
    """إحصائيات نظام التطور"""
    try:
        ledger_file = "/home/noogh/.noogh/evolution/evolution_ledger.jsonl"
        if not os.path.exists(ledger_file):
            return {"error": "Evolution ledger not found"}

        import time
        cutoff = time.time() - 1800  # آخر 30 دقيقة

        stats = {
            "proposals": 0,
            "approvals": 0,
            "rejections": 0,
            "canary_success": 0,
            "canary_failed": 0,
            "promoted": 0,
            "recent_events": []
        }

        with open(ledger_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('timestamp', 0) < cutoff:
                        continue

                    event_type = entry.get('type')
                    if event_type == 'proposal':
                        stats['proposals'] += 1
                    elif event_type == 'approval':
                        stats['approvals'] += 1
                    elif event_type == 'rejection':
                        stats['rejections'] += 1
                    elif event_type == 'canary_success':
                        stats['canary_success'] += 1
                    elif event_type == 'canary_failed':
                        stats['canary_failed'] += 1
                    elif event_type == 'promoted':
                        stats['promoted'] += 1

                    # أضف آخر 10 أحداث
                    if len(stats['recent_events']) < 10:
                        stats['recent_events'].append({
                            'type': event_type,
                            'timestamp': entry.get('timestamp'),
                            'data': entry.get('data', {})
                        })
                except:
                    continue

        stats['recent_events'].reverse()
        return stats
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/system/health")
def get_system_health():
    """صحة النظام"""
    import psutil

    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "percent": psutil.virtual_memory().percent,
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2)
        },
        "disk": {
            "percent": psutil.disk_usage('/').percent,
            "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
            "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2)
        },
        "processes": {
            "gateway": any("gateway" in p.name().lower() for p in psutil.process_iter(['name'])),
            "neural_engine": any("neural_engine" in " ".join(p.cmdline()).lower() for p in psutil.process_iter(['cmdline'])),
            "task_worker": any("task_worker" in " ".join(p.cmdline()).lower() for p in psutil.process_iter(['cmdline']))
        }
    }

@app.get("/api/beliefs/search")
def search_beliefs(q: str = "", limit: int = 100):
    """البحث في المعتقدات"""
    try:
        query = "SELECT key, value, updated_at FROM beliefs WHERE key LIKE ? ORDER BY updated_at DESC LIMIT ?"
        results = _query_db(query, (f"%{q}%", limit))
        return {"beliefs": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e), "beliefs": [], "count": 0}
