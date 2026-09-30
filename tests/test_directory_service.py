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
from expense_splitter.services.directories_service import (
    DELETE_CATEGORY_USAGE_CONFIRM,
    DirectoryService,
)
from expense_splitter.storage import initialize_data_files


@pytest.fixture
def repository(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [Participant("Alice"), Participant("Bob")], [])
    repository = YamlExpenseRepository(data_dir)
    repository.save_categories(
        LOCAL_TENANT_ID,
        [CategoryEntry("food"), CategoryEntry("transport")],
    )
    return repository


def test_directory_service_add_rename_archive_participant(repository):
    service = DirectoryService(repository, repository, repository, repository)
    service.add_participant(LOCAL_TENANT_ID, "  Carol  ")
    purchase = Purchase(
        id="p1",
        date=date(2026, 7, 1),
        amount=Decimal("90.00"),
        payer="Carol",
        participants=["Alice", "Carol"],
        purchase_name="Taxi",
    )
    repository.add_purchase(LOCAL_TENANT_ID, purchase)

    renamed = service.rename_participant(LOCAL_TENANT_ID, "Carol", "Maria")
    archived = service.archive_participant(LOCAL_TENANT_ID, "Maria")

    assert renamed.name == "Maria"
    assert archived.status == "archived"
    stored = repository.get_purchase(LOCAL_TENANT_ID, "p1")
    assert stored is not None
    assert stored.payer == "Maria"
    assert stored.participants == ["Alice", "Maria"]
    assert [row.name for row in service.list_participants(LOCAL_TENANT_ID)] == [
        "Alice",
        "Bob",
    ]


def test_directory_service_blocks_used_participant_delete(repository):
    service = DirectoryService(repository, repository, repository, repository)
    repository.add_purchase(
        LOCAL_TENANT_ID,
        Purchase(
            id="p1",
            date=date(2026, 7, 1),
            amount=Decimal("90.00"),
            payer="Alice",
            participants=["Alice", "Bob"],
            purchase_name="Taxi",
        ),
    )

    with pytest.raises(ValueError, match="используется"):
        service.delete_participant(LOCAL_TENANT_ID, "Alice")


def test_directory_service_renames_and_deletes_used_category(repository):
    service = DirectoryService(repository, repository, repository, repository)
    repository.add_purchase(
        LOCAL_TENANT_ID,
        Purchase(
            id="p1",
            date=date(2026, 7, 1),
            amount=Decimal("90.00"),
            payer="Alice",
            participants=["Alice", "Bob"],
            purchase_name="Taxi",
            category="food, transport",
        ),
    )

    service.rename_category(LOCAL_TENANT_ID, "transport", "taxi")
    stored = repository.get_purchase(LOCAL_TENANT_ID, "p1")
    assert stored is not None
    assert stored.category == "food, taxi"

    with pytest.raises(ValueError, match=DELETE_CATEGORY_USAGE_CONFIRM):
        service.delete_category(LOCAL_TENANT_ID, "food")

    deleted = service.delete_category(
        LOCAL_TENANT_ID,
        "food",
        DELETE_CATEGORY_USAGE_CONFIRM,
    )

    stored = repository.get_purchase(LOCAL_TENANT_ID, "p1")
    assert deleted.name == "food"
    assert stored is not None
    assert stored.category == "taxi"


def test_directory_service_renames_participant_in_period_settlements(repository):
    service = DirectoryService(repository, repository, repository, repository)
    period = SettlementPeriod(
        id="period-1",
        name="July",
        status="closed",
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        closed_at=datetime(2026, 8, 1, 10, 0, 0),
        purchase_ids=[],
        total_amount=Decimal("0.00"),
        settlements=[Settlement("Bob", "Alice", Decimal("10.00"))],
    )
    repository.save_period(LOCAL_TENANT_ID, period)

    service.rename_participant(LOCAL_TENANT_ID, "Bob", "Robert")

    stored_period = repository.get_period(LOCAL_TENANT_ID, "period-1")
    assert stored_period is not None
    assert stored_period.settlements[0].from_participant == "Robert"
