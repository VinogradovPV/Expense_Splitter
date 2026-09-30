from datetime import date
from decimal import Decimal

import pytest

pytest.importorskip("fastapi")

from expense_splitter.server.app import create_app
from expense_splitter.server.config import ServerSettings
from expense_splitter.server.routes import purchases as purchase_routes
from expense_splitter.server.schemas import PurchaseCreateRequest


def make_app(tmp_path):
    return create_app(
        ServerSettings(
            data_dir=tmp_path / "data",
            reports_dir=tmp_path / "reports",
            report_storage_backend="temp",
        )
    )


def participant_names(app):
    return [participant.name for participant in app.state.repository.list_participants("local")]


def test_purchase_endpoint_logic_creates_and_lists_purchase(tmp_path):
    app = make_app(tmp_path)
    payer, second = participant_names(app)[:2]

    created = purchase_routes.create_purchase(
        PurchaseCreateRequest(
            purchase_name="Server coffee",
            amount=Decimal("250.00"),
            payer=payer,
            participants=[payer, second],
            purchase_date=date(2026, 7, 1),
            category="coffee",
            comment="api",
        ),
        tenant_id="local",
        service=app.state.purchase_service,
    )
    listed = purchase_routes.list_purchases("local", app.state.repository)

    assert created.purchase_name == "Server coffee"
    assert created.amount == "250.00"
    assert listed.items == [created]


def test_balances_and_settlements_endpoints_use_services(tmp_path):
    app = make_app(tmp_path)
    payer, second = participant_names(app)[:2]
    purchase_routes.create_purchase(
        PurchaseCreateRequest(
            purchase_name="Server lunch",
            amount=Decimal("100.00"),
            payer=payer,
            participants=[payer, second],
            purchase_date=date(2026, 7, 1),
        ),
        tenant_id="local",
        service=app.state.purchase_service,
    )

    balances = purchase_routes.balances("local", app.state.settlement_service)
    settlements = purchase_routes.settlements("local", app.state.settlement_service)

    assert {item.participant for item in balances.items} >= {payer, second}
    assert len(settlements.items) == 1
    assert settlements.items[0].amount == "50.00"


def test_purchase_endpoint_returns_structured_validation_error(tmp_path):
    app = make_app(tmp_path)

    with pytest.raises(ValueError, match="Участник-плательщик"):
        purchase_routes.create_purchase(
            PurchaseCreateRequest(
                purchase_name="Invalid",
                amount=Decimal("100.00"),
                payer="missing",
                participants=["missing"],
                purchase_date=date(2026, 7, 1),
            ),
            tenant_id="local",
            service=app.state.purchase_service,
        )
