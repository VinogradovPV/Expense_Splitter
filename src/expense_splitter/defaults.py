from decimal import Decimal
from datetime import date
from expense_splitter.models import Participant, Group, Purchase

DEFAULT_PARTICIPANTS = [
    Participant(name="Павел"),
    Participant(name="Сергей"),
    Participant(name="Владимир"),
    Participant(name="Максим"),
    Participant(name="Елена"),
    Participant(name="Эмилия"),
    Participant(name="Мария"),
]

DEFAULT_GROUPS = [
    Group(name="809 кабинет", members=["Павел", "Сергей", "Максим", "Елена"]),
    Group(name="Кофе", members=["Павел", "Сергей", "Владимир", "Максим", "Елена", "Эмилия"]),
    Group(name="Еда", members=["Павел", "Сергей", "Владимир", "Максим", "Елена", "Мария"]),
    Group(name="На всех", members=["Павел", "Сергей", "Владимир", "Максим", "Елена", "Эмилия", "Мария"]),
]

# Example purchases for testing purposes
EXAMPLE_PURCHASES = [
    Purchase(
        id="1",
        date=date(2026, 6, 1),
        title="Кофе в офис",
        amount=Decimal("1200.00"),
        payer="Павел",
        participants=["Павел", "Сергей", "Владимир", "Максим", "Елена", "Эмилия"],
        category="Напитки",
        comment="Кофе для всех",
    ),
    Purchase(
        id="2",
        date=date(2026, 6, 2),
        title="Обед",
        amount=Decimal("1500.00"),
        payer="Елена",
        participants=["Павел", "Сергей", "Владимир", "Максим", "Елена", "Мария"],
        category="Еда",
        comment="Бизнес-ланч",
    ),
    Purchase(
        id="3",
        date=date(2026, 6, 3),
        title="Чай",
        amount=Decimal("300.00"),
        payer="Максим",
        participants=["Максим", "Елена"],
        category="Напитки",
        comment="Зеленый чай",
    ),
]
