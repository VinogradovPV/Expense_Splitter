from datetime import date, datetime
from decimal import Decimal

import pytest

from expense_splitter.models import Participant, Purchase, Settlement, SettlementPeriod
from expense_splitter.reports.output_adapters import TempReportOutputAdapter
from expense_splitter.repositories import LOCAL_TENANT_ID, YamlExpenseRepository
from expense_splitter.services import PurchaseService, ReportService, SettlementService
from expense_splitter.storage import initialize_data_files
from expense_splitter.telegram_bot import (
    BotServices,
    InMemoryBotSessionStore,
    TelegramBotHandler,
    TelegramContext,
)


@pytest.fixture
def bot(tmp_path):
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
            category="food",
        ),
    )
    services = BotServices(
        purchase_service=PurchaseService(repository, repository),
        settlement_service=SettlementService(repository, repository, repository),
        report_service=ReportService(
            repository,
            repository,
            repository,
            output_adapter=TempReportOutputAdapter(base_dir=tmp_path / "reports"),
        ),
        purchase_repository=repository,
        participant_repository=repository,
        category_repository=repository,
        settlement_period_repository=repository,
    )
    return TelegramBotHandler(services, InMemoryBotSessionStore()), repository


@pytest.fixture
def context():
    return TelegramContext(
        telegram_user_id=1001,
        tenant_id=LOCAL_TENANT_ID,
        participant_name="Alice",
    )


def test_current_report_commands_return_send_document_files(bot, context):
    handler, _repository = bot

    pdf = handler.handle_text(context, "/current_pdf")
    xlsx = handler.handle_text(context, "/current_xlsx")

    assert "Готово" in pdf.text
    assert [file.format for file in pdf.documents] == ["pdf"]
    assert pdf.documents[0].local_path is not None
    assert pdf.documents[0].local_path.is_file()
    assert "Готово" in xlsx.text
    assert [file.format for file in xlsx.documents] == ["xlsx"]


def test_analytics_command_returns_requested_report_file(bot, context):
    handler, _repository = bot

    reply = handler.handle_text(context, "/analytics month 2026 7 xlsx")

    assert "Готово" in reply.text
    assert [file.format for file in reply.documents] == ["xlsx"]


def test_periods_and_period_report_use_historical_snapshot(bot, context):
    handler, repository = bot
    repository.save_period(
        LOCAL_TENANT_ID,
        SettlementPeriod(
            id="period-1",
            name="July",
            status="closed",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            closed_at=datetime(2026, 8, 1, 10, 0, 0),
            purchase_ids=["p1"],
            total_amount=Decimal("100.00"),
            settlements=[Settlement("Bob", "Alice", Decimal("50.00"))],
        ),
    )

    periods = handler.handle_text(context, "/periods")
    report = handler.handle_text(context, "/period_report period-1 xlsx")

    assert "period-1" in periods.text
    assert "Готово" in report.text
    assert [file.format for file in report.documents] == ["xlsx"]


def test_close_period_requires_exact_confirmation_marker(bot, context):
    handler, repository = bot

    preview = handler.handle_text(
        context,
        "/close_period from=2026-07-01 to=2026-07-31 name=July",
    )
    assert "confirm=CLOSE_PERIOD" in preview.text
    assert repository.list_periods(LOCAL_TENANT_ID) == []
    assert not repository.get_purchase(LOCAL_TENANT_ID, "p1").settled

    closed = handler.handle_text(
        context,
        "/close_period from=2026-07-01 to=2026-07-31 name=July confirm=CLOSE_PERIOD",
    )

    periods = repository.list_periods(LOCAL_TENANT_ID)
    purchase = repository.get_purchase(LOCAL_TENANT_ID, "p1")
    assert len(periods) == 1
    assert periods[0].created_by == "telegram"
    assert periods[0].purchase_ids == ["p1"]
    assert purchase is not None
    assert purchase.settled
    assert "Период закрыт" in closed.text


def test_cancel_clears_add_purchase_flow(bot, context):
    handler, repository = bot

    handler.handle_text(context, "/add_purchase")
    handler.handle_text(context, "Coffee")
    cancel = handler.handle_text(context, "/cancel")
    unknown = handler.handle_text(context, "250")

    assert "отменено" in cancel.text.casefold()
    assert "не распознана" in unknown.text
    assert len(repository.list_purchases(LOCAL_TENANT_ID)) == 1
