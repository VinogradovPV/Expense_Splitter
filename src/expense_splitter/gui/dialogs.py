from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from datetime import date
from tkinter import messagebox, ttk


SETTLEMENT_WARNING = (
    "Покупки не будут удалены. Будет создан снимок взаиморасчетов, выбранные покупки "
    "будут помечены как закрытые. Новые текущие расчеты начнутся только по незакрытым покупкам."
)


@dataclass
class PurchaseInput:
    purchase_name: str
    amount: str
    payer: str
    participants: list[str]
    purchase_date: str
    category: str
    comment: str


@dataclass
class PeriodInput:
    date_from: str
    date_to: str
    name: str


class AddPurchaseDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, participant_names: list[str]):
        super().__init__(parent)
        self.title("Добавить покупку")
        self.resizable(False, False)
        self.result: PurchaseInput | None = None
        self.transient(parent)
        self.grab_set()

        self.name_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.payer_var = tk.StringVar(value=participant_names[0] if participant_names else "")
        self.participants_var = tk.StringVar(value=", ".join(participant_names))
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.category_var = tk.StringVar()
        self.comment_var = tk.StringVar()

        rows = (
            ("Наименование", self.name_var),
            ("Сумма", self.amount_var),
            ("Плательщик", self.payer_var),
            ("Участники через запятую", self.participants_var),
            ("Дата YYYY-MM-DD", self.date_var),
            ("Категория", self.category_var),
            ("Комментарий", self.comment_var),
        )
        for index, (label, variable) in enumerate(rows):
            ttk.Label(self, text=label).grid(row=index, column=0, sticky="w", padx=8, pady=4)
            ttk.Entry(self, textvariable=variable, width=48).grid(
                row=index, column=1, sticky="ew", padx=8, pady=4
            )

        buttons = ttk.Frame(self)
        buttons.grid(row=len(rows), column=0, columnspan=2, sticky="e", padx=8, pady=8)
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(buttons, text="Добавить", command=self._submit).pack(side="right", padx=4)

    def _submit(self) -> None:
        if not self.name_var.get().strip() or not self.amount_var.get().strip():
            messagebox.showerror("Ошибка", "Заполните наименование и сумму.", parent=self)
            return
        participants = [
            item.strip()
            for item in self.participants_var.get().split(",")
            if item.strip()
        ]
        if not participants:
            messagebox.showerror("Ошибка", "Укажите хотя бы одного участника.", parent=self)
            return
        self.result = PurchaseInput(
            purchase_name=self.name_var.get().strip(),
            amount=self.amount_var.get().strip(),
            payer=self.payer_var.get().strip(),
            participants=participants,
            purchase_date=self.date_var.get().strip(),
            category=self.category_var.get().strip(),
            comment=self.comment_var.get().strip(),
        )
        self.destroy()


class ClosePeriodDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Закрыть период")
        self.resizable(False, False)
        self.result: PeriodInput | None = None
        self.transient(parent)
        self.grab_set()

        today = date.today().isoformat()
        self.from_var = tk.StringVar(value=today)
        self.to_var = tk.StringVar(value=today)
        self.name_var = tk.StringVar(value=f"Период до {today}")

        rows = (
            ("Дата начала YYYY-MM-DD", self.from_var),
            ("Дата окончания YYYY-MM-DD", self.to_var),
            ("Название периода", self.name_var),
        )
        for index, (label, variable) in enumerate(rows):
            ttk.Label(self, text=label).grid(row=index, column=0, sticky="w", padx=8, pady=4)
            ttk.Entry(self, textvariable=variable, width=40).grid(
                row=index, column=1, sticky="ew", padx=8, pady=4
            )
        ttk.Label(self, text=SETTLEMENT_WARNING, wraplength=460).grid(
            row=len(rows), column=0, columnspan=2, sticky="w", padx=8, pady=8
        )

        buttons = ttk.Frame(self)
        buttons.grid(row=len(rows) + 1, column=0, columnspan=2, sticky="e", padx=8, pady=8)
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(buttons, text="Preview", command=self._submit).pack(side="right", padx=4)

    def _submit(self) -> None:
        self.result = PeriodInput(
            date_from=self.from_var.get().strip(),
            date_to=self.to_var.get().strip(),
            name=self.name_var.get().strip(),
        )
        self.destroy()
