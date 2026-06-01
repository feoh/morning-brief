"""Market price briefing module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import requests

from .base import BriefSection

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


@dataclass(frozen=True)
class MarketAsset:
    """A tracked market asset."""

    symbol: str
    label: str


@dataclass(frozen=True)
class MarketPrice:
    """Fetched market price data for one asset."""

    asset: MarketAsset
    price: float | None
    currency: str | None = "USD"
    error: str | None = None


DEFAULT_ASSETS = (
    MarketAsset("AMZN", "Amazon"),
    MarketAsset("GOOG", "Alphabet"),
    MarketAsset("AAPL", "Apple"),
    MarketAsset("MSFT", "Microsoft"),
    MarketAsset("BTC-USD", "Bitcoin"),
    MarketAsset("ETH-USD", "Ethereum"),
)


class MarketsModule:
    """Build a brief section containing current stock and crypto prices."""

    name = "markets"

    def __init__(self, assets: tuple[MarketAsset, ...] = DEFAULT_ASSETS) -> None:
        self.assets = assets

    def build_section(self) -> BriefSection:
        """Build the market-prices section."""

        prices = [fetch_price(asset) for asset in self.assets]
        return BriefSection(title="Markets", body=format_market_prices(prices))


def fetch_price(asset: MarketAsset) -> MarketPrice:
    """Fetch the current/latest price for one asset from Yahoo Finance's chart API."""

    try:
        response = requests.get(
            YAHOO_CHART_URL.format(symbol=asset.symbol),
            params={"range": "1d", "interval": "1m"},
            headers={"User-Agent": "Mozilla/5.0 (compatible; morning-brief/0.1)"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload["chart"]["result"][0]
        meta = result.get("meta", {})
        price = _extract_price(meta, result)
        currency = meta.get("currency", "USD")
        if price is None:
            return MarketPrice(
                asset=asset, price=None, currency=currency, error="price unavailable"
            )
        return MarketPrice(asset=asset, price=price, currency=currency)
    except requests.RequestException as exc:
        return MarketPrice(asset=asset, price=None, error=f"network error: {exc}")
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return MarketPrice(asset=asset, price=None, error=f"parse error: {exc}")


def _extract_price(meta: dict[str, Any], result: dict[str, Any]) -> float | None:
    """Extract the most useful price from a Yahoo Finance chart result."""

    for key in ("regularMarketPrice", "previousClose"):
        value = meta.get(key)
        if value is not None:
            return float(value)

    quotes = result.get("indicators", {}).get("quote", [])
    if not quotes:
        return None

    closes = quotes[0].get("close", [])
    for value in reversed(closes):
        if value is not None:
            return float(value)
    return None


def format_market_prices(prices: list[MarketPrice]) -> str:
    """Format market prices as Discord-friendly Markdown."""

    lines = [f"_As of {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_", ""]
    for market_price in prices:
        symbol = market_price.asset.symbol.replace("-USD", "")
        label = market_price.asset.label
        if market_price.price is None:
            detail = f"unavailable ({market_price.error or 'unknown error'})"
        else:
            detail = (
                f"{_currency_prefix(market_price.currency)}{market_price.price:,.2f}"
            )
        lines.append(f"- **{symbol}** ({label}): {detail}")
    return "\n".join(lines)


def _currency_prefix(currency: str | None) -> str:
    """Return a display prefix for a currency code."""

    if currency in {None, "USD", "$"}:
        return "$"
    return f"{currency} "
