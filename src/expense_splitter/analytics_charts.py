from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from expense_splitter.analytics import AnalyticsDataset, aggregate_daily_spending
from expense_splitter.report_tables import (
    BALANCE_CHART_TITLE,
    BALANCE_CHART_XLABEL,
    chart_display_title,
)
from expense_splitter.visual.palette import (
    EXPENSE_DIMENSION_COLOR_MAP,
    QUALITATIVE_PALETTE,
    build_period_color_map,
    build_stable_color_map,
    color_for_balance_status,
)

CHART_FILENAMES = (
    "spending_by_category.png",
    "spending_by_payer.png",
    "participant_share.png",
    "balances.png",
    "period_trend.png",
    "top_purchases.png",
)
PERIOD_TREND_CHART = "period_trend"
PERIOD_TREND_FILENAME = f"{PERIOD_TREND_CHART}.png"
PERIOD_TREND_WARNING_TYPE = "chart_not_enough_data"
PERIOD_TREND_WARNING_MESSAGE = "Недостаточно дат для построения динамики расходов."


def generate_analytics_charts(
    dataset: AnalyticsDataset,
    output_dir: Path,
) -> tuple[list[Path], list[dict[str, object]]]:
    """Generate available analytics charts and return paths plus non-fatal warnings."""
    output_dir.mkdir(parents=True, exist_ok=True)
    _clean_known_chart_outputs(output_dir)
    generated: list[Path] = []
    warnings: list[dict[str, object]] = []

    chart_specs = (
        ("spending_by_category.png", dataset.by_category, _spending_by_category),
        ("spending_by_payer.png", dataset.by_payer, _spending_by_payer),
        ("participant_share.png", dataset.by_participant, _participant_share),
        ("balances.png", dataset.balances, _balances),
        (PERIOD_TREND_FILENAME, dataset.purchases, _period_trend),
        ("top_purchases.png", dataset.top_purchases, _top_purchases),
    )

    for filename, rows, renderer in chart_specs:
        if not dataset.purchases or not rows:
            warnings.append(_chart_warning(filename))
            continue
        if (
            filename == PERIOD_TREND_FILENAME
            and len(aggregate_daily_spending(dataset.purchases)) < 2
        ):
            warnings.append(_period_trend_warning())
            continue
        path = output_dir / filename
        renderer(dataset, path)
        generated.append(path)

    return generated, warnings


def _clean_known_chart_outputs(output_dir: Path) -> None:
    for filename in CHART_FILENAMES:
        path = output_dir / filename
        if path.exists():
            path.unlink()


def _chart_warning(filename: str) -> dict[str, object]:
    return {
        "chart": Path(filename).stem,
        "warning_type": "chart_no_data",
        "purchase_id": "",
        "purchase_name": "",
        "message": (
            f"График «{chart_display_title(filename)}» не создан: "
            "за выбранный период нет данных."
        ),
    }


def _period_trend_warning() -> dict[str, object]:
    return {
        "chart": PERIOD_TREND_CHART,
        "warning_type": PERIOD_TREND_WARNING_TYPE,
        "purchase_id": "",
        "purchase_name": "",
        "message": PERIOD_TREND_WARNING_MESSAGE,
    }


def _save_barh(
    path: Path,
    labels: list[str],
    values: list[float],
    colors: list[str],
    title: str,
    xlabel: str,
    *,
    non_negative_x_axis: bool = False,
    value_label_colors: list[str] | None = None,
) -> None:
    height = max(4.0, min(9.0, 1.0 + len(labels) * 0.5))
    fig, ax = plt.subplots(figsize=(10, height))
    positions = range(len(labels))
    bars = ax.barh(positions, values, color=colors)
    ax.set_yticks(list(positions), labels=labels)
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=0.2)
    if non_negative_x_axis:
        set_non_negative_x_axis(ax, values)
    else:
        _pad_value_axis(ax, values)
    value_labels = ax.bar_label(
        bars,
        labels=[_format_chart_value(value) for value in values],
        padding=6,
        fontsize=9,
    )
    if value_label_colors is not None:
        for label, color in zip(value_labels, value_label_colors):
            label.set_color(color)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _pad_value_axis(ax, values: list[float]) -> None:
    if not values:
        return
    low = min(0.0, min(values))
    high = max(0.0, max(values))
    span = high - low or max(abs(high), abs(low), 1.0)
    pad = span * 0.24
    ax.set_xlim(low - pad, high + pad)


def set_non_negative_x_axis(ax, values: list[float]) -> None:
    if not values:
        return
    if any(value < 0 for value in values):
        _pad_value_axis(ax, values)
        return
    high = max(values)
    right = high * 1.18 if high > 0 else 1.0
    ax.set_xlim(left=0, right=right)


def _format_chart_value(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ")


def _line_label_offset(index: int, values: list[float]) -> tuple[int, int, str]:
    value = values[index]
    previous_value = values[index - 1] if index > 0 else None
    next_value = values[index + 1] if index < len(values) - 1 else None

    if previous_value is not None and next_value is not None:
        if value <= previous_value and value <= next_value:
            return 0, -14, "top"
        if value >= previous_value and value >= next_value:
            return 0, 10, "bottom"

    neighbor = next_value if previous_value is None else previous_value
    if neighbor is not None and value < neighbor:
        return 0, -14, "top"
    return 0, 10, "bottom"


def _spending_by_category(dataset: AnalyticsDataset, path: Path) -> None:
    labels = [str(row["category"]) for row in dataset.by_category]
    color_map = build_stable_color_map(sorted(labels))
    _save_barh(
        path,
        labels,
        [float(row["total_amount"]) for row in dataset.by_category],
        [color_map[label] for label in labels],
        "Расходы по категориям",
        "Сумма",
        non_negative_x_axis=True,
    )


def _spending_by_payer(dataset: AnalyticsDataset, path: Path) -> None:
    labels = [str(row["payer"]) for row in dataset.by_payer]
    color_map = build_stable_color_map(labels)
    _save_barh(
        path,
        labels,
        [float(row["total_paid"]) for row in dataset.by_payer],
        [color_map[label] for label in labels],
        "Расходы по плательщикам",
        "Сумма",
        non_negative_x_axis=True,
    )


def _participant_share(dataset: AnalyticsDataset, path: Path) -> None:
    labels = [str(row["participant"]) for row in dataset.by_participant]
    color_map = build_stable_color_map(labels)
    _save_barh(
        path,
        labels,
        [float(row["total_share"]) for row in dataset.by_participant],
        [color_map[label] for label in labels],
        chart_display_title("participant_share.png"),
        "Сумма",
        non_negative_x_axis=True,
    )


def _balances(dataset: AnalyticsDataset, path: Path) -> None:
    rows = sorted(dataset.balances, key=lambda row: row.net)
    labels = [row.participant for row in rows]
    colors = [color_for_balance_status(row.net) for row in rows]
    _save_barh(
        path,
        labels,
        [float(row.net) for row in rows],
        colors,
        BALANCE_CHART_TITLE,
        BALANCE_CHART_XLABEL,
        value_label_colors=colors,
    )


def _period_trend_points(dataset: AnalyticsDataset) -> tuple[list[str], list[float]]:
    points = aggregate_daily_spending(dataset.purchases)
    return [point.day.isoformat() for point in points], [float(point.amount) for point in points]


def _period_trend(dataset: AnalyticsDataset, path: Path) -> None:
    labels, values = _period_trend_points(dataset)
    period_colors = build_period_color_map(labels)
    positions = list(range(len(labels)))
    label_stride = max(1, (len(labels) + 11) // 12)
    labeled_indexes = set(range(0, len(labels), label_stride)) | {len(labels) - 1}
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(positions, values, color=EXPENSE_DIMENSION_COLOR_MAP["Период"])
    ax.scatter(positions, values, color=[period_colors[label] for label in labels], zorder=3)
    for index, (label, value) in enumerate(zip(labels, values)):
        if index not in labeled_indexes:
            continue
        x_offset, y_offset, vertical_alignment = _line_label_offset(index, values)
        ax.annotate(
            _format_chart_value(value),
            (index, value),
            textcoords="offset points",
            xytext=(x_offset, y_offset),
            ha="center",
            va=vertical_alignment,
            fontsize=9,
        )
    ax.set_title("Динамика расходов за период")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Сумма")
    ax.grid(alpha=0.2)
    ax.margins(y=0.2)
    tick_indexes = sorted(labeled_indexes)
    ax.set_xticks(tick_indexes, [labels[index] for index in tick_indexes])
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _top_purchases(dataset: AnalyticsDataset, path: Path) -> None:
    rows = dataset.top_purchases
    labels = [str(row["purchase_name"]) for row in rows]
    colors = [
        QUALITATIVE_PALETTE[(int(row["rank"]) - 1) % len(QUALITATIVE_PALETTE)] for row in rows
    ]
    _save_barh(
        path,
        labels,
        [float(row["amount"]) for row in rows],
        colors,
        "Крупнейшие покупки",
        "Сумма",
        non_negative_x_axis=True,
    )
