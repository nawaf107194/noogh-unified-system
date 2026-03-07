"""
Binance Futures Trading Integration for NOOGH System
⚠️ WARNING: Futures trading is extremely risky! Can lose more than invested.

Features:
- Futures account info
- Positions management
- Leverage control
- Funding rates
- Safety checks
"""

import os
import time
import math
from typing import Dict, List, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging

logger = logging.getLogger(__name__)


class BinanceFuturesManager:
    """
    Manages Binance Futures trading with strict safety features.

    ⚠️ EXTREME RISK WARNING:
    - Futures trading uses leverage (up to 125x)
    - Can lose MORE than your initial investment
    - Liquidation can happen in seconds
    - Only use with money you can afford to lose
    """

    def __init__(self, testnet: bool = True, read_only: bool = True, max_leverage: int = 5):
        """
        Initialize Futures Manager.

        Args:
            testnet: Use testnet (HIGHLY RECOMMENDED)
            read_only: Read-only mode (no trading)
            max_leverage: Maximum allowed leverage (safety limit)
        """
        self.testnet = testnet
        self.read_only = read_only
        self.max_leverage = min(max_leverage, 20)  # Hard cap at 20x for safety
        self.client: Optional[Client] = None
        self.last_request_time = 0
        self.min_request_interval = 0.1

        # Load API credentials
        if testnet:
            self.api_key = os.getenv("BINANCE_TESTNET_API_KEY", "")
            self.api_secret = os.getenv("BINANCE_TESTNET_SECRET", "")
            self.futures_url = "https://testnet.binancefuture.com"
        else:
            self.api_key = os.getenv("BINANCE_API_KEY", "")
            self.api_secret = os.getenv("BINANCE_SECRET", "")
            self.futures_url = "https://fapi.binance.com"

        # Exchange Info Cache
        self._exchange_info_cache = None
        self._exchange_info_time = 0
        self._exchange_info_ttl = 3600  # 1 hour cache to save API calls
        
        self._connect()

    def _connect(self):
        """Establish connection to Binance Futures API."""
        try:
            if not self.api_key or not self.api_secret:
                logger.warning("⚠️ Binance API credentials not found, connecting in public/anonymous mode")
                self.client = Client()
            else:
                self.client = Client(self.api_key, self.api_secret)

            if self.testnet:
                # Futures Testnet URLs (NOT Spot Testnet!)
                self.client.API_URL = 'https://testnet.binancefuture.com'
                self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
                logger.info("🧪 Connected to Binance Futures Testnet (testnet.binancefuture.com)")
            else:
                logger.warning("⚠️ Connected to Binance Futures PRODUCTION - BE CAREFUL!")

            # Test connection
            self.client.futures_ping()
            logger.info("✅ Futures connection successful")

        except Exception as e:
            logger.error(f"❌ Futures Connection Error: {e}")

    def _rate_limit(self):
        """Enforce rate limiting with backoff protection."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

        # Track requests per minute (Binance limit: 1200/min)
        if not hasattr(self, '_request_count'):
            self._request_count = 0
            self._request_window_start = time.time()
        self._request_count += 1
        if time.time() - self._request_window_start > 60:
            self._request_count = 1
            self._request_window_start = time.time()
        if self._request_count > 1100:  # Safety margin
            wait = 60 - (time.time() - self._request_window_start)
            if wait > 0:
                logger.warning(f"⚠️ Rate limit approaching ({self._request_count}/1200) — cooling {wait:.0f}s")
                time.sleep(wait)
                self._request_count = 0
                self._request_window_start = time.time()

    def _api_call_with_retry(self, func, *args, max_retries=3, **kwargs):
        """Execute API call with exponential backoff on rate limit errors."""
        for attempt in range(max_retries):
            self._rate_limit()
            try:
                return func(*args, **kwargs)
            except BinanceAPIException as e:
                if e.status_code in (429, 418):  # Rate limited or IP ban
                    wait = (2 ** attempt) * 5  # 5s, 10s, 20s
                    logger.warning(f"⚠️ Rate limited (HTTP {e.status_code}), waiting {wait}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait)
                else:
                    raise
        raise Exception(f"API call failed after {max_retries} retries")

    # ==========================================
    # SAFETY VERIFICATION METHODS
    # ==========================================

    def verify_balance_for_trade(self, required_margin: float) -> Dict:
        """
        Verify real Binance balance is sufficient before opening a trade.
        Returns: {ok: bool, real_balance: float, message: str}
        """
        try:
            account = self.get_futures_account()
            available = account.get('available_balance', 0)
            total = account.get('total_wallet_balance', 0)

            if available < required_margin:
                return {
                    'ok': False,
                    'real_balance': available,
                    'total_balance': total,
                    'message': f'Insufficient balance: ${available:.2f} available, ${required_margin:.2f} required'
                }
            return {
                'ok': True,
                'real_balance': available,
                'total_balance': total,
                'message': f'Balance OK: ${available:.2f} available'
            }
        except Exception as e:
            logger.error(f"❌ Balance verification failed: {e}")
            return {'ok': False, 'real_balance': 0, 'message': f'Verification error: {e}'}

    def verify_positions_have_sl(self) -> Dict:
        """
        Check all open positions have stop-loss orders on Binance.
        If missing, log a critical warning.
        Returns: {positions: int, protected: int, unprotected: list}
        """
        try:
            positions = self.get_positions()
            if not positions:
                return {'positions': 0, 'protected': 0, 'unprotected': []}

            unprotected = []
            protected = 0

            for pos in positions:
                symbol = pos['symbol']
                orders = self.get_open_orders(symbol)
                has_sl = any(
                    o.get('type') in ('STOP_MARKET', 'STOP')
                    for o in orders
                )
                if has_sl:
                    protected += 1
                    logger.info(f"✅ {symbol}: SL order active on Binance")
                else:
                    unprotected.append({
                        'symbol': symbol,
                        'side': 'LONG' if pos['position_amount'] > 0 else 'SHORT',
                        'qty': abs(pos['position_amount']),
                        'entry': pos['entry_price'],
                        'pnl': pos['unrealized_pnl']
                    })
                    logger.warning(f"🚨 {symbol}: NO STOP LOSS on Binance! Position exposed!")

            return {
                'positions': len(positions),
                'protected': protected,
                'unprotected': unprotected
            }
        except Exception as e:
            logger.error(f"❌ Position SL verification failed: {e}")
            return {'positions': 0, 'protected': 0, 'unprotected': [], 'error': str(e)}

    # ==========================================
    # ACCOUNT & BALANCE
    # ==========================================

    def get_futures_account(self) -> Dict:
        """Get futures account information."""
        if not self.api_key:
            return {'error': 'API key not configured'}

        self._rate_limit()
        try:
            account = self.client.futures_account()

            return {
                'total_wallet_balance': float(account.get('totalWalletBalance', 0)),
                'total_unrealized_pnl': float(account.get('totalUnrealizedProfit', 0)),
                'total_margin_balance': float(account.get('totalMarginBalance', 0)),
                'available_balance': float(account.get('availableBalance', 0)),
                'max_withdraw_amount': float(account.get('maxWithdrawAmount', 0)),
                'assets': [
                    {
                        'asset': a['asset'],
                        'wallet_balance': float(a['walletBalance']),
                        'unrealized_profit': float(a['unrealizedProfit']),
                        'margin_balance': float(a['marginBalance']),
                        'available_balance': float(a['availableBalance'])
                    }
                    for a in account.get('assets', [])
                    if float(a['walletBalance']) > 0
                ]
            }
        except BinanceAPIException as e:
            logger.error(f"Error fetching futures account: {e}")
            return {'error': str(e)}

    def get_futures_balance(self) -> List[Dict]:
        """Get futures account balance."""
        if not self.api_key:
            return []

        self._rate_limit()
        try:
            balance = self.client.futures_account_balance()
            return [
                {
                    'asset': b['asset'],
                    'balance': float(b['balance']),
                    'available_balance': float(b['availableBalance']),
                    'cross_wallet_balance': float(b.get('crossWalletBalance', 0)),
                    'cross_unpnl': float(b.get('crossUnPnl', 0))
                }
                for b in balance
                if float(b['balance']) > 0
            ]
        except BinanceAPIException as e:
            logger.error(f"Error fetching futures balance: {e}")
            return []

    # ==========================================
    # POSITIONS
    # ==========================================

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get current futures positions.

        Args:
            symbol: Filter by symbol (e.g., 'BTCUSDT')
        """
        if not self.api_key:
            return []

        self._rate_limit()
        try:
            positions = self.client.futures_position_information(symbol=symbol)

            # Filter only positions with size > 0
            active_positions = [
                {
                    'symbol': p['symbol'],
                    'position_side': p['positionSide'],
                    'position_amount': float(p['positionAmt']),
                    'entry_price': float(p['entryPrice']),
                    'mark_price': float(p['markPrice']),
                    'unrealized_pnl': float(p['unRealizedProfit']),
                    'leverage': int(p.get('leverage', 1)),
                    'liquidation_price': float(p.get('liquidationPrice', 0)),
                    'margin_type': p.get('marginType', 'cross'),
                    'isolated_wallet': float(p.get('isolatedWallet', 0))
                }
                for p in positions
                if float(p['positionAmt']) != 0
            ]

            return active_positions
        except BinanceAPIException as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get position risk information."""
        if not self.api_key:
            return []

        self._rate_limit()
        try:
            if symbol:
                risk = self.client.futures_position_information(symbol=symbol)
            else:
                risk = self.client.futures_position_information()

            return [
                {
                    'symbol': r['symbol'],
                    'position_amount': float(r['positionAmt']),
                    'entry_price': float(r['entryPrice']),
                    'mark_price': float(r['markPrice']),
                    'unrealized_pnl': float(r['unRealizedProfit']),
                    'liquidation_price': float(r['liquidationPrice']),
                    'leverage': int(r['leverage'])
                }
                for r in risk
                if float(r['positionAmt']) != 0
            ]
        except BinanceAPIException as e:
            logger.error(f"Error fetching position risk: {e}")
            return []

    # ==========================================
    # FUNDING RATE
    # ==========================================

    def get_funding_rate(self, symbol: str = 'BTCUSDT') -> Dict:
        """Get current funding rate for a symbol."""
        self._rate_limit()
        try:
            funding = self.client.futures_funding_rate(symbol=symbol, limit=1)
            if funding:
                rate = funding[0]
                return {
                    'symbol': rate['symbol'],
                    'funding_rate': float(rate['fundingRate']),
                    'funding_time': rate['fundingTime'],
                    'mark_price': float(rate.get('markPrice', 0))
                }
            return {}
        except BinanceAPIException as e:
            logger.error(f"Error fetching funding rate: {e}")
            return {}

    def get_all_funding_rates(self) -> List[Dict]:
        """Get funding rates for all symbols."""
        self._rate_limit()
        try:
            rates = self.client.futures_ticker()
            return [
                {
                    'symbol': r['symbol'],
                    'last_price': float(r['lastPrice']),
                    'mark_price': float(r['markPrice']),
                    'funding_rate': float(r.get('lastFundingRate', 0)),
                    'next_funding_time': r.get('nextFundingTime', 0)
                }
                for r in rates
                if 'USDT' in r['symbol']
            ][:20]  # Top 20
        except BinanceAPIException as e:
            logger.error(f"Error fetching funding rates: {e}")
            return []

    # ==========================================
    # ORDERS
    # ==========================================

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open futures orders."""
        if not self.api_key:
            return []

        self._rate_limit()
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol)
            else:
                orders = self.client.futures_get_open_orders()

            return [
                {
                    'symbol': o['symbol'],
                    'order_id': o['orderId'],
                    'side': o['side'],
                    'type': o['type'],
                    'position_side': o['positionSide'],
                    'price': float(o['price']),
                    'quantity': float(o['origQty']),
                    'executed_qty': float(o['executedQty']),
                    'status': o['status'],
                    'time': o['time']
                }
                for o in orders
            ]
        except BinanceAPIException as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    # ==========================================
    # LEVERAGE & MARGIN
    # ==========================================

    def change_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        Change leverage for a symbol.

        ⚠️ WARNING: Higher leverage = higher risk of liquidation!
        """
        if self.read_only:
            return {'error': 'Read-only mode enabled'}

        if leverage > self.max_leverage:
            return {'error': f'Leverage {leverage}x exceeds safety limit of {self.max_leverage}x'}

        if not self.api_key:
            return {'error': 'API key not configured'}

        self._rate_limit()
        try:
            result = self.client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            logger.info(f"✅ Leverage changed to {leverage}x for {symbol}")
            return {
                'symbol': result['symbol'],
                'leverage': result['leverage'],
                'max_notional_value': float(result.get('maxNotionalValue', 0))
            }
        except BinanceAPIException as e:
            logger.error(f"❌ Error changing leverage: {e}")
            return {'error': str(e)}

    def change_margin_type(self, symbol: str, margin_type: str) -> Dict:
        """
        Change margin type (ISOLATED or CROSSED).

        Args:
            symbol: Trading pair
            margin_type: 'ISOLATED' or 'CROSSED'
        """
        if self.read_only:
            return {'error': 'Read-only mode enabled'}

        if not self.api_key:
            return {'error': 'API key not configured'}

        self._rate_limit()
        try:
            result = self.client.futures_change_margin_type(
                symbol=symbol,
                marginType=margin_type.upper()
            )
            logger.info(f"✅ Margin type changed to {margin_type} for {symbol}")
            return result
        except BinanceAPIException as e:
            logger.error(f"❌ Error changing margin type: {e}")
            return {'error': str(e)}

    # ==========================================
    # MARKET DATA
    # ==========================================

    def get_futures_price(self, symbol: str) -> float:
        """Get current futures price."""
        self._rate_limit()
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Error fetching futures price: {e}")
            return 0.0

    def get_mark_price(self, symbol: str) -> Dict:
        """Get mark price and funding rate."""
        self._rate_limit()
        try:
            price = self.client.futures_mark_price(symbol=symbol)
            return {
                'symbol': price['symbol'],
                'mark_price': float(price['markPrice']),
                'index_price': float(price['indexPrice']),
                'funding_rate': float(price['lastFundingRate']),
                'next_funding_time': price['nextFundingTime']
            }
        except BinanceAPIException as e:
            logger.error(f"Error fetching mark price: {e}")
            return {}

    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100):
        """
        Get klines/candlestick data for a symbol.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch (max 1500)

        Returns:
            DataFrame with OHLCV data
        """
        self._rate_limit()
        try:
            import pandas as pd

            klines = self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])

            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume', 'taker_buy_base']:
                df[col] = df[col].astype(float)

            df.set_index('timestamp', inplace=True)

            return df

        except BinanceAPIException as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching klines: {e}")
            return None

    def get_account_balance(self) -> Dict:
        """Get total account balance (wrapper for get_futures_balance)."""
        balances = self.get_futures_balance()
        total = sum(float(b.get('balance', 0)) for b in balances if b.get('asset') == 'USDT')
        return {
            'total_balance': total,
            'balances': balances
        }

    # ==========================================
    # PRECISION & VALIDATION
    # ==========================================

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol exchange info (precision, lot size, min notional).

        Returns:
            Dict with precision info or None if error
        """
        try:
            # Check Cache first
            current_time = time.time()
            if self._exchange_info_cache is None or (current_time - self._exchange_info_time > self._exchange_info_ttl):
                self._rate_limit()
                self._exchange_info_cache = self.client.futures_exchange_info()
                self._exchange_info_time = current_time

            for s in self._exchange_info_cache['symbols']:
                if s['symbol'] == symbol.upper():
                    # Extract relevant filters
                    info = {
                        'symbol': s['symbol'],
                        'base_asset': s['baseAsset'],
                        'quote_asset': s['quoteAsset'],
                        'price_precision': s['pricePrecision'],
                        'quantity_precision': s['quantityPrecision'],
                        'base_asset_precision': s['baseAssetPrecision'],
                    }

                    # Extract LOT_SIZE filter
                    for f in s['filters']:
                        if f['filterType'] == 'LOT_SIZE':
                            info['min_qty'] = float(f['minQty'])
                            info['max_qty'] = float(f['maxQty'])
                            info['step_size'] = float(f['stepSize'])
                        elif f['filterType'] == 'MIN_NOTIONAL':
                            info['min_notional'] = float(f['notional'])
                        elif f['filterType'] == 'PRICE_FILTER':
                            info['min_price'] = float(f['minPrice'])
                            info['max_price'] = float(f['maxPrice'])
                            info['tick_size'] = float(f['tickSize'])

                    return info

            logger.warning(f"Symbol {symbol} not found in exchange info")
            return None

        except Exception as e:
            logger.error(f"Error fetching symbol info: {e}")
            return None

    def round_quantity(self, symbol: str, quantity: float) -> float:
        """
        Round quantity according to symbol's LOT_SIZE rules.

        Args:
            symbol: Trading pair
            quantity: Raw quantity

        Returns:
            Rounded quantity that meets exchange requirements
        """
        info = self.get_symbol_info(symbol)

        if not info:
            # Fallback: round to 3 decimals
            logger.warning(f"No symbol info for {symbol}, using default rounding")
            return round(quantity, 3)

        step_size = info.get('step_size', 0.001)
        min_qty = info.get('min_qty', 0.0)
        max_qty = info.get('max_qty', 1000000.0)

        # Round to step_size precision
        # Calculate number of decimals in step_size
        step_str = f"{step_size:.10f}".rstrip('0')
        if '.' in step_str:
            decimals = len(step_str.split('.')[1])
        else:
            decimals = 0

        # Round quantity to step_size increments (Using math.floor instead of round to prevent insufficient margin errors)
        rounded = math.floor(quantity / step_size) * step_size
        if step_size > 0:
            rounded = round(rounded, decimals)

        # Ensure within min/max bounds
        if rounded < min_qty:
            logger.warning(f"Quantity {rounded} below minimum {min_qty}, using minimum")
            rounded = min_qty
        elif rounded > max_qty:
            logger.warning(f"Quantity {rounded} above maximum {max_qty}, using maximum")
            rounded = max_qty

        logger.info(f"Rounded quantity for {symbol}: {quantity:.8f} → {rounded:.8f} (step: {step_size}, min: {min_qty})")

        return rounded
    def round_price(self, symbol: str, price: float) -> float:
        """Round price to symbol's tick_size precision (PRICE_FILTER)."""
        info = self.get_symbol_info(symbol)
        if not info:
            return round(price, 2)  # fallback
        tick_size = info.get('tick_size', 0.01)
        price_precision = info.get('price_precision', 2)
        rounded = round(math.floor(price / tick_size) * tick_size, price_precision)
        return rounded

    # ==========================================
    # TRADING OPERATIONS (Extremely Risky!)
    # ==========================================

    def open_position(self, symbol: str, side: str, quantity: float,
                     leverage: Optional[int] = None,
                     stop_loss: Optional[float] = None,
                     take_profit: Optional[float] = None) -> Dict:
        """
        Open a futures position (LONG or SHORT).

        ⚠️ EXTREME RISK WARNING:
        - Can lose MORE than your investment
        - Use stop loss to protect capital
        - Start with small positions

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' (LONG) or 'SELL' (SHORT)
            quantity: Position size
            leverage: Leverage multiplier (optional)
            stop_loss: Stop loss price (optional but RECOMMENDED)
            take_profit: Take profit price (optional)

        Returns:
            Order result dict
        """
        if self.read_only:
            return {'error': '🔒 Trading disabled - read-only mode enabled'}

        if not self.api_key:
            return {'error': 'API key not configured'}

        # Safety check: leverage
        if leverage and leverage > self.max_leverage:
            return {'error': f'⚠️ Leverage {leverage}x exceeds safety limit of {self.max_leverage}x'}

        self._rate_limit()
        try:
            # Round quantity to symbol's precision
            rounded_qty = self.round_quantity(symbol, quantity)

            if rounded_qty <= 0:
                return {'error': f'Invalid quantity after rounding: {rounded_qty}'}

            # Set leverage if provided
            if leverage:
                try:
                    self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
                except BinanceAPIException as lev_err:
                    logger.warning(f"Could not set leverage: {lev_err}")

            # Create market order with rounded quantity
            order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type='MARKET',
                quantity=rounded_qty
            )

            logger.warning(f"⚠️ POSITION OPENED: {side} {quantity} {symbol}")

            result = {
                'order_id': order.get('orderId', order.get('orderListId', 'unknown')),
                'symbol': order.get('symbol', symbol),
                'side': order.get('side', side),
                'quantity': float(order.get('origQty', rounded_qty)),
                'executed_qty': float(order.get('executedQty', 0)),
                'status': order.get('status', 'UNKNOWN'),
                'time': order.get('updateTime', int(time.time() * 1000))
            }

            # Set stop loss if provided (Emergency Backup - without closePosition)
            if stop_loss:
                try:
                    sl_side = 'SELL' if side.upper() == 'BUY' else 'BUY'
                    # First try passing the quantity to support proper partial tracking if using hedge mode
                    try:
                        sl_order = self.client.futures_create_order(
                            symbol=symbol.upper(),
                            side=sl_side,
                            type='STOP_MARKET',
                            stopPrice=self.round_price(symbol, stop_loss),
                            quantity=rounded_qty,
                            reduceOnly=True
                        )
                    except BinanceAPIException as e:
                        logger.warning(f"⚠️ STOP_MARKET with quantity failed: {e}. Trying fallback with closePosition=True...")
                        sl_order = self.client.futures_create_order(
                            symbol=symbol.upper(),
                            side=sl_side,
                            type='STOP_MARKET',
                            stopPrice=self.round_price(symbol, stop_loss),
                            closePosition=True
                        )
                    
                    result['stop_loss'] = {
                        'order_id': sl_order.get('orderId', 'unknown'),
                        'price': stop_loss
                    }
                    logger.info(f"✅ Stop loss Emergency Stop set at {stop_loss}")
                except Exception as sl_err:
                    logger.error(f"⚠️ Could not set stop loss: {sl_err}")
                    result['stop_loss_error'] = str(sl_err)

            # Set Take Profit if provided
            if take_profit:
                try:
                    tp_side = 'SELL' if side.upper() == 'BUY' else 'BUY'
                    try:
                        tp_order = self.client.futures_create_order(
                            symbol=symbol.upper(),
                            side=tp_side,
                            type='TAKE_PROFIT_MARKET',
                            stopPrice=self.round_price(symbol, take_profit),
                            quantity=rounded_qty,
                            reduceOnly=True
                        )
                    except BinanceAPIException:
                        tp_order = self.client.futures_create_order(
                            symbol=symbol.upper(),
                            side=tp_side,
                            type='TAKE_PROFIT_MARKET',
                            stopPrice=self.round_price(symbol, take_profit),
                            closePosition=True
                        )
                    result['take_profit'] = {
                        'order_id': tp_order.get('orderId', 'unknown'),
                        'price': take_profit
                    }
                    logger.info(f"✅ Take profit set at {take_profit}")
                except Exception as tp_err:
                    logger.error(f"⚠️ Could not set take profit: {tp_err}")
                    result['take_profit_error'] = str(tp_err)

            return result

        except BinanceAPIException as e:
            logger.error(f"❌ Error opening position: {e}")
            return {'error': str(e)}

    def close_position(self, symbol: str) -> Dict:
        """
        Close all positions for a symbol.

        Args:
            symbol: Trading pair to close

        Returns:
            Result dict
        """
        if self.read_only:
            return {'error': '🔒 Trading disabled - read-only mode enabled'}

        if not self.api_key:
            return {'error': 'API key not configured'}

        self._rate_limit()
        try:
            # Get current position
            positions = self.get_positions(symbol=symbol)

            if not positions:
                return {'error': f'No open position for {symbol}'}

            position = positions[0]
            position_amt = position['position_amount']

            if position_amt == 0:
                return {'error': f'No position to close for {symbol}'}

            # Determine side to close (opposite of current position)
            side = 'SELL' if position_amt > 0 else 'BUY'
            
            # Make sure to round closing qty using floor logic as well
            quantity = abs(position_amt)
            rounded_qty = self.round_quantity(symbol, quantity)

            # Create closing order
            order = self.client.futures_create_order(
                symbol=symbol.upper(),
                side=side,
                type='MARKET',
                quantity=rounded_qty,
                reduceOnly=True
            )

            logger.warning(f"✅ POSITION CLOSED: {symbol}")
            
            # Follow Up: Cancel pending TP/SL orders for this closed symbol
            try:
                self.cancel_all_orders(symbol)
            except Exception as e:
                logger.error(f"⚠️ Warning: Could not cancel pending orders for {symbol} after close: {e}")

            return {
                'success': True,
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'quantity': float(order['origQty']),
                'status': order['status'],
                'pnl': position.get('unrealized_pnl', 0),
                'time': order['updateTime']
            }

        except BinanceAPIException as e:
            logger.error(f"❌ Error closing position: {e}")
            return {'error': str(e)}

    def cancel_all_orders(self, symbol: str) -> Dict:
        """Cancel all open orders for a symbol."""
        if self.read_only:
            return {'error': '🔒 Trading disabled - read-only mode enabled'}

        if not self.api_key:
            return {'error': 'API key not configured'}

        self._rate_limit()
        try:
            result = self.client.futures_cancel_all_open_orders(symbol=symbol.upper())
            logger.info(f"✅ All orders cancelled for {symbol}")
            return {'success': True, 'message': f'Cancelled all orders for {symbol}'}
        except BinanceAPIException as e:
            logger.error(f"❌ Error cancelling orders: {e}")
            return {'error': str(e)}

    def get_exit_orders(self, symbol: str) -> Dict:
        """
        Fetch attached stop_loss and take_profit metadata from exchange orders.
        Useful for syncing the recovery tracker.
        """
        open_orders = self.get_open_orders(symbol)
        
        result = {
            'stop_loss_price': None,
            'take_profit_price': None,
            'order_ids': []
        }
        
        if not open_orders:
            return result

        for order in open_orders:
            result['order_ids'].append(order['order_id'])
            
            if order['type'] == 'STOP_MARKET':
                # Original stopPrice comes inside the original API output but might be missing in custom mapping
                # However we can call API to fetch full raw details if it's missing or rely on current price 
                pass # Using direct client request for accuracy
                
        # Direct raw payload check
        try:
            self._rate_limit()
            raw_orders = self.client.futures_get_open_orders(symbol=symbol.upper())
            for ro in raw_orders:
                typ = ro.get('type')
                sp = float(ro.get('stopPrice', 0))
                if typ == 'STOP_MARKET' and sp > 0:
                    result['stop_loss_price'] = sp
                elif typ == 'TAKE_PROFIT_MARKET' and sp > 0:
                    result['take_profit_price'] = sp
        except Exception as e:
            logger.error(f"Error fetching exit orders for {symbol}: {e}")

        return result


# Singleton instance
_futures_manager = None

def get_futures_manager(testnet: bool = True, read_only: bool = True, max_leverage: int = 5) -> BinanceFuturesManager:
    """Get or create Futures manager instance."""
    global _futures_manager
    if _futures_manager is None:
        _futures_manager = BinanceFuturesManager(
            testnet=testnet,
            read_only=read_only,
            max_leverage=max_leverage
        )
    return _futures_manager
