from __future__ import annotations

import os
import platform
import shutil
import subprocess
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.calculator import calculate_balances
from expense_splitter.current_report import build_current_report_dataset, generate_current_report
from expense_splitter.defaults import DEFAULT_CATEGORIES, DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.directories import (
    DELETE_CATEGORY_USAGE_CONFIRM as DIRECTORY_DELETE_CATEGORY_USAGE_CONFIRM,
)
from expense_splitter.directories import (
    add_category as directory_add_category,
)
from expense_splitter.directories import (
    add_participant as directory_add_participant,
)
from expense_splitter.directories import (
    archive_category as directory_archive_category,
)
from expense_splitter.directories import (
    archive_participant as directory_archive_participant,
)
from expense_splitter.directories import (
    delete_category as directory_delete_category,
)
from expense_splitter.directories import (
    delete_participant as directory_delete_participant,
)
from expense_splitter.directories import (
    list_category_rows,
    list_participant_rows,
)
from expense_splitter.directories import (
    rename_category as directory_rename_category,
)
from expense_splitter.directories import (
    rename_participant as directory_rename_participant,
)
from expense_splitter.gui.state import GuiState
from expense_splitter.models import Purchase
from expense_splitter.settlement import calculate_settlements
from expense_splitter.settlement_period_report import (
    build_settlement_period_report_dataset,
    generate_settlement_period_report,
)
from expense_splitter.settlement_periods import (
    DELETE_EMPTY_PERIOD_CONFIRM as SETTLEMENT_DELETE_EMPTY_PERIOD_CONFIRM,
)
from expense_splitter.settlement_periods import (
    DELETE_EMPTY_PERIODS_CONFIRM as SETTLEMENT_DELETE_EMPTY_PERIODS_CONFIRM,
)
from expense_splitter.settlement_periods import (
    close_settlement_period,
    delete_empty_settlement_period,
    delete_empty_settlement_periods,
    filter_purchases_by_settlement_scope,
    get_settlement_period,
    is_empty_settlement_period,
    parse_period_date,
    preview_settlement_period,
    reopen_settlement_period,
    suggest_next_settlement_period,
    update_settlement_period_metadata,
)
from expense_splitter.storage import (
    initialize_data_files,
    load_categories,
    load_groups,
    load_participants,
    load_purchases,
    load_settlement_periods,
    save_purchases,
    save_settlement_periods,
)
from expense_splitter.storage import (
    reset_test_data as storage_reset_test_data,
)

DELETE_CATEGORY_USAGE_CONFIRM = DIRECTORY_DELETE_CATEGORY_USAGE_CONFIRM
DELETE_EMPTY_PERIOD_CONFIRM = SETTLEMENT_DELETE_EMPTY_PERIOD_CONFIRM
DELETE_EMPTY_PERIODS_CONFIRM = SETTLEMENT_DELETE_EMPTY_PERIODS_CONFIRM


def ensure_data(state: GuiState) -> None:
    initialize_data_files(state.data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)


def participant_names(state: GuiState) -> list[str]:
    ensure_data(state)
    names = [
        participant.name
        for participant in load_participants(
            state.data_dir / "participants.yaml",
            include_archived=False,
        )
    ]
    return names or [participant.name for participant in DEFAULT_PARTICIPANTS]


def all_participant_names(state: GuiState) -> list[str]:
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


def filter_and_sort_purchases(
    purchases: list[Purchase],
    *,
    status: str = "all",
    category: str = "",
    date_from: str = "",
    date_to: str = "",
    search: str = "",
    sort_by: str = "date",
    descending: bool = False,
) -> list[Purchase]:
    if status not in {"open", "settled", "all"}:
        raise ValueError("Статус фильтра должен быть open, settled или all.")
    start = parse_period_date(date_from) if date_from else None
    end = parse_period_date(date_to) if date_to else None
    if start and end and start > end:
        raise ValueError("Дата начала фильтра не может быть позже даты окончания.")
    query = search.strip().casefold()
    category_key = category.strip().casefold()
    result = []
    for purchase in purchases:
        is_settled = bool(purchase.settled or purchase.settlement_period_id)
        if status == "open" and is_settled:
            continue
        if status == "settled" and not is_settled:
            continue
        if category_key and (purchase.category or "без категории").casefold() != category_key:
            continue
        if start and (purchase.date is None or purchase.date < start):
            continue
        if end and (purchase.date is None or purchase.date > end):
            continue
        if query and query not in purchase.purchase_name.casefold():
            continue
        result.append(purchase)

    keys = {
        "date": lambda item: item.date or date.min,
        "amount": lambda item: item.amount,
        "category": lambda item: (item.category or "").casefold(),
        "payer": lambda item: item.payer.casefold(),
    }
    if sort_by not in keys:
        raise ValueError("Неизвестное поле сортировки.")
    return sorted(result, key=keys[sort_by], reverse=descending)


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
    directory_add_category(state.data_dir, category)
    return category_names(state)


def participant_directory_rows(state: GuiState, include_archived: bool = False):
    ensure_data(state)
    return list_participant_rows(state.data_dir, include_archived=include_archived)


def category_directory_rows(state: GuiState, include_archived: bool = False):
    ensure_data(state)
    return list_category_rows(state.data_dir, include_archived=include_archived)


def add_participant(state: GuiState, name: str):
    ensure_data(state)
    return directory_add_participant(state.data_dir, name)


def rename_participant(state: GuiState, old_name: str, new_name: str):
    ensure_data(state)
    return directory_rename_participant(state.data_dir, old_name, new_name)


def archive_participant(state: GuiState, name: str):
    ensure_data(state)
    return directory_archive_participant(state.data_dir, name)


def delete_participant(state: GuiState, name: str):
    ensure_data(state)
    return directory_delete_participant(state.data_dir, name)


def rename_category(state: GuiState, old_name: str, new_name: str):
    ensure_data(state)
    return directory_rename_category(state.data_dir, old_name, new_name)


def archive_category(state: GuiState, name: str):
    ensure_data(state)
    return directory_archive_category(state.data_dir, name)


def delete_category(state: GuiState, name: str, usage_confirm: str = ""):
    ensure_data(state)
    return directory_delete_category(state.data_dir, name, usage_confirm)


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


def delete_purchase(state: GuiState, purchase_id: str, confirm: str) -> Purchase:
    if confirm != "DELETE_PURCHASE":
        raise ValueError("Для удаления введите DELETE_PURCHASE без изменений.")
    purchases = list_purchases(state)
    try:
        purchase = next(item for item in purchases if item.id == purchase_id)
    except StopIteration as exc:
        raise ValueError(f"Покупка не найдена: {purchase_id}") from exc
    if purchase.settled or purchase.settlement_period_id:
        raise ValueError(
            "Закрытую покупку удалить нельзя. Сначала переоткройте период "
            "или создайте корректирующую покупку."
        )
    save_purchases(
        state.data_dir / "purchases.yaml",
        [item for item in purchases if item.id != purchase_id],
    )
    return purchase


def reset_test_data(state: GuiState, confirm: str):
    ensure_data(state)
    return storage_reset_test_data(state.data_dir, confirm)


def balances(state: GuiState, scope: str = "open"):
    names = all_participant_names(state)
    purchases = filter_purchases_by_settlement_scope(list_purchases(state), scope=scope)
    return calculate_balances(purchases, names)


def current_balances(state: GuiState):
    return balances(state, "open")


def settlements(state: GuiState, scope: str = "open"):
    return calculate_settlements(balances(state, scope))


def current_settlements(state: GuiState):
    return settlements(state, "open")


def settlement_periods(state: GuiState):
    ensure_data(state)
    return load_settlement_periods(state.data_dir / "settlement_periods.yaml")


def visible_settlement_periods(
    state: GuiState,
    status_filter: str = "all",
    hide_empty: bool = True,
):
    rows = settlement_periods(state)
    if hide_empty:
        rows = [period for period in rows if not is_empty_settlement_period(period)]
    if status_filter == "closed":
        rows = [period for period in rows if period.status == "closed"]
    elif status_filter == "reopened":
        rows = [period for period in rows if period.status == "reopened"]
    elif status_filter == "empty":
        rows = [
            period
            for period in settlement_periods(state)
            if is_empty_settlement_period(period)
        ]
    elif status_filter == "with_purchases":
        rows = [period for period in rows if not is_empty_settlement_period(period)]
    elif status_filter != "all":
        raise ValueError(
            "Фильтр периодов должен быть all, closed, reopened, empty или with_purchases."
        )
    return rows


def is_empty_period(period) -> bool:
    return is_empty_settlement_period(period)


def suggest_close_period(state: GuiState):
    ensure_data(state)
    return suggest_next_settlement_period(list_purchases(state), settlement_periods(state))


def preview_close_period(state: GuiState, date_from: str, date_to: str):
    return preview_settlement_period(
        list_purchases(state),
        all_participant_names(state),
        parse_period_date(date_from),
        parse_period_date(date_to),
    )


def close_period(state: GuiState, date_from: str, date_to: str, name: str):
    purchases = list_purchases(state)
    periods = settlement_periods(state)
    period = close_settlement_period(
        purchases,
        periods,
        all_participant_names(state),
        parse_period_date(date_from),
        parse_period_date(date_to),
        name,
        created_by="gui",
    )
    save_purchases(state.data_dir / "purchases.yaml", purchases)
    save_settlement_periods(state.data_dir / "settlement_periods.yaml", periods)
    return period


def edit_period_metadata(
    state: GuiState,
    period_id: str,
    name: str,
    notes: str,
    date_from: str | None = None,
    date_to: str | None = None,
):
    periods = settlement_periods(state)
    period = update_settlement_period_metadata(
        periods,
        period_id,
        name=name,
        notes=notes,
        date_from=parse_period_date(date_from) if date_from else None,
        date_to=parse_period_date(date_to) if date_to else None,
    )
    save_settlement_periods(state.data_dir / "settlement_periods.yaml", periods)
    return period


def delete_empty_period(state: GuiState, period_id: str, confirm: str):
    periods = settlement_periods(state)
    period = delete_empty_settlement_period(periods, period_id, confirm)
    save_settlement_periods(state.data_dir / "settlement_periods.yaml", periods)
    return period


def delete_all_empty_periods(state: GuiState, confirm: str):
    periods = settlement_periods(state)
    deleted = delete_empty_settlement_periods(periods, confirm)
    if deleted:
        save_settlement_periods(state.data_dir / "settlement_periods.yaml", periods)
    return deleted


def settlement_period(state: GuiState, period_id: str):
    return get_settlement_period(settlement_periods(state), period_id)


def reopen_period(state: GuiState, period_id: str):
    purchases = list_purchases(state)
    periods = settlement_periods(state)
    period = reopen_settlement_period(purchases, periods, period_id)
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


def generate_current_state_report(state: GuiState, output_format: str = "all") -> Path:
    ensure_data(state)
    participants = load_participants(state.data_dir / "participants.yaml") or DEFAULT_PARTICIPANTS
    dataset = build_current_report_dataset(participants, list_purchases(state), scope="open")
    return generate_current_report(dataset, state.current_state_dir, output_format)


def generate_settlement_period_snapshot_report(
    state: GuiState,
    settlement_period_id: str,
    output_format: str = "all",
) -> Path:
    ensure_data(state)
    participants = load_participants(state.data_dir / "participants.yaml") or DEFAULT_PARTICIPANTS
    dataset = build_settlement_period_report_dataset(
        settlement_periods(state),
        list_purchases(state),
        participants,
        settlement_period_id,
    )
    return generate_settlement_period_report(
        dataset,
        state.reports_dir / "settlement_periods",
        output_format,
    )


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


def open_xlsx_report(report_dir: Path) -> None:
    matches = sorted(report_dir.glob("expense_analytics_*.xlsx"))
    if not matches:
        raise FileNotFoundError("XLSX-отчёт не создан. Сначала выберите формат XLSX или all.")
    xlsx_path = matches[0]
    if platform.system() == "Windows":
        os.startfile(xlsx_path)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(xlsx_path)])
    else:
        subprocess.Popen(["xdg-open", str(xlsx_path)])


def report_path(report_dir: Path, report_type: str) -> Path:
    patterns = {
        "html": "analytics_dashboard.html",
        "markdown": "analytics_report.md",
        "xlsx": "expense_analytics_*.xlsx",
        "pdf": "expense_analytics_*.pdf",
    }
    if report_type not in patterns:
        raise ValueError("Неизвестный тип отчёта.")
    matches = sorted(report_dir.glob(patterns[report_type]))
    if not matches:
        label = report_type.upper() if report_type != "markdown" else "Markdown"
        raise FileNotFoundError(
            f"{label}-отчёт не создан. Сначала создайте отчёт в нужном формате или all."
        )
    return matches[0]


def current_report_path(report_dir: Path, report_type: str) -> Path:
    names = {
        "html": "current_state_dashboard.html",
        "markdown": "current_state_report.md",
        "xlsx": "current_state.xlsx",
        "pdf": "current_state.pdf",
    }
    if report_type not in names:
        raise ValueError("Неизвестный тип отчета.")
    path = report_dir / names[report_type]
    if not path.is_file():
        label = report_type.upper() if report_type != "markdown" else "Markdown"
        raise FileNotFoundError(
            f"{label}-отчет текущих взаиморасчетов не создан. "
            "Сначала создайте отчет текущих взаиморасчетов."
        )
    return path


def settlement_period_report_path(report_dir: Path, report_type: str) -> Path:
    names = {
        "html": "settlement_period_dashboard.html",
        "markdown": "settlement_period_report.md",
        "xlsx": "settlement_period.xlsx",
        "pdf": "settlement_period.pdf",
    }
    if report_type not in names:
        raise ValueError("Неизвестный тип отчета.")
    path = report_dir / names[report_type]
    if not path.is_file():
        label = report_type.upper() if report_type != "markdown" else "Markdown"
        raise FileNotFoundError(
            f"{label}-отчет периода не создан. Сначала создайте отчет периода."
        )
    return path


def open_report(report_dir: Path, report_type: str) -> None:
    path = report_path(report_dir, report_type)
    if platform.system() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def open_current_report(report_dir: Path, report_type: str) -> None:
    path = current_report_path(report_dir, report_type)
    if platform.system() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def open_settlement_period_report(report_dir: Path, report_type: str) -> None:
    path = settlement_period_report_path(report_dir, report_type)
    if platform.system() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def create_data_backup(state: GuiState) -> Path:
    ensure_data(state)
    target = state.data_dir / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    target.mkdir(parents=True, exist_ok=False)
    for path in state.data_dir.glob("*.yaml"):
        shutil.copy2(path, target / path.name)
    return target
