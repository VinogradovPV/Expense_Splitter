from decimal import Decimal
from typing import List

from expense_splitter.models import Balance, Settlement


def calculate_settlements(balances: List[Balance]) -> List[Settlement]:
    """
    Calculates the minimum number of settlements (transfers) required to balance all accounts.
    Uses a greedy algorithm: matches the largest debtor with the largest creditor.
    """
    # Filter out participants with zero net balance
    active_balances = [b for b in balances if b.net != Decimal("0.00")]

    # Separate into debtors (net < 0) and creditors (net > 0)
    # Debtors owe money, so we take the absolute value for easier calculation
    debtors = [
        {"name": b.participant, "amount": -b.net}
        for b in active_balances
        if b.net < Decimal("0.00")
    ]
    creditors = [
        {"name": b.participant, "amount": b.net}
        for b in active_balances
        if b.net > Decimal("0.00")
    ]

    settlements = []

    # Continue until all debts are settled
    while debtors and creditors:
        # Sort to match largest debtor with largest creditor
        debtors.sort(key=lambda x: x['amount'], reverse=True)
        creditors.sort(key=lambda x: x['amount'], reverse=True)

        debtor = debtors[0]
        creditor = creditors[0]

        # Determine the settlement amount (minimum of what debtor owes and what creditor is owed)
        amount = min(debtor['amount'], creditor['amount'])

        # Add settlement to the list
        settlements.append(Settlement(
            from_participant=debtor['name'],
            to_participant=creditor['name'],
            amount=amount
        ))

        # Update remaining amounts
        debtor['amount'] -= amount
        creditor['amount'] -= amount

        # Remove settled parties from the lists
        if debtor['amount'] == Decimal("0.00"):
            debtors.pop(0)
        if creditor['amount'] == Decimal("0.00"):
            creditors.pop(0)

    return settlements
