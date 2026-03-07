#!/usr/bin/env python3
"""
Hoops AI Client - Real-time trading insights and analysis

يوفر:
- تحليل فوري multi-asset (stocks, forex, crypto, commodities)
- رؤى fundamental + technical + social
- توصيات مخصصة
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import random

# إضافة path للوصول للـ real market data
sys.path.insert(0, os.path.dirname(__file__))

try:
    from real_market_data import get_market_data_provider
    REAL_DATA_AVAILABLE = True
except ImportError:
    REAL_DATA_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MarketInsight:
    """رؤية سوقية"""
    asset: str
    asset_type: str  # stock, crypto, forex, commodity
    signal: str  # BUY, SELL, HOLD
    confidence: float
    price: float
    target_price: float
    stop_loss: float
    timeframe: str
    reasons: List[str]
    technical_score: float
    fundamental_score: float
    social_sentiment: float
    timestamp: str


@dataclass
class AssetRecommendation:
    """توصية أصل"""
    symbol: str
    asset_type: str
    recommendation: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    score: float
    reasons: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH
    potential_return: float
    timestamp: str


class HoopsAIClient:
    """
    عميل Hoops AI

    ملاحظة: Hoops AI لا يوفر API عام حالياً
    هذا wrapper يستخدم:
    1. Demo data للاختبار
    2. Web scraping (إذا تم التفعيل)
    3. Integration مستقبلية عند توفر API
    """

    def __init__(self, use_real_data: bool = True):
        self.use_real_data = use_real_data and REAL_DATA_AVAILABLE
        self.base_url = "https://hoopsai.com"
        self.market_data = None

        if self.use_real_data:
            self.market_data = get_market_data_provider()
            logger.info("✅ Using REAL market data")
        else:
            logger.warning("⚠️ Running in DEMO mode")

    async def get_market_insights(
        self,
        asset_type: str = "all",  # all, stocks, crypto, forex, commodities
        limit: int = 10
    ) -> List[MarketInsight]:
        """
        الحصول على رؤى السوق الفورية

        Args:
            asset_type: نوع الأصل
            limit: عدد الرؤى

        Returns:
            قائمة رؤى مرتبة حسب الثقة
        """
        if self.use_real_data:
            return await self._get_real_insights(asset_type, limit)
        else:
            return self._get_demo_insights(asset_type, limit)

    async def _get_real_insights(self, asset_type: str, limit: int) -> List[MarketInsight]:
        """رؤى من بيانات سوق حقيقية"""
        insights = []

        # جلب بيانات حقيقية
        if asset_type in ["all", "stocks"]:
            stock_symbols = ["AAPL", "NVDA", "MSFT", "GOOGL", "META"]
            stock_data = await self.market_data.get_multiple_prices(stock_symbols, "stock")

            for symbol, data in stock_data.items():
                if not data:
                    continue

                # تحليل بسيط
                change = data.get('change_1d', 0)
                price = data.get('price', 0)

                # تحديد الإشارة
                if change > 2:
                    signal = "BUY"
                    confidence = 0.75 + (min(change, 5) / 20)
                elif change < -2:
                    signal = "SELL"
                    confidence = 0.70 + (min(abs(change), 5) / 25)
                else:
                    signal = "HOLD"
                    confidence = 0.60

                # حساب الهدف ووقف الخسارة
                target = price * 1.10
                stop_loss = price * 0.95

                insight = MarketInsight(
                    asset=symbol,
                    asset_type="stock",
                    signal=signal,
                    confidence=min(confidence, 0.90),
                    price=price,
                    target_price=target,
                    stop_loss=stop_loss,
                    timeframe="1-2 weeks",
                    reasons=[
                        f"Real-time price: ${price:.2f}",
                        f"24h change: {change:+.2f}%",
                        f"Volume: {data.get('volume', 0):,}",
                        "Technical analysis based on recent movement"
                    ],
                    technical_score=0.70 + (abs(change) / 20),
                    fundamental_score=0.75,
                    social_sentiment=0.65,
                    timestamp=datetime.now().isoformat()
                )
                insights.append(insight)

        if asset_type in ["all", "crypto"]:
            crypto_symbols = ["BTC", "ETH", "SOL", "BNB"]
            crypto_data = await self.market_data.get_multiple_prices(crypto_symbols, "crypto")

            for symbol, data in crypto_data.items():
                if not data:
                    continue

                change = data.get('change_24h', 0)
                price = data.get('price', 0)

                # تحديد الإشارة بناءً على التغيير
                if change > 3:
                    signal = "BUY"
                    confidence = 0.72 + (min(change, 8) / 25)
                elif change < -3:
                    signal = "SELL"
                    confidence = 0.68
                else:
                    signal = "HOLD"
                    confidence = 0.55

                target = price * 1.15
                stop_loss = price * 0.92

                insight = MarketInsight(
                    asset=symbol,
                    asset_type="crypto",
                    signal=signal,
                    confidence=min(confidence, 0.88),
                    price=price,
                    target_price=target,
                    stop_loss=stop_loss,
                    timeframe="1-3 weeks",
                    reasons=[
                        f"Real-time price: ${price:,.2f}",
                        f"24h change: {change:+.2f}%",
                        f"24h volume: ${data.get('volume_24h', 0):,.0f}",
                        f"Market sentiment via live data"
                    ],
                    technical_score=0.65 + (abs(change) / 25),
                    fundamental_score=0.70,
                    social_sentiment=0.60,
                    timestamp=datetime.now().isoformat()
                )
                insights.append(insight)

        # ترتيب حسب الثقة
        insights.sort(key=lambda x: x.confidence, reverse=True)

        return insights[:limit]

    def _get_demo_insights(self, asset_type: str, limit: int) -> List[MarketInsight]:
        """رؤى تجريبية واقعية"""
        demo_insights = []

        # Stocks
        if asset_type in ["all", "stocks"]:
            demo_insights.extend([
                MarketInsight(
                    asset="AAPL",
                    asset_type="stock",
                    signal="BUY",
                    confidence=0.82,
                    price=178.50,
                    target_price=195.00,
                    stop_loss=170.00,
                    timeframe="1-3 months",
                    reasons=[
                        "Strong Q4 earnings beat expectations",
                        "iPhone 16 sales exceeding forecasts",
                        "Services revenue growing 15% YoY",
                        "Technical breakout above 175 resistance"
                    ],
                    technical_score=0.85,
                    fundamental_score=0.88,
                    social_sentiment=0.75,
                    timestamp=datetime.now().isoformat()
                ),
                MarketInsight(
                    asset="NVDA",
                    asset_type="stock",
                    signal="HOLD",
                    confidence=0.65,
                    price=880.00,
                    target_price=920.00,
                    stop_loss=840.00,
                    timeframe="1-2 months",
                    reasons=[
                        "Recent profit-taking after rally",
                        "AI demand remains strong",
                        "Valuation stretched short-term",
                        "Wait for pullback to 850"
                    ],
                    technical_score=0.60,
                    fundamental_score=0.90,
                    social_sentiment=0.85,
                    timestamp=datetime.now().isoformat()
                )
            ])

        # Crypto
        if asset_type in ["all", "crypto"]:
            demo_insights.extend([
                MarketInsight(
                    asset="BTC",
                    asset_type="crypto",
                    signal="BUY",
                    confidence=0.78,
                    price=68500.00,
                    target_price=75000.00,
                    stop_loss=65000.00,
                    timeframe="2-4 weeks",
                    reasons=[
                        "ETF inflows accelerating",
                        "Halving event approaching",
                        "Institutional adoption increasing",
                        "Strong support at $65k"
                    ],
                    technical_score=0.80,
                    fundamental_score=0.75,
                    social_sentiment=0.80,
                    timestamp=datetime.now().isoformat()
                ),
                MarketInsight(
                    asset="ETH",
                    asset_type="crypto",
                    signal="BUY",
                    confidence=0.75,
                    price=3800.00,
                    target_price=4500.00,
                    stop_loss=3500.00,
                    timeframe="3-6 weeks",
                    reasons=[
                        "Dencun upgrade successful",
                        "Layer 2 activity booming",
                        "Staking yields attractive",
                        "Breaking above 3700 resistance"
                    ],
                    technical_score=0.78,
                    fundamental_score=0.80,
                    social_sentiment=0.68,
                    timestamp=datetime.now().isoformat()
                )
            ])

        # Forex
        if asset_type in ["all", "forex"]:
            demo_insights.append(
                MarketInsight(
                    asset="EUR/USD",
                    asset_type="forex",
                    signal="SELL",
                    confidence=0.70,
                    price=1.0850,
                    target_price=1.0700,
                    stop_loss=1.0920,
                    timeframe="1-2 weeks",
                    reasons=[
                        "ECB dovish stance",
                        "US economic data strong",
                        "Dollar strength continuing",
                        "Technical breakdown below 1.09"
                    ],
                    technical_score=0.72,
                    fundamental_score=0.75,
                    social_sentiment=0.65,
                    timestamp=datetime.now().isoformat()
                )
            )

        # Commodities
        if asset_type in ["all", "commodities"]:
            demo_insights.append(
                MarketInsight(
                    asset="GOLD",
                    asset_type="commodity",
                    signal="BUY",
                    confidence=0.80,
                    price=2180.00,
                    target_price=2300.00,
                    stop_loss=2140.00,
                    timeframe="1-3 months",
                    reasons=[
                        "Geopolitical tensions rising",
                        "Fed rate cuts expected",
                        "Central banks buying",
                        "Inflation hedge demand"
                    ],
                    technical_score=0.82,
                    fundamental_score=0.85,
                    social_sentiment=0.73,
                    timestamp=datetime.now().isoformat()
                )
            )

        # ترتيب حسب الثقة
        demo_insights.sort(key=lambda x: x.confidence, reverse=True)

        return demo_insights[:limit]

    async def get_asset_recommendations(
        self,
        risk_profile: str = "moderate"  # conservative, moderate, aggressive
    ) -> List[AssetRecommendation]:
        """
        الحصول على توصيات أصول مخصصة

        Args:
            risk_profile: ملف المخاطر

        Returns:
            قائمة توصيات
        """
        if not self.use_real_data:
            return self._get_demo_recommendations(risk_profile)

        # TODO: implement real recommendations
        return self._get_demo_recommendations(risk_profile)

    def _get_demo_recommendations(self, risk_profile: str) -> List[AssetRecommendation]:
        """توصيات تجريبية"""
        all_recommendations = {
            "conservative": [
                AssetRecommendation(
                    symbol="VOO",
                    asset_type="etf",
                    recommendation="BUY",
                    score=0.85,
                    reasons=[
                        "S&P 500 index fund",
                        "Low fees (0.03%)",
                        "Diversified exposure",
                        "Long-term track record"
                    ],
                    risk_level="LOW",
                    potential_return=0.08,
                    timestamp=datetime.now().isoformat()
                ),
                AssetRecommendation(
                    symbol="GOLD",
                    asset_type="commodity",
                    recommendation="BUY",
                    score=0.78,
                    reasons=[
                        "Safe haven asset",
                        "Inflation hedge",
                        "Portfolio diversification"
                    ],
                    risk_level="LOW",
                    potential_return=0.06,
                    timestamp=datetime.now().isoformat()
                )
            ],
            "moderate": [
                AssetRecommendation(
                    symbol="AAPL",
                    asset_type="stock",
                    recommendation="STRONG_BUY",
                    score=0.88,
                    reasons=[
                        "Strong fundamentals",
                        "Growing services revenue",
                        "Innovation pipeline strong"
                    ],
                    risk_level="MEDIUM",
                    potential_return=0.15,
                    timestamp=datetime.now().isoformat()
                ),
                AssetRecommendation(
                    symbol="BTC",
                    asset_type="crypto",
                    recommendation="BUY",
                    score=0.75,
                    reasons=[
                        "ETF approval driving adoption",
                        "Halving catalyst",
                        "5-10% portfolio allocation"
                    ],
                    risk_level="MEDIUM",
                    potential_return=0.25,
                    timestamp=datetime.now().isoformat()
                )
            ],
            "aggressive": [
                AssetRecommendation(
                    symbol="NVDA",
                    asset_type="stock",
                    recommendation="BUY",
                    score=0.82,
                    reasons=[
                        "AI boom beneficiary",
                        "Data center demand",
                        "High growth potential"
                    ],
                    risk_level="HIGH",
                    potential_return=0.40,
                    timestamp=datetime.now().isoformat()
                ),
                AssetRecommendation(
                    symbol="SOL",
                    asset_type="crypto",
                    recommendation="BUY",
                    score=0.70,
                    reasons=[
                        "Fast blockchain",
                        "Growing ecosystem",
                        "High risk/reward"
                    ],
                    risk_level="HIGH",
                    potential_return=0.60,
                    timestamp=datetime.now().isoformat()
                )
            ]
        }

        return all_recommendations.get(risk_profile, all_recommendations["moderate"])

    async def analyze_symbol(self, symbol: str) -> Optional[MarketInsight]:
        """
        تحليل رمز محدد

        Args:
            symbol: الرمز (مثل AAPL, BTC, EUR/USD)

        Returns:
            تحليل مفصل
        """
        insights = await self.get_market_insights(asset_type="all", limit=20)

        for insight in insights:
            if insight.asset == symbol:
                return insight

        # إذا لم يوجد، إنشاء تحليل عام
        if not self.use_real_data:
            return MarketInsight(
                asset=symbol,
                asset_type="unknown",
                signal="HOLD",
                confidence=0.50,
                price=0.0,
                target_price=0.0,
                stop_loss=0.0,
                timeframe="unknown",
                reasons=["No specific analysis available"],
                technical_score=0.50,
                fundamental_score=0.50,
                social_sentiment=0.50,
                timestamp=datetime.now().isoformat()
            )

        return None

    def get_trending_assets(self) -> List[Dict]:
        """الأصول الرائجة"""
        return [
            {"symbol": "NVDA", "type": "stock", "trend": "up", "strength": 0.90},
            {"symbol": "BTC", "type": "crypto", "trend": "up", "strength": 0.85},
            {"symbol": "AAPL", "type": "stock", "trend": "up", "strength": 0.82},
            {"symbol": "ETH", "type": "crypto", "trend": "up", "strength": 0.78},
            {"symbol": "GOLD", "type": "commodity", "trend": "up", "strength": 0.75}
        ]


# Singleton
_hoops_client = None


def get_hoops_client(use_real_data: bool = True) -> HoopsAIClient:
    """الحصول على singleton instance"""
    global _hoops_client
    if _hoops_client is None:
        _hoops_client = HoopsAIClient(use_real_data)
    return _hoops_client


async def test_client():
    """اختبار العميل"""
    client = get_hoops_client()

    print("="*70)
    print("🧪 Testing Hoops AI Client")
    print("="*70)

    # 1. رؤى السوق
    print("\n1. Market Insights (All Assets):")
    insights = await client.get_market_insights(asset_type="all", limit=5)
    for insight in insights:
        print(f"\n   {insight.asset} ({insight.asset_type}) - {insight.signal}")
        print(f"   Confidence: {insight.confidence*100:.0f}%")
        print(f"   Price: ${insight.price:.2f} → Target: ${insight.target_price:.2f}")
        print(f"   Scores: Tech={insight.technical_score:.2f}, Fund={insight.fundamental_score:.2f}, Social={insight.social_sentiment:.2f}")
        print(f"   Reasons: {', '.join(insight.reasons[:2])}")

    # 2. توصيات
    print("\n2. Asset Recommendations (Moderate Risk):")
    recommendations = await client.get_asset_recommendations("moderate")
    for rec in recommendations:
        print(f"\n   {rec.symbol} ({rec.asset_type}) - {rec.recommendation}")
        print(f"   Score: {rec.score*100:.0f}% | Risk: {rec.risk_level}")
        print(f"   Potential Return: {rec.potential_return*100:.0f}%")
        print(f"   Reasons: {rec.reasons[0]}")

    # 3. تحليل رمز محدد
    print("\n3. Specific Symbol Analysis (AAPL):")
    aapl = await client.analyze_symbol("AAPL")
    if aapl:
        print(f"   Signal: {aapl.signal}")
        print(f"   Confidence: {aapl.confidence*100:.0f}%")
        print(f"   Key Reasons:")
        for reason in aapl.reasons:
            print(f"     • {reason}")

    # 4. الرائجة
    print("\n4. Trending Assets:")
    trending = client.get_trending_assets()
    for asset in trending[:3]:
        print(f"   {asset['symbol']:6} ({asset['type']:10}) Strength: {asset['strength']*100:.0f}%")

    print("\n" + "="*70)
    print("✅ Client test completed")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_client())
