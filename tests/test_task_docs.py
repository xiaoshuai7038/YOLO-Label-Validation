from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from yolo_label_validation.doc_check import run_task_doc_check


ROOT = Path(__file__).resolve().parents[1]


def test_repo_harness_task_docs_pass_gate() -> None:
    findings = run_task_doc_check(ROOT / "tasks" / "repo-harness-bootstrap")
    assert findings == []


def test_init_context_docs_scaffolds_required_files(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_context_docs.py"),
            "--workspace",
            str(tmp_path),
            "--task-slug",
            "demo-task",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert (tmp_path / "tasks" / "demo-task" / "discovery-report.md").exists()
    assert (tmp_path / "tasks" / "demo-task" / "needs-manifest.md").exists()
    assert "discovery-report.md" in result.stdout


def test_init_task_docs_supports_full_business_mode(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_task_docs.py"),
            "Demo Task",
            "--workspace",
            str(tmp_path),
            "--slug",
            "demo-task",
            "--with-full-business-testing",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    task_dir = tmp_path / "tasks" / "demo-task"
    assert (task_dir / "contract.md").exists()
    assert (task_dir / "requirements-traceability.md").exists()
    assert (task_dir / "business-process-map.md").exists()
    assert (task_dir / "uat-matrix.md").exists()
    assert "contract.md" in result.stdout


def test_task_doc_gate_reports_missing_headings(tmp_path) -> None:
    task_dir = tmp_path / "tasks" / "bad-task"
    task_dir.mkdir(parents=True)

    weak_docs = {
        "discovery-report.md": "# Discovery Report\n\n## Confirmed\n",
        "needs-manifest.md": "# Needs Manifest\n\n## Blocking Needs\n",
        "contract.md": "# Contract\n\n## Goal\n",
        "plan.md": "# Plan\n\n## Milestones\n",
        "implement.md": "# Implement\n\n## Execution Rules\n",
        "documentation.md": "# Documentation\n\n## Readiness Gate\n",
    }
    for filename, content in weak_docs.items():
        (task_dir / filename).write_text(content, encoding="utf-8")

    findings = run_task_doc_check(task_dir)
    assert findings
    assert any("missing heading" in finding.message for finding in findings)


def test_ci_workflow_references_quality_gates() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "pytest -q" in workflow
    assert "python scripts/check_task_docs.py tasks/repo-harness-bootstrap" in workflow
