import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.calculator import calculate_balances
from expense_splitter.defaults import DEFAULT_GROUPS, DEFAULT_PARTICIPANTS, EXAMPLE_PURCHASES
from expense_splitter.models import DEFAULT_PURCHASE_NAME, Purchase
from expense_splitter.reporting import generate_markdown_report
from expense_splitter.settlement import calculate_settlements
from expense_splitter.storage import (
    StorageError,
    initialize_data_files,
    load_groups,
    load_participants,
    load_purchases,
    save_purchases,
)

app = typer.Typer(help="Expense Splitter CLI")
console = Console()

# Default data directory
DATA_DIR = Path("data")


def get_data_dir() -> Path:
    return DATA_DIR


def handle_storage_error(error: StorageError):
    typer.echo(f"Data error in {error.file_path}: {error}")
    raise typer.Exit(1)


@app.command()
def init(
    data_dir: Path = typer.Option(DATA_DIR, help="Directory to initialize data files in."),
    with_examples: bool = typer.Option(False, "--with-examples", help="Include example purchases."),
):
    """Initialize data files with default participants and groups."""
    try:
        initialize_data_files(data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)
        if with_examples:
            purchases = load_purchases(data_dir / "purchases.yaml")
            if not purchases:
                save_purchases(data_dir / "purchases.yaml", EXAMPLE_PURCHASES)
                console.print(f"[green]Initialized data in {data_dir} with examples.[/green]")
            else:
                console.print(
                    f"[yellow]Purchases already exist in {data_dir}. Examples not added.[/yellow]"
                )
        else:
            console.print(f"[green]Initialized data in {data_dir}.[/green]")
    except StorageError as error:
        handle_storage_error(error)


@app.command()
def add_purchase(
    purchase_name: str = typer.Argument(..., help="Наименование покупки"),
    amount: str = typer.Argument(..., help="Amount of the purchase"),
    payer: str = typer.Argument(..., help="Name of the participant who paid"),
    group: str = typer.Option(
        None, "--group", "-g", help="Name of the group to split the expense among"
    ),
    participants: str = typer.Option(
        None, "--participants", "-p", help="Comma-separated list of participants"
    ),
    date_str: str = typer.Option(
        None, "--date", "-d", help="Date in YYYY-MM-DD format (defaults to today)"
    ),
    category: str = typer.Option(None, "--category", "-c", help="Category of the purchase"),
    comment: str = typer.Option(None, "--comment", help="Optional comment"),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory"),
):
    """Add a new purchase."""
    try:
        purchase_name = purchase_name.strip() or DEFAULT_PURCHASE_NAME
        participants_list = load_participants(data_dir / "participants.yaml")
        all_participant_names = [p.name for p in participants_list]

        if not all_participant_names:
            all_participant_names = [p.name for p in DEFAULT_PARTICIPANTS]

        if payer not in all_participant_names:
            console.print(f"[red]Error: Payer '{payer}' not found in participants.[/red]")
            raise typer.Exit(1)

        target_participants = []
        if group:
            groups = load_groups(data_dir / "participants.yaml")
            target_group = next((g for g in groups if g.name == group), None)
            if not target_group:
                console.print(f"[red]Error: Group '{group}' not found.[/red]")
                raise typer.Exit(1)
            target_participants = target_group.members
        elif participants:
            target_participants = [p.strip() for p in participants.split(",")]
        else:
            console.print("[red]Error: Must specify either --group or --participants.[/red]")
            raise typer.Exit(1)

        for p in target_participants:
            if p not in all_participant_names:
                console.print(
                    f"[red]Error: Participant '{p}' not found in global participants list.[/red]"
                )
                raise typer.Exit(1)

        purchase_date = date.fromisoformat(date_str) if date_str else date.today()
        try:
            purchase_amount = Decimal(amount)
        except Exception:
            console.print("[red]Error: Invalid amount format.[/red]")
            raise typer.Exit(1)

        new_purchase = Purchase(
            id=str(uuid.uuid4())[:8],
            date=purchase_date,
            amount=purchase_amount,
            payer=payer,
            participants=target_participants,
            purchase_name=purchase_name,
            category=category,
            comment=comment,
        )

        purchases = load_purchases(data_dir / "purchases.yaml")
        purchases.append(new_purchase)
        save_purchases(data_dir / "purchases.yaml", purchases)
        console.print(f"[green]Added purchase: {purchase_name} ({amount}) paid by {payer}.[/green]")
    except StorageError as error:
        handle_storage_error(error)


@app.command()
def list_purchases(data_dir: Path = typer.Option(DATA_DIR, help="Data directory")):
    """List all recorded purchases."""
    try:
        purchases = load_purchases(data_dir / "purchases.yaml")
    except StorageError as error:
        handle_storage_error(error)

    if not purchases:
        console.print("No purchases recorded.")
        return

    table = Table("ID", "Date", "Наименование покупки", "Amount", "Payer", "Participants")
    for p in sorted(purchases, key=lambda x: x.date or date.min):
        date_str = p.date.isoformat() if p.date else "N/A"
        table.add_row(
            p.id, date_str, p.purchase_name, f"{p.amount:.2f}", p.payer, ", ".join(p.participants)
        )
    console.print(table)


@app.command()
def balances(data_dir: Path = typer.Option(DATA_DIR, help="Data directory")):
    """Show current balances for all participants."""
    try:
        participants = load_participants(data_dir / "participants.yaml")
        purchases = load_purchases(data_dir / "purchases.yaml")
    except StorageError as error:
        handle_storage_error(error)

    all_names = [p.name for p in participants]

    # Handle the case where participants list might be empty or missing from YAML properly in tests
    if not all_names:
        all_names = [p.name for p in DEFAULT_PARTICIPANTS]

    bals = calculate_balances(purchases, all_names)

    table = Table("Participant", "Paid", "Share", "Net Balance")
    for b in sorted(bals, key=lambda x: x.participant):
        color = "green" if b.net > 0 else "red" if b.net < 0 else "white"
        table.add_row(
            b.participant, f"{b.paid:.2f}", f"{b.share:.2f}", f"[{color}]{b.net:.2f}[/{color}]"
        )
    console.print(table)


@app.command()
def settle(data_dir: Path = typer.Option(DATA_DIR, help="Data directory")):
    """Show minimum transfers required to settle all debts."""
    try:
        participants = load_participants(data_dir / "participants.yaml")
        purchases = load_purchases(data_dir / "purchases.yaml")
    except StorageError as error:
        handle_storage_error(error)

    all_names = [p.name for p in participants]

    if not all_names:
        all_names = [p.name for p in DEFAULT_PARTICIPANTS]

    bals = calculate_balances(purchases, all_names)
    settlements = calculate_settlements(bals)

    if not settlements:
        console.print("[green]All balances are settled. No transfers required.[/green]")
        return

    table = Table("From", "To", "Amount")
    for s in settlements:
        table.add_row(s.from_participant, s.to_participant, f"{s.amount:.2f}")
    console.print(table)


@app.command()
def report(
    output: Path = typer.Option(Path("reports/report.md"), help="Path to output Markdown report"),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory"),
):
    """Generate a detailed Markdown report."""
    try:
        participants = load_participants(data_dir / "participants.yaml")
        purchases = load_purchases(data_dir / "purchases.yaml")
    except StorageError as error:
        handle_storage_error(error)

    all_names = [p.name for p in participants]

    if not all_names:
        all_names = [p.name for p in DEFAULT_PARTICIPANTS]

    bals = calculate_balances(purchases, all_names)
    settlements = calculate_settlements(bals)

    generate_markdown_report(purchases, bals, settlements, output)
    console.print(f"[green]Report generated at {output}[/green]")


@app.command("analytics")
def analytics_command(
    period: str = typer.Option(..., "--period", help="Period type: month, quarter, year"),
    year: int = typer.Option(..., "--year", help="Analytics year"),
    month: int = typer.Option(None, "--month", help="Month number for month period"),
    quarter: int = typer.Option(None, "--quarter", help="Quarter number for quarter period"),
    output_format: str = typer.Option("all", "--format", help="Output: markdown, csv, png, all"),
    output_root: Path = typer.Option(
        Path("reports/analytics"), "--output-root", help="Analytics reports root"
    ),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory"),
):
    """Generate period analytics tables and charts."""
    try:
        period_spec = parse_period(period, year, month=month, quarter=quarter)
        participants = load_participants(data_dir / "participants.yaml")
        groups = load_groups(data_dir / "participants.yaml")
        purchases = load_purchases(data_dir / "purchases.yaml")
        if not participants:
            participants = DEFAULT_PARTICIPANTS
        dataset = build_analytics_dataset(participants, groups, purchases, period_spec)
        report_dir = generate_analytics_report(dataset, output_root, output_format)
    except StorageError as error:
        handle_storage_error(error)
    except ValueError as error:
        typer.echo(f"Analytics error: {error}")
        raise typer.Exit(2) from error

    console.print(f"[green]Analytics report generated at {report_dir}[/green]")


if __name__ == "__main__":
    app()
