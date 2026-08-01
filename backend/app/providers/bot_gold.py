import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.request import Request, urlopen

BOT_GOLD_URL = "https://rate.bot.com.tw/gold?Lang=zh-TW"
TPEX_GOLD_URL = "https://www.tpex.org.tw/openapi/v1/tpex_gold_latest"
TPEX_BOT_GOLD_CODE = "AU9901"
GRAMS_PER_MACE = Decimal("3.75")
TAIPEI_TIMEZONE = timezone(timedelta(hours=8))
_PRICE_PATTERN = re.compile(r"黃金存摺.*?本行買進.*?([0-9][0-9,]*)", re.DOTALL)
_TIME_PATTERN = re.compile(
    r"掛牌時間[：:]\s*(?:(\d{4})/(\d{2})/(\d{2})\s*)?(\d{2}):(\d{2})"
)


@dataclass(frozen=True)
class GoldQuote:
    price_per_gram: Decimal
    quoted_at: datetime
    source: str = BOT_GOLD_URL


class GoldPriceUnavailable(RuntimeError):
    pass


async def fetch_bot_gold_price() -> GoldQuote:
    return await asyncio.to_thread(_fetch_sync)


async def fetch_reference_gold_price() -> GoldQuote:
    """Prefer BOT's passbook quote and fall back to TPEx's official BOT-gold bid."""
    try:
        return await fetch_bot_gold_price()
    except GoldPriceUnavailable:
        return await asyncio.to_thread(_fetch_tpex_sync)


def parse_bot_gold_page(html: str, now: datetime | None = None) -> GoldQuote:
    price_match = _PRICE_PATTERN.search(html)
    time_match = _TIME_PATTERN.search(html)
    if price_match is None or time_match is None:
        raise GoldPriceUnavailable("臺銀黃金牌價格式無法辨識")

    active_now = (
        now.astimezone(TAIPEI_TIMEZONE) if now else datetime.now(TAIPEI_TIMEZONE)
    )
    year, month, day, hour, minute = time_match.groups()
    quoted_at = datetime(
        int(year) if year else active_now.year,
        int(month) if month else active_now.month,
        int(day) if day else active_now.day,
        int(hour),
        int(minute),
        tzinfo=TAIPEI_TIMEZONE,
    )
    return GoldQuote(
        price_per_gram=Decimal(price_match.group(1).replace(",", "")),
        quoted_at=quoted_at,
    )


def parse_tpex_gold_payload(payload: object) -> GoldQuote:
    if not isinstance(payload, list):
        raise GoldPriceUnavailable("櫃買中心黃金報價格式無法辨識")
    row = next(
        (
            item
            for item in payload
            if isinstance(item, dict) and item.get("GoldCode") == TPEX_BOT_GOLD_CODE
        ),
        None,
    )
    if row is None:
        raise GoldPriceUnavailable("櫃買中心沒有臺銀金報價")
    try:
        roc_date = str(row["Date"])
        quote_time = str(row["Time"])
        if len(roc_date) != 7 or len(quote_time) != 6:
            raise ValueError
        quoted_at = datetime(
            int(roc_date[:3]) + 1911,
            int(roc_date[3:5]),
            int(roc_date[5:7]),
            int(quote_time[:2]),
            int(quote_time[2:4]),
            int(quote_time[4:6]),
            tzinfo=TAIPEI_TIMEZONE,
        )
        bid_per_mace = Decimal(str(row["QuotedBuyingB.Price"]))
        if bid_per_mace <= 0:
            raise ValueError
    except (KeyError, ValueError, ArithmeticError) as error:
        raise GoldPriceUnavailable("櫃買中心臺銀金報價格式無法辨識") from error
    return GoldQuote(
        price_per_gram=bid_per_mace / GRAMS_PER_MACE,
        quoted_at=quoted_at,
        source=f"{TPEX_GOLD_URL}#AU9901-bid",
    )


def _fetch_sync() -> GoldQuote:
    request = Request(BOT_GOLD_URL, headers={"User-Agent": "Personal-Asset-OS/0.1"})
    try:
        with urlopen(request, timeout=8) as response:  # noqa: S310
            html = response.read().decode("utf-8")
    except OSError as error:
        raise GoldPriceUnavailable("臺銀黃金牌價目前無法取得") from error
    return parse_bot_gold_page(html)


def _fetch_tpex_sync() -> GoldQuote:
    request = Request(TPEX_GOLD_URL, headers={"User-Agent": "Personal-Asset-OS/0.1"})
    try:
        with urlopen(request, timeout=8) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoldPriceUnavailable("官方黃金參考價目前無法取得") from error
    return parse_tpex_gold_payload(payload)
