#!/usr/bin/env python3
"""
Potato AI Client - Thematic Investing Platform

يوفر:
- استثمار موضوعي (AI, Green Energy, Robotics, etc.)
- محافظ مخصصة
- تتبع اتجاهات السوق
- دعم multi-asset (stocks, forex, crypto)
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Theme:
    """موضوع استثماري"""
    id: str
    name: str
    description: str
    category: str
    trend_score: float
    growth_potential: float
    risk_level: str
    assets: List[Dict]
    performance_1m: float
    performance_3m: float
    performance_1y: float


@dataclass
class ThematicPortfolio:
    """محفظة موضوعية"""
    id: str
    theme_id: str
    theme_name: str
    assets: List[Dict]
    total_value: float
    allocation: Dict[str, float]
    performance: Dict[str, float]
    rebalance_needed: bool
    created_at: str


class PotatoAIClient:
    """
    عميل Potato AI

    ملاحظة: Potato API قيد التطوير
    هذا wrapper يستخدم demo data مع إمكانية التوسع
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("POTATO_API_KEY", "DEMO_KEY")
        self.base_url = "https://api.potato.trade/v1"
        self.is_demo = self.api_key == "DEMO_KEY"

        if self.is_demo:
            logger.warning("⚠️ Running in DEMO mode. Potato AI API integration pending.")

    async def get_trending_themes(self, min_score: float = 0.70) -> List[Theme]:
        """
        الحصول على المواضيع الرائجة

        Args:
            min_score: الحد الأدنى لنقاط الاتجاه

        Returns:
            قائمة مواضيع مرتبة حسب الاتجاه
        """
        if self.is_demo:
            return self._get_demo_themes(min_score)

        # TODO: API implementation
        return []

    def _get_demo_themes(self, min_score: float) -> List[Theme]:
        """مواضيع تجريبية"""
        all_themes = [
            Theme(
                id="ai_revolution",
                name="AI Revolution",
                description="Companies leading AI transformation",
                category="Technology",
                trend_score=0.95,
                growth_potential=0.90,
                risk_level="HIGH",
                assets=[
                    {"symbol": "NVDA", "type": "stock", "allocation": 0.30, "reason": "GPU leader"},
                    {"symbol": "MSFT", "type": "stock", "allocation": 0.25, "reason": "OpenAI investment"},
                    {"symbol": "GOOGL", "type": "stock", "allocation": 0.20, "reason": "Gemini AI"},
                    {"symbol": "META", "type": "stock", "allocation": 0.15, "reason": "LLaMA models"},
                    {"symbol": "AMD", "type": "stock", "allocation": 0.10, "reason": "AI chips"}
                ],
                performance_1m=0.12,
                performance_3m=0.35,
                performance_1y=0.85
            ),
            Theme(
                id="crypto_adoption",
                name="Crypto Mainstream Adoption",
                description="Cryptocurrencies gaining institutional acceptance",
                category="Crypto",
                trend_score=0.88,
                growth_potential=0.85,
                risk_level="HIGH",
                assets=[
                    {"symbol": "BTC", "type": "crypto", "allocation": 0.40, "reason": "ETF approval"},
                    {"symbol": "ETH", "type": "crypto", "allocation": 0.30, "reason": "DeFi ecosystem"},
                    {"symbol": "SOL", "type": "crypto", "allocation": 0.15, "reason": "Fast blockchain"},
                    {"symbol": "COIN", "type": "stock", "allocation": 0.15, "reason": "Crypto exchange"}
                ],
                performance_1m=0.08,
                performance_3m=0.25,
                performance_1y=0.120
            ),
            Theme(
                id="green_energy",
                name="Green Energy Transition",
                description="Renewable energy and sustainability",
                category="Energy",
                trend_score=0.82,
                growth_potential=0.80,
                risk_level="MEDIUM",
                assets=[
                    {"symbol": "TSLA", "type": "stock", "allocation": 0.25, "reason": "EV leader"},
                    {"symbol": "ENPH", "type": "stock", "allocation": 0.20, "reason": "Solar tech"},
                    {"symbol": "NEE", "type": "stock", "allocation": 0.20, "reason": "Clean utility"},
                    {"symbol": "ICLN", "type": "etf", "allocation": 0.20, "reason": "Clean energy ETF"},
                    {"symbol": "TAN", "type": "etf", "allocation": 0.15, "reason": "Solar ETF"}
                ],
                performance_1m=0.05,
                performance_3m=0.15,
                performance_1y=0.32
            ),
            Theme(
                id="robotics_automation",
                name="Robotics & Automation",
                description="Industrial and service robots",
                category="Technology",
                trend_score=0.78,
                growth_potential=0.75,
                risk_level="MEDIUM",
                assets=[
                    {"symbol": "ABB", "type": "stock", "allocation": 0.30, "reason": "Industrial robots"},
                    {"symbol": "ISRG", "type": "stock", "allocation": 0.25, "reason": "Surgical robots"},
                    {"symbol": "ROK", "type": "stock", "allocation": 0.20, "reason": "Factory automation"},
                    {"symbol": "BOTZ", "type": "etf", "allocation": 0.25, "reason": "Robotics ETF"}
                ],
                performance_1m=0.06,
                performance_3m=0.18,
                performance_1y=0.42
            ),
            Theme(
                id="healthcare_innovation",
                name="Healthcare Innovation",
                description="Biotech and digital health",
                category="Healthcare",
                trend_score=0.75,
                growth_potential=0.78,
                risk_level="MEDIUM",
                assets=[
                    {"symbol": "TDOC", "type": "stock", "allocation": 0.25, "reason": "Telemedicine"},
                    {"symbol": "ILMN", "type": "stock", "allocation": 0.25, "reason": "Genomics"},
                    {"symbol": "REGN", "type": "stock", "allocation": 0.20, "reason": "Biotech R&D"},
                    {"symbol": "XBI", "type": "etf", "allocation": 0.30, "reason": "Biotech ETF"}
                ],
                performance_1m=0.04,
                performance_3m=0.12,
                performance_1y=0.28
            ),
            Theme(
                id="fintech_revolution",
                name="FinTech Revolution",
                description="Digital payments and financial services",
                category="Finance",
                trend_score=0.72,
                growth_potential=0.72,
                risk_level="MEDIUM",
                assets=[
                    {"symbol": "SQ", "type": "stock", "allocation": 0.30, "reason": "Digital payments"},
                    {"symbol": "PYPL", "type": "stock", "allocation": 0.25, "reason": "Payment processor"},
                    {"symbol": "COIN", "type": "stock", "allocation": 0.20, "reason": "Crypto platform"},
                    {"symbol": "FINX", "type": "etf", "allocation": 0.25, "reason": "FinTech ETF"}
                ],
                performance_1m=0.07,
                performance_3m=0.20,
                performance_1y=0.45
            )
        ]

        # تصفية وترتيب
        filtered = [t for t in all_themes if t.trend_score >= min_score]
        filtered.sort(key=lambda t: t.trend_score, reverse=True)

        return filtered

    async def create_thematic_portfolio(
        self,
        theme: Theme,
        budget: float = 10000.0
    ) -> ThematicPortfolio:
        """
        إنشاء محفظة موضوعية

        Args:
            theme: الموضوع
            budget: الميزانية

        Returns:
            محفظة جاهزة
        """
        if self.is_demo:
            return self._create_demo_portfolio(theme, budget)

        # TODO: API implementation
        return None

    def _create_demo_portfolio(self, theme: Theme, budget: float) -> ThematicPortfolio:
        """إنشاء محفظة تجريبية"""
        # توزيع الميزانية حسب التخصيص
        portfolio_assets = []
        for asset in theme.assets:
            allocation_amount = budget * asset["allocation"]
            portfolio_assets.append({
                **asset,
                "invested": allocation_amount,
                "current_value": allocation_amount  # البداية
            })

        # حساب التخصيص النهائي
        allocation = {}
        for asset in portfolio_assets:
            asset_type = asset["type"]
            allocation[asset_type] = allocation.get(asset_type, 0) + asset["allocation"]

        return ThematicPortfolio(
            id=f"portfolio_{theme.id}_{int(datetime.now().timestamp())}",
            theme_id=theme.id,
            theme_name=theme.name,
            assets=portfolio_assets,
            total_value=budget,
            allocation=allocation,
            performance={
                "1m": theme.performance_1m,
                "3m": theme.performance_3m,
                "1y": theme.performance_1y
            },
            rebalance_needed=False,
            created_at=datetime.now().isoformat()
        )

    async def analyze_theme_performance(self, theme: Theme) -> Dict:
        """
        تحليل أداء موضوع

        Returns:
            تحليل مفصل
        """
        # حساب متوسطات
        avg_perf = (theme.performance_1m + theme.performance_3m + theme.performance_1y) / 3

        # تحديد قوة الاتجاه
        if theme.trend_score >= 0.85:
            trend_strength = "VERY_STRONG"
        elif theme.trend_score >= 0.75:
            trend_strength = "STRONG"
        elif theme.trend_score >= 0.65:
            trend_strength = "MODERATE"
        else:
            trend_strength = "WEAK"

        # توصية
        if theme.trend_score >= 0.80 and theme.growth_potential >= 0.75:
            recommendation = "STRONG_BUY"
        elif theme.trend_score >= 0.70:
            recommendation = "BUY"
        elif theme.trend_score >= 0.60:
            recommendation = "HOLD"
        else:
            recommendation = "AVOID"

        return {
            "theme": theme.name,
            "trend_score": theme.trend_score,
            "trend_strength": trend_strength,
            "growth_potential": theme.growth_potential,
            "risk_level": theme.risk_level,
            "avg_performance": avg_perf,
            "recommendation": recommendation,
            "top_assets": theme.assets[:3],
            "diversification": len(theme.assets)
        }

    def compare_themes(self, themes: List[Theme]) -> Dict:
        """مقارنة عدة مواضيع"""
        comparisons = []

        for theme in themes:
            score = (
                theme.trend_score * 0.4 +
                theme.growth_potential * 0.3 +
                theme.performance_1y * 0.3
            )
            comparisons.append({
                "theme": theme.name,
                "overall_score": score,
                "trend": theme.trend_score,
                "growth": theme.growth_potential,
                "performance_1y": theme.performance_1y,
                "risk": theme.risk_level
            })

        comparisons.sort(key=lambda c: c["overall_score"], reverse=True)

        return {
            "total_themes": len(themes),
            "comparisons": comparisons,
            "best_theme": comparisons[0] if comparisons else None
        }


# Singleton
_potato_client = None


def get_potato_client(api_key: Optional[str] = None) -> PotatoAIClient:
    """الحصول على singleton instance"""
    global _potato_client
    if _potato_client is None:
        _potato_client = PotatoAIClient(api_key)
    return _potato_client


async def test_client():
    """اختبار العميل"""
    client = get_potato_client()

    print("="*70)
    print("🧪 Testing Potato AI Client")
    print("="*70)

    # 1. المواضيع الرائجة
    print("\n1. Trending Themes:")
    themes = await client.get_trending_themes(min_score=0.70)
    for i, theme in enumerate(themes, 1):
        print(f"\n   {i}. {theme.name} ({theme.category})")
        print(f"      Trend Score: {theme.trend_score*100:.0f}%")
        print(f"      Growth Potential: {theme.growth_potential*100:.0f}%")
        print(f"      Risk: {theme.risk_level}")
        print(f"      1Y Performance: {theme.performance_1y*100:.0f}%")
        print(f"      Assets: {len(theme.assets)} ({', '.join([a['symbol'] for a in theme.assets[:3]])})")

    # 2. إنشاء محفظة
    if themes:
        print(f"\n2. Creating Portfolio for: {themes[0].name}")
        portfolio = await client.create_thematic_portfolio(themes[0], budget=10000)
        print(f"   Portfolio ID: {portfolio.id}")
        print(f"   Theme: {portfolio.theme_name}")
        print(f"   Total Value: ${portfolio.total_value:.2f}")
        print(f"   Asset Allocation:")
        for asset_type, alloc in portfolio.allocation.items():
            print(f"      {asset_type.capitalize()}: {alloc*100:.1f}%")
        print(f"   Performance:")
        for period, perf in portfolio.performance.items():
            print(f"      {period}: {perf*100:+.1f}%")

    # 3. تحليل أداء
    if themes:
        print(f"\n3. Theme Performance Analysis:")
        analysis = await client.analyze_theme_performance(themes[0])
        print(f"   Theme: {analysis['theme']}")
        print(f"   Trend Strength: {analysis['trend_strength']}")
        print(f"   Recommendation: {analysis['recommendation']}")
        print(f"   Avg Performance: {analysis['avg_performance']*100:.1f}%")
        print(f"   Top Assets:")
        for asset in analysis['top_assets']:
            print(f"      • {asset['symbol']} ({asset['allocation']*100:.0f}%) - {asset['reason']}")

    # 4. مقارنة
    print("\n4. Theme Comparison:")
    comparison = client.compare_themes(themes[:3])
    print(f"   Comparing {comparison['total_themes']} themes:")
    for comp in comparison['comparisons']:
        print(f"\n   • {comp['theme']}")
        print(f"     Overall Score: {comp['overall_score']:.2f}")
        print(f"     Trend: {comp['trend']:.2f} | Growth: {comp['growth']:.2f}")
        print(f"     1Y Performance: {comp['performance_1y']*100:.0f}% | Risk: {comp['risk']}")

    print("\n" + "="*70)
    print("✅ Client test completed")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_client())
