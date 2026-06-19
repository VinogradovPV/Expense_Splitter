from __future__ import annotations

import os
import platform
import subprocess
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.calculator import calculate_balances
from expense_splitter.defaults import DEFAULT_CATEGORIES, DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.gui.state import GuiState
from expense_splitter.models import Purchase
from expense_splitter.settlement import calculate_settlements
from expense_splitter.settlement_periods import (
    close_settlement_period,
    filter_purchases_by_settlement_scope,
    parse_period_date,
    preview_settlement_period,
)
from expense_splitter.storage import (
    initialize_data_files,
    load_categories,
    load_groups,
    load_participants,
    load_purchases,
    load_settlement_periods,
    save_categories,
    save_purchases,
    save_settlement_periods,
)
from expense_splitter.storage import (
    reset_test_data as storage_reset_test_data,
)


def ensure_data(state: GuiState) -> None:
    initialize_data_files(state.data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)


def participant_names(state: GuiState) -> list[str]:
    ensure_data(state)
    names = [
        participant.name for participant in load_participants(state.data_dir / "participants.yaml")
    ]
    return names or [participant.name for participant in DEFAULT_PARTICIPANTS]


def group_names(state: GuiState) -> list[str]:
    ensure_data(state)
    return [group.name for group in load_groups(state.data_dir / "participants.yaml")]


def list_purchases(state: GuiState) -> list[Purchase]:
    ensure_data(state)
    return load_purchases(state.data_dir / "purchases.yaml")


def purchase_row(purchase: Purchase) -> tuple[str, ...]:
    return (
        purchase.date.isoformat() if purchase.date else "",
        purchase.purchase_name,
        f"{purchase.amount:.2f}",
        purchase.payer,
        ", ".join(purchase.participants),
        purchase.category or "Без категории",
        purchase.settlement_period_id if purchase.settled else "open",
    )


def category_names(state: GuiState) -> list[str]:
    ensure_data(state)
    categories = load_categories(state.data_dir / "categories.yaml")
    return categories or list(DEFAULT_CATEGORIES)


def add_category(state: GuiState, category: str) -> list[str]:
    value = category.strip()
    if not value:
        raise ValueError("Категория не может быть пустой.")
    categories = category_names(state)
    if value.casefold() not in {item.casefold() for item in categories}:
        categories.append(value)
        save_categories(state.data_dir / "categories.yaml", categories)
    return categories


def add_purchase(
    state: GuiState,
    purchase_name: str,
    amount: str,
    payer: str,
    participants: list[str],
    purchase_date: str | None,
    category: str | None = None,
    comment: str | None = None,
) -> Purchase:
    ensure_data(state)
    parsed_amount = Decimal(amount)
    parsed_date = parse_period_date(purchase_date) if purchase_date else date.today()
    all_names = participant_names(state)
    if payer not in all_names:
        raise ValueError(f"Участник-плательщик не найден: {payer}")
    missing = [participant for participant in participants if participant not in all_names]
    if missing:
        raise ValueError(f"Участники не найдены: {', '.join(missing)}")

    purchase = Purchase(
        id=str(uuid.uuid4())[:8],
        date=parsed_date,
        amount=parsed_amount,
        payer=payer,
        participants=participants,
        purchase_name=purchase_name,
        category=category or None,
        comment=comment or None,
    )
    purchases = list_purchases(state)
    purchases.append(purchase)
    save_purchases(state.data_dir / "purchases.yaml", purchases)
    return purchase


def edit_purchase(
    state: GuiState,
    purchase_id: str,
    purchase_name: str,
    amount: str,
    payer: str,
    participants: list[str],
    purchase_date: str | None,
    category: str | None = None,
    comment: str | None = None,
) -> Purchase:
    purchases = list_purchases(state)
    try:
        index = next(i for i, item in enumerate(purchases) if item.id == purchase_id)
    except StopIteration as exc:
        raise ValueError(f"Покупка не найдена: {purchase_id}") from exc
    current = purchases[index]
    if current.settled or current.settlement_period_id:
        raise ValueError(
            "Покупка относится к закрытому периоду взаиморасчетов. "
            "Сначала переоткройте период или создайте корректирующую покупку."
        )

    all_names = participant_names(state)
    if payer not in all_names:
        raise ValueError(f"Участник-плательщик не найден: {payer}")
    missing = [participant for participant in participants if participant not in all_names]
    if missing:
        raise ValueError(f"Участники не найдены: {', '.join(missing)}")

    updated = Purchase(
        id=current.id,
        date=parse_period_date(purchase_date) if purchase_date else date.today(),
        purchase_name=purchase_name,
        amount=Decimal(amount),
        payer=payer,
        participants=participants,
        category=category or None,
        comment=comment or None,
        settled=current.settled,
        settlement_period_id=current.settlement_period_id,
    )
    purchases[index] = updated
    save_purchases(state.data_dir / "purchases.yaml", purchases)
    return updated


def reset_test_data(state: GuiState, confirm: str):
    ensure_data(state)
    return storage_reset_test_data(state.data_dir, confirm)


def current_balances(state: GuiState):
    names = participant_names(state)
    purchases = filter_purchases_by_settlement_scope(list_purchases(state), scope="open")
    return calculate_balances(purchases, names)


def current_settlements(state: GuiState):
    return calculate_settlements(current_balances(state))


def settlement_periods(state: GuiState):
    ensure_data(state)
    return load_settlement_periods(state.data_dir / "settlement_periods.yaml")


def preview_close_period(state: GuiState, date_from: str, date_to: str):
    return preview_settlement_period(
        list_purchases(state),
        participant_names(state),
        parse_period_date(date_from),
        parse_period_date(date_to),
    )


def close_period(state: GuiState, date_from: str, date_to: str, name: str):
    purchases = list_purchases(state)
    periods = settlement_periods(state)
    period = close_settlement_period(
        purchases,
        periods,
        participant_names(state),
        parse_period_date(date_from),
        parse_period_date(date_to),
        name,
        created_by="gui",
    )
    save_purchases(state.data_dir / "purchases.yaml", purchases)
    save_settlement_periods(state.data_dir / "settlement_periods.yaml", periods)
    return period


def generate_analytics(
    state: GuiState,
    period: str,
    year: int,
    month: int | None = None,
    quarter: int | None = None,
    output_format: str = "all",
) -> Path:
    ensure_data(state)
    period_spec = parse_period(period, year, month=month, quarter=quarter)
    participants = load_participants(state.data_dir / "participants.yaml") or DEFAULT_PARTICIPANTS
    groups = load_groups(state.data_dir / "participants.yaml") or DEFAULT_GROUPS
    dataset = build_analytics_dataset(participants, groups, list_purchases(state), period_spec)
    return generate_analytics_report(dataset, state.analytics_dir, output_format)


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def open_html_report(report_dir: Path) -> None:
    html_path = report_dir / "analytics_dashboard.html"
    if not html_path.is_file():
        raise FileNotFoundError("HTML-отчёт не создан. Сначала выберите формат HTML или all.")
    if platform.system() == "Windows":
        os.startfile(html_path)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(html_path)])
    else:
        subprocess.Popen(["xdg-open", str(html_path)])
