from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".csv",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".spec",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "reports",
    "venv",
}

MOJIBAKE_MARKERS = tuple(
    item.decode("cp1251")
    for item in (
        b"\xd0\x9f",
        b"\xd0\x90",
        b"\xd0\x91",
        b"\xd0\xb2",
        b"\xd0\xb5",
        b"\xc3\x90",
        b"\xc3\x91",
        b"\xe2\x95\xa8",
        b"\xe2\x95\xa4",
        b"\xef\xbf\xbd",
        b"\xe2\x80",
    )
) + ("\u00d0", "\u00d1", "\u2568", "\u2564", "\ufffd")

ALLOWED_MARKER_FILES = {
    Path("docs/prompts/expense_splitter_p2_gui_system_prompt_v2.md"),
    Path("docs/prompts/expense_splitter_p2_gui_step_by_step_v2_ru.md"),
    Path("docs/prompts/expense_splitter_p2_gui_system_prompt_v3.md"),
    Path("docs/prompts/expense_splitter_p2_gui_step_by_step_v3_ru.md"),
    Path("docs/prompts/expense_splitter_p2_system_prompt_v1.md"),
    Path("docs/prompts/expense_splitter_prod_ready_step_by_step_v5_ru.md"),
    Path("docs/prompts/expense_splitter_prod_ready_system_prompt_v5.md"),
    Path("scripts/qa/check_text_encoding.py"),
}


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = set(path.relative_to(root).parts)
        if relative_parts & SKIP_DIRS:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def is_allowed_marker_context(relative_path: Path, line: str) -> bool:
    if relative_path not in ALLOWED_MARKER_FILES:
        return False
    stripped = line.strip()
    if "MOJIBAKE_MARKERS" in line or 'decode("cp1251")' in line:
        return True
    tokens = stripped.split()
    return bool(tokens) and all(token in MOJIBAKE_MARKERS for token in tokens)


def main() -> int:
    problems: list[str] = []

    for path in iter_text_files(PROJECT_ROOT):
        relative_path = path.relative_to(PROJECT_ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            problems.append(f"{relative_path}: invalid UTF-8: {exc}")
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if is_allowed_marker_context(relative_path, line):
                continue
            marker = next((item for item in MOJIBAKE_MARKERS if item in line), None)
            if marker:
                problems.append(f"{relative_path}:{line_number}: mojibake marker {marker!r}")

    if problems:
        print("Text encoding check failed:")
        for item in problems[:200]:
            print(f"- {item}")
        if len(problems) > 200:
            print(f"- ... and {len(problems) - 200} more")
        return 1

    print("Text encoding check passed: UTF-8 files have no mojibake markers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
