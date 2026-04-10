from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .task_docs import OPTIONAL_TASK_DOCS, REQUIRED_CONTEXT_DOCS, REQUIRED_TASK_DOCS


PLACEHOLDER_MARKERS = ("TBD", "TODO", "{{", "}}", "<fill me>")

REQUIRED_HEADINGS: dict[str, tuple[str, ...]] = {
    "contract.md": ("## Goal", "## Scope", "## Done When", "## Changes"),
    "plan.md": ("## Milestones", "## Validation Route"),
    "implement.md": ("## Execution Rules", "## Iteration Loop", "## Verification Commands"),
    "documentation.md": ("## Readiness Gate", "## Log"),
    "discovery-report.md": ("## Confirmed", "## Existing Documentation Health"),
    "needs-manifest.md": ("## Blocking Needs", "## Deferred Needs"),
}

OPTIONAL_ID_MARKERS: dict[str, str] = {
    "requirements-traceability.md": "REQ-",
    "business-process-map.md": "FLOW-",
    "uat-matrix.md": "UAT-",
}


@dataclass(slots=True)
class CheckFinding:
    path: str
    message: str


def _check_file_headings(path: Path, text: str) -> list[CheckFinding]:
    findings: list[CheckFinding] = []
    for heading in REQUIRED_HEADINGS.get(path.name, ()):
        if heading not in text:
            findings.append(CheckFinding(str(path), f"missing heading: {heading}"))
    return findings


def _check_placeholders(path: Path, text: str) -> list[CheckFinding]:
    findings: list[CheckFinding] = []
    for marker in PLACEHOLDER_MARKERS:
        if marker in text:
            findings.append(CheckFinding(str(path), f"placeholder marker found: {marker}"))
    return findings


def run_task_doc_check(task_dir: Path) -> list[CheckFinding]:
    findings: list[CheckFinding] = []

    for filename in REQUIRED_CONTEXT_DOCS + REQUIRED_TASK_DOCS:
        path = task_dir / filename
        if not path.exists():
            findings.append(CheckFinding(str(path), "required file missing"))
            continue

        text = path.read_text(encoding="utf-8")
        findings.extend(_check_file_headings(path, text))
        findings.extend(_check_placeholders(path, text))

    for filename in OPTIONAL_TASK_DOCS:
        path = task_dir / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        findings.extend(_check_placeholders(path, text))

        marker = OPTIONAL_ID_MARKERS.get(filename)
        if marker and marker not in text:
            findings.append(CheckFinding(str(path), f"expected marker missing: {marker}"))

    return findings
