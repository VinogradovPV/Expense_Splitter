from datetime import date
from decimal import Decimal

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_charts import CHART_FILENAMES, generate_analytics_charts
from expense_splitter.models import Participant, Purchase


def build_dataset(with_purchase=True):
    participants = [Participant("Alice"), Participant("Bob")]
    purchases = []
    if with_purchase:
        purchases.append(
            Purchase(
                id="p1",
                date=date(2026, 6, 1),
                amount=Decimal("50.00"),
                payer="Alice",
                participants=["Alice", "Bob"],
                purchase_name="Lunch",
                category="Food",
            )
        )
    return build_analytics_dataset(
        participants, [], purchases, parse_period("month", 2026, month=6)
    )


def test_charts_are_headless_png_files(tmp_path):
    paths, warnings = generate_analytics_charts(build_dataset(), tmp_path)

    assert warnings == []
    assert {path.name for path in paths} == set(CHART_FILENAMES)
    assert all(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in paths)


def test_empty_dataset_returns_warnings_instead_of_failing(tmp_path):
    paths, warnings = generate_analytics_charts(build_dataset(False), tmp_path)

    assert paths == []
    assert len(warnings) == len(CHART_FILENAMES)
    assert {warning["warning_type"] for warning in warnings} == {"chart_no_data"}
