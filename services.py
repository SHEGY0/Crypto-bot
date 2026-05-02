import aiohttp
import asyncio
from config import COINGECKO_API, COIN_IDS, SUPPORTED_CRYPTO

_rate_cache = {}
_cache_ts = 0
CACHE_TTL = 60  # seconds


async def fetch_rates() -> dict:
    """Fetch live rates from CoinGecko"""
    global _rate_cache, _cache_ts
    import time
    now = time.time()
    if _rate_cache and now - _cache_ts < CACHE_TTL:
        return _rate_cache

    ids = ",".join(COIN_IDS[c] for c in SUPPORTED_CRYPTO if c in COIN_IDS)
    url = f"{COINGECKO_API}/simple/price?ids={ids}&vs_currencies=usd,rub,eur&include_24hr_change=true"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()

        rates = {}
        for symbol, cg_id in COIN_IDS.items():
            if cg_id in data:
                rates[symbol] = {
                    "usd": data[cg_id].get("usd", 0),
                    "rub": data[cg_id].get("rub", 0),
                    "eur": data[cg_id].get("eur", 0),
                    "change_24h": data[cg_id].get("usd_24h_change", 0),
                }

        _rate_cache = rates
        _cache_ts = now
        return rates
    except Exception as e:
        # Return cached data on error
        if _rate_cache:
            return _rate_cache
        raise e


async def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get exchange rate from one currency to another"""
    rates = await fetch_rates()

    fiat_map = {"USD": 1.0}

    # Refresh rates to get EUR/RUB
    if rates:
        sample = next(iter(rates.values()))
        eur_rate = 1 / sample.get("eur", 1) if sample.get("usd") and sample.get("eur") else None
        rub_rate = 1 / sample.get("rub", 1) if sample.get("usd") and sample.get("rub") else None

    # Both crypto
    if from_currency in rates and to_currency in rates:
        from_usd = rates[from_currency]["usd"]
        to_usd = rates[to_currency]["usd"]
        return from_usd / to_usd

    # Crypto to fiat
    if from_currency in rates:
        if to_currency == "USD":
            return rates[from_currency]["usd"]
        elif to_currency == "RUB":
            return rates[from_currency]["rub"]
        elif to_currency == "EUR":
            return rates[from_currency]["eur"]

    # Fiat to crypto
    if to_currency in rates:
        if from_currency == "USD":
            return 1 / rates[to_currency]["usd"]
        elif from_currency == "RUB":
            return 1 / rates[to_currency]["rub"]
        elif from_currency == "EUR":
            return 1 / rates[to_currency]["eur"]

    return 1.0


def format_rate_change(change: float) -> str:
    if change > 0:
        return f"🟢 +{change:.2f}%"
    elif change < 0:
        return f"🔴 {change:.2f}%"
    return f"⚪ {change:.2f}%"
