from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from app.providers.bot_gold import (
    GoldPriceUnavailable,
    parse_bot_gold_page,
    parse_tpex_gold_payload,
)


def test_parses_bank_of_taiwan_buy_price() -> None:
    html = """
    <div>掛牌時間：2026/08/01 10:54</div>
    <table><tr><td>黃金存摺</td><td>本行賣出</td><td>4,241</td></tr>
    <tr><td>黃金存摺</td><td>本行買進</td><td>4,190</td></tr></table>
    """
    quote = parse_bot_gold_page(
        html,
        now=datetime(2026, 8, 1, tzinfo=timezone(timedelta(hours=8))),
    )
    assert quote.price_per_gram == Decimal("4190")
    assert quote.quoted_at.isoformat() == "2026-08-01T10:54:00+08:00"


def test_rejects_unrecognized_provider_page() -> None:
    with pytest.raises(GoldPriceUnavailable):
        parse_bot_gold_page("maintenance")


def test_parses_tpex_bot_gold_bid_and_converts_mace_to_grams() -> None:
    quote = parse_tpex_gold_payload(
        [
            {
                "Date": "1150731",
                "Time": "163004",
                "GoldCode": "AU9901",
                "QuotedBuyingB.Price": "15880",
            }
        ]
    )
    assert quote.price_per_gram == Decimal("15880") / Decimal("3.75")
    assert quote.quoted_at.isoformat() == "2026-07-31T16:30:04+08:00"
    assert quote.source.endswith("#AU9901-bid")


def test_rejects_tpex_payload_without_bot_gold() -> None:
    with pytest.raises(GoldPriceUnavailable):
        parse_tpex_gold_payload([{"GoldCode": "AU9902"}])
