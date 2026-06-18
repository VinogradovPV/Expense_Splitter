import os
import platform
import subprocess
import sys
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.calculator import calculate_balances
from expense_splitter.cli import balances, list_purchases, settle
from expense_splitter.defaults import DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.models import DEFAULT_PURCHASE_NAME, Purchase
from expense_splitter.reporting import generate_markdown_report
from expense_splitter.settlement import calculate_settlements
from expense_splitter.storage import (
    initialize_data_files,
    load_groups,
    load_participants,
    load_purchases,
    save_purchases,
)

console = Console()
DATA_DIR = Path("data")


def open_folder(path: Path):
    """Open folder in OS file explorer."""
    path.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def get_participant_names():
    participants = load_participants(DATA_DIR / "participants.yaml")
    names = [p.name for p in participants]
    return names if names else [p.name for p in DEFAULT_PARTICIPANTS]


def get_group_names():
    groups = load_groups(DATA_DIR / "participants.yaml")
    return [g.name for g in groups]


def add_purchase_interactive():
    console.print("[bold cyan]Добавление новой покупки[/bold cyan]")

    purchase_name = Prompt.ask("Наименование покупки", default=DEFAULT_PURCHASE_NAME)
    purchase_name = purchase_name.strip() or DEFAULT_PURCHASE_NAME

    while True:
        amount_str = Prompt.ask("Сумма")
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                console.print("[red]Сумма должна быть больше нуля.[/red]")
                continue
            break
        except Exception:
            console.print("[red]Неверный формат суммы.[/red]")

    all_names = get_participant_names()

    while True:
        payer = Prompt.ask(f"Кто платил? (Доступно: {', '.join(all_names)})")
        if payer in all_names:
            break
        console.print(f"[red]Участник '{payer}' не найден.[/red]")

    groups = get_group_names()
    target_participants = []

    while not target_participants:
        choice = Prompt.ask(
            "Для кого покупка? (введите имя группы или список имен через запятую)", default="Все"
        )

        if choice in groups:
            loaded_groups = load_groups(DATA_DIR / "participants.yaml")
            group = next((g for g in loaded_groups if g.name == choice), None)
            if group:
                target_participants = group.members
        elif choice == "Все" or choice.lower() == "all":
            target_participants = all_names
        else:
            parts = [p.strip() for p in choice.split(",")]
            valid = True
            for p in parts:
                if p not in all_names:
                    console.print(f"[red]Участник '{p}' не найден.[/red]")
                    valid = False
                    break
            if valid:
                target_participants = parts

    date_str = Prompt.ask("Дата (YYYY-MM-DD)", default=date.today().isoformat())
    try:
        purchase_date = date.fromisoformat(date_str)
    except ValueError:
        console.print("[yellow]Неверный формат даты, используется сегодняшняя.[/yellow]")
        purchase_date = date.today()

    category = Prompt.ask("Категория", default="")
    comment = Prompt.ask("Комментарий", default="")

    new_purchase = Purchase(
        id=str(uuid.uuid4())[:8],
        date=purchase_date,
        amount=amount,
        payer=payer,
        participants=target_participants,
        purchase_name=purchase_name,
        category=category if category else None,
        comment=comment if comment else None,
    )

    purchases = load_purchases(DATA_DIR / "purchases.yaml")
    purchases.append(new_purchase)
    save_purchases(DATA_DIR / "purchases.yaml", purchases)

    console.print(
        f"\n[bold green]✓ Покупка '{purchase_name}' на сумму {amount} "
        "успешно добавлена![/bold green]"
    )


def generate_report_interactive():
    output_path = Path("reports/report.md")
    all_names = get_participant_names()
    purchases = load_purchases(DATA_DIR / "purchases.yaml")
    bals = calculate_balances(purchases, all_names)
    settlements = calculate_settlements(bals)

    generate_markdown_report(purchases, bals, settlements, output_path)
    console.print(f"[bold green]Отчет сгенерирован: {output_path}[/bold green]")
    if Confirm.ask("Открыть папку с отчетами?"):
        open_folder(Path("reports"))


def check_data_interactive():
    console.print("[cyan]Проверка данных...[/cyan]")
    try:
        get_participant_names()
        load_purchases(DATA_DIR / "purchases.yaml")
        console.print("[green]Данные загружаются без ошибок.[/green]")
    except Exception as e:
        console.print(f"[red]Ошибка при чтении данных: {e}[/red]")


def generate_analytics_interactive():
    period = Prompt.ask("Период", choices=["month", "quarter", "year"], default="month")
    year = int(Prompt.ask("Год", default=str(date.today().year)))
    month = None
    quarter = None
    if period == "month":
        month = int(Prompt.ask("Месяц", default=str(date.today().month)))
    elif period == "quarter":
        quarter = int(Prompt.ask("Квартал", choices=["1", "2", "3", "4"]))
    output_format = Prompt.ask(
        "Формат",
        choices=["markdown", "csv", "png", "all"],
        default="all",
    )

    try:
        period_spec = parse_period(period, year, month=month, quarter=quarter)
        participants = load_participants(DATA_DIR / "participants.yaml") or DEFAULT_PARTICIPANTS
        groups = load_groups(DATA_DIR / "participants.yaml")
        purchases = load_purchases(DATA_DIR / "purchases.yaml")
        dataset = build_analytics_dataset(participants, groups, purchases, period_spec)
        report_dir = generate_analytics_report(dataset, output_format=output_format)
    except Exception as error:
        console.print(f"[red]Ошибка аналитики: {error}[/red]")
        return

    console.print(f"[bold green]Аналитика создана: {report_dir}[/bold green]")


def show_help():
    console.print("Usage: expense-splitter-launcher [OPTIONS]")
    console.print("")
    console.print("Interactive launcher for Expense Splitter.")
    console.print("")
    console.print("Options:")
    console.print("  --help, -h    Show this message and exit.")


def main():
    if any(arg in {"--help", "-h"} for arg in sys.argv[1:]):
        show_help()
        return

    if not DATA_DIR.exists():
        initialize_data_files(DATA_DIR, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)
        console.print("[yellow]Созданы файлы данных по умолчанию.[/yellow]")

    while True:
        console.print("\n")
        console.print(
            Panel.fit(
                "[1] Добавить покупку\n"
                "[2] Показать покупки\n"
                "[3] Показать балансы\n"
                "[4] Показать итоговые переводы\n"
                "[5] Создать отчет\n"
                "[6] Открыть папку с данными\n"
                "[7] Открыть папку с отчетами\n"
                "[8] Проверить данные\n"
                "[9] Аналитика за период\n"
                "[10] Выход",
                title="Expense Splitter Launcher",
                border_style="cyan",
            )
        )

        choice = Prompt.ask(
            "Выберите действие", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        )

        console.print("\n")
        if choice == "1":
            add_purchase_interactive()
        elif choice == "2":
            list_purchases(data_dir=DATA_DIR)
        elif choice == "3":
            balances(data_dir=DATA_DIR)
        elif choice == "4":
            settle(data_dir=DATA_DIR)
        elif choice == "5":
            generate_report_interactive()
        elif choice == "6":
            open_folder(DATA_DIR)
        elif choice == "7":
            open_folder(Path("reports"))
        elif choice == "8":
            check_data_interactive()
        elif choice == "9":
            generate_analytics_interactive()
        elif choice == "10":
            console.print("[green]До свидания![/green]")
            sys.exit(0)


if __name__ == "__main__":
    main()
