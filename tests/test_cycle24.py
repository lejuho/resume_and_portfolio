"""Cycle 24: Review artifact hygiene tests.

Validates that advisor-feedback step files under .review/cycle-N/ do not contain
cross-cycle copies or wrong-cycle headings, and that .gitignore suppresses
.read-counter files.
"""

from __future__ import annotations

import re
from pathlib import Path

# ── Inline hygiene checker ────────────────────────────────────────────────────

_CROSS_REF_RE = re.compile(r"Session Cross-Reference", re.IGNORECASE)
_NEWER_HEADING_RE = re.compile(r"#\s+Advisor Feedback:\s+Cycle\s+(\d+)\s+Step", re.IGNORECASE)
_CYCLE_DIR_RE = re.compile(r"[/\\]cycle-(\d+)[/\\]")


def _advisor_hygiene_error(path: Path) -> str | None:
    """Return an error string if path violates advisor-feedback hygiene, else None.

    Rules (in order):
    1. Fail if first non-empty line contains "Session Cross-Reference".
    2. Fail if first non-empty line matches the newer heading format
       '# Advisor Feedback: Cycle N Step' and N does not match the
       cycle-N directory that contains the file.
    Older format '# Step NNN —' is skipped (no false positives on cycles 1-19).
    """
    text = path.read_text(encoding="utf-8")
    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")

    if _CROSS_REF_RE.search(first_line):
        return f"{path}: heading contains 'Session Cross-Reference': {first_line!r}"

    heading_match = _NEWER_HEADING_RE.search(first_line)
    if heading_match:
        heading_cycle = int(heading_match.group(1))
        dir_match = _CYCLE_DIR_RE.search(str(path))
        if dir_match:
            dir_cycle = int(dir_match.group(1))
            if heading_cycle != dir_cycle:
                return (
                    f"{path}: heading declares Cycle {heading_cycle} but file is "
                    f"in cycle-{dir_cycle} directory: {first_line!r}"
                )
    return None


# ── Fixture-driven tests ───────────────────────────────────────────────────────


def test_valid_advisor_file_passes(tmp_path):
    """A correctly headed advisor file in the matching cycle directory passes."""
    step_dir = tmp_path / "cycle-5" / "advisor-feedback"
    step_dir.mkdir(parents=True)
    step_file = step_dir / "step-001.md"
    step_file.write_text(
        "# Advisor Feedback: Cycle 5 Step-001 — Some implementation\n\nType: Approach check\n",
        encoding="utf-8",
    )
    assert _advisor_hygiene_error(step_file) is None


def test_cross_reference_advisor_file_fails(tmp_path):
    """A file with 'Session Cross-Reference' in the heading is rejected."""
    step_dir = tmp_path / "cycle-23" / "advisor-feedback"
    step_dir.mkdir(parents=True)
    step_file = step_dir / "step-004.md"
    step_file.write_text(
        "# Advisor Feedback: Session Cross-Reference — Cycle 21 ISSUE-10/11\n"
        "\nType: Approach check\n",
        encoding="utf-8",
    )
    error = _advisor_hygiene_error(step_file)
    assert error is not None
    assert "Session Cross-Reference" in error


def test_wrong_cycle_advisor_file_fails(tmp_path):
    """A file whose heading declares a different cycle than its directory is rejected."""
    step_dir = tmp_path / "cycle-5" / "advisor-feedback"
    step_dir.mkdir(parents=True)
    step_file = step_dir / "step-001.md"
    step_file.write_text(
        "# Advisor Feedback: Cycle 3 Step-001 — Some implementation\n\nType: Approach check\n",
        encoding="utf-8",
    )
    error = _advisor_hygiene_error(step_file)
    assert error is not None
    assert "Cycle 3" in error
    assert "cycle-5" in error


def test_gitignore_contains_read_counter_rule():
    """.gitignore suppresses .review/**/.read-counter files."""
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        gitignore = Path(__file__).parent.parent / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert ".review/**/.read-counter" in content, (
        ".gitignore must contain '.review/**/.read-counter' to suppress local session artifacts"
    )


def test_real_tree_advisor_hygiene():
    """No tracked or untracked advisor step file in the working tree violates hygiene rules."""
    repo_root = Path(__file__).parent.parent
    step_files = sorted(repo_root.glob(".review/cycle-*/advisor-feedback/step-*.md"))
    errors = [e for path in step_files if (e := _advisor_hygiene_error(path)) is not None]
    assert not errors, "Advisor hygiene violations found:\n" + "\n".join(errors)
