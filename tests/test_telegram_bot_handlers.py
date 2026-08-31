from decimal import Decimal

import pytest

from expense_splitter.models import Participant
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


def test_start_and_help_are_russian_and_list_safe_purchase_commands(bot, context):
    handler, _repository = bot

    start = handler.handle_text(context, "/start")
    help_reply = handler.handle_text(context, "/help")

    assert "Expense Splitter" in start.text
    assert "/edit_purchase" in help_reply.text
    assert "/delete_purchase" in help_reply.text
    assert "DELETE_PURCHASE" in help_reply.text


def test_add_purchase_flow_saves_purchase_through_service(bot, context):
    handler, repository = bot

    assert "название" in handler.handle_text(context, "/add_purchase").text
    assert "сумму" in handler.handle_text(context, "Coffee").text
    assert "плательщика" in handler.handle_text(context, "250.50").text
    assert "участников" in handler.handle_text(context, "-").text
    assert "категорию" in handler.handle_text(context, "Alice, Bob").text
    assert "дату" in handler.handle_text(context, "coffee").text
    assert "комментарий" in handler.handle_text(context, "2026-07-01").text
    preview = handler.handle_text(context, "-")
    assert "Проверьте покупку" in preview.text

    saved = handler.handle_text(context, "yes")

    purchases = repository.list_purchases(LOCAL_TENANT_ID)
    assert len(purchases) == 1
    assert purchases[0].purchase_name == "Coffee"
    assert purchases[0].amount == Decimal("250.50")
    assert purchases[0].payer == "Alice"
    assert purchases[0].participants == ["Alice", "Bob"]
    assert "Покупка добавлена" in saved.text


def test_edit_purchase_command_updates_only_open_purchase(bot, context):
    handler, repository = bot
    handler.handle_text(context, "/add_purchase")
    handler.handle_text(context, "Coffee")
    handler.handle_text(context, "250")
    handler.handle_text(context, "Alice")
    handler.handle_text(context, "Alice, Bob")
    handler.handle_text(context, "coffee")
    handler.handle_text(context, "2026-07-01")
    handler.handle_text(context, "-")
    handler.handle_text(context, "yes")
    purchase = repository.list_purchases(LOCAL_TENANT_ID)[0]

    reply = handler.handle_text(
        context,
        f"/edit_purchase {purchase.id} amount=300 category=еда comment=исправлено",
    )

    updated = repository.get_purchase(LOCAL_TENANT_ID, purchase.id)
    assert updated is not None
    assert updated.amount == Decimal("300")
    assert updated.category == "еда"
    assert updated.comment == "исправлено"
    assert "Покупка обновлена" in reply.text


def test_delete_purchase_command_requires_exact_confirmation(bot, context):
    handler, repository = bot
    handler.handle_text(context, "/add_purchase")
    handler.handle_text(context, "Tea")
    handler.handle_text(context, "100")
    handler.handle_text(context, "Alice")
    handler.handle_text(context, "Alice, Bob")
    handler.handle_text(context, "-")
    handler.handle_text(context, "2026-07-01")
    handler.handle_text(context, "-")
    handler.handle_text(context, "yes")
    purchase = repository.list_purchases(LOCAL_TENANT_ID)[0]

    preview = handler.handle_text(context, f"/delete_purchase {purchase.id}")
    assert "требует подтверждения" in preview.text
    assert repository.get_purchase(LOCAL_TENANT_ID, purchase.id) is not None

    deleted = handler.handle_text(context, "DELETE_PURCHASE")

    assert "Покупка удалена" in deleted.text
    assert repository.list_purchases(LOCAL_TENANT_ID) == []
