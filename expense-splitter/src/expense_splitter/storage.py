from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List, TypeVar

import yaml

from expense_splitter.models import Group, Participant, Purchase

T = TypeVar("T")

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
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def _save_yaml_data(file_path: Path, data: dict):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def load_participants(file_path: Path) -> List[Participant]:
    data = _load_yaml_data(file_path)
    return [Participant(**p) for p in data.get('participants', [])]

def save_participants(file_path: Path, participants: List[Participant]):
    data = {'participants': [p.__dict__ for p in participants]}
    _save_yaml_data(file_path, data)

def load_groups(file_path: Path) -> List[Group]:
    data = _load_yaml_data(file_path)
    return [Group(**g) for g in data.get('groups', [])]

def save_groups(file_path: Path, groups: List[Group]):
    data = {'groups': [g.__dict__ for g in groups]}
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
