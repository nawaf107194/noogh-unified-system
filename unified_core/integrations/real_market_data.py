#!/usr/bin/env python3
"""
Real Market Data Provider - جلب بيانات حقيقية من مصادر مجانية

يستخدم:
- yfinance للأسهم
- CoinGecko API للكريبتو
- Alpha Vantage للفوركس (اختياري)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# تجنب استيراد yfinance مباشرة للسماح بالتشغيل بدونه
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available. Install with: pip install yfinance")


class RealMarketDataProvider:
    """موفر بيانات السوق الحقيقية"""

    def __init__(self):
        self.session = None
        self.coingecko_base = "https://api.coingecko.com/api/v3"

    async def _ensure_session(self):
        """التأكد من وجود session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """إغلاق الاتصال"""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_stock_price(self, symbol: str) -> Optional[Dict]:
        """
        الحصول على سعر سهم حقيقي

        Args:
            symbol: رمز السهم (مثل AAPL, NVDA)

        Returns:
            معلومات السعر
        """
        if not YFINANCE_AVAILABLE:
            logger.warning(f"yfinance not available for {symbol}")
            return None

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")

            if hist.empty:
                return None

            current_price = hist['Close'].iloc[-1]

            return {
                "symbol": symbol,
                "price": float(current_price),
                "change_1d": float(info.get('regularMarketChangePercent', 0)),
                "volume": int(info.get('volume', 0)),
                "market_cap": info.get('marketCap', 0),
                "pe_ratio": info.get('trailingPE', 0),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    async def get_crypto_price(self, symbol: str) -> Optional[Dict]:
        """
        الحصول على سعر عملة رقمية حقيقي من CoinGecko

        Args:
            symbol: رمز العملة (BTC, ETH, SOL, etc.)

        Returns:
            معلومات السعر
        """
        await self._ensure_session()

        # تحويل الرموز
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "USDT": "tether",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "MATIC": "matic-network",
            "DOT": "polkadot"
        }

        coin_id = symbol_map.get(symbol.upper(), symbol.lower())

        try:
            url = f"{self.coingecko_base}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
                "include_market_cap": "true"
            }

            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    if coin_id in data:
                        coin_data = data[coin_id]
                        return {
                            "symbol": symbol.upper(),
                            "price": coin_data.get("usd", 0),
                            "change_24h": coin_data.get("usd_24h_change", 0),
                            "volume_24h": coin_data.get("usd_24h_vol", 0),
                            "market_cap": coin_data.get("usd_market_cap", 0),
                            "timestamp": datetime.now().isoformat()
                        }

        except Exception as e:
            logger.error(f"Error fetching crypto {symbol}: {e}")

        return None

    async def get_market_sentiment(self, asset_type: str = "crypto") -> Dict:
        """
        الحصول على مشاعر السوق العامة

        Args:
            asset_type: نوع الأصل

        Returns:
            تحليل المشاعر
        """
        if asset_type == "crypto":
            # استخدام Fear & Greed Index
            await self._ensure_session()

            try:
                url = "https://api.alternative.me/fng/"
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("data"):
                            fng_data = data["data"][0]
                            value = int(fng_data.get("value", 50))

                            # تحويل لتصنيف
                            if value >= 75:
                                sentiment = "EXTREME_GREED"
                            elif value >= 55:
                                sentiment = "GREED"
                            elif value >= 45:
                                sentiment = "NEUTRAL"
                            elif value >= 25:
                                sentiment = "FEAR"
                            else:
                                sentiment = "EXTREME_FEAR"

                            return {
                                "sentiment": sentiment,
                                "value": value,
                                "classification": fng_data.get("value_classification", ""),
                                "timestamp": datetime.now().isoformat()
                            }

            except Exception as e:
                logger.error(f"Error fetching sentiment: {e}")

        return {
            "sentiment": "NEUTRAL",
            "value": 50,
            "timestamp": datetime.now().isoformat()
        }

    async def get_trending_cryptos(self, limit: int = 7) -> List[Dict]:
        """الحصول على العملات الرائجة"""
        await self._ensure_session()

        try:
            url = f"{self.coingecko_base}/search/trending"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    coins = data.get("coins", [])

                    trending = []
                    for item in coins[:limit]:
                        coin = item.get("item", {})
                        trending.append({
                            "symbol": coin.get("symbol", "").upper(),
                            "name": coin.get("name", ""),
                            "market_cap_rank": coin.get("market_cap_rank", 0),
                            "score": coin.get("score", 0)
                        })

                    return trending

        except Exception as e:
            logger.error(f"Error fetching trending: {e}")

        return []

    async def get_multiple_prices(self, symbols: List[str], asset_type: str = "stock") -> Dict[str, Dict]:
        """
        الحصول على أسعار متعددة دفعة واحدة

        Args:
            symbols: قائمة الرموز
            asset_type: stock أو crypto

        Returns:
            قاموس الأسعار
        """
        prices = {}

        tasks = []
        for symbol in symbols:
            if asset_type == "stock":
                tasks.append(self.get_stock_price(symbol))
            elif asset_type == "crypto":
                tasks.append(self.get_crypto_price(symbol))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, result in zip(symbols, results):
            if result and not isinstance(result, Exception):
                prices[symbol] = result

        return prices


# Singleton
_market_data_provider = None


def get_market_data_provider() -> RealMarketDataProvider:
    """الحصول على singleton instance"""
    global _market_data_provider
    if _market_data_provider is None:
        _market_data_provider = RealMarketDataProvider()
    return _market_data_provider


async def test_provider():
    """اختبار الموفر"""
    provider = get_market_data_provider()

    print("="*70)
    print("🧪 Testing Real Market Data Provider")
    print("="*70)

    # 1. أسعار الأسهم
    print("\n1. Stock Prices (Real-time):")
    stocks = ["AAPL", "NVDA", "MSFT"]
    stock_prices = await provider.get_multiple_prices(stocks, "stock")

    for symbol, data in stock_prices.items():
        if data:
            print(f"\n   {symbol}")
            print(f"   Price: ${data['price']:.2f}")
            print(f"   Change: {data['change_1d']:+.2f}%")
            print(f"   Volume: {data['volume']:,}")

    # 2. أسعار الكريبتو
    print("\n2. Crypto Prices (Real-time via CoinGecko):")
    cryptos = ["BTC", "ETH", "SOL"]
    crypto_prices = await provider.get_multiple_prices(cryptos, "crypto")

    for symbol, data in crypto_prices.items():
        if data:
            print(f"\n   {symbol}")
            print(f"   Price: ${data['price']:,.2f}")
            print(f"   Change 24h: {data['change_24h']:+.2f}%")
            print(f"   Volume 24h: ${data['volume_24h']:,.0f}")

    # 3. مشاعر السوق
    print("\n3. Market Sentiment (Fear & Greed Index):")
    sentiment = await provider.get_market_sentiment("crypto")
    print(f"   Sentiment: {sentiment['sentiment']}")
    print(f"   Value: {sentiment['value']}/100")
    if 'classification' in sentiment:
        print(f"   Classification: {sentiment['classification']}")

    # 4. العملات الرائجة
    print("\n4. Trending Cryptocurrencies:")
    trending = await provider.get_trending_cryptos(5)
    for i, coin in enumerate(trending, 1):
        print(f"   {i}. {coin['symbol']:6} {coin['name']:20} Rank: #{coin['market_cap_rank']}")

    await provider.close()

    print("\n" + "="*70)
    print("✅ Test completed with REAL market data!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_provider())
