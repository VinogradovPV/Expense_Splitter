from __future__ import annotations

import argparse
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from expense_splitter.gui import actions
from expense_splitter.gui.dialogs import (
    SETTLEMENT_WARNING,
    AddPurchaseDialog,
    ClosePeriodDialog,
    EditPurchaseDialog,
    parse_comma_separated,
)
from expense_splitter.gui.state import GuiState
from expense_splitter.gui.widgets import clear_tree, make_tree


class ExpenseSplitterGui:
    def __init__(self, root: tk.Tk, state: GuiState):
        self.root = root
        self.state = state
        self.root.title("Expense Splitter")
        self.root.geometry("1100x720")
        self.status_var = tk.StringVar(value="Готово")
        self._build()
        self.refresh_all()

    def _build(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self._build_purchases_tab()
        self._build_balances_tab()
        self._build_periods_tab()
        self._build_analytics_tab()
        self._build_data_tab()
        self._build_help_tab()
        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(
            fill="x", padx=8, pady=4
        )

    def _build_purchases_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Покупки")
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=6, pady=6)
        ttk.Button(toolbar, text="Обновить", command=self.refresh_purchases).pack(side="left")
        ttk.Button(toolbar, text="Добавить покупку", command=self.add_purchase).pack(
            side="left", padx=6
        )
        ttk.Button(toolbar, text="Редактировать покупку", command=self.edit_purchase).pack(
            side="left", padx=6
        )
        self.purchases_tree = make_tree(
            tab,
            ("Дата", "Покупка", "Сумма", "Плательщик", "Участники", "Категория", "Статус"),
        )
        self.purchases_tree.pack(fill="both", expand=True, padx=6, pady=6)

    def _build_balances_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Текущие расчеты")
        ttk.Button(tab, text="Обновить", command=self.refresh_calculations).pack(
            anchor="w", padx=6, pady=6
        )
        pane = ttk.PanedWindow(tab, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=6, pady=6)
        balances_frame = ttk.LabelFrame(pane, text="Балансы open scope")
        settlements_frame = ttk.LabelFrame(pane, text="Итоговые переводы open scope")
        pane.add(balances_frame, weight=1)
        pane.add(settlements_frame, weight=1)
        self.balances_tree = make_tree(balances_frame, ("Участник", "Оплатил", "Доля", "Баланс"))
        self.balances_tree.pack(fill="both", expand=True)
        self.settlements_tree = make_tree(settlements_frame, ("От", "Кому", "Сумма"))
        self.settlements_tree.pack(fill="both", expand=True)

    def _build_periods_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Периоды взаиморасчетов")
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=6, pady=6)
        ttk.Button(toolbar, text="Обновить", command=self.refresh_periods).pack(side="left")
        ttk.Button(toolbar, text="Preview закрытия", command=self.preview_close_period).pack(
            side="left", padx=6
        )
        ttk.Button(
            toolbar,
            text="Закрыть период и обнулить текущие взаиморасчеты",
            command=self.close_period_flow,
        ).pack(side="left", padx=6)
        self.periods_tree = make_tree(
            tab,
            ("ID", "Название", "Статус", "С", "По", "Покупок", "Сумма"),
        )
        self.periods_tree.pack(fill="both", expand=True, padx=6, pady=6)

    def _build_analytics_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Аналитика и отчеты")
        form = ttk.Frame(tab)
        form.pack(anchor="nw", padx=8, pady=8)
        self.analytics_period_var = tk.StringVar(value="month")
        self.analytics_year_var = tk.StringVar(value=str(date.today().year))
        self.analytics_month_var = tk.StringVar(value=str(date.today().month))
        self.analytics_quarter_var = tk.StringVar(value="1")
        self.analytics_format_var = tk.StringVar(value="all")
        self.last_analytics_report_dir: Path | None = None
        rows = (
            ("Период", self.analytics_period_var, ("month", "quarter", "year")),
            ("Год", self.analytics_year_var, None),
            ("Месяц", self.analytics_month_var, None),
            ("Квартал", self.analytics_quarter_var, ("1", "2", "3", "4")),
            ("Формат", self.analytics_format_var, ("markdown", "csv", "png", "html", "all")),
        )
        for row, (label, variable, values) in enumerate(rows):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=4)
            if values:
                ttk.Combobox(form, textvariable=variable, values=values, state="readonly").grid(
                    row=row, column=1, sticky="ew", padx=4, pady=4
                )
            else:
                ttk.Entry(form, textvariable=variable).grid(
                    row=row, column=1, sticky="ew", padx=4, pady=4
                )
        ttk.Button(form, text="Создать отчет", command=self.generate_analytics).grid(
            row=len(rows), column=0, sticky="ew", padx=4, pady=8
        )
        ttk.Button(
            form,
            text="Открыть папку reports",
            command=lambda: self.open_path(self.state.reports_dir),
        ).grid(row=len(rows), column=1, sticky="ew", padx=4, pady=8)
        ttk.Button(form, text="Открыть HTML", command=self.open_html_report).grid(
            row=len(rows) + 1, column=0, columnspan=2, sticky="ew", padx=4, pady=4
        )

    def _build_data_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Данные и обслуживание")
        ttk.Button(
            tab,
            text="Открыть папку data",
            command=lambda: self.open_path(self.state.data_dir),
        ).pack(anchor="w", padx=8, pady=8)
        ttk.Button(
            tab,
            text="Открыть папку reports",
            command=lambda: self.open_path(self.state.reports_dir),
        ).pack(anchor="w", padx=8, pady=8)
        ttk.Button(tab, text="Проверить данные", command=self.validate_data).pack(
            anchor="w", padx=8, pady=8
        )
        ttk.Separator(tab, orient="horizontal").pack(fill="x", padx=8, pady=10)
        ttk.Label(
            tab,
            text=(
                "Сброс тестовых данных удаляет покупки и периоды, но сохраняет "
                "участников, группы и категории. Перед очисткой создаются backup-файлы."
            ),
            wraplength=720,
        ).pack(anchor="w", padx=8, pady=4)
        ttk.Button(
            tab,
            text="Сбросить тестовые данные",
            command=self.reset_test_data,
        ).pack(anchor="w", padx=8, pady=8)

    def _build_help_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Справка")
        text = tk.Text(tab, wrap="word", height=16)
        text.pack(fill="both", expand=True, padx=8, pady=8)
        text.insert(
            "1.0",
            "Expense Splitter GUI\n\n"
            "Покупки не удаляются при закрытии периода. Закрытие создает снимок "
            "взаиморасчетов и исключает выбранные покупки из текущего open scope.\n\n"
            "Сброс тестовых данных — отдельная операция: после typed confirm она создает "
            "backup и очищает покупки и периоды, сохраняя участников, группы и категории.\n\n"
            "HTML и XLSX отчеты будут доступны после соответствующих этапов P2.A.",
        )
        text.configure(state="disabled")

    def run_safely(self, action, success_status: str | None = None):
        try:
            result = action()
        except Exception as error:
            messagebox.showerror("Ошибка", str(error), parent=self.root)
            self.status_var.set("Ошибка")
            return None
        if success_status:
            self.status_var.set(success_status)
        return result

    def refresh_all(self) -> None:
        self.refresh_purchases()
        self.refresh_calculations()
        self.refresh_periods()

    def refresh_purchases(self) -> None:
        def action():
            clear_tree(self.purchases_tree)
            for purchase in actions.list_purchases(self.state):
                self.purchases_tree.insert(
                    "",
                    "end",
                    iid=purchase.id,
                    values=actions.purchase_row(purchase),
                )

        self.run_safely(action, "Покупки обновлены")

    def refresh_calculations(self) -> None:
        def action():
            clear_tree(self.balances_tree)
            for balance in actions.current_balances(self.state):
                self.balances_tree.insert(
                    "",
                    "end",
                    values=(
                        balance.participant,
                        f"{balance.paid:.2f}",
                        f"{balance.share:.2f}",
                        f"{balance.net:.2f}",
                    ),
                )
            clear_tree(self.settlements_tree)
            for settlement in actions.current_settlements(self.state):
                self.settlements_tree.insert(
                    "",
                    "end",
                    values=(
                        settlement.from_participant,
                        settlement.to_participant,
                        f"{settlement.amount:.2f}",
                    ),
                )

        self.run_safely(action, "Текущие расчеты обновлены")

    def refresh_periods(self) -> None:
        def action():
            clear_tree(self.periods_tree)
            for period in actions.settlement_periods(self.state):
                self.periods_tree.insert(
                    "",
                    "end",
                    values=(
                        period.id,
                        period.name,
                        period.status,
                        period.date_from.isoformat(),
                        period.date_to.isoformat(),
                        len(period.purchase_ids),
                        f"{period.total_amount:.2f}",
                    ),
                )

        self.run_safely(action, "Периоды обновлены")

    def add_purchase(self) -> None:
        names = actions.participant_names(self.state)
        dialog = AddPurchaseDialog(self.root, names, actions.category_names(self.state))
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        data = dialog.result
        if not self._confirm_new_categories(data.category):
            self.status_var.set("Добавление покупки отменено")
            return
        self.run_safely(
            lambda: actions.add_purchase(
                self.state,
                data.purchase_name,
                data.amount,
                data.payer,
                data.participants,
                data.purchase_date,
                data.category,
                data.comment,
            ),
            "Покупка добавлена",
        )
        self.refresh_all()

    def _confirm_new_categories(self, category_value: str) -> bool:
        known = {item.casefold() for item in actions.category_names(self.state)}
        for category in parse_comma_separated(category_value):
            if category.casefold() in known:
                continue
            if not messagebox.askyesno(
                "Новая категория",
                f'Категория "{category}" отсутствует в справочнике. Добавить ее?',
                parent=self.root,
            ):
                return False
            saved_categories = self.run_safely(
                lambda value=category: actions.add_category(self.state, value)
            )
            if saved_categories is None:
                return False
            known.add(category.casefold())
        return True

    def edit_purchase(self) -> None:
        selected = self.purchases_tree.selection()
        if not selected:
            messagebox.showwarning(
                "Редактирование", "Выберите покупку в таблице.", parent=self.root
            )
            return
        purchase_id = selected[0]
        purchase = next(
            (item for item in actions.list_purchases(self.state) if item.id == purchase_id),
            None,
        )
        if purchase is None:
            messagebox.showerror("Ошибка", "Выбранная покупка не найдена.", parent=self.root)
            return
        if purchase.settled or purchase.settlement_period_id:
            messagebox.showwarning(
                "Редактирование запрещено",
                "Покупка относится к закрытому периоду взаиморасчетов. "
                "Сначала переоткройте период или создайте корректирующую покупку.",
                parent=self.root,
            )
            return
        dialog = EditPurchaseDialog(
            self.root,
            actions.participant_names(self.state),
            actions.category_names(self.state),
            purchase,
        )
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        data = dialog.result
        if not self._confirm_new_categories(data.category):
            self.status_var.set("Редактирование отменено")
            return
        updated = self.run_safely(
            lambda: actions.edit_purchase(
                self.state,
                purchase.id,
                data.purchase_name,
                data.amount,
                data.payer,
                data.participants,
                data.purchase_date,
                data.category,
                data.comment,
            ),
            "Покупка изменена",
        )
        if updated:
            self.refresh_all()

    def reset_test_data(self) -> None:
        if not messagebox.askyesno(
            "Сброс тестовых данных",
            "Будет создан backup. Покупки и закрытые периоды взаиморасчетов будут "
            "очищены. Участники, группы и категории сохранятся. Продолжить?",
            parent=self.root,
        ):
            return
        confirm = simpledialog.askstring(
            "Typed confirm",
            "Введите RESET_TEST_DATA:",
            parent=self.root,
        )
        if confirm != "RESET_TEST_DATA":
            messagebox.showwarning("Сброс отменен", "Подтверждение не совпало.", parent=self.root)
            return
        result = self.run_safely(
            lambda: actions.reset_test_data(self.state, confirm),
            "Тестовые данные сброшены",
        )
        if result is None:
            return
        self.refresh_all()
        backups = "\n".join(str(path) for path in result.backup_paths) or "Новые файлы были пустыми"
        messagebox.showinfo(
            "Сброс завершен",
            "Покупки и периоды очищены. Участники, группы и категории сохранены.\n\n"
            f"Backup:\n{backups}",
            parent=self.root,
        )

    def _period_input(self):
        dialog = ClosePeriodDialog(self.root)
        self.root.wait_window(dialog)
        return dialog.result

    def preview_close_period(self) -> None:
        data = self._period_input()
        if not data:
            return

        def action():
            preview = actions.preview_close_period(self.state, data.date_from, data.date_to)
            messagebox.showinfo(
                "Preview закрытия периода",
                f"Покупок: {preview.purchase_count}\n"
                f"Сумма: {preview.total_amount:.2f}\n"
                f"Переводов: {len(preview.settlements)}\n\n"
                f"{SETTLEMENT_WARNING}",
                parent=self.root,
            )

        self.run_safely(action, "Preview закрытия периода построен")

    def close_period_flow(self) -> None:
        data = self._period_input()
        if not data:
            return
        preview = self.run_safely(
            lambda: actions.preview_close_period(self.state, data.date_from, data.date_to)
        )
        if preview is None:
            return
        if not messagebox.askyesno(
            "Подтверждение",
            f"{SETTLEMENT_WARNING}\n\n"
            f"Покупок: {preview.purchase_count}\nСумма: {preview.total_amount:.2f}\n\n"
            "Закрыть период?",
            parent=self.root,
        ):
            self.status_var.set("Закрытие периода отменено")
            return
        period = self.run_safely(
            lambda: actions.close_period(self.state, data.date_from, data.date_to, data.name),
            "Период закрыт",
        )
        if period:
            messagebox.showinfo("Период закрыт", f"Создан период {period.id}", parent=self.root)
        self.refresh_all()

    def generate_analytics(self) -> None:
        def action():
            period = self.analytics_period_var.get()
            year = int(self.analytics_year_var.get())
            month = int(self.analytics_month_var.get()) if period == "month" else None
            quarter = int(self.analytics_quarter_var.get()) if period == "quarter" else None
            output_format = self.analytics_format_var.get()
            return actions.generate_analytics(
                self.state,
                period,
                year,
                month=month,
                quarter=quarter,
                output_format=output_format,
            )

        report_dir = self.run_safely(action, "Аналитический отчет создан")
        if report_dir:
            self.last_analytics_report_dir = report_dir
            messagebox.showinfo("Отчет создан", f"Папка отчета:\n{report_dir}", parent=self.root)

    def open_html_report(self) -> None:
        if self.last_analytics_report_dir is None:
            messagebox.showerror(
                "HTML не найден",
                "Сначала создайте отчёт в формате HTML или all.",
                parent=self.root,
            )
            return
        self.run_safely(
            lambda: actions.open_html_report(self.last_analytics_report_dir),
            "HTML-отчёт открыт",
        )

    def open_path(self, path: Path) -> None:
        self.run_safely(lambda: actions.open_folder(path), f"Открыта папка {path}")

    def validate_data(self) -> None:
        def action():
            actions.participant_names(self.state)
            purchases = actions.list_purchases(self.state)
            messagebox.showinfo(
                "Проверка данных",
                f"Данные читаются корректно.\nПокупок: {len(purchases)}",
                parent=self.root,
            )

        self.run_safely(action, "Данные проверены")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Desktop GUI launcher for Expense Splitter.")
    parser.add_argument("--data-dir", default="data", help="Data directory")
    parser.add_argument("--reports-dir", default="reports", help="Reports directory")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    state = GuiState(
        data_dir=Path(args.data_dir),
        reports_dir=Path(args.reports_dir),
        analytics_dir=Path(args.reports_dir) / "analytics",
    )
    state.ensure_data_files()
    root = tk.Tk()
    ExpenseSplitterGui(root, state)
    root.mainloop()


if __name__ == "__main__":
    main()
