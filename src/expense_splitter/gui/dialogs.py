from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from datetime import date
from tkinter import messagebox, ttk

from expense_splitter.models import Purchase

SETTLEMENT_WARNING = (
    "Покупки не будут удалены. Они будут помечены как закрытые. "
    "Новые расчеты начнутся по открытым покупкам."
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


def purchase_input_from_purchase(purchase: Purchase) -> PurchaseInput:
    return PurchaseInput(
        purchase_name=purchase.purchase_name,
        amount=str(purchase.amount),
        payer=purchase.payer,
        participants=list(purchase.participants),
        purchase_date=purchase.date.isoformat() if purchase.date else "",
        category=purchase.category or "",
        comment=purchase.comment or "",
    )


@dataclass
class PeriodInput:
    date_from: str
    date_to: str
    name: str


@dataclass
class PeriodMetadataInput:
    name: str
    notes: str
    date_from: str
    date_to: str


class ChecklistDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        values: list[str],
        selected: list[str],
    ):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result: list[str] | None = None
        self.transient(parent)
        self.grab_set()
        selected_keys = {item.casefold() for item in selected}
        self.variables = {
            value: tk.BooleanVar(value=value.casefold() in selected_keys) for value in values
        }
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=8)
        for value, variable in self.variables.items():
            ttk.Checkbutton(body, text=value, variable=variable).pack(anchor="w")
        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=8, pady=8)
        ttk.Button(controls, text="Выбрать все", command=self._select_all).pack(side="left")
        ttk.Button(controls, text="Снять все", command=self._clear_all).pack(side="left", padx=4)
        ttk.Button(controls, text="Отмена", command=self.destroy).pack(side="right")
        ttk.Button(controls, text="Применить", command=self._apply).pack(side="right", padx=4)

    def _select_all(self) -> None:
        for variable in self.variables.values():
            variable.set(True)

    def _clear_all(self) -> None:
        for variable in self.variables.values():
            variable.set(False)

    def _apply(self) -> None:
        self.result = [value for value, variable in self.variables.items() if variable.get()]
        self.destroy()


def parse_comma_separated(value: str) -> list[str]:
    result = []
    seen = set()
    for item in value.split(","):
        clean = item.strip()
        key = clean.casefold()
        if clean and key not in seen:
            result.append(clean)
            seen.add(key)
    return result


def normalize_known_values(
    values: list[str], known_values: list[str]
) -> tuple[list[str], list[str]]:
    known_by_key = {value.casefold(): value for value in known_values}
    normalized = []
    unknown = []
    for value in values:
        canonical = known_by_key.get(value.casefold())
        if canonical is None:
            unknown.append(value)
        else:
            normalized.append(canonical)
    return normalized, unknown


class PurchaseDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        participant_names: list[str],
        categories: list[str],
        purchase: Purchase | None = None,
    ):
        super().__init__(parent)
        self.purchase = purchase
        self.title("Редактировать покупку" if purchase else "Добавить покупку")
        self.resizable(False, False)
        self.result: PurchaseInput | None = None
        self.transient(parent)
        self.grab_set()

        self.participant_names = participant_names
        self.categories = categories
        initial = purchase_input_from_purchase(purchase) if purchase else None
        self.name_var = tk.StringVar(value=initial.purchase_name if initial else "")
        self.amount_var = tk.StringVar(value=initial.amount if initial else "")
        default_payer = (
            initial.payer if initial else (participant_names[0] if participant_names else "")
        )
        self.payer_var = tk.StringVar(value=default_payer)
        selected_participants = initial.participants if initial else participant_names
        self.participants_var = tk.StringVar(value=", ".join(selected_participants))
        purchase_date = initial.purchase_date if initial else date.today().isoformat()
        self.date_var = tk.StringVar(value=purchase_date)
        self.category_var = tk.StringVar(value=initial.category if initial else "")
        self.comment_var = tk.StringVar(value=initial.comment if initial else "")

        ttk.Label(self, text="Наименование").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(self, textvariable=self.name_var, width=48).grid(
            row=0, column=1, sticky="ew", padx=8, pady=4
        )
        ttk.Label(self, text="Сумма").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(self, textvariable=self.amount_var).grid(
            row=1, column=1, sticky="ew", padx=8, pady=4
        )
        ttk.Label(self, text="Плательщик").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        ttk.Combobox(
            self, textvariable=self.payer_var, values=participant_names, state="readonly"
        ).grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(self, text="Участники через запятую").grid(
            row=3, column=0, sticky="w", padx=8, pady=4
        )
        participant_row = ttk.Frame(self)
        participant_row.grid(row=3, column=1, sticky="ew", padx=8, pady=4)
        ttk.Entry(participant_row, textvariable=self.participants_var, width=34).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(participant_row, text="Выбрать…", command=self._choose_participants).pack(
            side="left", padx=(4, 0)
        )
        ttk.Label(self, text="Дата YYYY-MM-DD").grid(row=4, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(self, textvariable=self.date_var).grid(
            row=4, column=1, sticky="ew", padx=8, pady=4
        )
        ttk.Label(self, text="Категория").grid(row=5, column=0, sticky="w", padx=8, pady=4)
        category_row = ttk.Frame(self)
        category_row.grid(row=5, column=1, sticky="ew", padx=8, pady=4)
        ttk.Combobox(
            category_row,
            textvariable=self.category_var,
            values=categories,
            state="normal",
            width=32,
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(category_row, text="Выбрать…", command=self._choose_categories).pack(
            side="left", padx=(4, 0)
        )
        ttk.Label(self, text="Комментарий").grid(row=6, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(self, textvariable=self.comment_var).grid(
            row=6, column=1, sticky="ew", padx=8, pady=4
        )

        buttons = ttk.Frame(self)
        buttons.grid(row=7, column=0, columnspan=2, sticky="e", padx=8, pady=8)
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="right", padx=4)
        submit_text = "Сохранить" if purchase else "Добавить"
        ttk.Button(buttons, text=submit_text, command=self._submit).pack(side="right", padx=4)

    def _choose_participants(self) -> None:
        dialog = ChecklistDialog(
            self,
            "Выбрать участников",
            self.participant_names,
            parse_comma_separated(self.participants_var.get()),
        )
        self.wait_window(dialog)
        if dialog.result is not None:
            self.participants_var.set(", ".join(dialog.result))

    def _choose_categories(self) -> None:
        dialog = ChecklistDialog(
            self,
            "Выбрать категории",
            self.categories,
            parse_comma_separated(self.category_var.get()),
        )
        self.wait_window(dialog)
        if dialog.result is not None:
            self.category_var.set(", ".join(dialog.result))

    def _submit(self) -> None:
        if not self.name_var.get().strip() or not self.amount_var.get().strip():
            messagebox.showerror("Ошибка", "Заполните наименование и сумму.", parent=self)
            return
        participants = parse_comma_separated(self.participants_var.get())
        if not participants:
            messagebox.showerror("Ошибка", "Укажите хотя бы одного участника.", parent=self)
            return
        participants, unknown = normalize_known_values(participants, self.participant_names)
        if unknown:
            messagebox.showwarning(
                "Неизвестные участники",
                "Следующие участники отсутствуют в справочнике и не были добавлены: "
                f"{', '.join(unknown)}. Исправьте список или сначала добавьте их в справочник.",
                parent=self,
            )
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


class AddPurchaseDialog(PurchaseDialog):
    def __init__(self, parent: tk.Tk, participant_names: list[str], categories: list[str]):
        super().__init__(parent, participant_names, categories)


class EditPurchaseDialog(PurchaseDialog):
    def __init__(
        self,
        parent: tk.Tk,
        participant_names: list[str],
        categories: list[str],
        purchase: Purchase,
    ):
        super().__init__(parent, participant_names, categories, purchase)


class ClosePeriodDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, suggested: PeriodInput | None = None):
        super().__init__(parent)
        self.title("Закрыть период")
        self.resizable(False, False)
        self.result: PeriodInput | None = None
        self.suggested = suggested
        self.transient(parent)
        self.grab_set()

        today = date.today().isoformat()
        self.from_var = tk.StringVar(value=today)
        self.to_var = tk.StringVar(value=today)
        self.name_var = tk.StringVar(value=f"Период до {today}")
        if suggested is not None:
            self.from_var.set(suggested.date_from)
            self.to_var.set(suggested.date_to)
            self.name_var.set(suggested.name)

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
        ttk.Button(buttons, text="Автозаполнить период", command=self._apply_suggestion).pack(
            side="right", padx=4
        )

    def _apply_suggestion(self) -> None:
        if self.suggested is None:
            return
        self.from_var.set(self.suggested.date_from)
        self.to_var.set(self.suggested.date_to)
        self.name_var.set(self.suggested.name)

    def _submit(self) -> None:
        self.result = PeriodInput(
            date_from=self.from_var.get().strip(),
            date_to=self.to_var.get().strip(),
            name=self.name_var.get().strip(),
        )
        self.destroy()


class PeriodMetadataDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, period, allow_dates: bool):
        super().__init__(parent)
        self.title("Редактировать период")
        self.resizable(False, False)
        self.result: PeriodMetadataInput | None = None
        self.transient(parent)
        self.grab_set()
        self.allow_dates = allow_dates

        self.name_var = tk.StringVar(value=period.name)
        self.notes_var = tk.StringVar(value=period.notes or "")
        self.from_var = tk.StringVar(value=period.date_from.isoformat())
        self.to_var = tk.StringVar(value=period.date_to.isoformat())

        rows = (
            ("Название периода", self.name_var, True),
            ("Notes", self.notes_var, True),
            ("Дата начала YYYY-MM-DD", self.from_var, allow_dates),
            ("Дата окончания YYYY-MM-DD", self.to_var, allow_dates),
        )
        for index, (label, variable, enabled) in enumerate(rows):
            ttk.Label(self, text=label).grid(row=index, column=0, sticky="w", padx=8, pady=4)
            state = "normal" if enabled else "disabled"
            ttk.Entry(self, textvariable=variable, width=48, state=state).grid(
                row=index,
                column=1,
                sticky="ew",
                padx=8,
                pady=4,
            )

        if not allow_dates:
            ttk.Label(
                self,
                text=(
                    "Даты закрытого периода с покупками нельзя изменить напрямую. "
                    "Переоткройте период и закройте новый диапазон."
                ),
                wraplength=460,
            ).grid(row=len(rows), column=0, columnspan=2, sticky="w", padx=8, pady=8)

        buttons = ttk.Frame(self)
        buttons.grid(row=len(rows) + 1, column=0, columnspan=2, sticky="e", padx=8, pady=8)
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(buttons, text="Сохранить", command=self._submit).pack(side="right", padx=4)

    def _submit(self) -> None:
        self.result = PeriodMetadataInput(
            name=self.name_var.get().strip(),
            notes=self.notes_var.get().strip(),
            date_from=self.from_var.get().strip(),
            date_to=self.to_var.get().strip(),
        )
        self.destroy()
