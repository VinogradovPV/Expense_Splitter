from datetime import date
from decimal import Decimal

import pytest

from expense_splitter.models import Participant, Purchase
from expense_splitter.repositories import LOCAL_TENANT_ID, YamlExpenseRepository
from expense_splitter.repositories.protocols import AddPurchaseCommand, PurchasePatch
from expense_splitter.services.purchases_service import (
    DELETE_PURCHASE_CONFIRM,
    PurchaseService,
)
from expense_splitter.storage import initialize_data_files


@pytest.fixture
def repository(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [Participant("Alice"), Participant("Bob")], [])
    return YamlExpenseRepository(data_dir)


def test_purchase_service_adds_normalized_purchase(repository):
    service = PurchaseService(repository, repository)

    purchase = service.add_purchase(
        LOCAL_TENANT_ID,
        AddPurchaseCommand(
            purchase_name="  Coffee  ",
            amount=Decimal("120.50"),
            payer="Alice",
            participants=["Alice", "Bob"],
            purchase_date=date(2026, 7, 1),
            category="food",
            comment="morning",
        ),
    )

    assert purchase.purchase_name == "Coffee"
    assert purchase.date == date(2026, 7, 1)
    assert repository.list_purchases(LOCAL_TENANT_ID) == [purchase]


def test_purchase_service_update_protects_settled_purchase(repository):
    service = PurchaseService(repository, repository)
    settled = Purchase(
        id="p1",
        date=date(2026, 7, 1),
        amount=Decimal("100.00"),
        payer="Alice",
        participants=["Alice", "Bob"],
        purchase_name="Dinner",
        settled=True,
        settlement_period_id="period-1",
    )
    repository.add_purchase(LOCAL_TENANT_ID, settled)

    with pytest.raises(ValueError, match="закрытому периоду"):
        service.update_purchase(
            LOCAL_TENANT_ID,
            "p1",
            PurchasePatch(amount=Decimal("125.00")),
        )


def test_purchase_service_delete_requires_confirm_and_open_purchase(repository):
    service = PurchaseService(repository, repository)
    purchase = Purchase(
        id="p1",
        date=date(2026, 7, 1),
        amount=Decimal("100.00"),
        payer="Alice",
        participants=["Alice", "Bob"],
        purchase_name="Dinner",
    )
    repository.add_purchase(LOCAL_TENANT_ID, purchase)

    with pytest.raises(ValueError, match=DELETE_PURCHASE_CONFIRM):
        service.delete_purchase(LOCAL_TENANT_ID, "p1", "delete")

    deleted = service.delete_purchase(LOCAL_TENANT_ID, "p1", DELETE_PURCHASE_CONFIRM)

    assert deleted == purchase
    assert repository.list_purchases(LOCAL_TENANT_ID) == []
