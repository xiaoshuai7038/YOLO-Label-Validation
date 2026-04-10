from pathlib import Path
import argparse
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yolo_label_validation.doc_check import run_task_doc_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a task documentation folder.",
    )
    parser.add_argument("task_dir")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    findings = run_task_doc_check(Path(args.task_dir))
    if findings:
        for finding in findings:
            print(f"{finding.path}: {finding.message}")
        return 1
    print("task docs check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
