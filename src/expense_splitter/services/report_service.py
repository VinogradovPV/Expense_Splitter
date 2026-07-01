"""Thin report service wrapper around existing report generators."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from expense_splitter.analytics import PeriodSpec, build_analytics_dataset
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.current_report import build_current_report_dataset, generate_current_report
from expense_splitter.repositories.protocols import (
    ParticipantRepository,
    PurchaseRepository,
    SettlementPeriodRepository,
)
from expense_splitter.settlement_period_report import (
    build_settlement_period_report_dataset,
    generate_settlement_period_report,
)


@dataclass(frozen=True)
class ReportServiceResult:
    report_id: str
    report_type: str
    formats: set[str]
    output_dir: Path
    files: list[Path]


class ReportService:
    """Service wrapper that returns structured report metadata."""

    def __init__(
        self,
        purchases: PurchaseRepository,
        participants: ParticipantRepository,
        settlement_periods: SettlementPeriodRepository,
    ) -> None:
        self.purchases = purchases
        self.participants = participants
        self.settlement_periods = settlement_periods

    def build_current_report(
        self,
        tenant_id: str,
        scope: str = "open",
        formats: set[str] | None = None,
        output_root: Path = Path("reports/current_state"),
    ) -> ReportServiceResult:
        requested_formats = formats or {"all"}
        dataset = build_current_report_dataset(
            self.participants.list_participants(tenant_id),
            self.purchases.list_purchases(tenant_id),
            scope=scope,
        )
        output_dir = generate_current_report(
            dataset,
            output_root=output_root,
            output_format=_single_generator_format(requested_formats),
        )
        return self._result("current", scope, requested_formats, output_dir)

    def build_analytics_report(
        self,
        tenant_id: str,
        period_spec: PeriodSpec,
        formats: set[str] | None = None,
        output_root: Path = Path("reports/analytics"),
        include_undated: bool = False,
    ) -> ReportServiceResult:
        requested_formats = formats or {"all"}
        dataset = build_analytics_dataset(
            self.participants.list_participants(tenant_id),
            [],
            self.purchases.list_purchases(tenant_id),
            period_spec,
            include_undated=include_undated,
        )
        output_dir = generate_analytics_report(
            dataset,
            output_root=output_root,
            output_format=_single_generator_format(requested_formats),
        )
        return self._result("analytics", period_spec.period_id, requested_formats, output_dir)

    def build_settlement_period_report(
        self,
        tenant_id: str,
        settlement_period_id: str,
        formats: set[str] | None = None,
        output_root: Path = Path("reports/settlement_periods"),
    ) -> ReportServiceResult:
        requested_formats = formats or {"all"}
        dataset = build_settlement_period_report_dataset(
            self.settlement_periods.list_periods(tenant_id),
            self.purchases.list_purchases(tenant_id),
            self.participants.list_participants(tenant_id),
            settlement_period_id,
        )
        output_dir = generate_settlement_period_report(
            dataset,
            output_root=output_root,
            output_format=_single_generator_format(requested_formats),
        )
        return self._result(
            "settlement_period",
            settlement_period_id,
            requested_formats,
            output_dir,
        )

    @staticmethod
    def _result(
        report_type: str,
        report_id: str,
        formats: set[str],
        output_dir: Path,
    ) -> ReportServiceResult:
        return ReportServiceResult(
            report_id=report_id,
            report_type=report_type,
            formats=set(formats),
            output_dir=output_dir,
            files=sorted(path for path in output_dir.rglob("*") if path.is_file()),
        )


def _single_generator_format(formats: set[str]) -> str:
    normalized = {item.lower() for item in formats}
    if not normalized:
        return "all"
    if "all" in normalized:
        return "all"
    if len(normalized) != 1:
        raise ValueError("Current report generators accept one format at a time.")
    return next(iter(normalized))
