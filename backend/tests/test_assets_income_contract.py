from pathlib import Path

from app.core.config import Settings
from app.core.readiness import ReadinessResult
from app.main import create_app
from app.models.finance import Base


class ReadyProbe:
    async def check(self) -> ReadinessResult:
        return ReadinessResult(postgres=True, redis=True)

    async def close(self) -> None:
        return None


def test_assets_income_schema_contains_append_only_ledgers() -> None:
    assert {
        "bank_accounts",
        "cash_entries",
        "gold_holdings",
        "gold_transactions",
        "gold_prices",
        "insurance_policies",
        "insurance_events",
        "salary_templates",
        "salary_records",
    } <= set(Base.metadata.tables)
    assert "reversed_by_id" in Base.metadata.tables["gold_transactions"].columns
    assert "reverses_id" in Base.metadata.tables["insurance_events"].columns
    assert "reverses_id" in Base.metadata.tables["salary_records"].columns


def test_assets_income_api_exposes_writes_and_linked_reversals() -> None:
    application = create_app(Settings(log_level="WARNING"), ReadyProbe())
    paths = application.openapi()["paths"]
    assert "post" in paths["/api/v1/gold/transactions"]
    assert "post" in paths["/api/v1/gold/transactions/{transaction_id}/reverse"]
    assert "post" in paths["/api/v1/insurance/events/{event_id}/reverse"]
    assert "post" in paths["/api/v1/salary/records/{record_id}/reverse"]


def test_explicit_migration_is_packaged() -> None:
    backend_root = Path(__file__).parents[1]
    assert (backend_root / "alembic.ini").is_file()
    assert (
        backend_root / "migrations" / "versions" / "20260801_01_assets_income.py"
    ).is_file()
