#!/usr/bin/env python3
"""
Option Alpha AI API Client
Wrapper للتعامل مع Option Alpha API
"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class OptionsStrategy:
    """استراتيجية خيارات"""
    id: str
    name: str
    symbol: str
    strategy_type: str  # iron_condor, bull_spread, etc
    legs: List[Dict]  # قائمة الخيارات المكونة للاستراتيجية
    entry_price: float
    max_profit: float
    max_loss: float
    probability_of_profit: float
    delta: float
    theta: float
    vega: float
    confidence: float
    expiration: str
    created_at: str


@dataclass
class BacktestResult:
    """نتيجة الاختبار التاريخي"""
    strategy_id: str
    start_date: str
    end_date: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Dict]


class OptionAlphaClient:
    """
    عميل Option Alpha API

    ملاحظة: هذا wrapper تجريبي. يجب الحصول على API key حقيقي
    من https://optionalpha.com/developers
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.optionalpha.com/v1"):
        self.api_key = api_key or os.getenv("OPTION_ALPHA_API_KEY", "DEMO_KEY")
        self.base_url = base_url
        self.session = None
        self.is_demo = self.api_key == "DEMO_KEY"

        if self.is_demo:
            logger.warning("⚠️ Running in DEMO mode. Get real API key from optionalpha.com")

    async def _ensure_session(self):
        """التأكد من وجود session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

    async def close(self):
        """إغلاق الاتصال"""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_strategies(
        self,
        symbol: str = "SPY",
        strategy_type: Optional[str] = None,
        min_probability: float = 0.6
    ) -> List[OptionsStrategy]:
        """
        الحصول على استراتيجيات خيارات مقترحة

        Args:
            symbol: رمز السهم (مثل SPY, QQQ)
            strategy_type: نوع الاستراتيجية (اختياري)
            min_probability: الحد الأدنى لاحتمالية الربح
        """
        if self.is_demo:
            return self._get_demo_strategies(symbol, strategy_type, min_probability)

        await self._ensure_session()

        try:
            params = {
                "symbol": symbol,
                "min_probability": min_probability
            }
            if strategy_type:
                params["type"] = strategy_type

            async with self.session.get(f"{self.base_url}/strategies", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [OptionsStrategy(**s) for s in data.get("strategies", [])]
                else:
                    logger.error(f"API Error: {resp.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching strategies: {e}")
            return []

    def _get_demo_strategies(self, symbol: str, strategy_type: Optional[str], min_prob: float) -> List[OptionsStrategy]:
        """استراتيجيات تجريبية للاختبار"""
        demo_strategies = [
            OptionsStrategy(
                id="demo_ic_spy_001",
                name="SPY Iron Condor",
                symbol="SPY",
                strategy_type="iron_condor",
                legs=[
                    {"type": "call", "strike": 590, "action": "sell", "quantity": 1},
                    {"type": "call", "strike": 595, "action": "buy", "quantity": 1},
                    {"type": "put", "strike": 570, "action": "sell", "quantity": 1},
                    {"type": "put", "strike": 565, "action": "buy", "quantity": 1}
                ],
                entry_price=2.50,
                max_profit=250.0,
                max_loss=-250.0,
                probability_of_profit=0.72,
                delta=0.05,
                theta=8.5,
                vega=-12.3,
                confidence=0.85,
                expiration=(datetime.now() + timedelta(days=45)).isoformat(),
                created_at=datetime.now().isoformat()
            ),
            OptionsStrategy(
                id="demo_bull_qqq_001",
                name="QQQ Bull Put Spread",
                symbol="QQQ",
                strategy_type="bull_put_spread",
                legs=[
                    {"type": "put", "strike": 480, "action": "sell", "quantity": 1},
                    {"type": "put", "strike": 475, "action": "buy", "quantity": 1}
                ],
                entry_price=1.80,
                max_profit=180.0,
                max_loss=-320.0,
                probability_of_profit=0.68,
                delta=0.25,
                theta=6.2,
                vega=-8.5,
                confidence=0.78,
                expiration=(datetime.now() + timedelta(days=30)).isoformat(),
                created_at=datetime.now().isoformat()
            ),
            OptionsStrategy(
                id="demo_straddle_spy_001",
                name="SPY Short Straddle",
                symbol="SPY",
                strategy_type="short_straddle",
                legs=[
                    {"type": "call", "strike": 580, "action": "sell", "quantity": 1},
                    {"type": "put", "strike": 580, "action": "sell", "quantity": 1}
                ],
                entry_price=8.50,
                max_profit=850.0,
                max_loss=-999999.0,  # محدود نظرياً فقط
                probability_of_profit=0.65,
                delta=0.0,
                theta=15.5,
                vega=-45.2,
                confidence=0.70,
                expiration=(datetime.now() + timedelta(days=21)).isoformat(),
                created_at=datetime.now().isoformat()
            )
        ]

        # تصفية
        filtered = [s for s in demo_strategies if s.probability_of_profit >= min_prob]
        if symbol:
            filtered = [s for s in filtered if s.symbol == symbol]
        if strategy_type:
            filtered = [s for s in filtered if s.strategy_type == strategy_type]

        return filtered

    async def backtest_strategy(
        self,
        strategy: OptionsStrategy,
        start_date: str,
        end_date: str
    ) -> BacktestResult:
        """
        اختبار استراتيجية بالبيانات التاريخية

        Args:
            strategy: الاستراتيجية للاختبار
            start_date: تاريخ البداية (YYYY-MM-DD)
            end_date: تاريخ النهاية (YYYY-MM-DD)
        """
        if self.is_demo:
            return self._get_demo_backtest(strategy, start_date, end_date)

        await self._ensure_session()

        try:
            payload = {
                "strategy_id": strategy.id,
                "start_date": start_date,
                "end_date": end_date
            }

            async with self.session.post(f"{self.base_url}/backtest", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return BacktestResult(**data)
                else:
                    logger.error(f"Backtest API Error: {resp.status}")
                    return None

        except Exception as e:
            logger.error(f"Error backtesting: {e}")
            return None

    def _get_demo_backtest(self, strategy: OptionsStrategy, start_date: str, end_date: str) -> BacktestResult:
        """نتائج backtest تجريبية"""
        import random
        random.seed(hash(strategy.id))

        total_trades = random.randint(50, 200)
        win_rate = strategy.probability_of_profit + random.uniform(-0.05, 0.05)
        winning_trades = int(total_trades * win_rate)
        losing_trades = total_trades - winning_trades

        avg_win = strategy.max_profit * 0.7
        avg_loss = abs(strategy.max_loss) * 0.3
        total_return = (winning_trades * avg_win) - (losing_trades * avg_loss)

        return BacktestResult(
            strategy_id=strategy.id,
            start_date=start_date,
            end_date=end_date,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            max_drawdown=abs(strategy.max_loss) * 1.5,
            sharpe_ratio=random.uniform(1.2, 2.5),
            trades=[]  # يمكن إضافة تفاصيل الصفقات لاحقاً
        )

    async def get_position_monitoring(self, position_id: str) -> Dict:
        """
        مراقبة موقف خيارات مفتوح

        Returns:
            معلومات فورية عن الموقف (P&L, Greeks, إلخ)
        """
        if self.is_demo:
            return {
                "position_id": position_id,
                "current_value": 2.35,
                "entry_value": 2.50,
                "pnl": -15.0,
                "pnl_pct": -6.0,
                "delta": 0.03,
                "theta": 7.8,
                "vega": -11.5,
                "days_to_expiration": 42,
                "probability_of_profit": 0.74,
                "updated_at": datetime.now().isoformat()
            }

        await self._ensure_session()

        try:
            async with self.session.get(f"{self.base_url}/positions/{position_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"Position monitoring error: {resp.status}")
                    return {}

        except Exception as e:
            logger.error(f"Error monitoring position: {e}")
            return {}

    async def execute_strategy(self, strategy: OptionsStrategy, quantity: int = 1) -> Dict:
        """
        تنفيذ استراتيجية خيارات (paper trading في الوضع التجريبي)

        Args:
            strategy: الاستراتيجية للتنفيذ
            quantity: عدد العقود
        """
        if self.is_demo:
            logger.info(f"📝 DEMO: Executing {strategy.name}")
            return {
                "order_id": f"demo_order_{int(datetime.now().timestamp())}",
                "strategy_id": strategy.id,
                "status": "FILLED",
                "filled_price": strategy.entry_price,
                "quantity": quantity,
                "mode": "PAPER_TRADING",
                "timestamp": datetime.now().isoformat()
            }

        await self._ensure_session()

        try:
            payload = {
                "strategy_id": strategy.id,
                "quantity": quantity,
                "order_type": "MARKET"
            }

            async with self.session.post(f"{self.base_url}/execute", json=payload) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"Execution error: {resp.status}")
                    return {"status": "FAILED"}

        except Exception as e:
            logger.error(f"Error executing strategy: {e}")
            return {"status": "ERROR", "message": str(e)}


# Singleton instance
_option_alpha_client = None


def get_option_alpha_client(api_key: Optional[str] = None) -> OptionAlphaClient:
    """الحصول على singleton instance"""
    global _option_alpha_client
    if _option_alpha_client is None:
        _option_alpha_client = OptionAlphaClient(api_key)
    return _option_alpha_client


async def test_client():
    """اختبار سريع للعميل"""
    client = get_option_alpha_client()

    print("="*60)
    print("🧪 Testing Option Alpha Client")
    print("="*60)

    # 1. الحصول على استراتيجيات
    print("\n1. Fetching strategies for SPY...")
    strategies = await client.get_strategies("SPY", min_probability=0.65)
    print(f"   Found {len(strategies)} strategies")

    for s in strategies:
        print(f"\n   • {s.name}")
        print(f"     Type: {s.strategy_type}")
        print(f"     Prob of Profit: {s.probability_of_profit*100:.1f}%")
        print(f"     Max Profit: ${s.max_profit:.2f}")
        print(f"     Confidence: {s.confidence*100:.1f}%")

    # 2. Backtesting
    if strategies:
        print(f"\n2. Backtesting {strategies[0].name}...")
        backtest = await client.backtest_strategy(
            strategies[0],
            start_date="2024-01-01",
            end_date="2026-03-07"
        )
        print(f"   Total Trades: {backtest.total_trades}")
        print(f"   Win Rate: {backtest.win_rate*100:.1f}%")
        print(f"   Total Return: ${backtest.total_return:.2f}")
        print(f"   Sharpe Ratio: {backtest.sharpe_ratio:.2f}")

    # 3. تنفيذ تجريبي
    if strategies:
        print(f"\n3. Executing {strategies[0].name} (DEMO)...")
        result = await client.execute_strategy(strategies[0])
        print(f"   Order ID: {result['order_id']}")
        print(f"   Status: {result['status']}")

    await client.close()

    print("\n" + "="*60)
    print("✅ Client test completed")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_client())
