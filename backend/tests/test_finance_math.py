from decimal import Decimal

import pytest
from app.services.finance_math import (
    DomainRuleError,
    apply_gold_buy,
    apply_gold_sell,
    gold_market_value,
    to_grams,
)


def test_gold_units_are_normalized_to_grams() -> None:
    assert to_grams(Decimal("2"), "mace") == Decimal("7.50000000")
    assert to_grams(Decimal("1"), "tael") == Decimal("37.50000000")


def test_moving_average_buy_and_sell_preserves_remaining_average() -> None:
    bought = apply_gold_buy(
        Decimal("10"),
        Decimal("20000"),
        Decimal("10"),
        Decimal("30000"),
        Decimal("100"),
    )
    assert bought.quantity_grams == Decimal("20")
    assert bought.total_cost == Decimal("50100")
    assert bought.bank_outflow == Decimal("30100")

    sold = apply_gold_sell(
        bought.quantity_grams,
        bought.total_cost,
        Decimal("5"),
        Decimal("15000"),
        Decimal("50"),
    )
    assert sold.quantity_grams == Decimal("15")
    assert sold.total_cost == Decimal("37575")
    assert sold.cost_removed == Decimal("12525")
    assert sold.bank_inflow == Decimal("14950")
    assert sold.realized_profit == Decimal("2425")


def test_sell_more_gold_than_owned_is_hard_rejected() -> None:
    with pytest.raises(DomainRuleError) as error:
        apply_gold_sell(
            Decimal("1"),
            Decimal("1000"),
            Decimal("2"),
            Decimal("2000"),
            Decimal("0"),
        )
    assert error.value.code == "INSUFFICIENT_GOLD"


def test_physical_gold_valuation_applies_purity_and_override() -> None:
    assert gold_market_value(
        Decimal("10"), Decimal("0.9"), Decimal("4000"), None
    ) == Decimal("36000.00")
    assert gold_market_value(
        Decimal("10"), Decimal("0.9"), Decimal("4000"), Decimal("3800")
    ) == Decimal("38000.00")
