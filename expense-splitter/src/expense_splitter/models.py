from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional


@dataclass
class Participant:
    name: str

@dataclass
class Group:
    name: str
    members: List[str]

@dataclass
class Purchase:
    id: str
    date: Optional[date]
    title: str
    amount: Decimal
    payer: str
    participants: List[str]
    category: Optional[str]
    comment: Optional[str]

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            raise TypeError("Amount must be a Decimal type.")
        if self.amount <= 0:
            raise ValueError("Purchase amount must be greater than zero.")
        if not self.participants:
            raise ValueError("Purchase must have at least one participant.")
        # Participant and payer existence will be validated against a global list later

@dataclass
class Balance:
    participant: str
    paid: Decimal
    share: Decimal
    net: Decimal

@dataclass
class Settlement:
    from_participant: str
    to_participant: str
    amount: Decimal

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            raise TypeError("Settlement amount must be a Decimal type.")
        if self.amount <= 0:
            raise ValueError("Settlement amount must be greater than zero.")
