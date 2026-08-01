from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CashEntry(Base):
    __tablename__ = "cash_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    bank_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="RESTRICT"), index=True
    )
    occurred_on: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    kind: Mapped[str] = mapped_column(String(40))
    reference_type: Mapped[str] = mapped_column(String(40))
    reference_id: Mapped[UUID] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class GoldHolding(Base):
    __tablename__ = "gold_holdings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    holding_type: Mapped[str] = mapped_column(String(20))
    quantity_grams: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    purity: Mapped[Decimal] = mapped_column(Numeric(12, 8))
    manual_price_per_gram: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    manual_price_date: Mapped[date | None] = mapped_column(Date)
    manual_price_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class GoldTransaction(Base):
    __tablename__ = "gold_transactions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    holding_id: Mapped[UUID] = mapped_column(
        ForeignKey("gold_holdings.id", ondelete="RESTRICT"), index=True
    )
    bank_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="RESTRICT")
    )
    kind: Mapped[str] = mapped_column(String(20))
    occurred_on: Mapped[date] = mapped_column(Date, index=True)
    quantity_grams: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    fees: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    cost_removed: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=Decimal("0"))
    realized_profit: Mapped[Decimal] = mapped_column(
        Numeric(24, 8), default=Decimal("0")
    )
    original_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    original_unit: Mapped[str] = mapped_column(String(10))
    reversed_by_id: Mapped[UUID | None] = mapped_column(index=True)
    reverses_id: Mapped[UUID | None] = mapped_column(index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class GoldPrice(Base):
    __tablename__ = "gold_prices"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    price_per_gram: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    quoted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    source: Mapped[str] = mapped_column(String(200))


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    insurer: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(150))
    policy_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="active")
    cumulative_premiums: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    cumulative_benefits: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    cash_value: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    valuation_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InsuranceEvent(Base):
    __tablename__ = "insurance_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    policy_id: Mapped[UUID] = mapped_column(
        ForeignKey("insurance_policies.id", ondelete="RESTRICT"), index=True
    )
    bank_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="RESTRICT")
    )
    kind: Mapped[str] = mapped_column(String(20))
    occurred_on: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    cash_value_after: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    status_after: Mapped[str | None] = mapped_column(String(20))
    details: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)
    reversed_by_id: Mapped[UUID | None] = mapped_column(index=True)
    reverses_id: Mapped[UUID | None] = mapped_column(index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SalaryTemplate(Base):
    __tablename__ = "salary_templates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    employer: Mapped[str] = mapped_column(String(150))
    default_pay_day: Mapped[int] = mapped_column()
    bank_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="RESTRICT")
    )
    earnings: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)
    deductions: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SalaryRecord(Base):
    __tablename__ = "salary_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("salary_templates.id", ondelete="SET NULL")
    )
    employer: Mapped[str] = mapped_column(String(150))
    bank_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="RESTRICT")
    )
    paid_on: Mapped[date] = mapped_column(Date, index=True)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    earnings: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)
    deductions: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)
    reversed_by_id: Mapped[UUID | None] = mapped_column(index=True)
    reverses_id: Mapped[UUID | None] = mapped_column(index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
