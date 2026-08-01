from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

GRAMS_PER_UNIT = {
    "gram": Decimal("1"),
    "mace": Decimal("3.75"),
    "tael": Decimal("37.5"),
}
EIGHT_PLACES = Decimal("0.00000001")
TWO_PLACES = Decimal("0.01")


class DomainRuleError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def to_grams(quantity: Decimal, unit: str) -> Decimal:
    if quantity <= 0:
        raise DomainRuleError("QUANTITY_MUST_BE_POSITIVE", "數量必須大於0")
    try:
        factor = GRAMS_PER_UNIT[unit]
    except KeyError as error:
        raise DomainRuleError("UNSUPPORTED_GOLD_UNIT", "不支援的黃金單位") from error
    return (quantity * factor).quantize(EIGHT_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class GoldBuyResult:
    quantity_grams: Decimal
    total_cost: Decimal
    bank_outflow: Decimal

    @property
    def average_cost(self) -> Decimal:
        return self.total_cost / self.quantity_grams


@dataclass(frozen=True)
class GoldSellResult:
    quantity_grams: Decimal
    total_cost: Decimal
    bank_inflow: Decimal
    cost_removed: Decimal
    realized_profit: Decimal


def apply_gold_buy(
    current_quantity: Decimal,
    current_cost: Decimal,
    bought_grams: Decimal,
    gross_amount: Decimal,
    fees: Decimal,
) -> GoldBuyResult:
    _validate_money(gross_amount, fees)
    return GoldBuyResult(
        quantity_grams=current_quantity + bought_grams,
        total_cost=current_cost + gross_amount + fees,
        bank_outflow=gross_amount + fees,
    )


def apply_gold_sell(
    current_quantity: Decimal,
    current_cost: Decimal,
    sold_grams: Decimal,
    gross_amount: Decimal,
    fees: Decimal,
) -> GoldSellResult:
    _validate_money(gross_amount, fees)
    if sold_grams > current_quantity:
        raise DomainRuleError("INSUFFICIENT_GOLD", "賣出數量超過目前持有量")
    average_cost = current_cost / current_quantity
    cost_removed = average_cost * sold_grams
    bank_inflow = gross_amount - fees
    if bank_inflow < 0:
        raise DomainRuleError("FEES_EXCEED_PROCEEDS", "費用不得超過賣出價款")
    remaining_quantity = current_quantity - sold_grams
    remaining_cost = current_cost - cost_removed
    if remaining_quantity == 0:
        remaining_cost = Decimal("0")
    return GoldSellResult(
        quantity_grams=remaining_quantity,
        total_cost=remaining_cost,
        bank_inflow=bank_inflow,
        cost_removed=cost_removed,
        realized_profit=bank_inflow - cost_removed,
    )


def gold_market_value(
    quantity_grams: Decimal,
    purity: Decimal,
    reference_price: Decimal | None,
    override_price: Decimal | None,
) -> Decimal | None:
    if override_price is not None:
        return (quantity_grams * override_price).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
    if reference_price is None:
        return None
    return (quantity_grams * purity * reference_price).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )


def _validate_money(gross_amount: Decimal, fees: Decimal) -> None:
    if gross_amount <= 0:
        raise DomainRuleError("AMOUNT_MUST_BE_POSITIVE", "成交價款必須大於0")
    if fees < 0:
        raise DomainRuleError("FEES_MUST_NOT_BE_NEGATIVE", "費用不得小於0")
