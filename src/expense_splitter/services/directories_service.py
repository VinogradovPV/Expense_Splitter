"""Participant and category directory use cases."""

from __future__ import annotations

from dataclasses import dataclass

from expense_splitter.models import CategoryEntry, Participant, Purchase, SettlementPeriod
from expense_splitter.repositories.protocols import (
    CategoryRepository,
    ParticipantRepository,
    PurchaseRepository,
    SettlementPeriodRepository,
)

DELETE_CATEGORY_USAGE_CONFIRM = "DELETE_CATEGORY_USAGE"


@dataclass(frozen=True)
class DirectoryUsage:
    open_count: int
    total_count: int

    @property
    def is_used(self) -> bool:
        return bool(self.open_count or self.total_count)


@dataclass(frozen=True)
class ParticipantDirectoryRow:
    name: str
    status: str
    open_count: int
    total_count: int


@dataclass(frozen=True)
class CategoryDirectoryRow:
    name: str
    status: str
    open_count: int
    total_count: int


class DirectoryService:
    """Directory orchestration above repositories, with no filesystem assumptions."""

    def __init__(
        self,
        participants: ParticipantRepository,
        categories: CategoryRepository,
        purchases: PurchaseRepository,
        settlement_periods: SettlementPeriodRepository,
    ) -> None:
        self.participants = participants
        self.categories = categories
        self.purchases = purchases
        self.settlement_periods = settlement_periods

    def list_participants(
        self,
        tenant_id: str,
        include_archived: bool = False,
    ) -> list[ParticipantDirectoryRow]:
        purchases = self.purchases.list_purchases(tenant_id)
        rows = []
        for participant in self.participants.list_participants(tenant_id):
            if participant.status == "archived" and not include_archived:
                continue
            usage = _participant_usage(participant.name, purchases)
            rows.append(
                ParticipantDirectoryRow(
                    name=participant.name,
                    status=participant.status,
                    open_count=usage.open_count,
                    total_count=usage.total_count,
                )
            )
        return sorted(rows, key=lambda row: (row.status != "active", row.name.casefold()))

    def add_participant(self, tenant_id: str, name: str) -> Participant:
        value = _clean_name(name, "Имя участника")
        participants = self.participants.list_participants(tenant_id)
        _ensure_unique(value, [participant.name for participant in participants], "Участник")
        participant = Participant(value)
        participants.append(participant)
        self.participants.save_participants(tenant_id, participants)
        return participant

    def rename_participant(
        self,
        tenant_id: str,
        old_name: str,
        new_name: str,
    ) -> Participant:
        old = _clean_name(old_name, "Имя участника")
        new = _clean_name(new_name, "Новое имя участника")
        participants = self.participants.list_participants(tenant_id)
        index = _participant_index(participants, old)
        _ensure_unique(
            new,
            [participant.name for i, participant in enumerate(participants) if i != index],
            "Участник",
        )

        participants[index] = Participant(new, status=participants[index].status)
        purchases = self.purchases.list_purchases(tenant_id)
        for purchase in purchases:
            if purchase.payer == old:
                purchase.payer = new
            purchase.participants = [
                new if participant == old else participant
                for participant in purchase.participants
            ]

        periods = self.settlement_periods.list_periods(tenant_id)
        for period in periods:
            for settlement in period.settlements:
                if settlement.from_participant == old:
                    settlement.from_participant = new
                if settlement.to_participant == old:
                    settlement.to_participant = new

        self.participants.save_participants(tenant_id, participants)
        self.purchases.replace_purchases(tenant_id, purchases)
        self.settlement_periods.replace_periods(tenant_id, periods)
        return participants[index]

    def archive_participant(self, tenant_id: str, name: str) -> Participant:
        participants = self.participants.list_participants(tenant_id)
        index = _participant_index(participants, name)
        participants[index] = Participant(participants[index].name, status="archived")
        self.participants.save_participants(tenant_id, participants)
        return participants[index]

    def delete_participant(self, tenant_id: str, name: str) -> Participant:
        participants = self.participants.list_participants(tenant_id)
        purchases = self.purchases.list_purchases(tenant_id)
        periods = self.settlement_periods.list_periods(tenant_id)
        index = _participant_index(participants, name)
        usage = _participant_usage(name, purchases)
        if _participant_used_in_periods(name, periods) or usage.is_used:
            raise ValueError(
                "Участник используется в покупках или периодах; удаление запрещено."
            )
        deleted = participants.pop(index)
        self.participants.save_participants(tenant_id, participants)
        return deleted

    def list_categories(
        self,
        tenant_id: str,
        include_archived: bool = False,
    ) -> list[CategoryDirectoryRow]:
        purchases = self.purchases.list_purchases(tenant_id)
        rows = []
        for category in self.categories.list_categories(tenant_id):
            if category.status == "archived" and not include_archived:
                continue
            usage = _category_usage(category.name, purchases)
            rows.append(
                CategoryDirectoryRow(
                    name=category.name,
                    status=category.status,
                    open_count=usage.open_count,
                    total_count=usage.total_count,
                )
            )
        return sorted(rows, key=lambda row: (row.status != "active", row.name.casefold()))

    def add_category(self, tenant_id: str, name: str) -> CategoryEntry:
        value = _clean_name(name, "Категория")
        categories = self.categories.list_categories(tenant_id)
        _ensure_unique(value, [category.name for category in categories], "Категория")
        category = CategoryEntry(value)
        categories.append(category)
        self.categories.save_categories(tenant_id, categories)
        return category

    def rename_category(
        self,
        tenant_id: str,
        old_name: str,
        new_name: str,
    ) -> CategoryEntry:
        old = _clean_name(old_name, "Категория")
        new = _clean_name(new_name, "Новая категория")
        categories = self.categories.list_categories(tenant_id)
        index = _category_index(categories, old)
        _ensure_unique(
            new,
            [category.name for i, category in enumerate(categories) if i != index],
            "Категория",
        )

        categories[index] = CategoryEntry(new, status=categories[index].status)
        purchases = self.purchases.list_purchases(tenant_id)
        for purchase in purchases:
            purchase.category = _rename_category_value(purchase.category, old, new)

        self.categories.save_categories(tenant_id, categories)
        self.purchases.replace_purchases(tenant_id, purchases)
        return categories[index]

    def archive_category(self, tenant_id: str, name: str) -> CategoryEntry:
        categories = self.categories.list_categories(tenant_id)
        index = _category_index(categories, name)
        categories[index] = CategoryEntry(categories[index].name, status="archived")
        self.categories.save_categories(tenant_id, categories)
        return categories[index]

    def delete_category(
        self,
        tenant_id: str,
        name: str,
        usage_confirm: str = "",
    ) -> CategoryEntry:
        categories = self.categories.list_categories(tenant_id)
        purchases = self.purchases.list_purchases(tenant_id)
        index = _category_index(categories, name)
        usage = _category_usage(name, purchases)
        if usage.is_used:
            if usage_confirm != DELETE_CATEGORY_USAGE_CONFIRM:
                raise ValueError(
                    "Категория используется. Для удаления с очисткой покупок введите "
                    f"{DELETE_CATEGORY_USAGE_CONFIRM}."
                )
            for purchase in purchases:
                purchase.category = _remove_category_value(
                    purchase.category,
                    categories[index].name,
                )
            self.purchases.replace_purchases(tenant_id, purchases)

        deleted = categories.pop(index)
        self.categories.save_categories(tenant_id, categories)
        return deleted


def _participant_usage(name: str, purchases: list[Purchase]) -> DirectoryUsage:
    open_count = 0
    total_count = 0
    for purchase in purchases:
        if purchase.payer != name and name not in purchase.participants:
            continue
        total_count += 1
        if not purchase.settled:
            open_count += 1
    return DirectoryUsage(open_count=open_count, total_count=total_count)


def _category_usage(name: str, purchases: list[Purchase]) -> DirectoryUsage:
    key = name.casefold()
    open_count = 0
    total_count = 0
    for purchase in purchases:
        if key not in {value.casefold() for value in _split_categories(purchase.category)}:
            continue
        total_count += 1
        if not purchase.settled:
            open_count += 1
    return DirectoryUsage(open_count=open_count, total_count=total_count)


def _participant_used_in_periods(
    name: str,
    periods: list[SettlementPeriod],
) -> bool:
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
    values = [
        item
        for item in _split_categories(value)
        if item.casefold() != name.casefold()
    ]
    return ", ".join(values) or None
