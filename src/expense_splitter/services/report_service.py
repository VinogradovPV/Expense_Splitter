"""Report service that returns delivery-ready report DTOs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from expense_splitter.analytics import PeriodSpec, build_analytics_dataset
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.current_report import build_current_report_dataset, generate_current_report
from expense_splitter.reports.output_adapters import (
    LocalReportOutputAdapter,
    ReportOutputAdapter,
)
from expense_splitter.reports.result import ReportResult
from expense_splitter.repositories.protocols import (
    ParticipantRepository,
    PurchaseRepository,
    SettlementPeriodRepository,
)
from expense_splitter.settlement_period_report import (
    build_settlement_period_report_dataset,
    generate_settlement_period_report,
)

ReportServiceResult = ReportResult


class ReportService:
    """Generate reports through an output adapter suitable for local or cloud delivery."""

    def __init__(
        self,
        purchases: PurchaseRepository,
        participants: ParticipantRepository,
        settlement_periods: SettlementPeriodRepository,
        output_adapter: ReportOutputAdapter | None = None,
    ) -> None:
        self.purchases = purchases
        self.participants = participants
        self.settlement_periods = settlement_periods
        self.output_adapter = output_adapter or LocalReportOutputAdapter()

    def create_current_report(
        self,
        tenant_id: str,
        scope: str = "open",
        formats: set[str] | None = None,
        output_root: Path = Path("reports/current_state"),
    ) -> ReportResult:
        requested_formats = _normalize_formats(formats)
        created_at = _now()
        dataset = build_current_report_dataset(
            self.participants.list_participants(tenant_id),
            self.purchases.list_purchases(tenant_id),
            scope=scope,
            generated_at=created_at,
        )
        report_dir = generate_current_report(
            dataset,
            output_root=self.output_adapter.output_root(output_root, "current"),
            output_format=_single_generator_format(requested_formats),
        )
        return self.output_adapter.build_result(
            tenant_id=tenant_id,
            report_type="current",
            report_id=scope,
            formats=requested_formats,
            report_dir=report_dir,
            created_at=created_at,
            telegram_caption=f"Отчет по текущим взаиморасчетам: {scope}",
            warnings=list(dataset.warnings),
            metadata={"scope": scope, "source": "repository_protocol"},
        )

    def build_current_report(
        self,
        tenant_id: str,
        scope: str = "open",
        formats: set[str] | None = None,
        output_root: Path = Path("reports/current_state"),
    ) -> ReportResult:
        return self.create_current_report(tenant_id, scope, formats, output_root)

    def create_analytics_report(
        self,
        tenant_id: str,
        period_spec: PeriodSpec,
        formats: set[str] | None = None,
        output_root: Path = Path("reports/analytics"),
        include_undated: bool = False,
    ) -> ReportResult:
        requested_formats = _normalize_formats(formats)
        created_at = _now()
        dataset = build_analytics_dataset(
            self.participants.list_participants(tenant_id),
            [],
            self.purchases.list_purchases(tenant_id),
            period_spec,
            include_undated=include_undated,
        )
        report_dir = generate_analytics_report(
            dataset,
            output_root=self.output_adapter.output_root(output_root, "analytics"),
            output_format=_single_generator_format(requested_formats),
        )
        warnings = _generated_warnings(report_dir, dataset.warnings)
        return self.output_adapter.build_result(
            tenant_id=tenant_id,
            report_type="analytics",
            report_id=period_spec.period_id,
            formats=requested_formats,
            report_dir=report_dir,
            created_at=created_at,
            telegram_caption=f"Аналитический отчет: {period_spec.period_id}",
            warnings=warnings,
            metadata={
                "period": period_spec.period,
                "period_id": period_spec.period_id,
                "source": "repository_protocol",
            },
        )

    def build_analytics_report(
        self,
        tenant_id: str,
        period_spec: PeriodSpec,
        formats: set[str] | None = None,
        output_root: Path = Path("reports/analytics"),
        include_undated: bool = False,
    ) -> ReportResult:
        return self.create_analytics_report(
            tenant_id,
            period_spec,
            formats,
            output_root,
            include_undated,
        )

    def create_settlement_period_report(
        self,
        tenant_id: str,
        settlement_period_id: str,
        formats: set[str] | None = None,
        output_root: Path = Path("reports/settlement_periods"),
    ) -> ReportResult:
        requested_formats = _normalize_formats(formats)
        created_at = _now()
        dataset = build_settlement_period_report_dataset(
            self.settlement_periods.list_periods(tenant_id),
            self.purchases.list_purchases(tenant_id),
            self.participants.list_participants(tenant_id),
            settlement_period_id,
            generated_at=created_at,
        )
        report_dir = generate_settlement_period_report(
            dataset,
            output_root=self.output_adapter.output_root(output_root, "settlement_period"),
            output_format=_single_generator_format(requested_formats),
        )
        return self.output_adapter.build_result(
            tenant_id=tenant_id,
            report_type="settlement_period",
            report_id=settlement_period_id,
            formats=requested_formats,
            report_dir=report_dir,
            created_at=created_at,
            telegram_caption=f"Отчет по периоду взаиморасчетов: {settlement_period_id}",
            warnings=list(dataset.warnings),
            metadata={
                "settlement_period_id": settlement_period_id,
                "balance_source": dataset.balance_source,
                "settlement_source": dataset.settlement_source,
                "source": "repository_protocol",
            },
        )

    def build_settlement_period_report(
        self,
        tenant_id: str,
        settlement_period_id: str,
        formats: set[str] | None = None,
        output_root: Path = Path("reports/settlement_periods"),
    ) -> ReportResult:
        return self.create_settlement_period_report(
            tenant_id,
            settlement_period_id,
            formats,
            output_root,
        )


def _normalize_formats(formats: set[str] | None) -> set[str]:
    return {item.lower() for item in (formats or {"all"})}


def _single_generator_format(formats: set[str]) -> str:
    if not formats:
        return "all"
    if "all" in formats:
        return "all"
    if len(formats) != 1:
        raise ValueError("Current report generators accept one format at a time.")
    return next(iter(formats))


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _generated_warnings(
    report_dir: Path,
    fallback: list[dict[str, object]],
) -> list[dict[str, object]]:
    metadata_path = report_dir / "metadata.json"
    if not metadata_path.is_file():
        return list(fallback)
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return list(fallback)
    warnings = metadata.get("warnings")
    if not isinstance(warnings, list):
        return list(fallback)
    return [dict(row) for row in warnings if isinstance(row, dict)]
