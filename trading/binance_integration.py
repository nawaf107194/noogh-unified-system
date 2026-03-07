"""
Binance Integration Module for NOOGH System
Provides secure trading capabilities with safety guards and testnet support.
"""

import os
import time
from typing import Dict, List, Optional, Tuple
from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging

logger = logging.getLogger(__name__)


class BinanceManager:
    """
    Manages Binance API connections and trading operations with built-in safety features.

    Features:
    - Testnet and Production support
    - Rate limiting
    - Safety checks
    - Read-only mode
    """

    def __init__(self, testnet: bool = True, read_only: bool = True):
        """
        Initialize Binance Manager.

        Args:
            testnet: Use testnet (True) or production (False)
            read_only: Enable read-only mode (no trading)
        """
        self.testnet = testnet
        self.read_only = read_only
        self.client: Optional[Client] = None
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests

        # Load API credentials
        if testnet:
            self.api_key = os.getenv("BINANCE_TESTNET_API_KEY", "")
            self.api_secret = os.getenv("BINANCE_TESTNET_SECRET", "")
        else:
            self.api_key = os.getenv("BINANCE_API_KEY", "")
            self.api_secret = os.getenv("BINANCE_SECRET", "")

        self._connect()

    def _connect(self):
        """Establish connection to Binance API."""
        try:
            if not self.api_key or not self.api_secret:
                logger.warning("⚠️ Binance API credentials not found. Using public endpoints only.")
                self.client = Client("", "")
                if self.testnet:
                    self.client.API_URL = 'https://testnet.binance.vision/api'
                return

            self.client = Client(self.api_key, self.api_secret)

            if self.testnet:
                self.client.API_URL = 'https://testnet.binance.vision/api'
                logger.info("🧪 Connected to Binance Testnet")
            else:
                logger.info("🔗 Connected to Binance Production")

            # Test connection
            self.client.ping()
            logger.info("✅ Binance connection successful")

        except BinanceAPIException as e:
            logger.error(f"❌ Binance API Error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Connection Error: {e}")
            raise

    def _rate_limit(self):
        """Enforce rate limiting."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    # ============================================
    # PUBLIC ENDPOINTS (No authentication needed)
    # ============================================

    def get_server_time(self) -> int:
        """Get Binance server time."""
        self._rate_limit()
        return self.client.get_server_time()['serverTime']

    def get_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')

        Returns:
            Current price as float
        """
        self._rate_limit()
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol.upper())
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0

    def get_all_prices(self) -> Dict[str, float]:
        """Get all symbol prices."""
        self._rate_limit()
        try:
            tickers = self.client.get_all_tickers()
            return {t['symbol']: float(t['price']) for t in tickers}
        except BinanceAPIException as e:
            logger.error(f"Error fetching all prices: {e}")
            return {}

    def get_24h_ticker(self, symbol: str) -> Dict:
        """
        Get 24h ticker statistics.

        Returns:
            Dict with priceChange, priceChangePercent, volume, etc.
        """
        self._rate_limit()
        try:
            ticker = self.client.get_ticker(symbol=symbol.upper())
            return {
                'symbol': ticker['symbol'],
                'price': float(ticker['lastPrice']),
                'change': float(ticker['priceChange']),
                'change_percent': float(ticker['priceChangePercent']),
                'high': float(ticker['highPrice']),
                'low': float(ticker['lowPrice']),
                'volume': float(ticker['volume']),
                'quote_volume': float(ticker['quoteVolume'])
            }
        except BinanceAPIException as e:
            logger.error(f"Error fetching 24h ticker for {symbol}: {e}")
            return {}

    def get_orderbook(self, symbol: str, limit: int = 10) -> Dict:
        """Get order book depth."""
        self._rate_limit()
        try:
            depth = self.client.get_order_book(symbol=symbol.upper(), limit=limit)
            return {
                'bids': [(float(p), float(q)) for p, q in depth['bids'][:limit]],
                'asks': [(float(p), float(q)) for p, q in depth['asks'][:limit]]
            }
        except BinanceAPIException as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return {'bids': [], 'asks': []}

    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """
        Get candlestick data.

        Args:
            symbol: Trading pair
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Number of candles

        Returns:
            List of candles with OHLCV data
        """
        self._rate_limit()
        try:
            klines = self.client.get_klines(symbol=symbol.upper(), interval=interval, limit=limit)
            return [{
                'time': k[0],
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5])
            } for k in klines]
        except BinanceAPIException as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return []

    # ==========================================
    # AUTHENTICATED ENDPOINTS (Require API key)
    # ==========================================

    def get_account_info(self) -> Dict:
        """Get account information including balances."""
        if not self.api_key:
            return {'error': 'API key not configured'}

        self._rate_limit()
        try:
            account = self.client.get_account()
            balances = [
                {
                    'asset': b['asset'],
                    'free': float(b['free']),
                    'locked': float(b['locked']),
                    'total': float(b['free']) + float(b['locked'])
                }
                for b in account['balances']
                if float(b['free']) > 0 or float(b['locked']) > 0
            ]

            return {
                'can_trade': account['canTrade'],
                'can_withdraw': account['canWithdraw'],
                'can_deposit': account['canDeposit'],
                'balances': balances,
                'update_time': account['updateTime']
            }
        except BinanceAPIException as e:
            logger.error(f"Error fetching account info: {e}")
            return {'error': str(e)}

    def get_balance(self, asset: str = 'USDT') -> Tuple[float, float]:
        """
        Get balance for specific asset.

        Returns:
            Tuple of (free, locked) amounts
        """
        if not self.api_key:
            return (0.0, 0.0)

        self._rate_limit()
        try:
            balance = self.client.get_asset_balance(asset=asset.upper())
            return (float(balance['free']), float(balance['locked']))
        except BinanceAPIException as e:
            logger.error(f"Error fetching balance for {asset}: {e}")
            return (0.0, 0.0)

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders."""
        if not self.api_key:
            return []

        self._rate_limit()
        try:
            if symbol:
                orders = self.client.get_open_orders(symbol=symbol.upper())
            else:
                orders = self.client.get_open_orders()

            return [{
                'symbol': o['symbol'],
                'order_id': o['orderId'],
                'side': o['side'],
                'type': o['type'],
                'price': float(o['price']),
                'quantity': float(o['origQty']),
                'executed_qty': float(o['executedQty']),
                'status': o['status'],
                'time': o['time']
            } for o in orders]
        except BinanceAPIException as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    def get_recent_trades(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Get recent trades for account."""
        if not self.api_key:
            return []

        self._rate_limit()
        try:
            trades = self.client.get_my_trades(symbol=symbol.upper(), limit=limit)
            return [{
                'id': t['id'],
                'order_id': t['orderId'],
                'price': float(t['price']),
                'qty': float(t['qty']),
                'commission': float(t['commission']),
                'commission_asset': t['commissionAsset'],
                'time': t['time'],
                'is_buyer': t['isBuyer']
            } for t in trades]
        except BinanceAPIException as e:
            logger.error(f"Error fetching recent trades: {e}")
            return []

    # ==========================================
    # TRADING OPERATIONS (With safety checks)
    # ==========================================

    def create_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """
        Create a market order (BUY or SELL).

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Amount to trade

        Returns:
            Order result dict
        """
        if self.read_only:
            return {'error': 'Trading disabled (read-only mode)'}

        if not self.api_key:
            return {'error': 'API key not configured'}

        self._rate_limit()
        try:
            order = self.client.order_market(
                symbol=symbol.upper(),
                side=side.upper(),
                quantity=quantity
            )

            logger.info(f"✅ Market order created: {side} {quantity} {symbol}")
            return {
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'status': order['status'],
                'executed_qty': float(order['executedQty']),
                'time': order['transactTime']
            }
        except BinanceAPIException as e:
            logger.error(f"❌ Error creating market order: {e}")
            return {'error': str(e)}

    def create_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """
        Create a limit order.

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Amount to trade
            price: Limit price

        Returns:
            Order result dict
        """
        if self.read_only:
            return {'error': 'Trading disabled (read-only mode)'}

        if not self.api_key:
            return {'error': 'API key not configured'}

        self._rate_limit()
        try:
            order = self.client.order_limit(
                symbol=symbol.upper(),
                side=side.upper(),
                quantity=quantity,
                price=str(price)
            )

            logger.info(f"✅ Limit order created: {side} {quantity} {symbol} @ {price}")
            return {
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'price': float(order['price']),
                'quantity': float(order['origQty']),
                'status': order['status'],
                'time': order['transactTime']
            }
        except BinanceAPIException as e:
            logger.error(f"❌ Error creating limit order: {e}")
            return {'error': str(e)}

    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an open order."""
        if self.read_only:
            return {'error': 'Trading disabled (read-only mode)'}

        if not self.api_key:
            return {'error': 'API key not configured'}

        self._rate_limit()
        try:
            result = self.client.cancel_order(symbol=symbol.upper(), orderId=order_id)
            logger.info(f"✅ Order cancelled: {order_id}")
            return {
                'order_id': result['orderId'],
                'symbol': result['symbol'],
                'status': result['status']
            }
        except BinanceAPIException as e:
            logger.error(f"❌ Error cancelling order: {e}")
            return {'error': str(e)}

    # ==========================================
    # UTILITY FUNCTIONS
    # ==========================================

    def get_symbol_info(self, symbol: str) -> Dict:
        """Get trading rules for a symbol."""
        self._rate_limit()
        try:
            info = self.client.get_symbol_info(symbol=symbol.upper())
            return {
                'symbol': info['symbol'],
                'status': info['status'],
                'base_asset': info['baseAsset'],
                'quote_asset': info['quoteAsset'],
                'filters': info['filters']
            }
        except BinanceAPIException as e:
            logger.error(f"Error fetching symbol info: {e}")
            return {}

    def format_amount(self, symbol: str, amount: float) -> str:
        """Format amount according to symbol precision."""
        info = self.get_symbol_info(symbol)
        if not info:
            return str(amount)

        # Get LOT_SIZE filter
        for f in info.get('filters', []):
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                precision = len(str(step_size).rstrip('0').split('.')[-1])
                return f"{amount:.{precision}f}"

        return str(amount)


# Singleton instance
_binance_manager = None

def get_binance_manager(testnet: bool = True, read_only: bool = True) -> BinanceManager:
    """Get or create Binance manager instance."""
    global _binance_manager
    if _binance_manager is None:
        _binance_manager = BinanceManager(testnet=testnet, read_only=read_only)
    return _binance_manager
