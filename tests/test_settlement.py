import pytest
from decimal import Decimal
from expense_splitter.models import Balance
from expense_splitter.settlement import calculate_settlements

def test_settlements_simple_case():
    balances = [
        Balance(participant="A", paid=Decimal("100"), share=Decimal("50"), net=Decimal("50")),
        Balance(participant="B", paid=Decimal("0"), share=Decimal("50"), net=Decimal("-50")),
    ]
    settlements = calculate_settlements(balances)
    assert len(settlements) == 1
    assert settlements[0].from_participant == "B"
    assert settlements[0].to_participant == "A"
    assert settlements[0].amount == Decimal("50")

def test_settlements_multiple_debtors_one_creditor():
    balances = [
        Balance(participant="A", paid=Decimal("150"), share=Decimal("50"), net=Decimal("100")),
        Balance(participant="B", paid=Decimal("0"), share=Decimal("50"), net=Decimal("-50")),
        Balance(participant="C", paid=Decimal("0"), share=Decimal("50"), net=Decimal("-50")),
    ]
    settlements = calculate_settlements(balances)
    assert len(settlements) == 2
    # Check that A receives 100 total
    assert sum(s.amount for s in settlements if s.to_participant == "A") == Decimal("100")
    # Check that B and C each pay 50
    assert any(s.from_participant == "B" and s.amount == Decimal("50") for s in settlements)
    assert any(s.from_participant == "C" and s.amount == Decimal("50") for s in settlements)

def test_settlements_complex_case():
    balances = [
        Balance(participant="A", paid=Decimal("0"), share=Decimal("0"), net=Decimal("150")),
        Balance(participant="B", paid=Decimal("0"), share=Decimal("0"), net=Decimal("50")),
        Balance(participant="C", paid=Decimal("0"), share=Decimal("0"), net=Decimal("-100")),
        Balance(participant="D", paid=Decimal("0"), share=Decimal("0"), net=Decimal("-100")),
    ]
    settlements = calculate_settlements(balances)
    assert len(settlements) == 3 # C->A (100), D->A (50), D->B (50) - one possible optimal outcome
    
    # Verify total amounts paid and received
    paid_by_c = sum(s.amount for s in settlements if s.from_participant == "C")
    paid_by_d = sum(s.amount for s in settlements if s.from_participant == "D")
    received_by_a = sum(s.amount for s in settlements if s.to_participant == "A")
    received_by_b = sum(s.amount for s in settlements if s.to_participant == "B")
    
    assert paid_by_c == Decimal("100")
    assert paid_by_d == Decimal("100")
    assert received_by_a == Decimal("150")
    assert received_by_b == Decimal("50")

def test_settlements_zero_balances():
    balances = [
        Balance(participant="A", paid=Decimal("50"), share=Decimal("50"), net=Decimal("0")),
        Balance(participant="B", paid=Decimal("50"), share=Decimal("50"), net=Decimal("0")),
    ]
    settlements = calculate_settlements(balances)
    assert len(settlements) == 0
