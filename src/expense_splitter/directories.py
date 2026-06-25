from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from expense_splitter.models import CategoryEntry, Participant, Purchase, SettlementPeriod
from expense_splitter.storage import (
    load_category_entries,
    load_groups,
    load_participants,
    load_purchases,
    load_settlement_periods,
    save_category_entries,
    save_groups,
    save_participants,
    save_purchases,
    save_settlement_periods,
)

DELETE_CATEGORY_USAGE_CONFIRM = "DELETE_CATEGORY_USAGE"


@dataclass(frozen=True)
class DirectoryUsage:
    open_count: int
    total_count: int
    groups: tuple[str, ...] = ()

    @property
    def is_used(self) -> bool:
        return bool(self.open_count or self.total_count or self.groups)


@dataclass(frozen=True)
class ParticipantDirectoryRow:
    name: str
    status: str
    open_count: int
    total_count: int
    groups: tuple[str, ...]


@dataclass(frozen=True)
class CategoryDirectoryRow:
    name: str
    status: str
    open_count: int
    total_count: int


def list_participant_rows(
    data_dir: Path,
    include_archived: bool = False,
) -> list[ParticipantDirectoryRow]:
    participants = load_participants(data_dir / "participants.yaml")
    groups = load_groups(data_dir / "participants.yaml")
    purchases = load_purchases(data_dir / "purchases.yaml")
    rows = []
    for participant in participants:
        if participant.status == "archived" and not include_archived:
            continue
        usage = participant_usage(participant.name, purchases, groups)
        rows.append(
            ParticipantDirectoryRow(
                name=participant.name,
                status=participant.status,
                open_count=usage.open_count,
                total_count=usage.total_count,
                groups=usage.groups,
            )
        )
    return sorted(rows, key=lambda row: (row.status != "active", row.name.casefold()))


def list_category_rows(
    data_dir: Path,
    include_archived: bool = False,
) -> list[CategoryDirectoryRow]:
    categories = load_category_entries(data_dir / "categories.yaml")
    purchases = load_purchases(data_dir / "purchases.yaml")
    rows = []
    for category in categories:
        if category.status == "archived" and not include_archived:
            continue
        usage = category_usage(category.name, purchases)
        rows.append(
            CategoryDirectoryRow(
                name=category.name,
                status=category.status,
                open_count=usage.open_count,
                total_count=usage.total_count,
            )
        )
    return sorted(rows, key=lambda row: (row.status != "active", row.name.casefold()))


def add_participant(data_dir: Path, name: str) -> Participant:
    value = _clean_name(name, "Имя участника")
    participants = load_participants(data_dir / "participants.yaml")
    _ensure_unique(value, [participant.name for participant in participants], "Участник")
    participant = Participant(name=value)
    participants.append(participant)
    save_participants(data_dir / "participants.yaml", participants)
    return participant


def rename_participant(data_dir: Path, old_name: str, new_name: str) -> Participant:
    old = _clean_name(old_name, "Имя участника")
    new = _clean_name(new_name, "Новое имя участника")
    participants_path = data_dir / "participants.yaml"
    purchases_path = data_dir / "purchases.yaml"
    periods_path = data_dir / "settlement_periods.yaml"
    participants = load_participants(participants_path)
    index = _participant_index(participants, old)
    _ensure_unique(new, [p.name for i, p in enumerate(participants) if i != index], "Участник")

    participants[index] = Participant(name=new, status=participants[index].status)
    groups = load_groups(participants_path)
    for group in groups:
        group.members = [new if member == old else member for member in group.members]

    purchases = load_purchases(purchases_path)
    for purchase in purchases:
        if purchase.payer == old:
            purchase.payer = new
        purchase.participants = [new if item == old else item for item in purchase.participants]

    periods = load_settlement_periods(periods_path)
    for period in periods:
        for settlement in period.settlements:
            if settlement.from_participant == old:
                settlement.from_participant = new
            if settlement.to_participant == old:
                settlement.to_participant = new

    save_participants(participants_path, participants)
    save_groups(participants_path, groups)
    save_purchases(purchases_path, purchases)
    save_settlement_periods(periods_path, periods)
    return participants[index]


def archive_participant(data_dir: Path, name: str) -> Participant:
    participants_path = data_dir / "participants.yaml"
    participants = load_participants(participants_path)
    index = _participant_index(participants, name)
    participants[index] = Participant(name=participants[index].name, status="archived")
    save_participants(participants_path, participants)
    return participants[index]


def delete_participant(data_dir: Path, name: str) -> Participant:
    participants_path = data_dir / "participants.yaml"
    participants = load_participants(participants_path)
    groups = load_groups(participants_path)
    purchases = load_purchases(data_dir / "purchases.yaml")
    periods = load_settlement_periods(data_dir / "settlement_periods.yaml")
    index = _participant_index(participants, name)
    usage = participant_usage(name, purchases, groups)
    if _participant_used_in_periods(name, periods) or usage.open_count or usage.total_count:
        raise ValueError("Участник используется в покупках или периодах; удаление запрещено.")
    deleted = participants.pop(index)
    for group in groups:
        group.members = [member for member in group.members if member != deleted.name]
    save_participants(participants_path, participants)
    save_groups(participants_path, groups)
    return deleted


def add_category(data_dir: Path, name: str) -> CategoryEntry:
    value = _clean_name(name, "Категория")
    categories = load_category_entries(data_dir / "categories.yaml")
    _ensure_unique(value, [category.name for category in categories], "Категория")
    category = CategoryEntry(name=value)
    categories.append(category)
    save_category_entries(data_dir / "categories.yaml", categories)
    return category


def rename_category(data_dir: Path, old_name: str, new_name: str) -> CategoryEntry:
    old = _clean_name(old_name, "Категория")
    new = _clean_name(new_name, "Новая категория")
    categories_path = data_dir / "categories.yaml"
    purchases_path = data_dir / "purchases.yaml"
    categories = load_category_entries(categories_path)
    index = _category_index(categories, old)
    _ensure_unique(new, [c.name for i, c in enumerate(categories) if i != index], "Категория")

    categories[index] = CategoryEntry(name=new, status=categories[index].status)
    purchases = load_purchases(purchases_path)
    for purchase in purchases:
        purchase.category = _rename_category_value(purchase.category, old, new)
    save_category_entries(categories_path, categories)
    save_purchases(purchases_path, purchases)
    return categories[index]


def archive_category(data_dir: Path, name: str) -> CategoryEntry:
    categories_path = data_dir / "categories.yaml"
    categories = load_category_entries(categories_path)
    index = _category_index(categories, name)
    categories[index] = CategoryEntry(name=categories[index].name, status="archived")
    save_category_entries(categories_path, categories)
    return categories[index]


def delete_category(
    data_dir: Path,
    name: str,
    usage_confirm: str = "",
) -> CategoryEntry:
    categories_path = data_dir / "categories.yaml"
    purchases_path = data_dir / "purchases.yaml"
    categories = load_category_entries(categories_path)
    purchases = load_purchases(purchases_path)
    index = _category_index(categories, name)
    usage = category_usage(name, purchases)
    if usage.open_count or usage.total_count:
        if usage_confirm != DELETE_CATEGORY_USAGE_CONFIRM:
            raise ValueError(
                "Категория используется. Для удаления с очисткой покупок введите "
                f"{DELETE_CATEGORY_USAGE_CONFIRM}."
            )
        for purchase in purchases:
            purchase.category = _remove_category_value(purchase.category, categories[index].name)
        save_purchases(purchases_path, purchases)
    deleted = categories.pop(index)
    save_category_entries(categories_path, categories)
    return deleted


def participant_usage(name: str, purchases: list[Purchase], groups) -> DirectoryUsage:
    open_count = 0
    total_count = 0
    for purchase in purchases:
        used = purchase.payer == name or name in purchase.participants
        if not used:
            continue
        total_count += 1
        if not purchase.settled:
            open_count += 1
    group_names = tuple(group.name for group in groups if name in group.members)
    return DirectoryUsage(open_count=open_count, total_count=total_count, groups=group_names)


def category_usage(name: str, purchases: list[Purchase]) -> DirectoryUsage:
    key = name.casefold()
    open_count = 0
    total_count = 0
    for purchase in purchases:
        values = _split_categories(purchase.category)
        if key not in {value.casefold() for value in values}:
            continue
        total_count += 1
        if not purchase.settled:
            open_count += 1
    return DirectoryUsage(open_count=open_count, total_count=total_count)


def _participant_used_in_periods(name: str, periods: list[SettlementPeriod]) -> bool:
    for period in periods:
        for settlement in period.settlements:
            if settlement.from_participant == name or settlement.to_participant == name:
                return True
    return False


def _clean_name(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} не может быть пустым.")
    return cleaned


def _ensure_unique(value: str, values: list[str], label: str) -> None:
    if value.casefold() in {item.casefold() for item in values}:
        raise ValueError(f"{label} уже существует: {value}")


def _participant_index(participants: list[Participant], name: str) -> int:
    key = name.casefold()
    for index, participant in enumerate(participants):
        if participant.name.casefold() == key:
            return index
    raise ValueError(f"Участник не найден: {name}")


def _category_index(categories: list[CategoryEntry], name: str) -> int:
    key = name.casefold()
    for index, category in enumerate(categories):
        if category.name.casefold() == key:
            return index
    raise ValueError(f"Категория не найдена: {name}")


def _split_categories(value: str | None) -> list[str]:
    if not value:
        return []
    result = []
    seen = set()
    for item in value.split(","):
        clean = item.strip()
        key = clean.casefold()
        if clean and key not in seen:
            result.append(clean)
            seen.add(key)
    return result


def _rename_category_value(value: str | None, old: str, new: str) -> str | None:
    values = [
        new if item.casefold() == old.casefold() else item
        for item in _split_categories(value)
    ]
    return ", ".join(values) or None


def _remove_category_value(value: str | None, name: str) -> str | None:
    values = [item for item in _split_categories(value) if item.casefold() != name.casefold()]
    return ", ".join(values) or None
