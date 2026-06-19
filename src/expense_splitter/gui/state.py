from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from expense_splitter.defaults import DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.storage import initialize_data_files


@dataclass
class GuiState:
    data_dir: Path = Path("data")
    reports_dir: Path = Path("reports")
    analytics_dir: Path = Path("reports/analytics")

    def ensure_data_files(self) -> None:
        initialize_data_files(self.data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)

