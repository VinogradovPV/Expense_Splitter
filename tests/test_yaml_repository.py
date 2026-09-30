from datetime import date, datetime
from decimal import Decimal

import pytest

from expense_splitter.models import (
    CategoryEntry,
    Participant,
    Purchase,
    Settlement,
    SettlementPeriod,
)
from expense_splitter.repositories import LOCAL_TENANT_ID, YamlExpenseRepository
from expense_splitter.repositories.protocols import PurchasePatch
from expense_splitter.repositories.yaml_repository import YamlRepositoryTenantError
from expense_splitter.storage import (
    StorageError,
    initialize_data_files,
    load_category_entries,
    load_participants,
    load_purchases,
    load_settlement_periods,
    save_purchases,
)


def make_purchase(purchase_id: str = "p1") -> Purchase:
    return Purchase(
        id=purchase_id,
        date=date(2026, 7, 1),
        amount=Decimal("100.00"),
        payer="Pavel",
        participants=["Pavel", "Sergey"],
        purchase_name="Coffee",
        category="coffee",
        comment="morning",
    )


def make_period(period_id: str = "period-1") -> SettlementPeriod:
    return SettlementPeriod(
        id=period_id,
        name="July",
        status="closed",
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        closed_at=datetime(2026, 8, 1, 10, 0, 0),
        purchase_ids=["p1"],
        total_amount=Decimal("100.00"),
        settlements=[Settlement("Sergey", "Pavel", Decimal("50.00"))],
    )


@pytest.fixture
def repository(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(
        data_dir,
        [Participant("Pavel"), Participant("Sergey")],
        [],
    )
    return YamlExpenseRepository(data_dir)


def test_yaml_repository_purchase_list_add_update_and_replace(repository):
    purchase = make_purchase()

    assert repository.list_purchases(LOCAL_TENANT_ID) == []
    assert repository.add_purchase(LOCAL_TENANT_ID, purchase) == purchase
    assert repository.list_purchases(LOCAL_TENANT_ID) == [purchase]
    assert repository.get_purchase(LOCAL_TENANT_ID, "p1") == purchase

    updated = repository.update_purchase(
        LOCAL_TENANT_ID,
        "p1",
        PurchasePatch(amount=Decimal("125.50"), comment="updated"),
    )

    assert updated.amount == Decimal("125.50")
    assert updated.comment == "updated"
    assert load_purchases(repository.data_dir / "purchases.yaml") == [updated]

    replacement = make_purchase("p2")
    repository.replace_purchases(LOCAL_TENANT_ID, [replacement])

    assert repository.list_purchases(LOCAL_TENANT_ID) == [replacement]


def test_yaml_repository_participants_categories_and_periods_round_trip(repository):
    participants = [Participant("Pavel"), Participant("Maria", status="archived")]
    categories = [CategoryEntry("food"), CategoryEntry("coffee", status="archived")]
    period = make_period()

    repository.save_participants(LOCAL_TENANT_ID, participants)
    repository.save_categories(LOCAL_TENANT_ID, categories)
    repository.save_period(LOCAL_TENANT_ID, period)

    assert repository.list_participants(LOCAL_TENANT_ID) == load_participants(
        repository.data_dir / "participants.yaml"
    )
    assert repository.list_categories(LOCAL_TENANT_ID) == load_category_entries(
        repository.data_dir / "categories.yaml"
    )
    assert repository.list_periods(LOCAL_TENANT_ID) == load_settlement_periods(
        repository.data_dir / "settlement_periods.yaml"
    )
    assert repository.get_period(LOCAL_TENANT_ID, period.id) == period

    replacement = make_period("period-2")
    repository.replace_periods(LOCAL_TENANT_ID, [replacement])

    assert repository.list_periods(LOCAL_TENANT_ID) == [replacement]


def test_yaml_repository_rejects_non_local_tenant(repository):
    with pytest.raises(YamlRepositoryTenantError, match="tenant_id='local'"):
        repository.list_purchases("tenant-2")


def test_yaml_repository_preserves_storage_error_for_corrupted_yaml(repository):
    (repository.data_dir / "purchases.yaml").write_text("purchases: [\n", encoding="utf-8")

    with pytest.raises(StorageError):
        repository.list_purchases(LOCAL_TENANT_ID)


def test_yaml_repository_uses_storage_backups(repository):
    save_purchases(repository.data_dir / "purchases.yaml", [make_purchase("existing")])

    repository.add_purchase(LOCAL_TENANT_ID, make_purchase("new"))

    assert list(repository.data_dir.glob("purchases.yaml.*.bak"))
