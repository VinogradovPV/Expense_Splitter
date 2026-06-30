from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from expense_splitter.analytics import AnalyticsDataset
from expense_splitter.report_tables import chart_display_title
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


def generate_analytics_charts(
    dataset: AnalyticsDataset,
    output_dir: Path,
) -> tuple[list[Path], list[dict[str, object]]]:
    """Generate available analytics charts and return paths plus non-fatal warnings."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    warnings: list[dict[str, object]] = []

    chart_specs = (
        ("spending_by_category.png", dataset.by_category, _spending_by_category),
        ("spending_by_payer.png", dataset.by_payer, _spending_by_payer),
        ("participant_share.png", dataset.by_participant, _participant_share),
        ("balances.png", dataset.balances, _balances),
        ("period_trend.png", dataset.purchases, _period_trend),
        ("top_purchases.png", dataset.top_purchases, _top_purchases),
    )

    for filename, rows, renderer in chart_specs:
        if not dataset.purchases or not rows:
            warnings.append(_chart_warning(filename))
            continue
        path = output_dir / filename
        renderer(dataset, path)
        generated.append(path)

    return generated, warnings


def _chart_warning(filename: str) -> dict[str, object]:
    return {
        "warning_type": "chart_no_data",
        "purchase_id": "",
        "purchase_name": "",
        "message": f"График {filename} не создан: за выбранный период нет данных.",
    }


def _save_barh(
    path: Path, labels: list[str], values: list[float], colors: list[str], title: str, xlabel: str
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
    _pad_value_axis(ax, values)
    ax.bar_label(
        bars,
        labels=[_format_chart_value(value) for value in values],
        padding=4,
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _pad_value_axis(ax, values: list[float]) -> None:
    if not values:
        return
    low = min(0.0, min(values))
    high = max(0.0, max(values))
    span = high - low or max(abs(high), abs(low), 1.0)
    pad = span * 0.18
    ax.set_xlim(low - pad, high + pad)


def _format_chart_value(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ")


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
        "Оплачено",
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
        "Доля расходов",
    )


def _balances(dataset: AnalyticsDataset, path: Path) -> None:
    rows = sorted(dataset.balances, key=lambda row: row.net)
    labels = [row.participant for row in rows]
    _save_barh(
        path,
        labels,
        [float(row.net) for row in rows],
        [color_for_balance_status(row.net) for row in rows],
        "Итоговые балансы",
        "Баланс",
    )


def _period_trend(dataset: AnalyticsDataset, path: Path) -> None:
    totals: dict[str, float] = defaultdict(float)
    for purchase in dataset.purchases:
        if purchase.date is None:
            continue
        key = (
            purchase.date.isoformat()
            if dataset.period_spec.period == "month"
            else purchase.date.strftime("%Y-%m")
        )
        totals[key] += float(purchase.amount)

    labels = sorted(totals)
    values = [totals[label] for label in labels]
    period_colors = build_period_color_map(labels)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(labels, values, color=EXPENSE_DIMENSION_COLOR_MAP["Период"])
    ax.scatter(labels, values, color=[period_colors[label] for label in labels], zorder=3)
    for label, value in zip(labels, values):
        ax.annotate(
            _format_chart_value(value),
            (label, value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=9,
        )
    ax.set_title("Динамика расходов за период")
    ax.set_xlabel("Дата" if dataset.period_spec.period == "month" else "Месяц")
    ax.set_ylabel("Сумма")
    ax.grid(alpha=0.2)
    ax.margins(y=0.2)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _top_purchases(dataset: AnalyticsDataset, path: Path) -> None:
    rows = list(reversed(dataset.top_purchases))
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
    )
