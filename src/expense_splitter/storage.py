import os
import shutil
import tempfile
import yaml
from pathlib import Path
from typing import List, TypeVar
from decimal import Decimal
from datetime import date, datetime

from expense_splitter.models import Participant, Group, Purchase

T = TypeVar("T")


class StorageError(RuntimeError):
    """Raised when user data cannot be safely read or written."""

    def __init__(self, message: str, file_path: Path):
        super().__init__(message)
        self.file_path = file_path

class DecimalYamlRepresenter(yaml.YAMLObject):
    yaml_tag = u'!decimal'

    @classmethod
    def from_yaml(cls, constructor, node):
        return Decimal(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, str(data))

class DateYamlRepresenter(yaml.YAMLObject):
    yaml_tag = u'!date'

    @classmethod
    def from_yaml(cls, constructor, node):
        return date.fromisoformat(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.isoformat())

yaml.add_representer(Decimal, DecimalYamlRepresenter.to_yaml)
yaml.add_constructor(u'!decimal', DecimalYamlRepresenter.from_yaml)
yaml.add_representer(date, DateYamlRepresenter.to_yaml)
yaml.add_constructor(u'!date', DateYamlRepresenter.from_yaml)


def _load_yaml_data(file_path: Path) -> dict:
    if not file_path.exists():
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise StorageError(f"Invalid YAML in {file_path}: {exc}", file_path) from exc
    except OSError as exc:
        raise StorageError(f"Cannot read {file_path}: {exc}", file_path) from exc

    if not isinstance(data, dict):
        raise StorageError(f"Invalid YAML structure in {file_path}: expected a mapping.", file_path)
    return data


def _create_backup(file_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    backup_path = file_path.with_name(f"{file_path.name}.{timestamp}.bak")
    shutil.copy2(file_path, backup_path)
    return backup_path

def _save_yaml_data(file_path: Path, data: dict):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists():
        _create_backup(file_path)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            'w',
            encoding='utf-8',
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as f:
            temp_path = Path(f.name)
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, file_path)
    except OSError as exc:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise StorageError(f"Cannot write {file_path}: {exc}", file_path) from exc

def load_participants(file_path: Path) -> List[Participant]:
    data = _load_yaml_data(file_path)
    return [Participant(**p) for p in data.get('participants', [])]

def save_participants(file_path: Path, participants: List[Participant]):
    data = _load_yaml_data(file_path)
    data['participants'] = [p.__dict__ for p in participants]
    _save_yaml_data(file_path, data)

def load_groups(file_path: Path) -> List[Group]:
    data = _load_yaml_data(file_path)
    return [Group(**g) for g in data.get('groups', [])]

def save_groups(file_path: Path, groups: List[Group]):
    data = _load_yaml_data(file_path)
    data['groups'] = [g.__dict__ for g in groups]
    _save_yaml_data(file_path, data)

def load_purchases(file_path: Path) -> List[Purchase]:
    data = _load_yaml_data(file_path)
    purchases = []
    for p in data.get('purchases', []):
        # Convert amount to Decimal if it's not already
        if 'amount' in p and not isinstance(p['amount'], Decimal):
            p['amount'] = Decimal(str(p['amount']))
        # Convert date to date object if it's not already
        if 'date' in p and isinstance(p['date'], str):
            p['date'] = date.fromisoformat(p['date'])
        purchases.append(Purchase(**p))
    return purchases

def save_purchases(file_path: Path, purchases: List[Purchase]):
    data = {'purchases': []}
    for p in purchases:
        p_dict = p.__dict__.copy()
        # Convert Decimal to string for YAML serialization if not handled by representer
        if isinstance(p_dict.get('amount'), Decimal):
            p_dict['amount'] = str(p_dict['amount'])
        if isinstance(p_dict.get('date'), date):
            p_dict['date'] = p_dict['date'].isoformat()
        data['purchases'].append(p_dict)
    _save_yaml_data(file_path, data)


def initialize_data_files(data_dir: Path, participants: List[Participant], groups: List[Group]):
    participants_path = data_dir / 'participants.yaml'
    purchases_path = data_dir / 'purchases.yaml'

    if not participants_path.exists():
        save_participants(participants_path, participants)
        save_groups(participants_path, groups) # Save groups to the same file as participants

    if not purchases_path.exists():
        _save_yaml_data(purchases_path, {'purchases': []})
