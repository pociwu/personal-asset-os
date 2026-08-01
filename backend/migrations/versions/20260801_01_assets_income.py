"""Create Usable Alpha assets and income ledger."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260801_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    timestamps = lambda: sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    op.create_table(
        "bank_accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("opening_balance", sa.Numeric(24, 8), nullable=False),
        timestamps(),
        sa.CheckConstraint("opening_balance >= 0", name="ck_bank_opening_nonnegative"),
    )
    op.create_table(
        "gold_holdings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("holding_type", sa.String(20), nullable=False),
        sa.Column("quantity_grams", sa.Numeric(24, 8), nullable=False),
        sa.Column("total_cost", sa.Numeric(24, 8), nullable=False),
        sa.Column("purity", sa.Numeric(12, 8), nullable=False),
        sa.Column("manual_price_per_gram", sa.Numeric(24, 8)),
        sa.Column("manual_price_date", sa.Date()),
        sa.Column("manual_price_reason", sa.Text()),
        timestamps(),
        sa.CheckConstraint(
            "holding_type IN ('physical','passbook')", name="ck_gold_holding_type"
        ),
        sa.CheckConstraint("quantity_grams >= 0", name="ck_gold_quantity_nonnegative"),
        sa.CheckConstraint("total_cost >= 0", name="ck_gold_cost_nonnegative"),
        sa.CheckConstraint("purity > 0 AND purity <= 1", name="ck_gold_purity"),
    )
    op.create_table(
        "insurance_policies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("insurer", sa.String(100), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("policy_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("cumulative_premiums", sa.Numeric(24, 8), nullable=False),
        sa.Column("cumulative_benefits", sa.Numeric(24, 8), nullable=False),
        sa.Column("cash_value", sa.Numeric(24, 8), nullable=False),
        sa.Column("valuation_date", sa.Date(), nullable=False),
        timestamps(),
        sa.CheckConstraint("status IN ('active','ended')", name="ck_policy_status"),
    )
    op.create_table(
        "salary_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("employer", sa.String(150), nullable=False),
        sa.Column("default_pay_day", sa.Integer(), nullable=False),
        sa.Column(
            "bank_account_id",
            sa.Uuid(),
            sa.ForeignKey("bank_accounts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("earnings", postgresql.JSONB(), nullable=False),
        sa.Column("deductions", postgresql.JSONB(), nullable=False),
        timestamps(),
        sa.CheckConstraint(
            "default_pay_day BETWEEN 1 AND 31", name="ck_salary_pay_day"
        ),
    )
    op.create_table(
        "gold_prices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("price_per_gram", sa.Numeric(24, 8), nullable=False),
        sa.Column("quoted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("source", sa.String(200), nullable=False),
        sa.CheckConstraint("price_per_gram > 0", name="ck_gold_price_positive"),
    )
    op.create_index("ix_gold_prices_quoted_at", "gold_prices", ["quoted_at"])
    op.create_table(
        "gold_transactions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "holding_id",
            sa.Uuid(),
            sa.ForeignKey("gold_holdings.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "bank_account_id",
            sa.Uuid(),
            sa.ForeignKey("bank_accounts.id", ondelete="RESTRICT"),
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("quantity_grams", sa.Numeric(24, 8), nullable=False),
        sa.Column("gross_amount", sa.Numeric(24, 8), nullable=False),
        sa.Column("fees", sa.Numeric(24, 8), nullable=False),
        sa.Column("cost_removed", sa.Numeric(24, 8), nullable=False),
        sa.Column("realized_profit", sa.Numeric(24, 8), nullable=False),
        sa.Column("original_quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("original_unit", sa.String(10), nullable=False),
        sa.Column("reversed_by_id", sa.Uuid()),
        sa.Column("reverses_id", sa.Uuid()),
        sa.Column("reason", sa.Text()),
        timestamps(),
    )
    op.create_index("ix_gold_transactions_holding", "gold_transactions", ["holding_id"])
    op.create_table(
        "insurance_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "policy_id",
            sa.Uuid(),
            sa.ForeignKey("insurance_policies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "bank_account_id",
            sa.Uuid(),
            sa.ForeignKey("bank_accounts.id", ondelete="RESTRICT"),
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(24, 8), nullable=False),
        sa.Column("cash_value_after", sa.Numeric(24, 8)),
        sa.Column("status_after", sa.String(20)),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.Column("reversed_by_id", sa.Uuid()),
        sa.Column("reverses_id", sa.Uuid()),
        sa.Column("reason", sa.Text()),
        timestamps(),
    )
    op.create_index("ix_insurance_events_policy", "insurance_events", ["policy_id"])
    op.create_table(
        "salary_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "template_id",
            sa.Uuid(),
            sa.ForeignKey("salary_templates.id", ondelete="SET NULL"),
        ),
        sa.Column("employer", sa.String(150), nullable=False),
        sa.Column(
            "bank_account_id",
            sa.Uuid(),
            sa.ForeignKey("bank_accounts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("net_amount", sa.Numeric(24, 8), nullable=False),
        sa.Column("earnings", postgresql.JSONB(), nullable=False),
        sa.Column("deductions", postgresql.JSONB(), nullable=False),
        sa.Column("reversed_by_id", sa.Uuid()),
        sa.Column("reverses_id", sa.Uuid()),
        sa.Column("reason", sa.Text()),
        timestamps(),
        sa.CheckConstraint("net_amount > 0", name="ck_salary_net_positive"),
    )
    op.create_table(
        "cash_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "bank_account_id",
            sa.Uuid(),
            sa.ForeignKey("bank_accounts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(24, 8), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("reference_type", sa.String(40), nullable=False),
        sa.Column("reference_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text()),
        timestamps(),
    )
    op.create_index(
        "ix_cash_entries_account_date",
        "cash_entries",
        ["bank_account_id", "occurred_on"],
    )
    op.create_index("ix_cash_entries_reference", "cash_entries", ["reference_id"])


def downgrade() -> None:
    for table in (
        "cash_entries",
        "salary_records",
        "insurance_events",
        "gold_transactions",
        "gold_prices",
        "salary_templates",
        "insurance_policies",
        "gold_holdings",
        "bank_accounts",
    ):
        op.drop_table(table)
