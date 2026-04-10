from pathlib import Path
import argparse
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yolo_label_validation.task_docs import scaffold_context_docs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scaffold discovery and needs docs for a task.",
    )
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--task-slug", required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    created = scaffold_context_docs(
        workspace=Path(args.workspace),
        task_slug=args.task_slug,
        overwrite=args.overwrite,
    )
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
