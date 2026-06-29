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
    PeriodInput,
    PeriodMetadataDialog,
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
        self.last_current_report_dir: Path | None = None
        self.last_period_report_dirs: dict[str, Path] = {}
        self._build()
        self.refresh_all()

    def _build(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self._build_purchases_tab()
        self._build_balances_tab()
        self._build_periods_tab()
        self._build_analytics_tab()
        self._build_directories_tab()
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
        self.period_status_filter_var = tk.StringVar(value="all")
        self.hide_empty_periods_var = tk.BooleanVar(value=True)
        ttk.Combobox(
            toolbar,
            textvariable=self.period_status_filter_var,
            values=("all", "closed", "reopened", "empty", "with_purchases"),
            state="readonly",
            width=16,
        ).pack(side="left", padx=6)
        ttk.Checkbutton(
            toolbar,
            text="Скрыть пустые",
            variable=self.hide_empty_periods_var,
            command=self.refresh_periods,
        ).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Обновить", command=self.refresh_purchases).pack(side="left")
        ttk.Button(toolbar, text="Добавить покупку", command=self.add_purchase).pack(
            side="left", padx=6
        )
        ttk.Button(toolbar, text="Редактировать покупку", command=self.edit_purchase).pack(
            side="left", padx=6
        )
        ttk.Button(toolbar, text="Детали", command=self.show_purchase_details).pack(
            side="left", padx=6
        )
        ttk.Button(toolbar, text="Удалить покупку", command=self.delete_purchase).pack(
            side="left", padx=6
        )
        ttk.Button(toolbar, text="Период покупки", command=self.show_purchase_period).pack(
            side="left", padx=6
        )
        filters = ttk.LabelFrame(tab, text="Фильтры")
        filters.pack(fill="x", padx=6, pady=(0, 6))
        self.purchase_status_var = tk.StringVar(value="all")
        self.purchase_category_filter_var = tk.StringVar()
        self.purchase_from_var = tk.StringVar()
        self.purchase_to_var = tk.StringVar()
        self.purchase_search_var = tk.StringVar()
        filter_specs = (
            ("Статус", self.purchase_status_var, ("all", "open", "settled")),
            (
                "Категория",
                self.purchase_category_filter_var,
                ("", *actions.category_names(self.state)),
            ),
            ("С YYYY-MM-DD", self.purchase_from_var, None),
            ("По YYYY-MM-DD", self.purchase_to_var, None),
            ("Поиск", self.purchase_search_var, None),
        )
        for column, (label, variable, values) in enumerate(filter_specs):
            ttk.Label(filters, text=label).grid(row=0, column=column, padx=3, sticky="w")
            if values is None:
                ttk.Entry(filters, textvariable=variable, width=16).grid(
                    row=1, column=column, padx=3
                )
            else:
                combo = ttk.Combobox(
                    filters, textvariable=variable, values=values, state="readonly", width=16
                )
                combo.grid(row=1, column=column, padx=3)
                if variable is self.purchase_category_filter_var:
                    self.purchase_category_filter_combo = combo
        ttk.Button(filters, text="Применить", command=self.refresh_purchases).grid(
            row=1, column=5, padx=6
        )
        self.purchase_sort_by = "date"
        self.purchase_sort_desc = True
        self.purchases_tree = make_tree(
            tab,
            ("Дата", "Покупка", "Сумма", "Плательщик", "Участники", "Категория", "Статус"),
        )
        self.purchases_tree.pack(fill="both", expand=True, padx=6, pady=6)
        for column, sort_key in {
            "Дата": "date",
            "Сумма": "amount",
            "Категория": "category",
            "Плательщик": "payer",
        }.items():
            self.purchases_tree.heading(
                column, text=column, command=lambda key=sort_key: self.sort_purchases(key)
            )

    def _build_balances_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Текущие расчеты")
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=6, pady=6)
        self.calculation_scope_var = tk.StringVar(value="open")
        ttk.Button(toolbar, text="Обновить", command=self.refresh_calculations).pack(side="left")
        ttk.Button(
            toolbar, text="Только открытые", command=lambda: self.set_calculation_scope("open")
        ).pack(side="left", padx=6)
        ttk.Button(
            toolbar,
            text="Показать все с историей",
            command=lambda: self.set_calculation_scope("all"),
        ).pack(side="left", padx=6)
        ttk.Button(
            toolbar,
            text="Создать отчет текущих взаиморасчетов",
            command=self.generate_current_state_report,
        ).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Открыть HTML", command=self.open_current_html_report).pack(
            side="left", padx=6
        )
        ttk.Button(toolbar, text="Открыть XLSX", command=self.open_current_xlsx_report).pack(
            side="left", padx=6
        )
        ttk.Button(
            toolbar,
            text="Открыть папку отчета",
            command=self.open_current_report_folder,
        ).pack(side="left", padx=6)
        self.scope_label_var = tk.StringVar()
        ttk.Label(tab, textvariable=self.scope_label_var, wraplength=900).pack(anchor="w", padx=6)
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
        ttk.Button(toolbar, text="Детали периода", command=self.show_period_details).pack(
            side="left", padx=6
        )
        ttk.Button(toolbar, text="Переоткрыть период", command=self.reopen_period).pack(
            side="left", padx=6
        )
        ttk.Button(
            toolbar,
            text="Создать отчет периода",
            command=self.generate_period_report,
        ).pack(side="left", padx=6)
        ttk.Button(
            toolbar,
            text="Открыть HTML отчета периода",
            command=self.open_period_html_report,
        ).pack(side="left", padx=6)
        ttk.Button(
            toolbar,
            text="Открыть XLSX отчета периода",
            command=self.open_period_xlsx_report,
        ).pack(side="left", padx=6)
        ttk.Button(
            toolbar,
            text="Открыть папку отчета периода",
            command=self.open_period_report_folder,
        ).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Редактировать период", command=self.edit_period).pack(
            side="left", padx=6
        )
        ttk.Button(toolbar, text="Удалить период", command=self.delete_empty_period).pack(
            side="left", padx=6
        )
        ttk.Button(
            toolbar,
            text="Удалить пустые тестовые периоды",
            command=self.delete_all_empty_periods,
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
        self.last_report_status_var = tk.StringVar(value="Отчёт ещё не создавался")
        rows = (
            ("Период", self.analytics_period_var, ("month", "quarter", "year")),
            ("Год", self.analytics_year_var, None),
            ("Месяц", self.analytics_month_var, None),
            ("Квартал", self.analytics_quarter_var, ("1", "2", "3", "4")),
            (
                "Формат",
                self.analytics_format_var,
                ("markdown", "csv", "png", "html", "xlsx", "all"),
            ),
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
            text="Открыть папку отчета",
            command=self.open_report_folder,
        ).grid(row=len(rows), column=1, sticky="ew", padx=4, pady=8)
        ttk.Button(form, text="Открыть HTML", command=self.open_html_report).grid(
            row=len(rows) + 1, column=0, sticky="ew", padx=4, pady=4
        )
        ttk.Button(form, text="Открыть XLSX", command=self.open_xlsx_report).grid(
            row=len(rows) + 1, column=1, sticky="ew", padx=4, pady=4
        )
        ttk.Button(form, text="Открыть Markdown", command=self.open_markdown_report).grid(
            row=len(rows) + 2, column=0, columnspan=2, sticky="ew", padx=4, pady=4
        )
        ttk.Label(form, textvariable=self.last_report_status_var, wraplength=500).grid(
            row=len(rows) + 3, column=0, columnspan=2, sticky="w", padx=4, pady=8
        )

    def _build_directories_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Справочники")
        pane = ttk.PanedWindow(tab, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=6, pady=6)

        participants_frame = ttk.LabelFrame(pane, text="Участники")
        categories_frame = ttk.LabelFrame(pane, text="Категории")
        pane.add(participants_frame, weight=1)
        pane.add(categories_frame, weight=1)

        participants_toolbar = ttk.Frame(participants_frame)
        participants_toolbar.pack(fill="x", padx=4, pady=4)
        ttk.Button(
            participants_toolbar,
            text="Добавить участника",
            command=self.add_directory_participant,
        ).pack(side="left")
        ttk.Button(
            participants_toolbar,
            text="Переименовать участника",
            command=self.rename_directory_participant,
        ).pack(side="left", padx=4)
        ttk.Button(
            participants_toolbar,
            text="Архивировать участника",
            command=self.archive_directory_participant,
        ).pack(side="left", padx=4)
        ttk.Button(
            participants_toolbar,
            text="Удалить участника",
            command=self.delete_directory_participant,
        ).pack(side="left", padx=4)
        ttk.Button(
            participants_toolbar, text="Обновить", command=self.refresh_directories
        ).pack(side="left", padx=4)
        self.show_archived_participants_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            participants_toolbar,
            text="Показать архивные",
            variable=self.show_archived_participants_var,
            command=self.refresh_directories,
        ).pack(side="left", padx=8)

        self.participants_directory_tree = make_tree(
            participants_frame,
            ("Имя", "Статус", "Открытые покупки", "Всего покупок", "Группы"),
        )
        self.participants_directory_tree.pack(fill="both", expand=True, padx=4, pady=4)

        categories_toolbar = ttk.Frame(categories_frame)
        categories_toolbar.pack(fill="x", padx=4, pady=4)
        ttk.Button(
            categories_toolbar,
            text="Добавить категорию",
            command=self.add_directory_category,
        ).pack(side="left")
        ttk.Button(
            categories_toolbar,
            text="Переименовать категорию",
            command=self.rename_directory_category,
        ).pack(side="left", padx=4)
        ttk.Button(
            categories_toolbar,
            text="Архивировать категорию",
            command=self.archive_directory_category,
        ).pack(side="left", padx=4)
        ttk.Button(
            categories_toolbar,
            text="Удалить категорию",
            command=self.delete_directory_category,
        ).pack(side="left", padx=4)
        ttk.Button(categories_toolbar, text="Обновить", command=self.refresh_directories).pack(
            side="left", padx=4
        )
        self.show_archived_categories_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            categories_toolbar,
            text="Показать архивные",
            variable=self.show_archived_categories_var,
            command=self.refresh_directories,
        ).pack(side="left", padx=8)

        self.categories_directory_tree = make_tree(
            categories_frame,
            ("Категория", "Статус", "Открытые покупки", "Всего покупок"),
        )
        self.categories_directory_tree.pack(fill="both", expand=True, padx=4, pady=4)

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
        ttk.Button(tab, text="Создать backup данных", command=self.create_backup).pack(
            anchor="w", padx=8, pady=8
        )

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
        self.refresh_directories()

    def refresh_purchases(self) -> None:
        def action():
            if hasattr(self, "purchase_category_filter_combo"):
                self.purchase_category_filter_combo.configure(
                    values=("", *actions.category_names(self.state))
                )
            clear_tree(self.purchases_tree)
            purchases = actions.filter_and_sort_purchases(
                actions.list_purchases(self.state),
                status=self.purchase_status_var.get(),
                category=self.purchase_category_filter_var.get(),
                date_from=self.purchase_from_var.get().strip(),
                date_to=self.purchase_to_var.get().strip(),
                search=self.purchase_search_var.get(),
                sort_by=self.purchase_sort_by,
                descending=self.purchase_sort_desc,
            )
            for purchase in purchases:
                self.purchases_tree.insert(
                    "",
                    "end",
                    iid=purchase.id,
                    values=actions.purchase_row(purchase),
                )

        self.run_safely(action, "Покупки обновлены")

    def sort_purchases(self, sort_by: str) -> None:
        if self.purchase_sort_by == sort_by:
            self.purchase_sort_desc = not self.purchase_sort_desc
        else:
            self.purchase_sort_by = sort_by
            self.purchase_sort_desc = False
        self.refresh_purchases()

    def _selected_purchase(self):
        selected = self.purchases_tree.selection()
        if not selected:
            messagebox.showwarning("Покупки", "Выберите покупку в таблице.", parent=self.root)
            return None
        purchase_id = selected[0]
        return next(
            (item for item in actions.list_purchases(self.state) if item.id == purchase_id),
            None,
        )

    def show_purchase_details(self) -> None:
        purchase = self._selected_purchase()
        if purchase is None:
            return
        messagebox.showinfo(
            "Детали покупки",
            f"Покупка: {purchase.purchase_name}\nДата: {purchase.date}\n"
            f"Сумма: {purchase.amount:.2f}\nПлательщик: {purchase.payer}\n"
            f"Участники: {', '.join(purchase.participants)}\n"
            f"Категория: {purchase.category or 'Без категории'}\n"
            f"Комментарий: {purchase.comment or '—'}\n"
            f"Статус: {'settled' if purchase.settled else 'open'}",
            parent=self.root,
        )

    def delete_purchase(self) -> None:
        purchase = self._selected_purchase()
        if purchase is None:
            return
        if purchase.settled or purchase.settlement_period_id:
            messagebox.showwarning(
                "Удаление запрещено",
                "Закрытую покупку удалить нельзя. Сначала переоткройте период "
                "или создайте корректирующую покупку.",
                parent=self.root,
            )
            return
        if not messagebox.askyesno(
            "Удалить покупку",
            f'Будет создан backup. Удалить покупку "{purchase.purchase_name}"?',
            parent=self.root,
        ):
            return
        confirm = simpledialog.askstring(
            "Typed confirm",
            "Введите DELETE_PURCHASE:",
            parent=self.root,
        )
        if confirm != "DELETE_PURCHASE":
            messagebox.showwarning(
                "Удаление отменено", "Подтверждение не совпало.", parent=self.root
            )
            return
        deleted = self.run_safely(
            lambda: actions.delete_purchase(self.state, purchase.id, confirm),
            "Покупка удалена",
        )
        if deleted:
            self.refresh_all()

    def show_purchase_period(self) -> None:
        purchase = self._selected_purchase()
        if purchase is None:
            return
        if not purchase.settlement_period_id:
            messagebox.showinfo(
                "Период покупки",
                "Покупка открыта и не относится к закрытому периоду.",
                parent=self.root,
            )
            return
        self._show_period(actions.settlement_period(self.state, purchase.settlement_period_id))

    def set_calculation_scope(self, scope: str) -> None:
        self.calculation_scope_var.set(scope)
        self.refresh_calculations()

    def refresh_calculations(self) -> None:
        def action():
            scope = self.calculation_scope_var.get()
            self.scope_label_var.set(
                "Scope: open — закрытые покупки не входят в текущие расчёты."
                if scope == "open"
                else "Scope: all — показан расчёт по всей истории, включая закрытые покупки."
            )
            clear_tree(self.balances_tree)
            for balance in actions.balances(self.state, scope):
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
            for settlement in actions.settlements(self.state, scope):
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

    def generate_current_state_report(self) -> None:
        report_dir = self.run_safely(
            lambda: actions.generate_current_state_report(self.state),
            None,
        )
        if report_dir:
            self.last_current_report_dir = report_dir
            message = f"Отчет текущих взаиморасчетов создан: {report_dir}"
            self.status_var.set(message)
            messagebox.showinfo("Отчет создан", f"Папка отчета:\n{report_dir}", parent=self.root)

    def _require_current_report_dir(self) -> Path | None:
        if self.last_current_report_dir is None:
            messagebox.showerror(
                "Отчет не создан",
                "Сначала создайте отчет текущих взаиморасчетов.",
                parent=self.root,
            )
            return None
        return self.last_current_report_dir

    def open_current_html_report(self) -> None:
        report_dir = self._require_current_report_dir()
        if report_dir is None:
            return
        self.run_safely(
            lambda: actions.open_current_report(report_dir, "html"),
            "HTML-отчет текущих взаиморасчетов открыт",
        )

    def open_current_xlsx_report(self) -> None:
        report_dir = self._require_current_report_dir()
        if report_dir is None:
            return
        self.run_safely(
            lambda: actions.open_current_report(report_dir, "xlsx"),
            "XLSX-отчет текущих взаиморасчетов открыт",
        )

    def open_current_report_folder(self) -> None:
        report_dir = self._require_current_report_dir()
        if report_dir is None:
            return
        self.open_path(report_dir)

    def refresh_periods(self) -> None:
        def action():
            clear_tree(self.periods_tree)
            for period in actions.visible_settlement_periods(
                self.state,
                self.period_status_filter_var.get(),
                self.hide_empty_periods_var.get(),
            ):
                self.periods_tree.insert(
                    "",
                    "end",
                    iid=period.id,
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

    def refresh_directories(self) -> None:
        if not hasattr(self, "participants_directory_tree"):
            return

        def action():
            clear_tree(self.participants_directory_tree)
            for row in actions.participant_directory_rows(
                self.state,
                include_archived=self.show_archived_participants_var.get(),
            ):
                self.participants_directory_tree.insert(
                    "",
                    "end",
                    iid=row.name,
                    values=(
                        row.name,
                        row.status,
                        row.open_count,
                        row.total_count,
                        ", ".join(row.groups),
                    ),
                )
            clear_tree(self.categories_directory_tree)
            for row in actions.category_directory_rows(
                self.state,
                include_archived=self.show_archived_categories_var.get(),
            ):
                self.categories_directory_tree.insert(
                    "",
                    "end",
                    iid=row.name,
                    values=(row.name, row.status, row.open_count, row.total_count),
                )

        self.run_safely(action, "Справочники обновлены")

    def _selected_directory_participant(self) -> str | None:
        selected = self.participants_directory_tree.selection()
        if not selected:
            messagebox.showwarning("Справочники", "Выберите участника.", parent=self.root)
            return None
        return selected[0]

    def _selected_directory_category(self) -> str | None:
        selected = self.categories_directory_tree.selection()
        if not selected:
            messagebox.showwarning("Справочники", "Выберите категорию.", parent=self.root)
            return None
        return selected[0]

    def _refresh_after_directory_change(self) -> None:
        self.refresh_directories()
        self.refresh_purchases()
        self.refresh_calculations()

    def add_directory_participant(self) -> None:
        name = simpledialog.askstring("Добавить участника", "Имя участника:", parent=self.root)
        if name is None:
            return
        result = self.run_safely(
            lambda: actions.add_participant(self.state, name),
            "Участник добавлен",
        )
        if result:
            self._refresh_after_directory_change()

    def rename_directory_participant(self) -> None:
        old_name = self._selected_directory_participant()
        if old_name is None:
            return
        new_name = simpledialog.askstring(
            "Переименовать участника",
            "Новое имя участника:",
            initialvalue=old_name,
            parent=self.root,
        )
        if new_name is None:
            return
        if not messagebox.askyesno(
            "Подтверждение",
            "Будут обновлены участник, группы, покупки и snapshots периодов. Продолжить?",
            parent=self.root,
        ):
            return
        result = self.run_safely(
            lambda: actions.rename_participant(self.state, old_name, new_name),
            "Участник переименован",
        )
        if result:
            self._refresh_after_directory_change()
            self.refresh_periods()

    def archive_directory_participant(self) -> None:
        name = self._selected_directory_participant()
        if name is None:
            return
        if not messagebox.askyesno(
            "Архивировать участника",
            f'Архивировать участника "{name}"? Он исчезнет из новых покупок.',
            parent=self.root,
        ):
            return
        result = self.run_safely(
            lambda: actions.archive_participant(self.state, name),
            "Участник архивирован",
        )
        if result:
            self._refresh_after_directory_change()

    def delete_directory_participant(self) -> None:
        name = self._selected_directory_participant()
        if name is None:
            return
        if not messagebox.askyesno(
            "Удалить участника",
            f'Удалить участника "{name}"? Используемый участник не будет удален.',
            parent=self.root,
        ):
            return
        result = self.run_safely(
            lambda: actions.delete_participant(self.state, name),
            "Участник удален",
        )
        if result:
            self._refresh_after_directory_change()

    def add_directory_category(self) -> None:
        name = simpledialog.askstring("Добавить категорию", "Категория:", parent=self.root)
        if name is None:
            return
        result = self.run_safely(
            lambda: actions.add_category(self.state, name),
            "Категория добавлена",
        )
        if result:
            self._refresh_after_directory_change()

    def rename_directory_category(self) -> None:
        old_name = self._selected_directory_category()
        if old_name is None:
            return
        new_name = simpledialog.askstring(
            "Переименовать категорию",
            "Новая категория:",
            initialvalue=old_name,
            parent=self.root,
        )
        if new_name is None:
            return
        if not messagebox.askyesno(
            "Подтверждение",
            "Категория будет обновлена во всех покупках, включая строки с несколькими "
            "категориями. Продолжить?",
            parent=self.root,
        ):
            return
        result = self.run_safely(
            lambda: actions.rename_category(self.state, old_name, new_name),
            "Категория переименована",
        )
        if result:
            self._refresh_after_directory_change()

    def archive_directory_category(self) -> None:
        name = self._selected_directory_category()
        if name is None:
            return
        if not messagebox.askyesno(
            "Архивировать категорию",
            f'Архивировать категорию "{name}"? Она исчезнет из новых покупок.',
            parent=self.root,
        ):
            return
        result = self.run_safely(
            lambda: actions.archive_category(self.state, name),
            "Категория архивирована",
        )
        if result:
            self._refresh_after_directory_change()

    def delete_directory_category(self) -> None:
        name = self._selected_directory_category()
        if name is None:
            return
        confirm = ""
        if not messagebox.askyesno(
            "Удалить категорию",
            f'Удалить категорию "{name}"? Если она используется, потребуется typed confirm.',
            parent=self.root,
        ):
            return
        confirm = simpledialog.askstring(
            "Typed confirm",
            f"Если категория используется и нужно очистить ее в покупках, введите "
            f"{actions.DELETE_CATEGORY_USAGE_CONFIRM}:",
            parent=self.root,
        ) or ""
        result = self.run_safely(
            lambda: actions.delete_category(self.state, name, confirm),
            "Категория удалена",
        )
        if result:
            self._refresh_after_directory_change()

    def _selected_period(self):
        selected = self.periods_tree.selection()
        if not selected:
            messagebox.showwarning("Периоды", "Выберите период в таблице.", parent=self.root)
            return None
        return actions.settlement_period(self.state, selected[0])

    def _require_period_report_dir(self) -> tuple[object, Path] | tuple[None, None]:
        period = self._selected_period()
        if not period:
            return None, None
        report_dir = self.last_period_report_dirs.get(period.id)
        if report_dir is None:
            messagebox.showerror(
                "Отчет не создан",
                "Сначала создайте отчет периода.",
                parent=self.root,
            )
            return None, None
        return period, report_dir

    def generate_period_report(self) -> None:
        period = self._selected_period()
        if not period:
            return
        if period.status == "reopened":
            messagebox.showwarning(
                "Период переоткрыт",
                "Период был переоткрыт. Отчет показывает сохраненный snapshot периода.",
                parent=self.root,
            )
        report_dir = self.run_safely(
            lambda: actions.generate_settlement_period_snapshot_report(self.state, period.id),
            None,
        )
        if report_dir:
            self.last_period_report_dirs[period.id] = report_dir
            message = f"Отчет периода создан: {report_dir}"
            self.status_var.set(message)
            messagebox.showinfo("Отчет создан", f"Папка отчета:\n{report_dir}", parent=self.root)

    def open_period_html_report(self) -> None:
        period, report_dir = self._require_period_report_dir()
        if period is None or report_dir is None:
            return
        self.run_safely(
            lambda: actions.open_settlement_period_report(report_dir, "html"),
            "HTML-отчет периода открыт",
        )

    def open_period_xlsx_report(self) -> None:
        period, report_dir = self._require_period_report_dir()
        if period is None or report_dir is None:
            return
        self.run_safely(
            lambda: actions.open_settlement_period_report(report_dir, "xlsx"),
            "XLSX-отчет периода открыт",
        )

    def open_period_report_folder(self) -> None:
        period, report_dir = self._require_period_report_dir()
        if period is None or report_dir is None:
            return
        self.open_path(report_dir)

    def _show_period(self, period) -> None:
        transfers = (
            "\n".join(
                f"{item.from_participant} → {item.to_participant}: {item.amount:.2f}"
                for item in period.settlements
            )
            or "Переводов нет"
        )
        messagebox.showinfo(
            "Детали периода",
            f"ID: {period.id}\nНазвание: {period.name}\nСтатус: {period.status}\n"
            f"Даты: {period.date_from} — {period.date_to}\n"
            f"Покупок: {len(period.purchase_ids)}\nСумма: {period.total_amount:.2f}\n\n"
            f"Переводы:\n{transfers}",
            parent=self.root,
        )

    def show_period_details(self) -> None:
        period = self._selected_period()
        if period:
            self._show_period(period)

    def edit_period(self) -> None:
        period = self._selected_period()
        if not period:
            return
        allow_dates = actions.is_empty_period(period)
        dialog = PeriodMetadataDialog(self.root, period, allow_dates)
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        data = dialog.result
        result = self.run_safely(
            lambda: actions.edit_period_metadata(
                self.state,
                period.id,
                data.name,
                data.notes,
                data.date_from if allow_dates else None,
                data.date_to if allow_dates else None,
            ),
            "Период изменен",
        )
        if result:
            self.refresh_periods()

    def delete_empty_period(self) -> None:
        period = self._selected_period()
        if not period:
            return
        if not actions.is_empty_period(period):
            messagebox.showerror(
                "Удаление запрещено",
                "Период содержит покупки или переводы. Для сохранения истории его нельзя удалить. "
                "Используйте переоткрытие периода или отчет периода.",
                parent=self.root,
            )
            return
        confirm = simpledialog.askstring(
            "Typed confirm",
            f"Введите {actions.DELETE_EMPTY_PERIOD_CONFIRM}:",
            parent=self.root,
        )
        result = self.run_safely(
            lambda: actions.delete_empty_period(self.state, period.id, confirm or ""),
            "Пустой период удален",
        )
        if result:
            self.refresh_periods()

    def delete_all_empty_periods(self) -> None:
        periods = [
            period
            for period in actions.settlement_periods(self.state)
            if actions.is_empty_period(period)
        ]
        if not periods:
            messagebox.showinfo("Пустые периоды", "Пустых тестовых периодов нет.", parent=self.root)
            return
        names = "\n".join(f"{period.id} — {period.name}" for period in periods)
        if not messagebox.askyesno(
            "Удалить пустые периоды",
            f"Будут удалены только пустые периоды:\n\n{names}\n\nПродолжить?",
            parent=self.root,
        ):
            return
        confirm = simpledialog.askstring(
            "Typed confirm",
            f"Введите {actions.DELETE_EMPTY_PERIODS_CONFIRM}:",
            parent=self.root,
        )
        deleted = self.run_safely(
            lambda: actions.delete_all_empty_periods(self.state, confirm or ""),
            "Пустые периоды удалены",
        )
        if deleted is not None:
            self.refresh_periods()

    def reopen_period(self) -> None:
        period = self._selected_period()
        if not period:
            return
        if not messagebox.askyesno(
            "Переоткрыть период",
            "Покупки периода снова войдут в текущие расчёты. Продолжить?",
            parent=self.root,
        ):
            return
        result = self.run_safely(
            lambda: actions.reopen_period(self.state, period.id),
            "Период переоткрыт",
        )
        if result:
            self.refresh_all()

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
        suggestion = self.run_safely(lambda: actions.suggest_close_period(self.state))
        suggested = None
        if suggestion is not None:
            suggested = PeriodInput(
                suggestion.date_from.isoformat(),
                suggestion.date_to.isoformat(),
                suggestion.name,
            )
        dialog = ClosePeriodDialog(self.root, suggested)
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
                f"Участников: {len(preview.balances)}\n"
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
        if preview.purchase_count == 0:
            messagebox.showwarning(
                "Пустой период",
                "Период без покупок не создается обычным close flow. "
                "Скорректируйте даты или используйте отдельный advanced-flow.",
                parent=self.root,
            )
            self.status_var.set("Закрытие пустого периода отменено")
            return
        if not messagebox.askyesno(
            "Подтверждение",
            f"{SETTLEMENT_WARNING}\n\n"
            f"Покупок: {preview.purchase_count}\n"
            f"Сумма: {preview.total_amount:.2f}\n"
            f"Участников: {len(preview.balances)}\n"
            f"Переводов: {len(preview.settlements)}\n\n"
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
            self.last_report_status_var.set(
                f"Последний отчёт: {report_dir} ({self.analytics_format_var.get()})"
            )
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
            lambda: actions.open_report(self.last_analytics_report_dir, "html"), "HTML-отчёт открыт"
        )

    def open_xlsx_report(self) -> None:
        if self.last_analytics_report_dir is None:
            messagebox.showerror(
                "XLSX не найден",
                "Сначала создайте отчёт в формате XLSX или all.",
                parent=self.root,
            )
            return
        self.run_safely(
            lambda: actions.open_report(self.last_analytics_report_dir, "xlsx"), "XLSX-отчёт открыт"
        )

    def open_markdown_report(self) -> None:
        if self.last_analytics_report_dir is None:
            messagebox.showerror("Markdown не найден", "Сначала создайте отчёт.", parent=self.root)
            return
        self.run_safely(
            lambda: actions.open_report(self.last_analytics_report_dir, "markdown"),
            "Markdown-отчёт открыт",
        )

    def open_report_folder(self) -> None:
        self.open_path(self.last_analytics_report_dir or self.state.analytics_dir)

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

    def create_backup(self) -> None:
        path = self.run_safely(lambda: actions.create_data_backup(self.state), "Backup создан")
        if path:
            messagebox.showinfo("Backup создан", f"Папка backup:\n{path}", parent=self.root)


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
        current_state_dir=Path(args.reports_dir) / "current_state",
    )
    state.ensure_data_files()
    root = tk.Tk()
    ExpenseSplitterGui(root, state)
    root.mainloop()


if __name__ == "__main__":
    main()
