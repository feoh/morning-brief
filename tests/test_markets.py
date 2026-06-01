from __future__ import annotations

from importlib import import_module


def test_format_market_prices() -> None:
    markets = import_module("morning_brief.modules.markets")
    prices = [
        markets.MarketPrice(
            asset=markets.MarketAsset("AMZN", "Amazon"),
            price=123.45,
            currency="USD",
        ),
        markets.MarketPrice(
            asset=markets.MarketAsset("BTC-USD", "Bitcoin"),
            price=None,
            error="nope",
        ),
    ]

    output = markets.format_market_prices(prices)

    assert "**AMZN** (Amazon): $123.45" in output
    assert "**BTC** (Bitcoin): unavailable (nope)" in output
