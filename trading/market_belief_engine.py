"""
Market Belief Engine - محرك معتقدات السوق
==========================================

يحول بيانات السوق وتحليلاتها إلى معتقدات (Beliefs) في WorldModel.
Converts market data and analysis into beliefs in the WorldModel.

Features:
- Observes market conditions and creates beliefs
- Tracks belief confidence based on outcomes
- Falsifies beliefs when predictions fail
- Integrates with trading events for validation

Usage:
    from trading.market_belief_engine import MarketBeliefEngine

    engine = MarketBeliefEngine()
    await engine.setup()

    # Observe market data
    await engine.observe_market("BTCUSDT", df)

    # Validate beliefs with trade outcomes
    await engine.validate_beliefs_from_trade(trade_result)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import pandas as pd

from unified_core.core.world_model import WorldModel

logger = logging.getLogger(__name__)


class MarketBeliefEngine:
    """
    محرك معتقدات السوق - Market Belief Engine

    يحلل بيانات السوق وينشئ beliefs في WorldModel:
    - Trend beliefs (اتجاه صاعد/هابط)
    - Volatility beliefs (تقلب عالي/منخفض)
    - Correlation beliefs (ارتباط مع BTC)
    - Regime beliefs (نظام السوق)
    - Pattern beliefs (أنماط سعرية)
    """

    def __init__(self):
        """Initialize Market Belief Engine."""
        self.world_model = WorldModel()
        self._active_beliefs: Dict[str, str] = {}  # symbol -> belief_id mapping
        self._prediction_map: Dict[str, List[str]] = {}  # prediction_id -> belief_ids

        logger.info("MarketBeliefEngine initialized")

    async def setup(self):
        """Setup the engine."""
        await self.world_model.setup()
        logger.info("MarketBeliefEngine ready")

    async def observe_market(
        self,
        symbol: str,
        df: pd.DataFrame,
        additional_context: Optional[Dict] = None
    ) -> List[str]:
        """
        مراقبة السوق وإنشاء beliefs.
        Observe market and create beliefs.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            df: OHLCV DataFrame with indicators
            additional_context: Extra context (correlations, funding, etc.)

        Returns:
            List of belief IDs created
        """
        if df.empty or len(df) < 20:
            logger.warning(f"Insufficient data for {symbol}")
            return []

        beliefs_created = []
        context = additional_context or {}

        # 1. Trend Belief
        trend_belief_id = await self._create_trend_belief(symbol, df)
        if trend_belief_id:
            beliefs_created.append(trend_belief_id)

        # 2. Volatility Belief
        vol_belief_id = await self._create_volatility_belief(symbol, df)
        if vol_belief_id:
            beliefs_created.append(vol_belief_id)

        # 3. Momentum Belief
        momentum_belief_id = await self._create_momentum_belief(symbol, df)
        if momentum_belief_id:
            beliefs_created.append(momentum_belief_id)

        # 4. Correlation Belief (if BTC context provided)
        if 'btc_correlation' in context:
            corr_belief_id = await self._create_correlation_belief(
                symbol, context['btc_correlation']
            )
            if corr_belief_id:
                beliefs_created.append(corr_belief_id)

        # 5. Regime Belief
        regime_belief_id = await self._create_regime_belief(symbol, df, context)
        if regime_belief_id:
            beliefs_created.append(regime_belief_id)

        # Store active beliefs for this symbol
        if beliefs_created:
            self._active_beliefs[symbol] = beliefs_created[-1]
            logger.info(f"Created {len(beliefs_created)} beliefs for {symbol}")

        return beliefs_created

    async def _create_trend_belief(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> Optional[str]:
        """Create trend belief from price action."""
        try:
            latest = df.iloc[-1]
            prev_20 = df.iloc[-20]

            price_change = (latest['close'] - prev_20['close']) / prev_20['close']

            # Determine trend
            if price_change > 0.05:  # +5% over 20 periods
                direction = "صاعد قوي"
                confidence = min(0.6 + abs(price_change), 0.95)
            elif price_change > 0.02:  # +2%
                direction = "صاعد"
                confidence = min(0.5 + abs(price_change), 0.85)
            elif price_change < -0.05:  # -5%
                direction = "هابط قوي"
                confidence = min(0.6 + abs(price_change), 0.95)
            elif price_change < -0.02:  # -2%
                direction = "هابط"
                confidence = min(0.5 + abs(price_change), 0.85)
            else:
                direction = "متذبذب"
                confidence = 0.6

            proposition = f"{symbol} في اتجاه {direction} (تغير {price_change*100:.1f}%)"

            belief = await self.world_model.add_belief(
                proposition,
                initial_confidence=confidence
            )

            return belief.belief_id

        except Exception as e:
            logger.error(f"Error creating trend belief: {e}")
            return None

    async def _create_volatility_belief(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> Optional[str]:
        """Create volatility belief."""
        try:
            # Calculate recent volatility
            if 'atr' in df.columns:
                recent_atr = df['atr'].iloc[-5:].mean()
                avg_atr = df['atr'].mean()

                if recent_atr > avg_atr * 1.5:
                    level = "عالي جداً"
                    confidence = 0.85
                elif recent_atr > avg_atr * 1.2:
                    level = "عالي"
                    confidence = 0.75
                elif recent_atr < avg_atr * 0.7:
                    level = "منخفض"
                    confidence = 0.75
                else:
                    level = "متوسط"
                    confidence = 0.65

                proposition = f"{symbol} لديه تقلب {level}"

                belief = await self.world_model.add_belief(
                    proposition,
                    initial_confidence=confidence
                )

                return belief.belief_id

        except Exception as e:
            logger.error(f"Error creating volatility belief: {e}")
            return None

    async def _create_momentum_belief(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> Optional[str]:
        """Create momentum belief from RSI/volume."""
        try:
            if 'rsi' not in df.columns:
                return None

            latest_rsi = df['rsi'].iloc[-1]
            latest_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].mean()

            # Volume confirmation
            volume_ratio = latest_volume / avg_volume

            if latest_rsi > 70:
                if volume_ratio > 1.5:
                    state = "زخم شراء قوي مع حجم عالي"
                    confidence = 0.80
                else:
                    state = "تشبع شرائي"
                    confidence = 0.70
            elif latest_rsi < 30:
                if volume_ratio > 1.5:
                    state = "زخم بيع قوي مع حجم عالي"
                    confidence = 0.80
                else:
                    state = "تشبع بيعي"
                    confidence = 0.70
            elif 45 < latest_rsi < 55:
                state = "متوازن"
                confidence = 0.65
            else:
                state = "محايد"
                confidence = 0.60

            proposition = f"{symbol} في حالة {state} (RSI: {latest_rsi:.1f})"

            belief = await self.world_model.add_belief(
                proposition,
                initial_confidence=confidence
            )

            return belief.belief_id

        except Exception as e:
            logger.error(f"Error creating momentum belief: {e}")
            return None

    async def _create_correlation_belief(
        self,
        symbol: str,
        correlation: float
    ) -> Optional[str]:
        """Create BTC correlation belief."""
        try:
            if abs(correlation) > 0.8:
                strength = "قوي جداً"
                confidence = 0.90
            elif abs(correlation) > 0.6:
                strength = "قوي"
                confidence = 0.80
            elif abs(correlation) > 0.4:
                strength = "متوسط"
                confidence = 0.70
            else:
                strength = "ضعيف"
                confidence = 0.60

            direction = "إيجابي" if correlation > 0 else "سلبي"

            proposition = f"{symbol} لديه ارتباط {direction} {strength} مع BTC ({correlation:.2f})"

            belief = await self.world_model.add_belief(
                proposition,
                initial_confidence=confidence
            )

            return belief.belief_id

        except Exception as e:
            logger.error(f"Error creating correlation belief: {e}")
            return None

    async def _create_regime_belief(
        self,
        symbol: str,
        df: pd.DataFrame,
        context: Dict
    ) -> Optional[str]:
        """Create market regime belief."""
        try:
            # Simple regime detection
            latest = df.iloc[-1]
            recent_range = df.iloc[-20:]

            # Check if ranging or trending
            high_low_range = (recent_range['high'].max() - recent_range['low'].min()) / latest['close']

            if high_low_range < 0.05:  # Less than 5% range
                regime = "ضمن نطاق ضيق"
                confidence = 0.75
            elif high_low_range > 0.15:  # More than 15% range
                regime = "متقلب للغاية"
                confidence = 0.80
            else:
                # Check trend strength
                sma_20 = recent_range['close'].mean()
                if latest['close'] > sma_20 * 1.03:
                    regime = "اتجاه صاعد نشط"
                    confidence = 0.75
                elif latest['close'] < sma_20 * 0.97:
                    regime = "اتجاه هابط نشط"
                    confidence = 0.75
                else:
                    regime = "تماسك"
                    confidence = 0.65

            proposition = f"السوق ({symbol}) في نظام {regime}"

            belief = await self.world_model.add_belief(
                proposition,
                initial_confidence=confidence
            )

            return belief.belief_id

        except Exception as e:
            logger.error(f"Error creating regime belief: {e}")
            return None

    async def validate_beliefs_from_trade(
        self,
        symbol: str,
        direction: str,
        pnl: float,
        entry_beliefs: Optional[List[str]] = None
    ):
        """
        التحقق من beliefs بناءً على نتيجة الصفقة.
        Validate beliefs based on trade outcome.

        Args:
            symbol: Trading pair
            direction: Trade direction (LONG/SHORT)
            pnl: Profit/Loss
            entry_beliefs: List of belief IDs that led to the trade
        """
        try:
            # If trade was profitable, beliefs were correct
            # If trade lost, beliefs might be wrong - falsify them

            if pnl < 0 and entry_beliefs:
                logger.info(f"Trade loss on {symbol}: falsifying {len(entry_beliefs)} beliefs")

                # Create prediction for falsification
                prediction = await self.world_model.predict(
                    f"{direction} trade on {symbol}",
                    based_on=entry_beliefs
                )

                # Falsify with actual outcome
                await self.world_model.falsify(
                    prediction.prediction_id,
                    {
                        "success": False,
                        "pnl": pnl,
                        "reason": f"Trade resulted in loss of ${abs(pnl):.2f}"
                    }
                )

                logger.info(f"Falsified prediction {prediction.prediction_id[:8]}")

        except Exception as e:
            logger.error(f"Error validating beliefs: {e}")

    async def get_market_summary(self, symbol: str) -> Dict:
        """
        الحصول على ملخص معتقدات السوق لرمز معين.
        Get market beliefs summary for a symbol.
        """
        try:
            # Get all beliefs
            all_beliefs = await self.world_model.get_usable_beliefs()

            # Filter beliefs for this symbol
            symbol_beliefs = [
                b for b in all_beliefs
                if symbol in b.proposition
            ]

            if not symbol_beliefs:
                return {
                    "symbol": symbol,
                    "beliefs_count": 0,
                    "summary": "No beliefs available"
                }

            # Categorize beliefs
            categories = {
                "trend": [],
                "volatility": [],
                "momentum": [],
                "correlation": [],
                "regime": []
            }

            for belief in symbol_beliefs:
                prop = belief.proposition
                if "اتجاه" in prop:
                    categories["trend"].append(belief)
                elif "تقلب" in prop:
                    categories["volatility"].append(belief)
                elif "زخم" in prop or "RSI" in prop:
                    categories["momentum"].append(belief)
                elif "ارتباط" in prop:
                    categories["correlation"].append(belief)
                elif "نظام" in prop or "تماسك" in prop:
                    categories["regime"].append(belief)

            # Build summary
            summary_lines = []
            for category, beliefs in categories.items():
                if beliefs:
                    highest_conf = max(beliefs, key=lambda b: b.confidence)
                    summary_lines.append(
                        f"{category.title()}: {highest_conf.proposition[:60]} "
                        f"(conf: {highest_conf.confidence:.2f})"
                    )

            return {
                "symbol": symbol,
                "beliefs_count": len(symbol_beliefs),
                "categories": {k: len(v) for k, v in categories.items()},
                "summary": "\n".join(summary_lines) if summary_lines else "No clear beliefs"
            }

        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {
                "symbol": symbol,
                "error": str(e)
            }


# ============================================================
#  Singleton Instance
# ============================================================

_market_belief_engine: Optional[MarketBeliefEngine] = None


def get_market_belief_engine() -> MarketBeliefEngine:
    """Get singleton Market Belief Engine instance."""
    global _market_belief_engine
    if _market_belief_engine is None:
        _market_belief_engine = MarketBeliefEngine()
    return _market_belief_engine
