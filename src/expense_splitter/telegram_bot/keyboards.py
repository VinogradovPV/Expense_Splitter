"""Framework-neutral keyboard descriptions for future Telegram SDK wiring."""

from __future__ import annotations

from dataclasses import dataclass

from expense_splitter.services import DELETE_PURCHASE_CONFIRM


@dataclass(frozen=True)
class KeyboardButton:
    text: str
    callback_data: str | None = None


def main_menu() -> list[list[KeyboardButton]]:
    return [
        [KeyboardButton("Добавить покупку", "/add_purchase")],
        [
            KeyboardButton("Текущий PDF", "/current_pdf"),
            KeyboardButton("Текущий XLSX", "/current_xlsx"),
        ],
        [KeyboardButton("Периоды", "/periods")],
    ]


def confirm_purchase_keyboard() -> list[list[KeyboardButton]]:
    return [
        [
            KeyboardButton("Сохранить", "confirm_purchase:yes"),
            KeyboardButton("Отменить", "confirm_purchase:no"),
        ]
    ]


def delete_purchase_hint(purchase_id: str) -> str:
    return f"/delete_purchase {purchase_id} {DELETE_PURCHASE_CONFIRM}"
