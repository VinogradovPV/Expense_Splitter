import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from datetime import date
from decimal import Decimal
import uuid

from expense_splitter.models import Purchase
from expense_splitter.storage import (
    load_participants, save_participants,
    load_groups, save_groups,
    load_purchases, save_purchases,
    initialize_data_files,
    StorageError
)
from expense_splitter.defaults import DEFAULT_PARTICIPANTS, DEFAULT_GROUPS, EXAMPLE_PURCHASES
from expense_splitter.calculator import calculate_balances
from expense_splitter.settlement import calculate_settlements
from expense_splitter.reporting import generate_markdown_report

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
    with_examples: bool = typer.Option(False, "--with-examples", help="Include example purchases.")
):
    """Initialize data files with default participants and groups."""
    try:
        initialize_data_files(data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)
        if with_examples:
            purchases = load_purchases(data_dir / 'purchases.yaml')
            if not purchases:
                save_purchases(data_dir / 'purchases.yaml', EXAMPLE_PURCHASES)
                console.print(f"[green]Initialized data in {data_dir} with examples.[/green]")
            else:
                console.print(f"[yellow]Purchases already exist in {data_dir}. Examples not added.[/yellow]")
        else:
            console.print(f"[green]Initialized data in {data_dir}.[/green]")
    except StorageError as error:
        handle_storage_error(error)


@app.command()
def add_purchase(
    title: str = typer.Argument(..., help="Title of the purchase"),
    amount: str = typer.Argument(..., help="Amount of the purchase"),
    payer: str = typer.Argument(..., help="Name of the participant who paid"),
    group: str = typer.Option(None, "--group", "-g", help="Name of the group to split the expense among"),
    participants: str = typer.Option(None, "--participants", "-p", help="Comma-separated list of participants"),
    date_str: str = typer.Option(None, "--date", "-d", help="Date in YYYY-MM-DD format (defaults to today)"),
    category: str = typer.Option(None, "--category", "-c", help="Category of the purchase"),
    comment: str = typer.Option(None, "--comment", help="Optional comment"),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory")
):
    """Add a new purchase."""
    try:
        participants_list = load_participants(data_dir / 'participants.yaml')
        all_participant_names = [p.name for p in participants_list]

        if not all_participant_names:
            all_participant_names = [p.name for p in DEFAULT_PARTICIPANTS]

        if payer not in all_participant_names:
            console.print(f"[red]Error: Payer '{payer}' not found in participants.[/red]")
            raise typer.Exit(1)

        target_participants = []
        if group:
            groups = load_groups(data_dir / 'participants.yaml')
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
                console.print(f"[red]Error: Participant '{p}' not found in global participants list.[/red]")
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
            title=title,
            amount=purchase_amount,
            payer=payer,
            participants=target_participants,
            category=category,
            comment=comment
        )

        purchases = load_purchases(data_dir / 'purchases.yaml')
        purchases.append(new_purchase)
        save_purchases(data_dir / 'purchases.yaml', purchases)
        console.print(f"[green]Added purchase: {title} ({amount}) paid by {payer}.[/green]")
    except StorageError as error:
        handle_storage_error(error)


@app.command()
def list_purchases(data_dir: Path = typer.Option(DATA_DIR, help="Data directory")):
    """List all recorded purchases."""
    try:
        purchases = load_purchases(data_dir / 'purchases.yaml')
    except StorageError as error:
        handle_storage_error(error)

    if not purchases:
        console.print("No purchases recorded.")
        return

    table = Table("ID", "Date", "Title", "Amount", "Payer", "Participants")
    for p in sorted(purchases, key=lambda x: x.date or date.min):
        date_str = p.date.isoformat() if p.date else "N/A"
        table.add_row(p.id, date_str, p.title, f"{p.amount:.2f}", p.payer, ", ".join(p.participants))
    console.print(table)


@app.command()
def balances(data_dir: Path = typer.Option(DATA_DIR, help="Data directory")):
    """Show current balances for all participants."""
    try:
        participants = load_participants(data_dir / 'participants.yaml')
        purchases = load_purchases(data_dir / 'purchases.yaml')
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
        table.add_row(b.participant, f"{b.paid:.2f}", f"{b.share:.2f}", f"[{color}]{b.net:.2f}[/{color}]")
    console.print(table)


@app.command()
def settle(data_dir: Path = typer.Option(DATA_DIR, help="Data directory")):
    """Show minimum transfers required to settle all debts."""
    try:
        participants = load_participants(data_dir / 'participants.yaml')
        purchases = load_purchases(data_dir / 'purchases.yaml')
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
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory")
):
    """Generate a detailed Markdown report."""
    try:
        participants = load_participants(data_dir / 'participants.yaml')
        purchases = load_purchases(data_dir / 'purchases.yaml')
    except StorageError as error:
        handle_storage_error(error)

    all_names = [p.name for p in participants]
    
    if not all_names:
        all_names = [p.name for p in DEFAULT_PARTICIPANTS]
    
    bals = calculate_balances(purchases, all_names)
    settlements = calculate_settlements(bals)
    
    generate_markdown_report(purchases, bals, settlements, output)
    console.print(f"[green]Report generated at {output}[/green]")


if __name__ == "__main__":
    app()
