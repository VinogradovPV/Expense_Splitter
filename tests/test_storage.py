from decimal import Decimal

import pytest
import yaml

from expense_splitter.defaults import DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.models import Group, Participant, Purchase
from expense_splitter.storage import (
    StorageError,
    initialize_data_files,
    load_groups,
    load_participants,
    load_purchases,
    save_groups,
    save_participants,
    save_purchases,
)


def test_initialize_data_files_keeps_participants_and_groups(tmp_path):
    data_dir = tmp_path / "data"

    initialize_data_files(data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)

    participants_path = data_dir / "participants.yaml"
    purchases_path = data_dir / "purchases.yaml"
    settlement_periods_path = data_dir / "settlement_periods.yaml"

    assert participants_path.exists()
    assert purchases_path.exists()
    assert settlement_periods_path.exists()

    participants = load_participants(participants_path)
    groups = load_groups(participants_path)
    purchases = load_purchases(purchases_path)

    assert [p.name for p in participants] == [p.name for p in DEFAULT_PARTICIPANTS]
    assert [g.name for g in groups] == [g.name for g in DEFAULT_GROUPS]
    assert purchases == []

    raw_participants = yaml.safe_load(participants_path.read_text(encoding="utf-8"))
    raw_purchases = yaml.safe_load(purchases_path.read_text(encoding="utf-8"))
    raw_settlement_periods = yaml.safe_load(
        settlement_periods_path.read_text(encoding="utf-8")
    )
    assert set(raw_participants) == {"participants", "groups"}
    assert raw_purchases == {"schema_version": 1, "purchases": []}
    assert raw_settlement_periods == {"schema_version": 1, "settlement_periods": []}


def test_save_participants_preserves_existing_groups(tmp_path):
    file_path = tmp_path / "participants.yaml"
    groups = [Group(name="Team", members=["Alice", "Bob"])]

    save_groups(file_path, groups)
    save_participants(file_path, [Participant(name="Alice"), Participant(name="Bob")])

    assert [p.name for p in load_participants(file_path)] == ["Alice", "Bob"]
    assert load_groups(file_path) == groups


def test_save_groups_preserves_existing_participants(tmp_path):
    file_path = tmp_path / "participants.yaml"
    participants = [Participant(name="Alice"), Participant(name="Bob")]

    save_participants(file_path, participants)
    save_groups(file_path, [Group(name="Team", members=["Alice", "Bob"])])

    assert load_participants(file_path) == participants
    assert [g.name for g in load_groups(file_path)] == ["Team"]


def test_initialize_data_files_does_not_overwrite_existing_data(tmp_path):
    data_dir = tmp_path / "data"
    participants_path = data_dir / "participants.yaml"
    purchases_path = data_dir / "purchases.yaml"
    custom_participants = [Participant(name="Alice")]
    custom_groups = [Group(name="Custom", members=["Alice"])]
    custom_purchase = Purchase(
        id="p1",
        date=None,
        amount=Decimal("10.00"),
        payer="Alice",
        participants=["Alice"],
        purchase_name="Tea",
        category=None,
        comment=None,
    )

    save_participants(participants_path, custom_participants)
    save_groups(participants_path, custom_groups)
    save_purchases(purchases_path, [custom_purchase])

    initialize_data_files(data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)

    assert load_participants(participants_path) == custom_participants
    assert load_groups(participants_path) == custom_groups
    assert load_purchases(purchases_path) == [custom_purchase]


def test_save_creates_timestamped_backup_before_replacing_yaml(tmp_path):
    file_path = tmp_path / "participants.yaml"
    save_participants(file_path, [Participant(name="Alice")])

    save_participants(file_path, [Participant(name="Bob")])

    backups = list(tmp_path.glob("participants.yaml.*.bak"))
    assert len(backups) == 1
    assert load_participants(backups[0]) == [Participant(name="Alice")]
    assert load_participants(file_path) == [Participant(name="Bob")]


def test_atomic_write_keeps_original_file_when_replace_fails(tmp_path, monkeypatch):
    file_path = tmp_path / "participants.yaml"
    save_participants(file_path, [Participant(name="Alice")])

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr("expense_splitter.storage.os.replace", fail_replace)

    with pytest.raises(StorageError, match="Cannot write"):
        save_participants(file_path, [Participant(name="Bob")])

    assert load_participants(file_path) == [Participant(name="Alice")]
    assert not list(tmp_path.glob(".participants.yaml.*.tmp"))


def test_load_corrupted_yaml_raises_storage_error_with_path(tmp_path):
    file_path = tmp_path / "purchases.yaml"
    file_path.write_text("purchases: [\n", encoding="utf-8")

    with pytest.raises(StorageError) as exc_info:
        load_purchases(file_path)

    assert exc_info.value.file_path == file_path
    assert "Invalid YAML" in str(exc_info.value)


def test_load_purchases_maps_legacy_title_to_purchase_name(tmp_path):
    file_path = tmp_path / "purchases.yaml"
    file_path.write_text(
        yaml.safe_dump(
            {
                "purchases": [
                    {
                        "id": "p1",
                        "date": "2026-06-18",
                        "title": "Legacy title",
                        "amount": "10.00",
                        "payer": "Alice",
                        "participants": ["Alice"],
                        "category": None,
                        "comment": None,
                    }
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    purchase = load_purchases(file_path)[0]

    assert purchase.purchase_name == "Legacy title"
    assert purchase.title == "Legacy title"


def test_load_purchases_defaults_missing_purchase_name(tmp_path):
    file_path = tmp_path / "purchases.yaml"
    file_path.write_text(
        yaml.safe_dump(
            {
                "purchases": [
                    {
                        "id": "p1",
                        "date": None,
                        "amount": "10.00",
                        "payer": "Alice",
                        "participants": ["Alice"],
                        "category": None,
                        "comment": None,
                    }
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    purchase = load_purchases(file_path)[0]

    assert purchase.purchase_name == "н/д"


def test_save_purchases_writes_purchase_name_without_legacy_title(tmp_path):
    file_path = tmp_path / "purchases.yaml"
    purchase = Purchase(
        id="p1",
        date=None,
        amount=Decimal("10.00"),
        payer="Alice",
        participants=["Alice"],
        purchase_name="Tea",
        category=None,
        comment=None,
    )

    save_purchases(file_path, [purchase])

    raw = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    saved_purchase = raw["purchases"][0]
    assert saved_purchase["purchase_name"] == "Tea"
    assert "title" not in saved_purchase
