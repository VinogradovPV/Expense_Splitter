from datetime import datetime
from pathlib import Path
from typing import List

from expense_splitter.models import Balance, Purchase, Settlement
from expense_splitter.ui_labels import label_for_purchase_status


def generate_markdown_report(
    purchases: List[Purchase],
    balances: List[Balance],
    settlements: List[Settlement],
    output_path: Path
):
    """Generates a detailed Markdown report of expenses, balances, and settlements."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_lines = [
        "# Отчет Expense Splitter",
        f"**Дата формирования отчета:** {now}",
        "",
        "## 1. Сводка балансов",
        "",
        "| Участник | Оплатил | Доля | Баланс |",
        "|---|---|---|---|"
    ]

    for b in sorted(balances, key=lambda x: x.participant):
        report_lines.append(
            f"| {b.participant} | {b.paid:.2f} | {b.share:.2f} | {b.net:.2f} |"
        )

    report_lines.extend([
        "",
        "## 2. Итоговые переводы",
        ""
    ])

    if not settlements:
        report_lines.append("Все балансы закрыты. Переводы не требуются.")
    else:
        report_lines.extend([
            "| От | Кому | Сумма |",
            "|---|---|---|"
        ])
        for s in settlements:
            report_lines.append(
                f"| {s.from_participant} | {s.to_participant} | {s.amount:.2f} |"
            )

    report_lines.extend([
        "",
        "## 3. Список покупок",
        ""
    ])

    if not purchases:
        report_lines.append("Покупок нет.")
    else:
        report_lines.extend([
            "| Дата | Покупка | Плательщик | Сумма | Участники | Категория | Статус |",
            "|---|---|---|---|---|---|---|"
        ])
        for p in sorted(purchases, key=lambda x: x.date or datetime.min.date()):
            date_str = p.date.isoformat() if p.date else "Не указана"
            participants_str = ", ".join(p.participants)
            cat_str = p.category or "Без категории"
            settlement_str = label_for_purchase_status("settled" if p.settled else "open")
            report_lines.append(
                f"| {date_str} | {p.purchase_name} | {p.payer} | {p.amount:.2f} | "
                f"{participants_str} | {cat_str} | {settlement_str} |"
            )

    report_lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
