from datetime import date, datetime
from decimal import Decimal

from typer.testing import CliRunner

from expense_splitter.cli import app
from expense_splitter.models import Group, Participant, Purchase, SettlementPeriod
from expense_splitter.settlement_periods import (
    DELETE_EMPTY_PERIOD_CONFIRM,
    DELETE_EMPTY_PERIODS_CONFIRM,
    close_settlement_period,
    filter_purchases_by_settlement_scope,
    preview_settlement_period,
    reopen_settlement_period,
)
from expense_splitter.storage import (
    initialize_data_files,
    load_purchases,
    load_settlement_periods,
    save_purchases,
    save_settlement_periods,
)

runner = CliRunner()


def make_purchase(
    purchase_id: str,
    purchase_date: date,
    amount: str,
    payer: str,
    participants: list[str],
) -> Purchase:
    return Purchase(
        id=purchase_id,
        date=purchase_date,
        amount=Decimal(amount),
        payer=payer,
        participants=participants,
        purchase_name=f"Purchase {purchase_id}",
    )


def test_legacy_purchases_without_settlement_fields_are_open(tmp_path):
    path = tmp_path / "purchases.yaml"
    path.write_text(
        """
purchases:
  - id: p1
    date: '2026-06-01'
    purchase_name: Coffee
    amount: '120.00'
    payer: Alice
    participants:
      - Alice
      - Bob
    category: Office
    comment: Legacy row
""".lstrip(),
        encoding="utf-8",
    )

    purchases = load_purchases(path)

    assert purchases[0].settled is False
    assert purchases[0].settlement_period_id is None


def test_preview_does_not_mutate_purchases():
    purchases = [
        make_purchase("p1", date(2026, 6, 1), "100.00", "Alice", ["Alice", "Bob"]),
        make_purchase("p2", date(2026, 6, 20), "50.00", "Bob", ["Alice", "Bob"]),
    ]

    preview = preview_settlement_period(
        purchases,
        ["Alice", "Bob"],
        date(2026, 6, 1),
        date(2026, 6, 19),
    )

    assert preview.purchase_count == 1
    assert preview.total_amount == Decimal("100.00")
    assert purchases[0].settled is False
    assert purchases[0].settlement_period_id is None


def test_close_marks_selected_purchases_without_deleting_history():
    purchases = [
        make_purchase("p1", date(2026, 6, 1), "100.00", "Alice", ["Alice", "Bob"]),
        make_purchase("p2", date(2026, 6, 19), "60.00", "Bob", ["Alice", "Bob"]),
        make_purchase("p3", date(2026, 6, 20), "50.00", "Alice", ["Alice", "Bob"]),
    ]
    periods: list[SettlementPeriod] = []

    period = close_settlement_period(
        purchases,
        periods,
        ["Alice", "Bob"],
        date(2026, 6, 1),
        date(2026, 6, 19),
        "June before payday",
        closed_at=datetime(2026, 6, 19, 12, 0, 0),
    )

    assert period.id == "settlement_2026_06_19_001"
    assert period.purchase_ids == ["p1", "p2"]
    assert period.total_amount == Decimal("160.00")
    assert len(period.settlements) == 1
    assert len(purchases) == 3
    assert purchases[0].settled is True
    assert purchases[0].settlement_period_id == period.id
    assert purchases[2].settled is False


def test_scope_filters_open_all_and_specific_period():
    purchases = [
        make_purchase("p1", date(2026, 6, 1), "100.00", "Alice", ["Alice", "Bob"]),
        make_purchase("p2", date(2026, 6, 20), "50.00", "Alice", ["Alice", "Bob"]),
    ]
    periods: list[SettlementPeriod] = []
    period = close_settlement_period(
        purchases,
        periods,
        ["Alice", "Bob"],
        date(2026, 6, 1),
        date(2026, 6, 1),
        "One day",
    )

    assert [p.id for p in filter_purchases_by_settlement_scope(purchases, "open")] == ["p2"]
    assert [p.id for p in filter_purchases_by_settlement_scope(purchases, "all")] == [
        "p1",
        "p2",
    ]
    assert [
        p.id
        for p in filter_purchases_by_settlement_scope(
            purchases,
            settlement_period_id=period.id,
        )
    ] == ["p1"]


def test_reopen_returns_period_purchases_to_open_scope():
    purchases = [make_purchase("p1", date(2026, 6, 1), "100.00", "Alice", ["Alice", "Bob"])]
    periods: list[SettlementPeriod] = []
    period = close_settlement_period(
        purchases,
        periods,
        ["Alice", "Bob"],
        date(2026, 6, 1),
        date(2026, 6, 1),
        "One day",
    )

    reopened = reopen_settlement_period(
        purchases,
        periods,
        period.id,
        reopened_at=datetime(2026, 6, 20, 9, 0, 0),
    )

    assert reopened.status == "reopened"
    assert reopened.reopened_at == datetime(2026, 6, 20, 9, 0, 0)
    assert purchases[0].settled is False
    assert purchases[0].settlement_period_id is None


def test_settlement_period_storage_round_trip(tmp_path):
    purchases = [make_purchase("p1", date(2026, 6, 1), "100.00", "Alice", ["Alice", "Bob"])]
    periods: list[SettlementPeriod] = []
    period = close_settlement_period(
        purchases,
        periods,
        ["Alice", "Bob"],
        date(2026, 6, 1),
        date(2026, 6, 1),
        "One day",
        closed_at=datetime(2026, 6, 19, 12, 0, 0),
    )
    path = tmp_path / "settlement_periods.yaml"

    save_settlement_periods(path, periods)
    loaded = load_settlement_periods(path)

    assert loaded[0].id == period.id
    assert loaded[0].date_from == date(2026, 6, 1)
    assert loaded[0].closed_at == datetime(2026, 6, 19, 12, 0, 0)
    assert loaded[0].settlements[0].amount == Decimal("50.00")


def test_cli_close_list_show_reopen_and_scopes(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(
        data_dir,
        [Participant("Alice"), Participant("Bob")],
        [Group("All", ["Alice", "Bob"])],
    )
    save_purchases(
        data_dir / "purchases.yaml",
        [
            make_purchase("p1", date(2026, 6, 1), "100.00", "Alice", ["Alice", "Bob"]),
            make_purchase("p2", date(2026, 6, 20), "50.00", "Bob", ["Alice", "Bob"]),
        ],
    )

    preview = runner.invoke(
        app,
        [
            "settlement-period",
            "preview",
            "--from",
            "2026-06-01",
            "--to",
            "2026-06-19",
            "--data-dir",
            str(data_dir),
        ],
    )
    assert preview.exit_code == 0
    assert "Purchases: 1" in preview.stdout

    close = runner.invoke(
        app,
        [
            "settlement-period",
            "close",
            "--from",
            "2026-06-01",
            "--to",
            "2026-06-19",
            "--name",
            "June before payday",
            "--confirm",
            "CLOSE_PERIOD",
            "--data-dir",
            str(data_dir),
        ],
    )
    assert close.exit_code == 0
    assert "settlement_2026_06_19_001" in close.stdout

    purchases = load_purchases(data_dir / "purchases.yaml")
    assert [purchase.id for purchase in filter_purchases_by_settlement_scope(purchases)] == ["p2"]

    list_result = runner.invoke(
        app,
        ["settlement-period", "list", "--data-dir", str(data_dir)],
    )
    assert list_result.exit_code == 0
    assert "June" in list_result.stdout
    assert "payday" in list_result.stdout

    show_result = runner.invoke(
        app,
        [
            "settlement-period",
            "show",
            "settlement_2026_06_19_001",
            "--data-dir",
            str(data_dir),
        ],
    )
    assert show_result.exit_code == 0
    assert "Total amount: 100.00" in show_result.stdout

    open_balances = runner.invoke(app, ["balances", "--data-dir", str(data_dir)])
    all_balances = runner.invoke(
        app,
        ["balances", "--scope", "all", "--data-dir", str(data_dir)],
    )
    period_balances = runner.invoke(
        app,
        [
            "balances",
            "--settlement-period",
            "settlement_2026_06_19_001",
            "--data-dir",
            str(data_dir),
        ],
    )
    assert open_balances.exit_code == 0
    assert all_balances.exit_code == 0
    assert period_balances.exit_code == 0

    reopen = runner.invoke(
        app,
        [
            "settlement-period",
            "reopen",
            "settlement_2026_06_19_001",
            "--confirm",
            "REOPEN_PERIOD",
            "--data-dir",
            str(data_dir),
        ],
    )
    assert reopen.exit_code == 0
    purchases = load_purchases(data_dir / "purchases.yaml")
    assert all(not purchase.settled for purchase in purchases)


def test_cli_suggest_rename_and_delete_empty_periods(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(
        data_dir,
        [Participant("Alice"), Participant("Bob")],
        [Group("All", ["Alice", "Bob"])],
    )
    save_purchases(
        data_dir / "purchases.yaml",
        [make_purchase("p1", date(2026, 6, 1), "100.00", "Alice", ["Alice", "Bob"])],
    )
    empty_period = SettlementPeriod(
        id="empty",
        name="Empty",
        status="closed",
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 1),
        closed_at=datetime(2026, 6, 1, 12, 0, 0),
        purchase_ids=[],
        total_amount=Decimal("0.00"),
        settlements=[],
    )
    keep_period = SettlementPeriod(
        id="keep",
        name="Keep",
        status="closed",
        date_from=date(2026, 6, 2),
        date_to=date(2026, 6, 2),
        closed_at=datetime(2026, 6, 2, 12, 0, 0),
        purchase_ids=["p1"],
        total_amount=Decimal("100.00"),
        settlements=[],
    )
    save_settlement_periods(data_dir / "settlement_periods.yaml", [empty_period, keep_period])

    suggest = runner.invoke(app, ["settlement-period", "suggest", "--data-dir", str(data_dir)])
    assert suggest.exit_code == 0
    assert "2026-06-03" in suggest.stdout

    rename = runner.invoke(
        app,
        [
            "settlement-period",
            "rename",
            "keep",
            "--name",
            "Renamed",
            "--notes",
            "safe metadata",
            "--data-dir",
            str(data_dir),
        ],
    )
    assert rename.exit_code == 0
    periods = load_settlement_periods(data_dir / "settlement_periods.yaml")
    assert next(period for period in periods if period.id == "keep").name == "Renamed"

    blocked = runner.invoke(
        app,
        [
            "settlement-period",
            "delete-empty",
            "keep",
            "--confirm",
            DELETE_EMPTY_PERIOD_CONFIRM,
            "--data-dir",
            str(data_dir),
        ],
    )
    assert blocked.exit_code != 0
    assert "нельзя удалить" in blocked.stdout

    deleted = runner.invoke(
        app,
        [
            "settlement-period",
            "delete-empty",
            "empty",
            "--confirm",
            DELETE_EMPTY_PERIOD_CONFIRM,
            "--data-dir",
            str(data_dir),
        ],
    )
    assert deleted.exit_code == 0
    periods = load_settlement_periods(data_dir / "settlement_periods.yaml")
    assert [period.id for period in periods] == ["keep"]

    delete_all = runner.invoke(
        app,
        [
            "settlement-period",
            "delete-empty-all",
            "--confirm",
            DELETE_EMPTY_PERIODS_CONFIRM,
            "--data-dir",
            str(data_dir),
        ],
    )
    assert delete_all.exit_code == 0
    assert "0" in delete_all.stdout
