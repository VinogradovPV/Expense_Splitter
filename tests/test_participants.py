from datetime import date, datetime
from decimal import Decimal

import pytest

from expense_splitter.directories import (
    add_participant,
    archive_participant,
    delete_participant,
    list_participant_rows,
    rename_participant,
)
from expense_splitter.models import Group, Participant, Purchase, Settlement, SettlementPeriod
from expense_splitter.storage import (
    initialize_data_files,
    load_groups,
    load_participants,
    load_purchases,
    load_settlement_periods,
    save_groups,
    save_participants,
    save_purchases,
    save_settlement_periods,
)


def prepare_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [], [])
    return data_dir


def test_add_participant_trims_and_rejects_case_insensitive_duplicates(tmp_path):
    data_dir = prepare_data_dir(tmp_path)
    add_participant(data_dir, " Alice ")

    assert load_participants(data_dir / "participants.yaml") == [Participant("Alice")]
    with pytest.raises(ValueError, match="уже существует"):
        add_participant(data_dir, "alice")
    with pytest.raises(ValueError, match="не может быть пустым"):
        add_participant(data_dir, " ")


def test_rename_participant_cascades_to_groups_purchases_and_period_settlements(tmp_path):
    data_dir = prepare_data_dir(tmp_path)
    save_participants(data_dir / "participants.yaml", [Participant("Alice"), Participant("Bob")])
    save_groups(data_dir / "participants.yaml", [Group("Team", ["Alice", "Bob"])])
    save_purchases(
        data_dir / "purchases.yaml",
        [
            Purchase(
                id="p1",
                date=date(2026, 6, 25),
                amount=Decimal("90.00"),
                payer="Alice",
                participants=["Alice", "Bob"],
                purchase_name="Lunch",
            )
        ],
    )
    save_settlement_periods(
        data_dir / "settlement_periods.yaml",
        [
            SettlementPeriod(
                id="period-1",
                name="Period",
                status="closed",
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
                closed_at=datetime(2026, 6, 30, 12, 0, 0),
                purchase_ids=["p1"],
                total_amount=Decimal("90.00"),
                settlements=[Settlement("Bob", "Alice", Decimal("45.00"))],
            )
        ],
    )

    rename_participant(data_dir, "Alice", "Alicia")

    participant_names = [
        participant.name for participant in load_participants(data_dir / "participants.yaml")
    ]
    assert participant_names == [
        "Alicia",
        "Bob",
    ]
    assert load_groups(data_dir / "participants.yaml")[0].members == ["Alicia", "Bob"]
    purchase = load_purchases(data_dir / "purchases.yaml")[0]
    assert purchase.payer == "Alicia"
    assert purchase.participants == ["Alicia", "Bob"]
    settlement = load_settlement_periods(data_dir / "settlement_periods.yaml")[0].settlements[0]
    assert settlement.to_participant == "Alicia"
    assert list(data_dir.glob("participants.yaml.*.bak"))
    assert list(data_dir.glob("purchases.yaml.*.bak"))
    assert list(data_dir.glob("settlement_periods.yaml.*.bak"))


def test_delete_used_participant_is_blocked_but_unused_can_be_deleted(tmp_path):
    data_dir = prepare_data_dir(tmp_path)
    save_participants(
        data_dir / "participants.yaml",
        [Participant("Alice"), Participant("Bob"), Participant("Unused")],
    )
    save_purchases(
        data_dir / "purchases.yaml",
        [
            Purchase(
                id="p1",
                date=None,
                amount=Decimal("10.00"),
                payer="Alice",
                participants=["Alice", "Bob"],
                purchase_name="Tea",
            )
        ],
    )

    with pytest.raises(ValueError, match="используется"):
        delete_participant(data_dir, "Alice")

    deleted = delete_participant(data_dir, "Unused")

    assert deleted.name == "Unused"
    participant_names = [
        participant.name for participant in load_participants(data_dir / "participants.yaml")
    ]
    assert participant_names == [
        "Alice",
        "Bob",
    ]


def test_archive_participant_hides_from_active_load_but_keeps_directory_row(tmp_path):
    data_dir = prepare_data_dir(tmp_path)
    save_participants(data_dir / "participants.yaml", [Participant("Alice"), Participant("Bob")])

    archive_participant(data_dir, "Bob")

    assert [p.name for p in load_participants(data_dir / "participants.yaml", False)] == ["Alice"]
    rows = list_participant_rows(data_dir, include_archived=True)
    assert [(row.name, row.status) for row in rows] == [("Alice", "active"), ("Bob", "archived")]
