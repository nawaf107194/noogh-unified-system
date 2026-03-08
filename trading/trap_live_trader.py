"""
Trap Live Trader - Production Wrapper
Uses TrapHybridEngine for live/paper trading

Usage:
    from trading.trap_live_trader import TrapLiveTrader

    trader = TrapLiveTrader(
        testnet=True,
        read_only=True,  # Paper trading
        risk_per_trade=0.01
    )

    # Check for signals
    signal = trader.check_signal('BTCUSDT')

    # Execute if signal found
    if signal.signal != 'NONE':
        result = trader.execute_signal(signal)

    # Monitor active positions
    trader.monitor_positions()
"""
import logging
import asyncio
import json
import os
import re
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
from unified_core.neural_bridge import NeuralEngineClient

# EventBus Integration
try:
    from unified_core.integration import get_event_bus, StandardEvents, EventPriority
    _EVENT_BUS_AVAILABLE = True
except ImportError:
    _EVENT_BUS_AVAILABLE = False

from .trap_hybrid_engine import TrapHybridEngine, TrapSignal, TrapPosition, get_trap_hybrid_engine
from .binance_futures import BinanceFuturesManager, get_futures_manager
from .market_belief_engine import MarketBeliefEngine, get_market_belief_engine

# NeuronFabric Integration
try:
    from unified_core.core.neuron_fabric import get_neuron_fabric, NeuronType
    _NEURON_FABRIC_AVAILABLE = True
except ImportError:
    _NEURON_FABRIC_AVAILABLE = False
    logger.warning("NeuronFabric not available")

# AMLA Integration
try:
    from unified_core.core.amla import get_amla, AMLAActionRequest, AMLAVerdict
    _AMLA_AVAILABLE = True
except ImportError:
    _AMLA_AVAILABLE = False
    logger.warning("AMLA not available")

# ConsequenceEngine Integration
try:
    from unified_core.core.consequence import ConsequenceEngine, Action, Outcome
    _CONSEQUENCE_AVAILABLE = True
except ImportError:
    _CONSEQUENCE_AVAILABLE = False
    logger.warning("ConsequenceEngine not available")

# ScarTissue Integration
try:
    from unified_core.core.scar import FailureRecord, Failure
    _SCAR_AVAILABLE = True
except ImportError:
    _SCAR_AVAILABLE = False
    logger.warning("ScarTissue not available")

logger = logging.getLogger(__name__)


class TrapLiveTrader:
    """
    Live/Paper trading wrapper for Trap Hybrid Engine.

    Features:
    - Real-time signal detection
    - Automatic position management
    - 50/50 hybrid exits (quick TP + trailing)
    - Risk-based position sizing
    """

    def __init__(
        self,
        testnet: bool = True,
        read_only: bool = True,
        mode: str = "paper",  # "live", "paper", or "observe"
        risk_per_trade: float = 0.01,
        max_leverage: int = 5,
        initial_capital: float = 10_000.0,
        max_positions: int = 3
    ):
        """
        Initialize live trader.

        Args:
            testnet: Use Binance testnet
            read_only: (Legacy) Paper trading mode (no real orders)
            mode: Operating mode ("live", "paper", "observe")
            risk_per_trade: Risk percentage per trade (0.01 = 1%)
            max_leverage: Maximum leverage
            initial_capital: Starting capital
            max_positions: Maximum concurrent live positions
        """
        # Reconcile mode with legacy read_only
        if mode == "observe":
            self.read_only = True
            self.mode = "observe"
        elif mode == "live":
            self.read_only = False
            self.mode = "live"
        else:
            self.read_only = read_only
            self.mode = "paper" if read_only else "live"

        self.futures = get_futures_manager(testnet=testnet, read_only=self.read_only, max_leverage=max_leverage)
        self.engine = get_trap_hybrid_engine()
        self.testnet = testnet
        self.risk_per_trade = risk_per_trade
        self.initial_capital = initial_capital
        self.max_positions = max_positions

        # Track active positions
        self.positions: Dict[str, TrapPosition] = {}

        # EventBus integration
        self._event_bus = None
        if _EVENT_BUS_AVAILABLE:
            try:
                self._event_bus = get_event_bus()
                logger.debug("EventBus connected to TrapLiveTrader")
            except Exception as e:
                logger.warning(f"Could not connect to EventBus: {e}")

        # Market Belief Engine integration
        self.belief_engine = get_market_belief_engine()
        self._belief_setup_done = False

        # NeuronFabric integration
        self.neuron_fabric = None
        self._trade_neurons: Dict[str, str] = {}  # symbol -> neuron_id mapping
        if _NEURON_FABRIC_AVAILABLE:
            try:
                self.neuron_fabric = get_neuron_fabric()
                logger.debug("NeuronFabric connected to TrapLiveTrader")
            except Exception as e:
                logger.warning(f"Could not connect to NeuronFabric: {e}")

        # AMLA integration
        self.amla = None
        if _AMLA_AVAILABLE:
            try:
                self.amla = get_amla()
                logger.debug("AMLA connected to TrapLiveTrader")
            except Exception as e:
                logger.warning(f"Could not connect to AMLA: {e}")

        # ConsequenceEngine integration
        self.consequence_engine = None
        if _CONSEQUENCE_AVAILABLE:
            try:
                self.consequence_engine = ConsequenceEngine(storage_name="trading_consequences.jsonl")
                logger.debug("ConsequenceEngine connected to TrapLiveTrader")
            except Exception as e:
                logger.warning(f"Could not connect to ConsequenceEngine: {e}")

        # ScarTissue integration
        self.scar_tissue = None
        if _SCAR_AVAILABLE:
            try:
                self.scar_tissue = FailureRecord(enable_enforcement=False)
                logger.debug("ScarTissue connected to TrapLiveTrader")
            except Exception as e:
                logger.warning(f"Could not connect to ScarTissue: {e}")

        logger.info("🚀 Trap Live Trader initialized")
        logger.info(f"   Network: {'TESTNET' if testnet else 'PRODUCTION'}")
        logger.info(f"   Mode: {self.mode.upper()}")
        logger.info(f"   Risk: {risk_per_trade*100}% per trade | Leverage: {max_leverage}x")

    def get_market_data(
        self,
        symbol: str,
        interval: str = '5m',
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch recent market data.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe ('5m', '15m', '1h')
            limit: Number of candles

        Returns:
            DataFrame with OHLCV + taker_buy_base
        """
        try:
            klines = self.futures.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume', 'taker_buy_base']:
                df[col] = df[col].astype(float)

            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return pd.DataFrame()

    def check_signal(self, symbol: str) -> TrapSignal:
        """
        Check for entry signal on symbol.

        Args:
            symbol: Trading pair

        Returns:
            TrapSignal (signal='NONE' if no signal)
        """
        try:
            # Don't check if already in position
            if symbol in self.positions:
                return TrapSignal(
                    signal='NONE',
                    entry_price=0.0,
                    stop_loss=0.0,
                    quick_tp=0.0,
                    atr=0.0,
                    timestamp=datetime.now(),
                    reasons=['Already in position']
                )

            # Fetch data
            df = self.get_market_data(symbol, interval='5m', limit=100)
            if df.empty:
                return TrapSignal(
                    signal='NONE',
                    entry_price=0.0,
                    stop_loss=0.0,
                    quick_tp=0.0,
                    atr=0.0,
                    timestamp=datetime.now(),
                    reasons=['Failed to fetch data']
                )

            # Cognitive Market Analysis (Sovereign Brain)
            # We bypass the mathematical TrapEngine entirely and ask the Brain directly.
            
            # Format the last 20 candles into a readable string
            recent_klines = df.tail(20)
            klines_str = recent_klines[['open', 'high', 'low', 'close', 'volume', 'taker_buy_base']].to_string()
            
            prompt = f"""You are NOOGH's Sovereign Trading Brain. You have absolute financial control.
Analyze the following recent 5-minute Klines for {symbol}.
Determine if there is a high-probability LONG or SHORT entry right now based on price action, volume, and Order Flow (taker_buy_base).

Klines (Last 20 periods):
{klines_str}

Return ONLY a valid JSON object with the following schema:
{{
  "signal": "LONG" | "SHORT" | "NONE",
  "entry_price": float (approximate current price),
  "stop_loss": float (calculated logical stop loss level),
  "quick_tp": float (1:1 Risk-Reward first take profit level),
  "atr": float (approximate volatility based on recent candles),
  "reasons": ["Reason 1", "Reason 2"]
}}
If the setup is weak, return "signal": "NONE".
"""
            # v21: Sync brain call — DeepSeek R1 API (primary) with Ollama fallback
            import requests as _requests
            try:
                _api_key = os.environ.get("DEEPSEEK_API_KEY", "")
                _api_url = os.environ.get("NEURAL_ENGINE_URL", "http://localhost:11434")
                _model = os.environ.get("VLLM_MODEL_NAME", "qwen2.5-coder:14b")
                
                if _api_key and "deepseek" in _api_url:
                    # DeepSeek Cloud API (OpenAI-compatible)
                    resp = _requests.post(
                        f"{_api_url}/v1/chat/completions",
                        json={
                            "model": _model,
                            "messages": [
                                {"role": "system", "content": "أنت محلل أسواق مالية محترف. حلّل البيانات وأعط إشارة تداول بصيغة JSON."},
                                {"role": "user", "content": prompt},
                            ],
                            "max_tokens": 1024,
                            "temperature": 0.3,
                        },
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {_api_key}",
                        },
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        content_resp = resp.json()["choices"][0]["message"]["content"].strip()
                    else:
                        logger.warning(f"DeepSeek returned {resp.status_code}, falling back to Ollama")
                        raise ConnectionError("DeepSeek failed")
                else:
                    # Fallback: Local Ollama
                    resp = _requests.post(
                        "http://localhost:11434/api/generate",
                        json={"model": _model, "prompt": prompt, "stream": False},
                        timeout=30,
                    )
                    content_resp = resp.json().get("response", "").strip() if resp.status_code == 200 else ""
                
                match = re.search(r'\{.*\}', content_resp, re.DOTALL)
                brain_signal = json.loads(match.group(0)) if match else None
            except Exception as brain_err:
                logger.warning(f"Brain call failed: {brain_err}")
                brain_signal = None
            
            if brain_signal and isinstance(brain_signal, dict):
                signal_type = str(brain_signal.get("signal", "NONE")).upper()
                if signal_type in ["LONG", "SHORT", "NONE"]:
                    logger.info(f"  🧠 Brain analyzed {symbol} and decided: {signal_type}")
                    signal = TrapSignal(
                        signal=signal_type,
                        entry_price=float(brain_signal.get("entry_price", df['close'].iloc[-1])),
                        stop_loss=float(brain_signal.get("stop_loss", 0.0)),
                        quick_tp=float(brain_signal.get("quick_tp", 0.0)),
                        atr=float(brain_signal.get("atr", 0.0)),
                        timestamp=datetime.now(),
                        reasons=brain_signal.get("reasons", ["Brain decided"])
                    )
                else:
                    signal = TrapSignal(signal='NONE', entry_price=0.0, stop_loss=0.0, quick_tp=0.0, atr=0.0, timestamp=datetime.now(), reasons=["Invalid brain signal"])
            else:
                signal = TrapSignal(signal='NONE', entry_price=0.0, stop_loss=0.0, quick_tp=0.0, atr=0.0, timestamp=datetime.now(), reasons=["Brain context parsing failed"])

            if signal.signal != 'NONE':
                logger.info(f"📊 Cognitive Signal detected: {signal.signal} {symbol} @ ${signal.entry_price:.2f}")
                logger.info(f"   SL: ${signal.stop_loss:.2f} | TP1: ${signal.quick_tp:.2f}")
                logger.info(f"   Reasons: {', '.join(signal.reasons)}")

            # Publish TRADE_SIGNAL event
            if self._event_bus and signal.signal != 'NONE':
                try:
                    self._event_bus.publish_sync(
                        StandardEvents.TRADE_SIGNAL,
                        {
                            "symbol": symbol,
                            "signal": signal.signal,
                            "entry_price": signal.entry_price,
                            "stop_loss": signal.stop_loss,
                            "quick_tp": signal.quick_tp,
                            "atr": signal.atr,
                            "strength": signal.strength,
                            "reasons": signal.reasons,
                            "timestamp": datetime.now().isoformat()
                        },
                        "trap_live_trader",
                        EventPriority.NORMAL
                    )
                except Exception as e:
                    logger.debug(f"Failed to publish trade_signal event: {e}")

            return signal

        except Exception as e:
            logger.error(f"Error checking signal: {e}")
            return TrapSignal(
                signal='NONE',
                entry_price=0.0,
                stop_loss=0.0,
                quick_tp=0.0,
                atr=0.0,
                timestamp=datetime.now(),
                reasons=[f'Error: {str(e)}']
            )

    def _check_volatility_filter(self, symbol: str, df) -> tuple[bool, str]:
        """
        🛡️ Volatility Circuit Breaker

        Blocks trades when market volatility is too high (unsafe conditions)

        Args:
            symbol: Trading pair
            df: DataFrame with indicators (must have ATR)

        Returns:
            (allowed: bool, reason: str)
        """
        try:
            if df is None or len(df) < 2:
                return True, "Insufficient data for volatility check"

            latest = df.iloc[-1]

            # ATR-based volatility check
            atr = float(latest.get('ATR', 0))
            close = float(latest.get('close', 0))

            if close <= 0:
                return True, "Invalid price data"

            # ATR as percentage of price
            atr_pct = (atr / close) * 100

            # Price range check (high-low as % of close)
            high = float(latest.get('high', close))
            low = float(latest.get('low', close))
            range_pct = ((high - low) / close) * 100

            # Thresholds (configurable)
            max_atr_pct = 3.0  # 3% ATR is very high volatility
            max_range_pct = 5.0  # 5% range is extreme

            if atr_pct > max_atr_pct:
                return False, f"High volatility: ATR {atr_pct:.2f}% > {max_atr_pct}%"

            if range_pct > max_range_pct:
                return False, f"Extreme range: {range_pct:.2f}% > {max_range_pct}%"

            return True, f"Volatility OK (ATR: {atr_pct:.2f}%, Range: {range_pct:.2f}%)"

        except Exception as e:
            logger.warning(f"Volatility check error: {e}")
            return True, f"Volatility check failed: {str(e)}"

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """
        Calculate position size based on risk.

        Args:
            symbol: Trading pair
            entry_price: Entry price
            stop_loss: Stop loss price

        Returns:
            Position size (quantity)
        """
        # Get current balance
        if self.read_only:
            capital = self.initial_capital
        else:
            balance_info = self.futures.get_account_balance()
            capital = balance_info.get('total_balance', self.initial_capital)

        # Calculate risk
        risk_amount = capital * self.risk_per_trade
        per_unit_risk = abs(entry_price - stop_loss)

        if per_unit_risk <= 0:
            return 0.0

        qty = risk_amount / per_unit_risk

        # Apply leverage cap
        max_qty = (capital * self.futures.max_leverage) / entry_price if entry_price > 0 else 0.0

        return min(qty, max_qty)

    def execute_signal(
        self,
        signal: TrapSignal,
        symbol: str
    ) -> Dict:
        """
        Execute entry based on signal.

        Args:
            signal: TrapSignal from check_signal()
            symbol: Trading pair

        Returns:
            Execution result dict
        """
        if signal.signal == 'NONE':
            return {
                'success': False,
                'message': 'No signal to execute',
                'reasons': signal.reasons
            }

        try:
            # 🛡️ Volatility Circuit Breaker Check
            df = self.get_market_data(symbol, interval='5m', limit=20)
            volatility_allowed, volatility_reason = self._check_volatility_filter(symbol, df)
            if not volatility_allowed:
                logger.warning(f"🚫 Trade blocked by volatility filter: {volatility_reason}")
                return {
                    'success': False,
                    'message': f'Volatility filter: {volatility_reason}',
                    'reasons': [volatility_reason]
                }
            else:
                logger.info(f"✅ Volatility check passed: {volatility_reason}")

            # Calculate position size
            raw_qty = self.calculate_position_size(symbol, signal.entry_price, signal.stop_loss)
            qty = self.futures.round_quantity(symbol, raw_qty)

            if len(self.positions) >= self.max_positions:
                return {
                    'success': False,
                    'message': f'Max positions limit reached ({self.max_positions})',
                    'qty': qty
                }

            if qty <= 0:
                return {
                    'success': False,
                    'message': f'Position size too small after rounding (Raw: {raw_qty}, Rounded: {qty})',
                    'qty': qty
                }

            logger.info(f"📍 Executing {signal.signal} {symbol}: {qty:.4f} @ ${signal.entry_price:.2f}")

            # AMLA Audit before execution
            if self.amla:
                try:
                    risk_usd = abs(signal.entry_price - signal.stop_loss) * qty
                    risk_percent = risk_usd / (self.initial_capital if self.read_only else 10000)  # Rough estimate

                    audit_request = AMLAActionRequest(
                        action_type="OPEN_TRADE",
                        params={
                            "symbol": symbol,
                            "direction": signal.signal,
                            "entry_price": signal.entry_price,
                            "quantity": qty,
                            "stop_loss": signal.stop_loss,
                            "risk_usd": risk_usd
                        },
                        source_beliefs=[],  # TODO: Get from MarketBeliefEngine
                        confidence=signal.strength,
                        impact_level=min(risk_percent, 1.0)
                    )

                    audit_result = self.amla.evaluate(audit_request)

                    if audit_result.verdict == AMLAVerdict.BLOCKED:
                        logger.warning(f"🚫 AMLA BLOCKED trade: {audit_result.blocked_reason}")
                        logger.warning(f"   DFE: {audit_result.fragility_extreme:.2%}")
                        return {
                            'success': False,
                            'message': f'AMLA blocked: {audit_result.blocked_reason}',
                            'audit_result': audit_result.to_dict()
                        }
                    elif audit_result.requires_acknowledgment:
                        logger.warning(f"⚠️  AMLA requires acknowledgment (DFE: {audit_result.fragility_extreme:.2%})")
                        logger.warning(f"   {audit_result.advisory_message}")

                    logger.info(f"✓ AMLA approved (DFE: {audit_result.fragility_extreme:.2%})")

                except Exception as e:
                    logger.debug(f"AMLA audit failed: {e}")

            if self.mode == "observe":
                # Observation mode: log signal analysis without taking a position
                logger.info(f"   [OBSERVE MODE - Signal evaluated, no position created]")
                return {
                    'success': True,
                    'message': f'Observation only: {signal.signal} {symbol}',
                    'position': None,
                    'mode': 'observe'
                }

            if self.read_only or self.mode == "paper":
                # Paper trading: just create position
                logger.info("   [PAPER TRADE - Not executed on exchange]")

                position = self.engine.create_position(signal, qty)
                if position:
                    self.positions[symbol] = position

                    # Create trading neuron
                    if self.neuron_fabric:
                        try:
                            reasons_str = ", ".join(signal.reasons[:3])  # First 3 reasons
                            neuron = self.neuron_fabric.create_neuron(
                                proposition=f"{signal.signal} {symbol} @ ${signal.entry_price:.2f} [{reasons_str}]",
                                neuron_type=NeuronType.MOTOR,
                                confidence=signal.strength,
                                domain="trading",
                                tags=["trade", signal.signal.lower(), symbol],
                                metadata={
                                    "symbol": symbol,
                                    "direction": signal.signal,
                                    "entry_price": signal.entry_price,
                                    "mode": "paper"
                                }
                            )
                            self._trade_neurons[symbol] = neuron.neuron_id
                            logger.debug(f"🧬 Trading neuron created: {neuron.neuron_id[:8]}")
                        except Exception as e:
                            logger.debug(f"Failed to create trading neuron: {e}")

                    # Publish TRADE_OPENED event
                    if self._event_bus:
                        try:
                            self._event_bus.publish_sync(
                                StandardEvents.TRADE_OPENED,
                                {
                                    "symbol": symbol,
                                    "direction": signal.signal,
                                    "entry_price": signal.entry_price,
                                    "quantity": qty,
                                    "stop_loss": signal.stop_loss,
                                    "quick_tp": signal.quick_tp,
                                    "mode": "paper",
                                    "timestamp": datetime.now().isoformat()
                                },
                                "trap_live_trader",
                                EventPriority.HIGH
                            )
                        except Exception as e:
                            logger.debug(f"Failed to publish trade_opened event: {e}")

                return {
                    'success': True,
                    'message': f'Paper trade created: {signal.signal} {symbol}',
                    'position': position,
                    'paper_trade': True,
                    'mode': 'paper'
                }

            else:
                # Real trading: execute on exchange
                side = 'BUY' if signal.signal == 'LONG' else 'SELL'

                result = self.futures.open_position(
                    symbol=symbol,
                    side=side,
                    quantity=qty,
                    leverage=self.futures.max_leverage,
                    stop_loss=signal.stop_loss
                    # 'take_profit' IS DELIBERATELY OMITTED to prevent Binance Order Conflicts with our Logic
                )

                if 'error' in result:
                    return {
                        'success': False,
                        'message': f"Exchange error: {result['error']}",
                        'result': result
                    }

                # Log successful order (note: Binance returns 'order_id', not 'orderId')
                logger.info(f"   ✅ Order executed: {result.get('order_id', 'N/A')}")

                # Create position tracker (safe - won't fail the trade if tracking fails)
                position = None
                try:
                    position = self.engine.create_position(signal, qty)
                    if position:
                        self.positions[symbol] = position
                        logger.info(f"   📊 Position tracker created for {symbol}")

                        # Create trading neuron
                        if self.neuron_fabric:
                            try:
                                reasons_str = ", ".join(signal.reasons[:3])
                                neuron = self.neuron_fabric.create_neuron(
                                    proposition=f"{signal.signal} {symbol} @ ${signal.entry_price:.2f} [{reasons_str}]",
                                    neuron_type=NeuronType.MOTOR,
                                    confidence=signal.strength,
                                    domain="trading",
                                    tags=["trade", signal.signal.lower(), symbol],
                                    metadata={
                                        "symbol": symbol,
                                        "direction": signal.signal,
                                        "entry_price": signal.entry_price,
                                        "mode": "live",
                                        "order_id": result.get('order_id', 'N/A')
                                    }
                                )
                                self._trade_neurons[symbol] = neuron.neuron_id
                                logger.debug(f"🧬 Trading neuron created: {neuron.neuron_id[:8]}")
                            except Exception as e:
                                logger.debug(f"Failed to create trading neuron: {e}")

                        # Publish TRADE_OPENED event
                        if self._event_bus:
                            try:
                                self._event_bus.publish_sync(
                                    StandardEvents.TRADE_OPENED,
                                    {
                                        "symbol": symbol,
                                        "direction": signal.signal,
                                        "entry_price": signal.entry_price,
                                        "quantity": qty,
                                        "stop_loss": signal.stop_loss,
                                        "quick_tp": signal.quick_tp,
                                        "mode": "live",
                                        "order_id": result.get('order_id', 'N/A'),
                                        "timestamp": datetime.now().isoformat()
                                    },
                                    "trap_live_trader",
                                    EventPriority.HIGH
                                )
                            except Exception as e:
                                logger.debug(f"Failed to publish trade_opened event: {e}")
                    else:
                        logger.warning(f"   ⚠️ Position tracker failed for {symbol} - will recover on next monitor cycle")
                except Exception as track_err:
                    logger.error(f"   ⚠️ Position tracking error (trade still executed): {track_err}")

                return {
                    'success': True,
                    'message': f'Live order executed: {signal.signal} {symbol}',
                    'position': position,
                    'exchange_result': result,
                    'paper_trade': False,
                    'mode': 'live'
                }

        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'message': f'Execution error: {str(e)}'
            }

    def monitor_positions(self) -> Dict:
        """
        Monitor and update all active positions.

        Returns:
            Status dict with exits and updates
        """
        if not self.positions:
            return {'message': 'No active positions', 'exits': [], 'updates': []}

        exits = []
        updates = []

        # Reconcile missing live positions on Exchange vs Memory Tracker first
        if not self.read_only:
            try:
                exchange_positions = self.futures.get_positions()
                exchange_symbols = [p['symbol'] for p in exchange_positions]
                
                # Delete tracked positions if they randomly vanished from Binance (closed externally/liquidated)
                to_remove = []
                for symbol in self.positions:
                    if symbol not in exchange_symbols:
                        logger.warning(f"⚠️ Reconciliation Disconnected: Tracker had {symbol} but Binance shows NOTHING. Synchronizing Trackers...")
                        to_remove.append(symbol)
                for tr in to_remove:
                    del self.positions[tr]
            except Exception as e:
                logger.error(f"⚠️ Reconciliation Error: {e}")

        try:
            for symbol, position in list(self.positions.items()):
                # Fetch current data
                df = self.get_market_data(symbol, interval='5m', limit=5)
                if df.empty:
                    continue

                # Compute ATR for trailing
                df = self.engine.compute_indicators(df)
                current_atr = df['atr'].iloc[-1]

                latest_bar = df.iloc[-1]
                h, l, c = latest_bar['high'], latest_bar['low'], latest_bar['close']

                # Check for exits
                exit_events, updated_position = self.engine.check_exits(
                    position, h, l, c, current_atr
                )

                # Process aggregate exit per-symbol logic
                if exit_events:
                    total_exit_qty = sum(q for _, _, q in exit_events)
                    last_reason = exit_events[-1][0]
                    last_price = exit_events[-1][1]
                    total_pnl = sum((p - position.entry_price) * q if position.side == 'LONG' else (position.entry_price - p) * q for _, p, q in exit_events)

                    logger.info(f"🚪 Aggregate Exit ({last_reason}): {symbol} @ ${last_price:.2f} | PnL: ${total_pnl:.2f}")

                    exits.append({
                        'symbol': symbol,
                        'reason': f"Aggregated [{last_reason}]",
                        'price': last_price,
                        'qty': total_exit_qty,
                        'pnl': total_pnl,
                        'timestamp': datetime.now(),
                        'side': position.side
                    })

                    # Execute close order on exchange if not read_only (Single bulk order instead of duplicate partials)
                    if not self.read_only:
                        try:
                            # Determine side to close (opposite of position)
                            close_side = 'SELL' if position.side == 'LONG' else 'BUY'

                            # Round aggregated quantity
                            rounded_total_qty = self.futures.round_quantity(symbol, total_exit_qty)

                            # Place market order to close
                            close_order = self.futures.client.futures_create_order(
                                symbol=symbol.upper(),
                                side=close_side,
                                type='MARKET',
                                quantity=rounded_total_qty,
                                reduceOnly=True
                            )
                            logger.info(f"   ✅ Closed {rounded_total_qty} {symbol} on Binance (Order: {close_order.get('orderId', 'N/A')})")
                            
                            # Follow Up: Cancel pending TP/SL orders for this closed symbol
                            try:
                                self.futures.cancel_all_orders(symbol)
                            except Exception as e:
                                logger.error(f"  ⚠️ Warning: Could not cancel pending orders for {symbol} after close: {e}")
                                
                        except Exception as close_err:
                            logger.error(f"   ❌ Failed to close position on Binance: {close_err}")

                # Update position
                self.positions[symbol] = updated_position

                # Remove if fully closed
                if self.engine.is_position_closed(updated_position):
                    # Publish TRADE_CLOSED event
                    if self._event_bus and exits:
                        exit_info = exits[-1]  # Get the last exit info
                        pnl = exit_info['pnl']
                        try:
                            # Publish TRADE_CLOSED
                            self._event_bus.publish_sync(
                                StandardEvents.TRADE_CLOSED,
                                {
                                    "symbol": symbol,
                                    "direction": position.side,
                                    "entry_price": position.entry_price,
                                    "exit_price": exit_info['price'],
                                    "quantity": exit_info['qty'],
                                    "pnl": pnl,
                                    "reason": exit_info['reason'],
                                    "timestamp": datetime.now().isoformat()
                                },
                                "trap_live_trader",
                                EventPriority.HIGH
                            )

                            # Publish TRADE_PROFIT or TRADE_LOSS
                            event_type = StandardEvents.TRADE_PROFIT if pnl > 0 else StandardEvents.TRADE_LOSS
                            self._event_bus.publish_sync(
                                event_type,
                                {
                                    "symbol": symbol,
                                    "pnl": pnl,
                                    "pnl_percent": (pnl / (position.entry_price * exit_info['qty'])) * 100,
                                    "duration_minutes": (datetime.now() - position.timestamp).total_seconds() / 60,
                                    "reason": exit_info['reason'],
                                    "timestamp": datetime.now().isoformat()
                                },
                                "trap_live_trader",
                                EventPriority.HIGH
                            )
                        except Exception as e:
                            logger.debug(f"Failed to publish trade close events: {e}")

                    # Hebbian learning from trade outcome
                    if self.neuron_fabric and symbol in self._trade_neurons:
                        try:
                            neuron_id = self._trade_neurons[symbol]
                            success = pnl > 0
                            impact = min(abs(pnl) / 100, 1.0)  # Normalize impact (max 1.0)

                            # Activate the neuron and learn from outcome
                            activated = self.neuron_fabric.activate(neuron_id, signal=1.0)
                            self.neuron_fabric.learn_from_outcome(
                                activated_neurons=activated,
                                success=success,
                                impact=impact
                            )

                            result_emoji = "📈" if success else "📉"
                            logger.info(f"   {result_emoji} Hebbian learning: {'reinforced' if success else 'weakened'} "
                                      f"(impact: {impact:.2f})")

                            # Remove neuron mapping
                            del self._trade_neurons[symbol]

                        except Exception as e:
                            logger.debug(f"Failed to apply Hebbian learning: {e}")

                    # ConsequenceEngine tracking
                    if self.consequence_engine and exits:
                        try:
                            exit_info = exits[-1]
                            pnl = exit_info['pnl']

                            action = Action(
                                action_type="TRADE",
                                parameters={
                                    "symbol": symbol,
                                    "direction": position.side,
                                    "entry_price": position.entry_price,
                                    "exit_price": exit_info['price'],
                                    "quantity": exit_info['qty']
                                }
                            )

                            outcome = Outcome(
                                success=(pnl > 0),
                                result={
                                    "pnl_usd": pnl,
                                    "pnl_percent": (pnl / (position.entry_price * exit_info['qty'])) * 100,
                                    "exit_reason": exit_info['reason']
                                }
                            )

                            consequence_hash = self.consequence_engine.commit(action, outcome)
                            logger.debug(f"   📝 Consequence recorded: {consequence_hash[:12]}...")

                        except Exception as e:
                            logger.debug(f"Failed to record consequence: {e}")

                    # ScarTissue for large losses
                    if self.scar_tissue and exits:
                        try:
                            exit_info = exits[-1]
                            pnl = exit_info['pnl']
                            pnl_percent = (pnl / (position.entry_price * exit_info['qty'])) * 100

                            # Inflict scar for losses > 3%
                            if pnl_percent < -3.0:
                                failure = Failure(
                                    failure_id=f"trade_loss_{symbol}_{int(datetime.now().timestamp())}",
                                    action_type="LARGE_TRADING_LOSS",
                                    action_params={
                                        "symbol": symbol,
                                        "direction": position.side,
                                        "pnl_percent": pnl_percent,
                                        "pnl_usd": pnl
                                    },
                                    error_message=f"Lost {abs(pnl_percent):.1f}% on {symbol} {position.side}",
                                    belief_ids_involved=[]
                                )

                                # Determine severity
                                if abs(pnl_percent) > 10:
                                    severity = "catastrophic"
                                elif abs(pnl_percent) > 7:
                                    severity = "high"
                                elif abs(pnl_percent) > 5:
                                    severity = "medium"
                                else:
                                    severity = "low"

                                # Inflict scar asynchronously
                                import asyncio
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        asyncio.create_task(self.scar_tissue.inflict(failure, severity=severity))
                                    else:
                                        asyncio.run(self.scar_tissue.inflict(failure, severity=severity))
                                    logger.warning(f"   💔 SCAR INFLICTED: {severity} ({pnl_percent:.1f}%)")
                                except:
                                    # Fallback: just log
                                    logger.warning(f"   💔 Large loss detected: {pnl_percent:.1f}% (scar recording failed)")

                        except Exception as e:
                            logger.debug(f"Failed to process scar tissue: {e}")

                    del self.positions[symbol]
                    logger.info(f"   Position closed: {symbol}")
                else:
                    # Log trailing stop update
                    if updated_position.quick_tp_hit:
                        updates.append({
                            'symbol': symbol,
                            'trailing_stop': updated_position.trailing_stop,
                            'qty_remaining': updated_position.qty_trail
                        })

            return {
                'message': f'Monitored {len(self.positions)} positions',
                'exits': exits,
                'updates': updates,
                'active_positions': len(self.positions)
            }

        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
            return {
                'message': f'Monitor error: {str(e)}',
                'exits': [],
                'updates': []
            }

    def recover_positions_from_exchange(self) -> int:
        """
        Recover open positions from Binance and add to tracker.

        Call this on startup to resume monitoring positions that were
        opened but not tracked (e.g., after crash or restart).

        Returns:
            Number of positions recovered
        """
        if self.read_only or self.mode == "observe":
            logger.info(f"📝 {self.mode.capitalize()} mode - no position recovery needed")
            return 0

        try:
            # Get all open positions from Binance
            positions_raw = self.futures.client.futures_position_information()

            recovered = 0
            for pos in positions_raw:
                amt = float(pos['positionAmt'])
                if amt == 0:
                    continue

                symbol = pos['symbol']

                # Skip if already tracking
                if symbol in self.positions:
                    logger.info(f"   Already tracking {symbol}")
                    continue

                # Recover position details
                entry_price = float(pos['entryPrice'])
                side = 'LONG' if amt > 0 else 'SHORT'
                qty = abs(amt)

                # Estimate ATR and stops
                df = self.get_market_data(symbol, interval='5m', limit=20)
                if not df.empty:
                    df = self.engine.compute_indicators(df)
                    atr = df['atr'].iloc[-1]
                else:
                    atr = entry_price * 0.02  # Fallback: 2% of entry

                # First query Exchange for explicit exit orders
                exit_metadata = self.futures.get_exit_orders(symbol)
                exchange_sl = exit_metadata.get('stop_loss_price')
                
                # Reconstruct stop loss (From Exchange or 2x ATR from entry)
                if side == 'LONG':
                    stop_loss = exchange_sl if exchange_sl else entry_price - (atr * 2.0)
                    quick_tp = entry_price + atr  # 1R target
                else:
                    stop_loss = exchange_sl if exchange_sl else entry_price + (atr * 2.0)
                    quick_tp = entry_price - atr

                # Create TrapPosition
                from .trap_hybrid_engine import TrapPosition
                position = TrapPosition(
                    side=side,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    quick_tp=quick_tp,
                    trailing_stop=stop_loss,  # Start at SL
                    qty_quick=qty * 0.5,      # Assume 50/50 split
                    qty_trail=qty * 0.5,
                    quick_tp_hit=False,
                    entry_time=datetime.now(),  # We don't know actual entry time
                    atr_at_entry=atr
                )

                self.positions[symbol] = position
                recovered += 1

                logger.info(f"   🔄 Recovered {side} {symbol}: {qty:.4f} @ ${entry_price:.4f}")
                logger.info(f"      SL: ${stop_loss:.4f} | TP: ${quick_tp:.4f}")

            if recovered > 0:
                logger.info(f"✅ Recovered {recovered} positions from Binance")
            else:
                logger.info("✅ No positions to recover")

            return recovered

        except Exception as e:
            logger.error(f"❌ Position recovery error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return 0

    def get_status(self) -> Dict:
        """Get trader status summary."""
        return {
            'network': 'TESTNET' if self.testnet else 'PRODUCTION',
            'mode': self.mode,
            'paper_trade': self.read_only,
            'active_positions': len(self.positions),
            'positions': {
                symbol: {
                    'side': pos.side,
                    'entry': pos.entry_price,
                    'quick_tp_hit': pos.quick_tp_hit,
                    'trailing_stop': pos.trailing_stop,
                    'qty_remaining': pos.qty_quick + pos.qty_trail
                }
                for symbol, pos in self.positions.items()
            }
        }

    def check_signal_math(self, symbol: str) -> TrapSignal:
        """
        Check for entry signal using TrapHybridEngine (quantitative, proven PF 1.12).
        This is the primary signal source - deterministic, no LLM required.
        Args:
            symbol: Trading pair
        Returns:
            TrapSignal from mathematical engine
        """
        try:
            if symbol in self.positions:
                return TrapSignal(
                    signal='NONE', entry_price=0.0, stop_loss=0.0, quick_tp=0.0, atr=0.0,
                    timestamp=datetime.now(), reasons=['Already in position']
                )
            df = self.get_market_data(symbol, interval='5m', limit=100)
            if df.empty:
                return TrapSignal(
                    signal='NONE', entry_price=0.0, stop_loss=0.0, quick_tp=0.0, atr=0.0,
                    timestamp=datetime.now(), reasons=['Failed to fetch data']
                )
            df_ind = self.engine.compute_indicators(df)
            signal = self.engine.generate_signal(df_ind)
            if signal.signal != 'NONE':
                logger.info(f"📊 Math Signal: {signal.signal} {symbol} @ ${signal.entry_price:.2f}")
                logger.info(f"   SL: ${signal.stop_loss:.2f} | TP1: ${signal.quick_tp:.2f} | ATR: {signal.atr:.2f}")
                logger.info(f"   Reasons: {', '.join(signal.reasons)}")
                if self._event_bus and signal.signal != 'NONE':
                    try:
                        self._event_bus.publish_sync(
                            StandardEvents.TRADE_SIGNAL,
                            {'symbol': symbol, 'signal': signal.signal,
                             'entry_price': signal.entry_price, 'stop_loss': signal.stop_loss,
                             'quick_tp': signal.quick_tp, 'atr': signal.atr,
                             'reasons': signal.reasons, 'timestamp': datetime.now().isoformat()},
                            'trap_live_trader', EventPriority.NORMAL
                        )
                    except Exception as e:
                        logger.debug(f'Failed to publish trade_signal event: {e}')
            return signal
        except Exception as e:
            logger.error(f'Error in check_signal_math: {e}')
            return TrapSignal(
                signal='NONE', entry_price=0.0, stop_loss=0.0, quick_tp=0.0, atr=0.0,
                timestamp=datetime.now(), reasons=[f'Math engine error: {str(e)}']
            )

# Singleton
_trader = None

def get_trap_live_trader(**kwargs) -> TrapLiveTrader:
    """Get or create live trader instance."""
    global _trader
    if _trader is None:
        _trader = TrapLiveTrader(**kwargs)
    return _trader
