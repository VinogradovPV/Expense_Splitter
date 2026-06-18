import pytest
from decimal import Decimal
from datetime import date

from expense_splitter.models import Purchase
from expense_splitter.calculator import calculate_balances


def make_purchase(id_, title, amount, payer, participants, date_=None):
    return Purchase(
        id=id_,
        date=date_ or date(2026, 6, 1),
        title=title,
        amount=Decimal(str(amount)),
        payer=payer,
        participants=participants,
        category=None,
        comment=None,
    )


ALL_PARTICIPANTS = ["Павел", "Сергей", "Максим", "Елена"]


def test_single_purchase_equal_split():
    purchases = [make_purchase("1", "Кофе", "400.00", "Павел", ALL_PARTICIPANTS)]
    balances = calculate_balances(purchases, ALL_PARTICIPANTS)
    bal = {b.participant: b for b in balances}

    assert bal["Павел"].paid == Decimal("400.00")
    assert bal["Павел"].share == Decimal("100.00")
    assert bal["Павел"].net == Decimal("300.00")

    assert bal["Сергей"].paid == Decimal("0.00")
    assert bal["Сергей"].share == Decimal("100.00")
    assert bal["Сергей"].net == Decimal("-100.00")


def test_multiple_purchases():
    purchases = [
        make_purchase("1", "Кофе", "200.00", "Павел", ["Павел", "Сергей"]),
        make_purchase("2", "Чай", "100.00", "Сергей", ["Павел", "Сергей"]),
    ]
    balances = calculate_balances(purchases, ["Павел", "Сергей"])
    bal = {b.participant: b for b in balances}

    assert bal["Павел"].paid == Decimal("200.00")
    assert bal["Павел"].share == Decimal("150.00")
    assert bal["Павел"].net == Decimal("50.00")

    assert bal["Сергей"].paid == Decimal("100.00")
    assert bal["Сергей"].share == Decimal("150.00")
    assert bal["Сергей"].net == Decimal("-50.00")


def test_net_sum_is_zero():
    purchases = [
        make_purchase("1", "Обед", "1500.00", "Елена", ALL_PARTICIPANTS),
        make_purchase("2", "Кофе", "300.00", "Максим", ["Максим", "Елена"]),
    ]
    balances = calculate_balances(purchases, ALL_PARTICIPANTS)
    total_net = sum(b.net for b in balances)
    assert total_net == Decimal("0.00")


def test_no_purchases():
    balances = calculate_balances([], ALL_PARTICIPANTS)
    for b in balances:
        assert b.paid == Decimal("0.00")
        assert b.share == Decimal("0.00")
        assert b.net == Decimal("0.00")


def test_rounding_remainder_correct():
    purchases = [make_purchase("1", "Тест", "10.00", "Павел", ["Павел", "Сергей", "Максим"])]
    balances = calculate_balances(purchases, ["Павел", "Сергей", "Максим"])
    total_share = sum(b.share for b in balances)
    assert total_share == Decimal("10.00")


def test_participant_not_in_global_list_raises():
    purchases = [make_purchase("1", "Кофе", "100.00", "Павел", ["Павел", "Незнакомец"])]
    with pytest.raises(ValueError, match="Незнакомец"):
        calculate_balances(purchases, ALL_PARTICIPANTS)


def test_payer_not_in_global_list_raises():
    purchases = [make_purchase("1", "Кофе", "100.00", "Незнакомец", ["Павел"])]
    with pytest.raises(ValueError, match="Незнакомец"):
        calculate_balances(purchases, ALL_PARTICIPANTS)


def test_decimal_not_float():
    purchases = [make_purchase("1", "Кофе", "100.00", "Павел", ["Павел", "Сергей"])]
    balances = calculate_balances(purchases, ["Павел", "Сергей"])
    for b in balances:
        assert isinstance(b.paid, Decimal)
        assert isinstance(b.share, Decimal)
        assert isinstance(b.net, Decimal)
