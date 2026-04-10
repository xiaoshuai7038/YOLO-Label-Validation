from pathlib import Path
import argparse
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yolo_label_validation.task_docs import scaffold_task_docs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scaffold execution docs for a task.",
    )
    parser.add_argument("task_name")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--with-requirements-traceability", action="store_true")
    parser.add_argument("--with-business-process-map", action="store_true")
    parser.add_argument("--with-uat-matrix", action="store_true")
    parser.add_argument("--with-full-business-testing", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    full_business = args.with_full_business_testing
    created = scaffold_task_docs(
        workspace=Path(args.workspace),
        task_name=args.task_name,
        task_slug=args.slug,
        overwrite=args.overwrite,
        include_requirements_traceability=(
            args.with_requirements_traceability or full_business
        ),
        include_business_process_map=(
            args.with_business_process_map or full_business
        ),
        include_uat_matrix=args.with_uat_matrix or full_business,
    )
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
