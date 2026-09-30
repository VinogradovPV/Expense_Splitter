from datetime import date, datetime
from decimal import Decimal

import pytest

from expense_splitter.models import Participant, Purchase, SettlementPeriod
from expense_splitter.repositories import LOCAL_TENANT_ID, YamlExpenseRepository
from expense_splitter.repositories.protocols import ClosePeriodCommand
from expense_splitter.services.settlement_service import SettlementService
from expense_splitter.settlement_periods import DELETE_EMPTY_PERIOD_CONFIRM
from expense_splitter.storage import initialize_data_files


@pytest.fixture
def repository(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [Participant("Alice"), Participant("Bob")], [])
    repository = YamlExpenseRepository(data_dir)
    repository.add_purchase(
        LOCAL_TENANT_ID,
        Purchase(
            id="p1",
            date=date(2026, 7, 1),
            amount=Decimal("100.00"),
            payer="Alice",
            participants=["Alice", "Bob"],
            purchase_name="Dinner",
        ),
    )
    return repository


def test_settlement_service_balances_and_settlements(repository):
    service = SettlementService(repository, repository, repository)

    balances = service.balances(LOCAL_TENANT_ID)
    settlements = service.settlements(LOCAL_TENANT_ID)

    assert {balance.participant for balance in balances} == {"Alice", "Bob"}
    assert [(item.from_participant, item.to_participant, item.amount) for item in settlements] == [
        ("Bob", "Alice", Decimal("50.00"))
    ]


def test_settlement_service_preview_close_and_reopen_period(repository):
    service = SettlementService(repository, repository, repository)
    command = ClosePeriodCommand(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        name="July",
        created_by="service-test",
    )

    preview = service.preview_period(LOCAL_TENANT_ID, command)
    period = service.close_period(LOCAL_TENANT_ID, command)

    assert preview.purchase_count == 1
    assert period.purchase_ids == ["p1"]
    stored_purchase = repository.get_purchase(LOCAL_TENANT_ID, "p1")
    assert stored_purchase is not None
    assert stored_purchase.settled is True
    stored_periods = repository.list_periods(LOCAL_TENANT_ID)
    assert [stored_period.id for stored_period in stored_periods] == [period.id]
    assert stored_periods[0].purchase_ids == ["p1"]

    reopened = service.reopen_period(LOCAL_TENANT_ID, period.id)

    assert reopened.status == "reopened"
    reopened_purchase = repository.get_purchase(LOCAL_TENANT_ID, "p1")
    assert reopened_purchase is not None
    assert reopened_purchase.settled is False


def test_settlement_service_rename_and_delete_empty_period(repository):
    service = SettlementService(repository, repository, repository)
    empty = SettlementPeriod(
        id="empty",
        name="Empty",
        status="closed",
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        closed_at=datetime(2026, 8, 1, 10, 0, 0),
        purchase_ids=[],
        total_amount=Decimal("0.00"),
        settlements=[],
    )
    repository.save_period(LOCAL_TENANT_ID, empty)

    renamed = service.rename_period(LOCAL_TENANT_ID, "empty", name="Renamed")
    deleted = service.delete_empty_period(
        LOCAL_TENANT_ID,
        "empty",
        DELETE_EMPTY_PERIOD_CONFIRM,
    )

    assert renamed.name == "Renamed"
    assert deleted.id == "empty"
    assert repository.list_periods(LOCAL_TENANT_ID) == []


def test_settlement_service_suggest_next_period(repository):
    service = SettlementService(repository, repository, repository)

    suggestion = service.suggest_next_period(LOCAL_TENANT_ID)

    assert suggestion.date_from == date(2026, 7, 1)
    assert suggestion.reason == "first_open_purchase_date"
