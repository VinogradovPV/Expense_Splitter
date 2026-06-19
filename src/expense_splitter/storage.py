import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, TypeVar

import yaml

from expense_splitter.models import (
    DEFAULT_PURCHASE_NAME,
    Group,
    Participant,
    Purchase,
    Settlement,
    SettlementPeriod,
)

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


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ResetTestResult:
    backup_paths: tuple[Path, ...]


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

def _save_yaml_data(file_path: Path, data: dict, *, create_backup: bool = True) -> Path | None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if create_backup and file_path.exists():
        backup_path = _create_backup(file_path)
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
        return backup_path
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
        p_dict = dict(p)
        # Convert amount to Decimal if it's not already
        if 'amount' in p_dict and not isinstance(p_dict['amount'], Decimal):
            p_dict['amount'] = Decimal(str(p_dict['amount']))
        # Convert date to date object if it's not already
        if 'date' in p_dict and isinstance(p_dict['date'], str):
            p_dict['date'] = date.fromisoformat(p_dict['date'])
        if not p_dict.get('purchase_name'):
            p_dict['purchase_name'] = p_dict.get('title') or DEFAULT_PURCHASE_NAME
        p_dict.pop('title', None)
        p_dict['settled'] = bool(p_dict.get('settled', False))
        if not p_dict.get('settlement_period_id'):
            p_dict['settlement_period_id'] = None
        purchases.append(Purchase(**p_dict))
    return purchases

def save_purchases(file_path: Path, purchases: List[Purchase]):
    data = {'schema_version': SCHEMA_VERSION, 'purchases': []}
    for p in purchases:
        p_dict = {
            'id': p.id,
            'date': p.date,
            'purchase_name': p.purchase_name,
            'amount': p.amount,
            'payer': p.payer,
            'participants': p.participants,
            'category': p.category,
            'comment': p.comment,
            'settled': p.settled,
            'settlement_period_id': p.settlement_period_id,
        }
        # Convert Decimal to string for YAML serialization if not handled by representer
        if isinstance(p_dict.get('amount'), Decimal):
            p_dict['amount'] = str(p_dict['amount'])
        if isinstance(p_dict.get('date'), date):
            p_dict['date'] = p_dict['date'].isoformat()
        data['purchases'].append(p_dict)
    return _save_yaml_data(file_path, data)


def load_categories(file_path: Path) -> list[str]:
    data = _load_yaml_data(file_path)
    values = data.get('categories', [])
    if not isinstance(values, list):
        raise StorageError(f"Invalid categories in {file_path}: expected a list.", file_path)
    return _unique_categories(values)


def _unique_categories(categories) -> list[str]:
    result = []
    seen = set()
    for value in categories:
        category = str(value).strip()
        key = category.casefold()
        if category and key not in seen:
            result.append(category)
            seen.add(key)
    return result


def save_categories(file_path: Path, categories: list[str]):
    data = {
        'schema_version': SCHEMA_VERSION,
        'categories': _unique_categories(categories),
    }
    return _save_yaml_data(file_path, data)


def _parse_period_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _parse_period_date(value) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def _load_settlement(settlement_data: dict) -> Settlement:
    return Settlement(
        from_participant=settlement_data.get('from') or settlement_data.get('from_participant'),
        to_participant=settlement_data.get('to') or settlement_data.get('to_participant'),
        amount=Decimal(str(settlement_data['amount'])),
    )


def load_settlement_periods(file_path: Path) -> List[SettlementPeriod]:
    data = _load_yaml_data(file_path)
    periods = []
    for period_data in data.get('settlement_periods', []):
        p_dict = dict(period_data)
        settlements = [_load_settlement(item) for item in p_dict.get('settlements', [])]
        periods.append(
            SettlementPeriod(
                id=p_dict['id'],
                name=p_dict['name'],
                status=p_dict.get('status', 'closed'),
                date_from=_parse_period_date(p_dict.get('date_from')),
                date_to=_parse_period_date(p_dict.get('date_to')),
                closed_at=_parse_period_datetime(p_dict.get('closed_at')),
                purchase_ids=list(p_dict.get('purchase_ids', [])),
                total_amount=Decimal(str(p_dict.get('total_amount', '0.00'))),
                settlements=settlements,
                created_by=p_dict.get('created_by', 'cli'),
                notes=p_dict.get('notes'),
                reopened_at=(
                    _parse_period_datetime(p_dict['reopened_at'])
                    if p_dict.get('reopened_at')
                    else None
                ),
            )
        )
    return periods


def save_settlement_periods(file_path: Path, periods: List[SettlementPeriod]):
    data = {'schema_version': SCHEMA_VERSION, 'settlement_periods': []}
    for period in periods:
        data['settlement_periods'].append(
            {
                'id': period.id,
                'name': period.name,
                'status': period.status,
                'date_from': period.date_from.isoformat(),
                'date_to': period.date_to.isoformat(),
                'closed_at': period.closed_at.isoformat(timespec='seconds'),
                'purchase_ids': list(period.purchase_ids),
                'total_amount': str(period.total_amount),
                'settlements': [
                    {
                        'from': settlement.from_participant,
                        'to': settlement.to_participant,
                        'amount': str(settlement.amount),
                    }
                    for settlement in period.settlements
                ],
                'created_by': period.created_by,
                'notes': period.notes,
                'reopened_at': (
                    period.reopened_at.isoformat(timespec='seconds')
                    if period.reopened_at
                    else None
                ),
            }
        )
    return _save_yaml_data(file_path, data)


def initialize_data_files(data_dir: Path, participants: List[Participant], groups: List[Group]):
    from expense_splitter.defaults import DEFAULT_CATEGORIES

    participants_path = data_dir / 'participants.yaml'
    purchases_path = data_dir / 'purchases.yaml'
    settlement_periods_path = data_dir / 'settlement_periods.yaml'
    categories_path = data_dir / 'categories.yaml'

    if not participants_path.exists():
        save_participants(participants_path, participants)
        save_groups(participants_path, groups) # Save groups to the same file as participants

    if not purchases_path.exists():
        _save_yaml_data(purchases_path, {'schema_version': SCHEMA_VERSION, 'purchases': []})

    if not settlement_periods_path.exists():
        _save_yaml_data(
            settlement_periods_path,
            {'schema_version': SCHEMA_VERSION, 'settlement_periods': []},
        )

    if not categories_path.exists():
        save_categories(categories_path, DEFAULT_CATEGORIES)


def reset_test_data(data_dir: Path, confirm: str) -> ResetTestResult:
    if confirm != "RESET_TEST_DATA":
        raise ValueError("Для сброса введите RESET_TEST_DATA без изменений.")

    purchases_path = data_dir / 'purchases.yaml'
    periods_path = data_dir / 'settlement_periods.yaml'
    missing = [path for path in (purchases_path, periods_path) if not path.exists()]
    if missing:
        raise StorageError(f"Cannot reset missing data file: {missing[0]}", missing[0])

    # Both backups must exist before either live file is cleared.
    backup_paths = (_create_backup(purchases_path), _create_backup(periods_path))
    _save_yaml_data(
        purchases_path,
        {'schema_version': SCHEMA_VERSION, 'purchases': []},
        create_backup=False,
    )
    _save_yaml_data(
        periods_path,
        {'schema_version': SCHEMA_VERSION, 'settlement_periods': []},
        create_backup=False,
    )
    return ResetTestResult(backup_paths=backup_paths)
