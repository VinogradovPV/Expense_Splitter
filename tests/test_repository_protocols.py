import ast
from datetime import date
from decimal import Decimal

from expense_splitter.models import Purchase
from expense_splitter.repositories.protocols import (
    AddPurchaseCommand,
    ClosePeriodCommand,
    PurchasePatch,
    ReportRequest,
)


def test_repository_protocols_import_without_interface_dependencies():
    import expense_splitter.repositories.protocols as protocols

    source = protocols.__loader__.get_source(protocols.__name__)
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )

    assert {"typer", "rich", "tkinter", "messagebox", "subprocess"}.isdisjoint(imported_roots)


def test_purchase_patch_is_optional_and_storage_neutral():
    patch = PurchasePatch(amount=Decimal("10.50"), comment="updated")

    assert patch.amount == Decimal("10.50")
    assert patch.comment == "updated"
    assert patch.purchase_name is None
    assert patch.settled is None


def test_add_purchase_command_matches_domain_purchase_fields():
    command = AddPurchaseCommand(
        purchase_name="Кофе",
        purchase_date=date(2026, 7, 1),
        amount=Decimal("350.00"),
        payer="Павел",
        participants=["Павел", "Сергей"],
        category="кофе",
        comment="после встречи",
    )
    purchase = Purchase(
        id="purchase-1",
        date=command.purchase_date,
        amount=command.amount,
        payer=command.payer,
        participants=command.participants,
        purchase_name=command.purchase_name,
        category=command.category,
        comment=command.comment,
    )

    assert purchase.purchase_name == "Кофе"
    assert purchase.amount == Decimal("350.00")
    assert purchase.participants == ["Павел", "Сергей"]


def test_close_period_command_and_report_request_dtos():
    close_command = ClosePeriodCommand(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        name="Июль 2026",
    )
    report_request = ReportRequest(
        report_type="current",
        scope="open",
        formats={"pdf", "xlsx"},
    )

    assert close_command.created_by == "service"
    assert close_command.date_from <= close_command.date_to
    assert report_request.formats == {"pdf", "xlsx"}
    assert report_request.settlement_period_id is None
