from decimal import Decimal

import yaml

from expense_splitter.defaults import DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.models import Group, Participant, Purchase
from expense_splitter.storage import (
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

    assert participants_path.exists()
    assert purchases_path.exists()

    participants = load_participants(participants_path)
    groups = load_groups(participants_path)
    purchases = load_purchases(purchases_path)

    assert [p.name for p in participants] == [p.name for p in DEFAULT_PARTICIPANTS]
    assert [g.name for g in groups] == [g.name for g in DEFAULT_GROUPS]
    assert purchases == []

    raw_participants = yaml.safe_load(participants_path.read_text(encoding="utf-8"))
    raw_purchases = yaml.safe_load(purchases_path.read_text(encoding="utf-8"))
    assert set(raw_participants) == {"participants", "groups"}
    assert raw_purchases == {"purchases": []}


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
        title="Tea",
        amount=Decimal("10.00"),
        payer="Alice",
        participants=["Alice"],
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
