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
from expense_splitter.settlement_periods import (
    close_settlement_period,
    filter_purchases_by_settlement_scope,
    get_settlement_period,
    parse_period_date,
    preview_settlement_period,
    reopen_settlement_period,
)
from expense_splitter.storage import (
    StorageError,
    initialize_data_files,
    load_groups,
    load_participants,
    load_purchases,
    load_settlement_periods,
    save_purchases,
    save_settlement_periods,
)

app = typer.Typer(help="Expense Splitter CLI")
settlement_period_app = typer.Typer(help="Settlement period commands")
app.add_typer(settlement_period_app, name="settlement-period")
console = Console()

# Default data directory
DATA_DIR = Path("data")
SETTLEMENT_PERIODS_FILE = "settlement_periods.yaml"


def get_data_dir() -> Path:
    return DATA_DIR


def handle_storage_error(error: StorageError):
    typer.echo(f"Data error in {error.file_path}: {error}")
    raise typer.Exit(1)


def get_participant_names(data_dir: Path) -> list[str]:
    participants = load_participants(data_dir / "participants.yaml")
    all_names = [p.name for p in participants]
    return all_names or [p.name for p in DEFAULT_PARTICIPANTS]


def select_purchases_for_calculation(
    purchases: list[Purchase],
    scope: str,
    settlement_period_id: str | None,
) -> list[Purchase]:
    try:
        return filter_purchases_by_settlement_scope(
            purchases,
            scope=scope,  # type: ignore[arg-type]
            settlement_period_id=settlement_period_id,
        )
    except ValueError as error:
        typer.echo(str(error))
        raise typer.Exit(2) from error


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
def balances(
    scope: str = typer.Option("open", "--scope", help="Calculation scope: open or all"),
    settlement_period_id: str = typer.Option(
        None, "--settlement-period", help="Calculate only one closed settlement period"
    ),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory"),
):
    """Show current balances for all participants."""
    try:
        all_names = get_participant_names(data_dir)
        purchases = load_purchases(data_dir / "purchases.yaml")
    except StorageError as error:
        handle_storage_error(error)

    selected_purchases = select_purchases_for_calculation(purchases, scope, settlement_period_id)
    bals = calculate_balances(selected_purchases, all_names)

    table = Table("Participant", "Paid", "Share", "Net Balance")
    for b in sorted(bals, key=lambda x: x.participant):
        color = "green" if b.net > 0 else "red" if b.net < 0 else "white"
        table.add_row(
            b.participant, f"{b.paid:.2f}", f"{b.share:.2f}", f"[{color}]{b.net:.2f}[/{color}]"
        )
    console.print(table)


@app.command()
def settle(
    scope: str = typer.Option("open", "--scope", help="Calculation scope: open or all"),
    settlement_period_id: str = typer.Option(
        None, "--settlement-period", help="Calculate only one closed settlement period"
    ),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory"),
):
    """Show minimum transfers required to settle all debts."""
    try:
        all_names = get_participant_names(data_dir)
        purchases = load_purchases(data_dir / "purchases.yaml")
    except StorageError as error:
        handle_storage_error(error)

    selected_purchases = select_purchases_for_calculation(purchases, scope, settlement_period_id)
    bals = calculate_balances(selected_purchases, all_names)
    settlements = calculate_settlements(bals)

    if not settlements:
        console.print("[green]All balances are settled. No transfers required.[/green]")
        return

    table = Table("From", "To", "Amount")
    for s in settlements:
        table.add_row(s.from_participant, s.to_participant, f"{s.amount:.2f}")
    console.print(table)


@settlement_period_app.command("preview")
def settlement_period_preview(
    from_date: str = typer.Option(..., "--from", help="Start date in YYYY-MM-DD format"),
    to_date: str = typer.Option(..., "--to", help="End date in YYYY-MM-DD format"),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory"),
):
    """Preview settlement period close without changing data."""
    try:
        date_from = parse_period_date(from_date)
        date_to = parse_period_date(to_date)
        all_names = get_participant_names(data_dir)
        purchases = load_purchases(data_dir / "purchases.yaml")
        preview = preview_settlement_period(purchases, all_names, date_from, date_to)
    except StorageError as error:
        handle_storage_error(error)
    except ValueError as error:
        typer.echo(str(error))
        raise typer.Exit(2) from error

    console.print(
        f"[bold]Preview:[/bold] {preview.date_from.isoformat()}..{preview.date_to.isoformat()}"
    )
    console.print(f"Purchases: {preview.purchase_count}")
    console.print(f"Total amount: {preview.total_amount:.2f}")
    if not preview.settlements:
        console.print("[green]All selected purchases are already balanced.[/green]")
        return

    table = Table("From", "To", "Amount")
    for item in preview.settlements:
        table.add_row(item.from_participant, item.to_participant, f"{item.amount:.2f}")
    console.print(table)


@settlement_period_app.command("close")
def settlement_period_close(
    from_date: str = typer.Option(..., "--from", help="Start date in YYYY-MM-DD format"),
    to_date: str = typer.Option(..., "--to", help="End date in YYYY-MM-DD format"),
    name: str = typer.Option(..., "--name", help="Settlement period name"),
    confirm: str = typer.Option("", "--confirm", help="Must be CLOSE_PERIOD"),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory"),
):
    """Close open purchases in a date range without deleting them."""
    if confirm != "CLOSE_PERIOD":
        console.print("[red]Close aborted: pass --confirm CLOSE_PERIOD.[/red]")
        raise typer.Exit(2)
    try:
        date_from = parse_period_date(from_date)
        date_to = parse_period_date(to_date)
        all_names = get_participant_names(data_dir)
        purchases_path = data_dir / "purchases.yaml"
        periods_path = data_dir / SETTLEMENT_PERIODS_FILE
        purchases = load_purchases(purchases_path)
        periods = load_settlement_periods(periods_path)
        period = close_settlement_period(purchases, periods, all_names, date_from, date_to, name)
        save_purchases(purchases_path, purchases)
        save_settlement_periods(periods_path, periods)
    except StorageError as error:
        handle_storage_error(error)
    except ValueError as error:
        typer.echo(str(error))
        raise typer.Exit(2) from error

    console.print(
        f"[green]Closed settlement period {period.id}: "
        f"{len(period.purchase_ids)} purchases, {period.total_amount:.2f}.[/green]"
    )


@settlement_period_app.command("list")
def settlement_period_list(data_dir: Path = typer.Option(DATA_DIR, help="Data directory")):
    """List settlement periods."""
    try:
        periods = load_settlement_periods(data_dir / SETTLEMENT_PERIODS_FILE)
    except StorageError as error:
        handle_storage_error(error)

    if not periods:
        console.print("No settlement periods recorded.")
        return

    table = Table("ID", "Name", "Status", "From", "To", "Purchases", "Total")
    for period in sorted(periods, key=lambda item: (item.date_to, item.id), reverse=True):
        table.add_row(
            period.id,
            period.name,
            period.status,
            period.date_from.isoformat(),
            period.date_to.isoformat(),
            str(len(period.purchase_ids)),
            f"{period.total_amount:.2f}",
        )
    console.print(table)


@settlement_period_app.command("show")
def settlement_period_show(
    settlement_period_id: str = typer.Argument(..., help="Settlement period id"),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory"),
):
    """Show settlement period details and snapshot settlements."""
    try:
        periods = load_settlement_periods(data_dir / SETTLEMENT_PERIODS_FILE)
        period = get_settlement_period(periods, settlement_period_id)
    except StorageError as error:
        handle_storage_error(error)
    except ValueError as error:
        typer.echo(str(error))
        raise typer.Exit(2) from error

    console.print(f"[bold]{period.id}[/bold] - {period.name}")
    console.print(f"Status: {period.status}")
    console.print(f"Dates: {period.date_from.isoformat()}..{period.date_to.isoformat()}")
    console.print(f"Purchases: {len(period.purchase_ids)}")
    console.print(f"Total amount: {period.total_amount:.2f}")
    if period.reopened_at:
        console.print(f"Reopened at: {period.reopened_at.isoformat(timespec='seconds')}")

    if not period.settlements:
        console.print("[green]No transfers required.[/green]")
        return

    table = Table("From", "To", "Amount")
    for item in period.settlements:
        table.add_row(item.from_participant, item.to_participant, f"{item.amount:.2f}")
    console.print(table)


@settlement_period_app.command("reopen")
def settlement_period_reopen(
    settlement_period_id: str = typer.Argument(..., help="Settlement period id"),
    confirm: str = typer.Option("", "--confirm", help="Must be REOPEN_PERIOD"),
    data_dir: Path = typer.Option(DATA_DIR, help="Data directory"),
):
    """Reopen a closed settlement period and return its purchases to open scope."""
    if confirm != "REOPEN_PERIOD":
        console.print("[red]Reopen aborted: pass --confirm REOPEN_PERIOD.[/red]")
        raise typer.Exit(2)
    try:
        purchases_path = data_dir / "purchases.yaml"
        periods_path = data_dir / SETTLEMENT_PERIODS_FILE
        purchases = load_purchases(purchases_path)
        periods = load_settlement_periods(periods_path)
        period = reopen_settlement_period(purchases, periods, settlement_period_id)
        save_purchases(purchases_path, purchases)
        save_settlement_periods(periods_path, periods)
    except StorageError as error:
        handle_storage_error(error)
    except ValueError as error:
        typer.echo(str(error))
        raise typer.Exit(2) from error

    console.print(f"[green]Reopened settlement period {period.id}.[/green]")


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
    output_format: str = typer.Option(
        "all", "--format", help="Output: markdown, csv, png, html, all"
    ),
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
