from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

DEFAULT_PURCHASE_NAME = "н/д"

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
    amount: Decimal
    payer: str
    participants: List[str]
    purchase_name: str = DEFAULT_PURCHASE_NAME
    category: Optional[str] = None
    comment: Optional[str] = None
    settled: bool = False
    settlement_period_id: Optional[str] = None

    @property
    def title(self) -> str:
        """Legacy read alias for pre-v2 code paths."""
        return self.purchase_name

    @title.setter
    def title(self, value: str) -> None:
        self.purchase_name = value

    def __post_init__(self):
        purchase_name = str(self.purchase_name).strip() if self.purchase_name is not None else ""
        self.purchase_name = purchase_name or DEFAULT_PURCHASE_NAME
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


@dataclass
class SettlementPeriod:
    id: str
    name: str
    status: str
    date_from: date
    date_to: date
    closed_at: datetime
    purchase_ids: List[str]
    total_amount: Decimal
    settlements: List[Settlement] = field(default_factory=list)
    created_by: str = "cli"
    notes: Optional[str] = None
    reopened_at: Optional[datetime] = None

    def __post_init__(self):
        if self.status not in {"closed", "reopened"}:
            raise ValueError("Settlement period status must be 'closed' or 'reopened'.")
        if self.date_from > self.date_to:
            raise ValueError("Settlement period start date must not be after end date.")
        if not isinstance(self.total_amount, Decimal):
            raise TypeError("Settlement period total amount must be a Decimal type.")
        if self.total_amount < 0:
            raise ValueError("Settlement period total amount must not be negative.")
