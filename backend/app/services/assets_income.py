from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import (
    BankAccount,
    CashEntry,
    GoldHolding,
    GoldPrice,
    GoldTransaction,
    InsuranceEvent,
    InsurancePolicy,
    SalaryRecord,
    SalaryTemplate,
)
from app.providers.bot_gold import GoldQuote, fetch_reference_gold_price
from app.services.finance_math import (
    DomainRuleError,
    apply_gold_buy,
    apply_gold_sell,
    gold_market_value,
    to_grams,
)


async def bank_balance(session: AsyncSession, account_id: UUID) -> Decimal:
    account = await session.get(BankAccount, account_id)
    if account is None:
        raise DomainRuleError("BANK_ACCOUNT_NOT_FOUND", "找不到銀行帳戶")
    entries = await session.scalar(
        select(func.coalesce(func.sum(CashEntry.amount), Decimal("0"))).where(
            CashEntry.bank_account_id == account_id
        )
    )
    return account.opening_balance + (entries or Decimal("0"))


async def create_bank_account(
    session: AsyncSession, name: str, opening_balance: Decimal
) -> BankAccount:
    if opening_balance < 0:
        raise DomainRuleError("NEGATIVE_OPENING_BALANCE", "期初現金不得小於0")
    account = BankAccount(name=name.strip(), opening_balance=opening_balance)
    session.add(account)
    await session.flush()
    return account


async def list_bank_accounts(session: AsyncSession) -> list[dict[str, object]]:
    statement = select(BankAccount).order_by(BankAccount.created_at)
    accounts = list((await session.scalars(statement)).all())
    return [
        {
            "id": str(account.id),
            "name": account.name,
            "balance": money(await bank_balance(session, account.id)),
        }
        for account in accounts
    ]


async def create_opening_gold(
    session: AsyncSession,
    *,
    name: str,
    holding_type: str,
    quantity: Decimal,
    unit: str,
    purity: Decimal,
    total_cost: Decimal,
    valuation_price: Decimal | None,
    valuation_date: date | None,
    valuation_reason: str | None,
) -> GoldHolding:
    grams = to_grams(quantity, unit)
    _validate_gold_holding(holding_type, purity, total_cost)
    if valuation_price is not None and valuation_price <= 0:
        raise DomainRuleError("INVALID_VALUATION_PRICE", "覆寫估值必須大於0")
    holding = GoldHolding(
        name=name.strip(),
        holding_type=holding_type,
        quantity_grams=grams,
        total_cost=total_cost,
        purity=Decimal("1") if holding_type == "passbook" else purity,
        manual_price_per_gram=valuation_price,
        manual_price_date=valuation_date,
        manual_price_reason=valuation_reason,
    )
    session.add(holding)
    await session.flush()
    session.add(
        GoldTransaction(
            holding_id=holding.id,
            bank_account_id=None,
            kind="opening",
            occurred_on=valuation_date or date.today(),
            quantity_grams=grams,
            gross_amount=total_cost,
            fees=Decimal("0"),
            cost_removed=Decimal("0"),
            realized_profit=Decimal("0"),
            original_quantity=quantity,
            original_unit=unit,
            reason="期初黃金",
        )
    )
    return holding


async def transact_gold(
    session: AsyncSession,
    *,
    holding_id: UUID,
    bank_account_id: UUID,
    kind: str,
    occurred_on: date,
    quantity: Decimal,
    unit: str,
    gross_amount: Decimal,
    fees: Decimal,
) -> GoldTransaction:
    holding = await session.scalar(
        select(GoldHolding).where(GoldHolding.id == holding_id).with_for_update()
    )
    if holding is None:
        raise DomainRuleError("GOLD_HOLDING_NOT_FOUND", "找不到黃金持有項目")
    account = await session.scalar(
        select(BankAccount).where(BankAccount.id == bank_account_id).with_for_update()
    )
    if account is None:
        raise DomainRuleError("BANK_ACCOUNT_NOT_FOUND", "找不到銀行帳戶")
    grams = to_grams(quantity, unit)
    transaction_id = uuid4()
    if kind == "buy":
        result = apply_gold_buy(
            holding.quantity_grams,
            holding.total_cost,
            grams,
            gross_amount,
            fees,
        )
        available = await bank_balance(session, bank_account_id)
        if available < result.bank_outflow:
            raise DomainRuleError("INSUFFICIENT_CASH", "銀行餘額不足，黃金買入未成立")
        holding.quantity_grams = result.quantity_grams
        holding.total_cost = result.total_cost
        cash_amount = -result.bank_outflow
        cost_removed = Decimal("0")
        realized_profit = Decimal("0")
    elif kind == "sell":
        sell = apply_gold_sell(
            holding.quantity_grams,
            holding.total_cost,
            grams,
            gross_amount,
            fees,
        )
        holding.quantity_grams = sell.quantity_grams
        holding.total_cost = sell.total_cost
        cash_amount = sell.bank_inflow
        cost_removed = sell.cost_removed
        realized_profit = sell.realized_profit
    else:
        raise DomainRuleError("INVALID_GOLD_TRANSACTION", "黃金交易只接受買入或賣出")

    transaction = GoldTransaction(
        id=transaction_id,
        holding_id=holding_id,
        bank_account_id=bank_account_id,
        kind=kind,
        occurred_on=occurred_on,
        quantity_grams=grams,
        gross_amount=gross_amount,
        fees=fees,
        cost_removed=cost_removed,
        realized_profit=realized_profit,
        original_quantity=quantity,
        original_unit=unit,
    )
    session.add_all(
        [
            transaction,
            CashEntry(
                bank_account_id=bank_account_id,
                occurred_on=occurred_on,
                amount=cash_amount,
                kind=f"gold_{kind}",
                reference_type="gold_transaction",
                reference_id=transaction_id,
                description=holding.name,
            ),
        ]
    )
    await session.flush()
    return transaction


async def latest_gold_price(
    session: AsyncSession,
    *,
    refresh: bool = True,
    fetcher: Callable[[], Awaitable[GoldQuote]] = fetch_reference_gold_price,
) -> tuple[GoldPrice | None, bool]:
    latest = await session.scalar(
        select(GoldPrice).order_by(GoldPrice.quoted_at.desc()).limit(1)
    )
    today = datetime.now(UTC).date()
    if latest is not None and latest.fetched_at.date() >= today:
        return latest, False
    if refresh:
        try:
            quote = await fetcher()
        except RuntimeError:
            return latest, latest is not None
        latest = GoldPrice(
            price_per_gram=quote.price_per_gram,
            quoted_at=quote.quoted_at,
            source=quote.source,
        )
        session.add(latest)
        await session.flush()
        return latest, False
    return latest, latest is not None


async def list_gold_holdings(
    session: AsyncSession, reference_price: GoldPrice | None
) -> list[dict[str, object]]:
    statement = select(GoldHolding).order_by(GoldHolding.created_at)
    holdings = list((await session.scalars(statement)).all())
    result: list[dict[str, object]] = []
    for holding in holdings:
        average = (
            holding.total_cost / holding.quantity_grams
            if holding.quantity_grams > 0
            else Decimal("0")
        )
        value = gold_market_value(
            holding.quantity_grams,
            holding.purity,
            reference_price.price_per_gram if reference_price else None,
            holding.manual_price_per_gram,
        )
        value_date = (
            holding.manual_price_date
            if holding.manual_price_per_gram is not None
            else reference_price.quoted_at.date()
            if reference_price
            else None
        )
        result.append(
            {
                "id": str(holding.id),
                "name": holding.name,
                "holding_type": holding.holding_type,
                "quantity_grams": decimal_text(holding.quantity_grams),
                "purity": decimal_text(holding.purity),
                "total_cost": money(holding.total_cost),
                "average_cost_per_gram": money(average),
                "market_value": money(value) if value is not None else None,
                "valuation_date": value_date.isoformat() if value_date else None,
                "valuation_stale": bool(
                    value_date and value_date < date.today() - timedelta(days=30)
                ),
                "price_source": (
                    "owner_override"
                    if holding.manual_price_per_gram is not None
                    else reference_price.source
                    if reference_price is not None
                    else None
                ),
            }
        )
    return result


async def list_gold_transactions(session: AsyncSession) -> list[dict[str, object]]:
    statement = (
        select(GoldTransaction)
        .where(GoldTransaction.reverses_id.is_(None))
        .order_by(GoldTransaction.occurred_on.desc(), GoldTransaction.created_at.desc())
    )
    transactions = list((await session.scalars(statement)).all())
    return [
        {
            "id": str(item.id),
            "holding_id": str(item.holding_id),
            "kind": item.kind,
            "occurred_on": item.occurred_on.isoformat(),
            "quantity_grams": decimal_text(item.quantity_grams),
            "gross_amount": money(item.gross_amount),
            "fees": money(item.fees),
            "realized_profit": money(item.realized_profit),
            "reversed": item.reversed_by_id is not None,
        }
        for item in transactions
    ]


async def create_policy(
    session: AsyncSession,
    *,
    insurer: str,
    name: str,
    policy_type: str,
    cumulative_premiums: Decimal,
    cumulative_benefits: Decimal,
    cash_value: Decimal,
    valuation_date: date,
) -> InsurancePolicy:
    if min(cumulative_premiums, cumulative_benefits, cash_value) < 0:
        raise DomainRuleError("NEGATIVE_POLICY_AMOUNT", "保單金額不得小於0")
    policy = InsurancePolicy(
        insurer=insurer.strip(),
        name=name.strip(),
        policy_type=policy_type.strip(),
        status="active",
        cumulative_premiums=cumulative_premiums,
        cumulative_benefits=cumulative_benefits,
        cash_value=cash_value,
        valuation_date=valuation_date,
    )
    session.add(policy)
    await session.flush()
    session.add(
        InsuranceEvent(
            policy_id=policy.id,
            bank_account_id=None,
            kind="opening",
            occurred_on=valuation_date,
            amount=cumulative_premiums,
            cash_value_after=cash_value,
            status_after="active",
            details={"cumulative_benefits": decimal_text(cumulative_benefits)},
            reason="期初保單",
        )
    )
    return policy


async def add_policy_event(
    session: AsyncSession,
    *,
    policy_id: UUID,
    kind: str,
    occurred_on: date,
    amount: Decimal,
    bank_account_id: UUID | None,
    cash_value_after: Decimal | None,
    status_after: str | None,
) -> InsuranceEvent:
    policy = await session.scalar(
        select(InsurancePolicy).where(InsurancePolicy.id == policy_id).with_for_update()
    )
    if policy is None:
        raise DomainRuleError("POLICY_NOT_FOUND", "找不到保單")
    if amount < 0 or (cash_value_after is not None and cash_value_after < 0):
        raise DomainRuleError("NEGATIVE_POLICY_AMOUNT", "保單金額不得小於0")
    event_id = uuid4()
    cash_amount: Decimal | None = None
    if kind == "premium":
        if amount <= 0 or bank_account_id is None:
            raise DomainRuleError("INVALID_PREMIUM", "繳費必須指定銀行及正數金額")
        if await bank_balance(session, bank_account_id) < amount:
            raise DomainRuleError("INSUFFICIENT_CASH", "銀行餘額不足，保費未成立")
        policy.cumulative_premiums += amount
        cash_amount = -amount
    elif kind == "benefit":
        if amount <= 0 or bank_account_id is None or status_after is None:
            raise DomainRuleError("INVALID_POLICY_BENEFIT", "給付資料不完整")
        policy.cumulative_benefits += amount
        policy.status = status_after
        if cash_value_after is not None:
            policy.cash_value = cash_value_after
            policy.valuation_date = occurred_on
        cash_amount = amount
    elif kind == "valuation":
        if cash_value_after is None:
            raise DomainRuleError("INVALID_POLICY_VALUATION", "請輸入保單現金價值")
        policy.cash_value = cash_value_after
        policy.valuation_date = occurred_on
    else:
        raise DomainRuleError("INVALID_POLICY_EVENT", "不支援的保單事件")

    event = InsuranceEvent(
        id=event_id,
        policy_id=policy_id,
        bank_account_id=bank_account_id,
        kind=kind,
        occurred_on=occurred_on,
        amount=amount,
        cash_value_after=cash_value_after,
        status_after=status_after,
        details={},
    )
    session.add(event)
    if cash_amount is not None and bank_account_id is not None:
        session.add(
            CashEntry(
                bank_account_id=bank_account_id,
                occurred_on=occurred_on,
                amount=cash_amount,
                kind=f"insurance_{kind}",
                reference_type="insurance_event",
                reference_id=event_id,
                description=policy.name,
            )
        )
    await session.flush()
    return event


async def list_policies(session: AsyncSession) -> list[dict[str, object]]:
    policies = list(
        (
            await session.scalars(
                select(InsurancePolicy).order_by(InsurancePolicy.created_at)
            )
        ).all()
    )
    return [
        {
            "id": str(policy.id),
            "insurer": policy.insurer,
            "name": policy.name,
            "policy_type": policy.policy_type,
            "status": policy.status,
            "cumulative_premiums": money(policy.cumulative_premiums),
            "cumulative_benefits": money(policy.cumulative_benefits),
            "cash_value": money(policy.cash_value),
            "valuation_date": policy.valuation_date.isoformat(),
            "valuation_stale": policy.valuation_date
            < date.today() - timedelta(days=365),
        }
        for policy in policies
    ]


async def list_insurance_events(session: AsyncSession) -> list[dict[str, object]]:
    statement = (
        select(InsuranceEvent)
        .where(InsuranceEvent.reverses_id.is_(None))
        .order_by(InsuranceEvent.occurred_on.desc(), InsuranceEvent.created_at.desc())
    )
    events = list((await session.scalars(statement)).all())
    return [
        {
            "id": str(item.id),
            "policy_id": str(item.policy_id),
            "kind": item.kind,
            "occurred_on": item.occurred_on.isoformat(),
            "amount": money(item.amount),
            "cash_value_after": (
                money(item.cash_value_after)
                if item.cash_value_after is not None
                else None
            ),
            "reversed": item.reversed_by_id is not None,
        }
        for item in events
    ]


async def create_salary_template(
    session: AsyncSession,
    *,
    employer: str,
    default_pay_day: int,
    bank_account_id: UUID,
    earnings: dict[str, str],
    deductions: dict[str, str],
) -> SalaryTemplate:
    _validate_detail_amounts(earnings)
    _validate_detail_amounts(deductions)
    if not 1 <= default_pay_day <= 31:
        raise DomainRuleError("INVALID_PAY_DAY", "發薪日必須介於1到31")
    if await session.get(BankAccount, bank_account_id) is None:
        raise DomainRuleError("BANK_ACCOUNT_NOT_FOUND", "找不到銀行帳戶")
    template = SalaryTemplate(
        employer=employer.strip(),
        default_pay_day=default_pay_day,
        bank_account_id=bank_account_id,
        earnings=earnings,
        deductions=deductions,
    )
    session.add(template)
    await session.flush()
    return template


async def record_salary(
    session: AsyncSession,
    *,
    employer: str,
    bank_account_id: UUID,
    paid_on: date,
    net_amount: Decimal,
    earnings: dict[str, str],
    deductions: dict[str, str],
    template_id: UUID | None,
) -> SalaryRecord:
    _validate_detail_amounts(earnings)
    _validate_detail_amounts(deductions)
    if net_amount <= 0:
        raise DomainRuleError("INVALID_NET_SALARY", "實領金額必須大於0")
    if await session.get(BankAccount, bank_account_id) is None:
        raise DomainRuleError("BANK_ACCOUNT_NOT_FOUND", "找不到銀行帳戶")
    record_id = uuid4()
    record = SalaryRecord(
        id=record_id,
        template_id=template_id,
        employer=employer.strip(),
        bank_account_id=bank_account_id,
        paid_on=paid_on,
        net_amount=net_amount,
        earnings=earnings,
        deductions=deductions,
    )
    session.add_all(
        [
            record,
            CashEntry(
                bank_account_id=bank_account_id,
                occurred_on=paid_on,
                amount=net_amount,
                kind="salary",
                reference_type="salary_record",
                reference_id=record_id,
                description=employer,
            ),
        ]
    )
    await session.flush()
    return record


async def list_salary_records(session: AsyncSession) -> list[dict[str, object]]:
    records = list(
        (
            await session.scalars(
                select(SalaryRecord)
                .where(SalaryRecord.reverses_id.is_(None))
                .order_by(SalaryRecord.paid_on.desc())
            )
        ).all()
    )
    return [
        {
            "id": str(record.id),
            "employer": record.employer,
            "paid_on": record.paid_on.isoformat(),
            "net_amount": money(record.net_amount),
            "earnings": record.earnings,
            "deductions": record.deductions,
            "reversed": record.reversed_by_id is not None,
        }
        for record in records
    ]


async def reverse_gold_transaction(
    session: AsyncSession, transaction_id: UUID, reason: str
) -> GoldTransaction:
    target = await session.scalar(
        select(GoldTransaction)
        .where(GoldTransaction.id == transaction_id)
        .with_for_update()
    )
    if target is None or target.reverses_id is not None:
        raise DomainRuleError("GOLD_TRANSACTION_NOT_FOUND", "找不到可沖銷的黃金交易")
    if target.reversed_by_id is not None:
        raise DomainRuleError("TRANSACTION_ALREADY_REVERSED", "這筆黃金交易已經沖銷")

    holding = await session.scalar(
        select(GoldHolding).where(GoldHolding.id == target.holding_id).with_for_update()
    )
    if holding is None:
        raise DomainRuleError("GOLD_HOLDING_NOT_FOUND", "找不到黃金持有項目")

    statement = (
        select(GoldTransaction)
        .where(
            GoldTransaction.holding_id == target.holding_id,
            GoldTransaction.reverses_id.is_(None),
            GoldTransaction.reversed_by_id.is_(None),
            GoldTransaction.id != target.id,
        )
        .order_by(GoldTransaction.occurred_on, GoldTransaction.created_at)
    )
    active = list((await session.scalars(statement)).all())
    quantity = Decimal("0")
    total_cost = Decimal("0")
    for item in active:
        if item.kind == "opening":
            quantity += item.quantity_grams
            total_cost += item.gross_amount
        elif item.kind == "buy":
            result = apply_gold_buy(
                quantity,
                total_cost,
                item.quantity_grams,
                item.gross_amount,
                item.fees,
            )
            quantity, total_cost = result.quantity_grams, result.total_cost
        elif item.kind == "sell":
            result_sell = apply_gold_sell(
                quantity,
                total_cost,
                item.quantity_grams,
                item.gross_amount,
                item.fees,
            )
            quantity, total_cost = result_sell.quantity_grams, result_sell.total_cost

    reversal_id = uuid4()
    cash_amount: Decimal | None = None
    if target.kind == "buy":
        cash_amount = target.gross_amount + target.fees
    elif target.kind == "sell":
        cash_amount = -(target.gross_amount - target.fees)
        if target.bank_account_id is not None:
            available = await bank_balance(session, target.bank_account_id)
            if available + cash_amount < 0:
                raise DomainRuleError(
                    "INSUFFICIENT_CASH", "銀行餘額不足，無法沖銷黃金賣出"
                )

    reversal = GoldTransaction(
        id=reversal_id,
        holding_id=target.holding_id,
        bank_account_id=target.bank_account_id,
        kind="reversal",
        occurred_on=target.occurred_on,
        quantity_grams=target.quantity_grams,
        gross_amount=target.gross_amount,
        fees=target.fees,
        cost_removed=-target.cost_removed,
        realized_profit=-target.realized_profit,
        original_quantity=target.original_quantity,
        original_unit=target.original_unit,
        reverses_id=target.id,
        reason=reason.strip(),
    )
    target.reversed_by_id = reversal_id
    holding.quantity_grams = quantity
    holding.total_cost = total_cost
    session.add(reversal)
    if cash_amount is not None and target.bank_account_id is not None:
        session.add(
            CashEntry(
                bank_account_id=target.bank_account_id,
                occurred_on=target.occurred_on,
                amount=cash_amount,
                kind="gold_reversal",
                reference_type="gold_transaction",
                reference_id=reversal_id,
                description=reason.strip(),
            )
        )
    await session.flush()
    return reversal


async def reverse_insurance_event(
    session: AsyncSession, event_id: UUID, reason: str
) -> InsuranceEvent:
    target = await session.scalar(
        select(InsuranceEvent).where(InsuranceEvent.id == event_id).with_for_update()
    )
    if target is None or target.reverses_id is not None:
        raise DomainRuleError("POLICY_EVENT_NOT_FOUND", "找不到可沖銷的保單紀錄")
    if target.reversed_by_id is not None:
        raise DomainRuleError("POLICY_EVENT_ALREADY_REVERSED", "這筆保單紀錄已經沖銷")
    policy = await session.scalar(
        select(InsurancePolicy)
        .where(InsurancePolicy.id == target.policy_id)
        .with_for_update()
    )
    if policy is None:
        raise DomainRuleError("POLICY_NOT_FOUND", "找不到保單")

    statement = (
        select(InsuranceEvent)
        .where(
            InsuranceEvent.policy_id == target.policy_id,
            InsuranceEvent.reverses_id.is_(None),
            InsuranceEvent.reversed_by_id.is_(None),
            InsuranceEvent.id != target.id,
        )
        .order_by(InsuranceEvent.occurred_on, InsuranceEvent.created_at)
    )
    active = list((await session.scalars(statement)).all())
    premiums = Decimal("0")
    benefits = Decimal("0")
    cash_value = Decimal("0")
    valuation_date = policy.valuation_date
    policy_status = "active"
    for item in active:
        if item.kind == "opening":
            premiums = item.amount
            benefits = Decimal(item.details.get("cumulative_benefits", "0"))
            cash_value = item.cash_value_after or Decimal("0")
            valuation_date = item.occurred_on
            policy_status = item.status_after or "active"
        elif item.kind == "premium":
            premiums += item.amount
        elif item.kind == "benefit":
            benefits += item.amount
            cash_value = item.cash_value_after or cash_value
            valuation_date = item.occurred_on
            policy_status = item.status_after or policy_status
        elif item.kind == "valuation":
            cash_value = item.cash_value_after or Decimal("0")
            valuation_date = item.occurred_on

    reversal_id = uuid4()
    cash_amount: Decimal | None = None
    if target.kind == "premium":
        cash_amount = target.amount
    elif target.kind == "benefit":
        cash_amount = -target.amount
        if target.bank_account_id is not None:
            available = await bank_balance(session, target.bank_account_id)
            if available + cash_amount < 0:
                raise DomainRuleError(
                    "INSUFFICIENT_CASH", "銀行餘額不足，無法沖銷保單給付"
                )

    reversal = InsuranceEvent(
        id=reversal_id,
        policy_id=target.policy_id,
        bank_account_id=target.bank_account_id,
        kind="reversal",
        occurred_on=target.occurred_on,
        amount=target.amount,
        cash_value_after=cash_value,
        status_after=policy_status,
        details={},
        reverses_id=target.id,
        reason=reason.strip(),
    )
    target.reversed_by_id = reversal_id
    policy.cumulative_premiums = premiums
    policy.cumulative_benefits = benefits
    policy.cash_value = cash_value
    policy.valuation_date = valuation_date
    policy.status = policy_status
    session.add(reversal)
    if cash_amount is not None and target.bank_account_id is not None:
        session.add(
            CashEntry(
                bank_account_id=target.bank_account_id,
                occurred_on=target.occurred_on,
                amount=cash_amount,
                kind="insurance_reversal",
                reference_type="insurance_event",
                reference_id=reversal_id,
                description=reason.strip(),
            )
        )
    await session.flush()
    return reversal


async def reverse_salary_record(
    session: AsyncSession, record_id: UUID, reason: str
) -> SalaryRecord:
    target = await session.scalar(
        select(SalaryRecord).where(SalaryRecord.id == record_id).with_for_update()
    )
    if target is None or target.reverses_id is not None:
        raise DomainRuleError("SALARY_RECORD_NOT_FOUND", "找不到可沖銷的薪資紀錄")
    if target.reversed_by_id is not None:
        raise DomainRuleError("SALARY_ALREADY_REVERSED", "這筆薪資已經沖銷")
    available = await bank_balance(session, target.bank_account_id)
    if available < target.net_amount:
        raise DomainRuleError("INSUFFICIENT_CASH", "銀行餘額不足，無法沖銷薪資")

    reversal_id = uuid4()
    reversal = SalaryRecord(
        id=reversal_id,
        template_id=target.template_id,
        employer=target.employer,
        bank_account_id=target.bank_account_id,
        paid_on=target.paid_on,
        net_amount=target.net_amount,
        earnings=target.earnings,
        deductions=target.deductions,
        reverses_id=target.id,
        reason=reason.strip(),
    )
    target.reversed_by_id = reversal_id
    session.add_all(
        [
            reversal,
            CashEntry(
                bank_account_id=target.bank_account_id,
                occurred_on=target.paid_on,
                amount=-target.net_amount,
                kind="salary_reversal",
                reference_type="salary_record",
                reference_id=reversal_id,
                description=reason.strip(),
            ),
        ]
    )
    await session.flush()
    return reversal


async def dashboard_summary(session: AsyncSession) -> dict[str, object]:
    price, price_stale = await latest_gold_price(session, refresh=False)
    banks = await list_bank_accounts(session)
    gold = await list_gold_holdings(session, price)
    policies = await list_policies(session)
    bank_values = (Decimal(str(item["balance"])) for item in banks)
    cash_total = sum(bank_values, Decimal("0"))
    gold_values: list[Decimal] = []
    for item in gold:
        if item["market_value"]:
            gold_values.append(Decimal(str(item["market_value"])))
    insurance_total = sum(
        (Decimal(str(item["cash_value"])) for item in policies), Decimal("0")
    )
    return {
        "bank_cash": money(cash_total),
        "gold_value": money(sum(gold_values, Decimal("0"))) if gold_values else None,
        "insurance_cash_value": money(insurance_total),
        "total_assets": money(
            cash_total + sum(gold_values, Decimal("0")) + insurance_total
        ),
        "alerts": {
            "gold_price_stale": price_stale,
            "gold_valuation_stale_count": sum(
                1 for item in gold if item["valuation_stale"]
            ),
            "policy_valuation_stale_count": sum(
                1 for item in policies if item["valuation_stale"]
            ),
        },
    }


def decimal_text(value: Decimal) -> str:
    return format(value, "f")


def money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _validate_gold_holding(
    holding_type: str, purity: Decimal, total_cost: Decimal
) -> None:
    if holding_type not in {"physical", "passbook"}:
        raise DomainRuleError("INVALID_GOLD_TYPE", "黃金類型不正確")
    if not Decimal("0") < purity <= Decimal("1"):
        raise DomainRuleError("INVALID_GOLD_PURITY", "黃金純度必須大於0且不超過1")
    if total_cost < 0:
        raise DomainRuleError("NEGATIVE_GOLD_COST", "黃金成本不得小於0")


def _validate_detail_amounts(details: dict[str, str]) -> None:
    for value in details.values():
        try:
            amount = Decimal(value)
        except InvalidOperation as error:
            raise DomainRuleError(
                "INVALID_SALARY_DETAIL", "薪資明細必須是金額"
            ) from error
        if amount < 0:
            raise DomainRuleError("NEGATIVE_SALARY_DETAIL", "薪資明細不得小於0")
