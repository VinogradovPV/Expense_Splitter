from decimal import Decimal
from typing import List
from datetime import datetime
from pathlib import Path

from expense_splitter.models import Purchase, Balance, Settlement

def generate_markdown_report(
    purchases: List[Purchase],
    balances: List[Balance],
    settlements: List[Settlement],
    output_path: Path
):
    """Generates a detailed Markdown report of expenses, balances, and settlements."""
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_lines = [
        "# Expense Splitter Report",
        f"**Generated:** {now}",
        "",
        "## 1. Summary of Balances",
        "",
        "| Participant | Paid | Share | Net Balance |",
        "|---|---|---|---|"
    ]
    
    for b in sorted(balances, key=lambda x: x.participant):
        report_lines.append(f"| {b.participant} | {b.paid:.2f} | {b.share:.2f} | {b.net:.2f} |")
        
    report_lines.extend([
        "",
        "## 2. Required Settlements",
        ""
    ])
    
    if not settlements:
        report_lines.append("All balances are settled. No transfers required.")
    else:
        report_lines.extend([
            "| From | To | Amount |",
            "|---|---|---|"
        ])
        for s in settlements:
            report_lines.append(f"| {s.from_participant} | {s.to_participant} | {s.amount:.2f} |")
            
    report_lines.extend([
        "",
        "## 3. List of Purchases",
        ""
    ])
    
    if not purchases:
        report_lines.append("No purchases recorded.")
    else:
        report_lines.extend([
            "| Date | Title | Payer | Amount | Participants | Category |",
            "|---|---|---|---|---|---|"
        ])
        for p in sorted(purchases, key=lambda x: x.date or datetime.min.date()):
            date_str = p.date.isoformat() if p.date else "N/A"
            participants_str = ", ".join(p.participants)
            cat_str = p.category or "N/A"
            report_lines.append(f"| {date_str} | {p.title} | {p.payer} | {p.amount:.2f} | {participants_str} | {cat_str} |")
            
    report_lines.append("")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
