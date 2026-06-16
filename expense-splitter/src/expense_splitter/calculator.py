from collections import defaultdict
from decimal import Decimal, getcontext
from typing import List

from expense_splitter.models import Balance, Purchase

# Set precision for Decimal calculations
getcontext().prec = 10

def calculate_balances(purchases: List[Purchase], all_participants: List[str]) -> List[Balance]:
    paid_amounts = defaultdict(lambda: Decimal("0.00"))
    share_amounts = defaultdict(lambda: Decimal("0.00"))

    for purchase in purchases:
        # Validate participants in purchase against all_participants
        for p in purchase.participants:
            if p not in all_participants:
                raise ValueError(f"Participant \'{p}\' in purchase \'{purchase.id}\' not found in global participants list.")
        if purchase.payer not in all_participants:
            raise ValueError(f"Payer \'{purchase.payer}\' in purchase \'{purchase.id}\' not found in global participants list.")

        paid_amounts[purchase.payer] += purchase.amount

        num_participants = len(purchase.participants)
        if num_participants == 0:
            continue # Should be caught by Purchase validation, but as a safeguard

        # Calculate individual share, rounded to 2 decimal places
        individual_share = (purchase.amount / Decimal(num_participants)).quantize(Decimal("0.01"))

        # Distribute shares, ensuring total matches purchase amount due to rounding
        total_distributed_share = Decimal("0.00")
        for i, participant in enumerate(purchase.participants):
            if i == num_participants - 1:  # Last participant gets the remainder
                share_amounts[participant] += purchase.amount - total_distributed_share
            else:
                share_amounts[participant] += individual_share
                total_distributed_share += individual_share

    balances = []
    for participant_name in all_participants:
        paid = paid_amounts[participant_name]
        share = share_amounts[participant_name]
        net = paid - share
        balances.append(Balance(participant=participant_name, paid=paid, share=share, net=net))

    return balances
