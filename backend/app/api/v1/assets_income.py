from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.finance import SalaryTemplate
from app.services import assets_income as service
from app.services.finance_math import DomainRuleError

router = APIRouter(tags=["assets-income"])
Session = Annotated[AsyncSession, Depends(get_session)]
Money = Annotated[Decimal, Field(max_digits=24, decimal_places=8)]


class BankAccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    opening_balance: Money = Decimal("0")


class OpeningGoldCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    holding_type: Literal["physical", "passbook"]
    quantity: Money
    unit: Literal["gram", "mace", "tael"]
    purity: Money = Decimal("1")
    total_cost: Money
    valuation_price: Money | None = None
    valuation_date: date | None = None
    valuation_reason: str | None = Field(default=None, max_length=500)


class GoldTransactionCreate(BaseModel):
    holding_id: UUID
    bank_account_id: UUID
    kind: Literal["buy", "sell"]
    occurred_on: date
    quantity: Money
    unit: Literal["gram", "mace", "tael"]
    gross_amount: Money
    fees: Money = Decimal("0")


class PolicyCreate(BaseModel):
    insurer: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=150)
    policy_type: str = Field(min_length=1, max_length=50)
    cumulative_premiums: Money = Decimal("0")
    cumulative_benefits: Money = Decimal("0")
    cash_value: Money = Decimal("0")
    valuation_date: date


class PolicyEventCreate(BaseModel):
    kind: Literal["premium", "benefit", "valuation"]
    occurred_on: date
    amount: Money = Decimal("0")
    bank_account_id: UUID | None = None
    cash_value_after: Money | None = None
    status_after: Literal["active", "ended"] | None = None


class SalaryTemplateCreate(BaseModel):
    employer: str = Field(min_length=1, max_length=150)
    default_pay_day: int = Field(ge=1, le=31)
    bank_account_id: UUID
    earnings: dict[str, str] = Field(default_factory=dict)
    deductions: dict[str, str] = Field(default_factory=dict)


class SalaryRecordCreate(BaseModel):
    employer: str = Field(min_length=1, max_length=150)
    bank_account_id: UUID
    paid_on: date
    net_amount: Money
    earnings: dict[str, str] = Field(default_factory=dict)
    deductions: dict[str, str] = Field(default_factory=dict)
    template_id: UUID | None = None


class CorrectionCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


@router.get("/bank-accounts")
async def get_bank_accounts(session: Session) -> list[dict[str, object]]:
    return await service.list_bank_accounts(session)


@router.post("/bank-accounts", status_code=status.HTTP_201_CREATED)
async def post_bank_account(
    payload: BankAccountCreate, session: Session
) -> dict[str, object]:
    try:
        async with session.begin():
            account = await service.create_bank_account(
                session, payload.name, payload.opening_balance
            )
        return {
            "id": str(account.id),
            "name": account.name,
            "balance": service.money(account.opening_balance),
        }
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.get("/gold/holdings")
async def get_gold_holdings(session: Session) -> dict[str, object]:
    async with session.begin():
        price, stale = await service.latest_gold_price(session)
        holdings = await service.list_gold_holdings(session, price)
    return {
        "holdings": holdings,
        "reference_price": service.money(price.price_per_gram) if price else None,
        "reference_price_date": price.quoted_at.date().isoformat() if price else None,
        "reference_price_stale": stale,
        "reference_price_source": price.source if price else None,
    }


@router.post("/gold/holdings", status_code=status.HTTP_201_CREATED)
async def post_opening_gold(
    payload: OpeningGoldCreate, session: Session
) -> dict[str, str]:
    try:
        async with session.begin():
            holding = await service.create_opening_gold(
                session,
                name=payload.name,
                holding_type=payload.holding_type,
                quantity=payload.quantity,
                unit=payload.unit,
                purity=payload.purity,
                total_cost=payload.total_cost,
                valuation_price=payload.valuation_price,
                valuation_date=payload.valuation_date,
                valuation_reason=payload.valuation_reason,
            )
        return {"id": str(holding.id)}
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.post("/gold/transactions", status_code=status.HTTP_201_CREATED)
async def post_gold_transaction(
    payload: GoldTransactionCreate, session: Session
) -> dict[str, str]:
    try:
        async with session.begin():
            transaction = await service.transact_gold(
                session,
                holding_id=payload.holding_id,
                bank_account_id=payload.bank_account_id,
                kind=payload.kind,
                occurred_on=payload.occurred_on,
                quantity=payload.quantity,
                unit=payload.unit,
                gross_amount=payload.gross_amount,
                fees=payload.fees,
            )
        return {
            "id": str(transaction.id),
            "realized_profit": service.money(transaction.realized_profit),
        }
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.get("/gold/transactions")
async def get_gold_transactions(session: Session) -> list[dict[str, object]]:
    return await service.list_gold_transactions(session)


@router.post(
    "/gold/transactions/{transaction_id}/reverse",
    status_code=status.HTTP_201_CREATED,
)
async def reverse_gold_transaction(
    transaction_id: UUID, payload: CorrectionCreate, session: Session
) -> dict[str, str]:
    try:
        async with session.begin():
            reversal = await service.reverse_gold_transaction(
                session, transaction_id, payload.reason
            )
        return {"id": str(reversal.id), "reverses_id": str(transaction_id)}
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.get("/insurance/policies")
async def get_policies(session: Session) -> list[dict[str, object]]:
    return await service.list_policies(session)


@router.post("/insurance/policies", status_code=status.HTTP_201_CREATED)
async def post_policy(payload: PolicyCreate, session: Session) -> dict[str, str]:
    try:
        async with session.begin():
            policy = await service.create_policy(
                session,
                insurer=payload.insurer,
                name=payload.name,
                policy_type=payload.policy_type,
                cumulative_premiums=payload.cumulative_premiums,
                cumulative_benefits=payload.cumulative_benefits,
                cash_value=payload.cash_value,
                valuation_date=payload.valuation_date,
            )
        return {"id": str(policy.id)}
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.post(
    "/insurance/policies/{policy_id}/events",
    status_code=status.HTTP_201_CREATED,
)
async def post_policy_event(
    policy_id: UUID, payload: PolicyEventCreate, session: Session
) -> dict[str, str]:
    try:
        async with session.begin():
            event = await service.add_policy_event(
                session,
                policy_id=policy_id,
                kind=payload.kind,
                occurred_on=payload.occurred_on,
                amount=payload.amount,
                bank_account_id=payload.bank_account_id,
                cash_value_after=payload.cash_value_after,
                status_after=payload.status_after,
            )
        return {"id": str(event.id)}
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.get("/insurance/events")
async def get_policy_events(session: Session) -> list[dict[str, object]]:
    return await service.list_insurance_events(session)


@router.post(
    "/insurance/events/{event_id}/reverse",
    status_code=status.HTTP_201_CREATED,
)
async def reverse_policy_event(
    event_id: UUID, payload: CorrectionCreate, session: Session
) -> dict[str, str]:
    try:
        async with session.begin():
            reversal = await service.reverse_insurance_event(
                session, event_id, payload.reason
            )
        return {"id": str(reversal.id), "reverses_id": str(event_id)}
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.get("/salary/templates")
async def get_salary_templates(session: Session) -> list[dict[str, object]]:
    templates = list(
        (
            await session.scalars(
                select(SalaryTemplate).order_by(SalaryTemplate.created_at)
            )
        ).all()
    )
    return [
        {
            "id": str(item.id),
            "employer": item.employer,
            "default_pay_day": item.default_pay_day,
            "bank_account_id": str(item.bank_account_id),
            "earnings": item.earnings,
            "deductions": item.deductions,
        }
        for item in templates
    ]


@router.post("/salary/templates", status_code=status.HTTP_201_CREATED)
async def post_salary_template(
    payload: SalaryTemplateCreate, session: Session
) -> dict[str, str]:
    try:
        async with session.begin():
            template = await service.create_salary_template(
                session,
                employer=payload.employer,
                default_pay_day=payload.default_pay_day,
                bank_account_id=payload.bank_account_id,
                earnings=payload.earnings,
                deductions=payload.deductions,
            )
        return {"id": str(template.id)}
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.get("/salary/records")
async def get_salary_records(session: Session) -> list[dict[str, object]]:
    return await service.list_salary_records(session)


@router.post("/salary/records", status_code=status.HTTP_201_CREATED)
async def post_salary_record(
    payload: SalaryRecordCreate, session: Session
) -> dict[str, str]:
    try:
        async with session.begin():
            record = await service.record_salary(
                session,
                employer=payload.employer,
                bank_account_id=payload.bank_account_id,
                paid_on=payload.paid_on,
                net_amount=payload.net_amount,
                earnings=payload.earnings,
                deductions=payload.deductions,
                template_id=payload.template_id,
            )
        return {"id": str(record.id)}
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.post(
    "/salary/records/{record_id}/reverse",
    status_code=status.HTTP_201_CREATED,
)
async def reverse_salary_record(
    record_id: UUID, payload: CorrectionCreate, session: Session
) -> dict[str, str]:
    try:
        async with session.begin():
            reversal = await service.reverse_salary_record(
                session, record_id, payload.reason
            )
        return {"id": str(reversal.id), "reverses_id": str(record_id)}
    except DomainRuleError as error:
        raise _http_error(error) from error


@router.get("/dashboard/assets-income")
async def get_dashboard_assets_income(session: Session) -> dict[str, object]:
    async with session.begin():
        return await service.dashboard_summary(session)


def _http_error(error: DomainRuleError) -> HTTPException:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if error.code.endswith("NOT_FOUND")
        else status.HTTP_409_CONFLICT
    )
    return HTTPException(
        status_code=status_code,
        detail={"code": error.code, "message": str(error)},
    )
