from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .bootstrap import initialize_run_directory, render_layout_table
from .contracts import DEFAULT_SOURCE_FORMATS, RunManifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yolo-label-validation",
        description="Bootstrap and inspect the YOLO label validation harness.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "show-layout",
        help="Print the canonical artifact layout for one audit run.",
    )

    init_run = subparsers.add_parser(
        "init-run",
        help="Create an empty but valid run workspace with canonical artifacts.",
    )
    init_run.add_argument("--run-id", required=True)
    init_run.add_argument("--output-dir", required=True)
    init_run.add_argument("--dataset-version", default="ds_bootstrap")
    init_run.add_argument("--class-map-version", default="classes_v1")
    init_run.add_argument("--prelabel-source", default="prelabel_model_v1")
    init_run.add_argument(
        "--source-format",
        action="append",
        dest="source_formats",
        default=None,
        help="May be repeated. Defaults to YOLO txt + COCO JSON.",
    )
    init_run.add_argument(
        "--primary-model-version",
        default="prelabel_model_v1",
    )
    init_run.add_argument(
        "--secondary-detector-version",
        default="detector_b_v0",
    )
    init_run.add_argument("--vlm-version", default="qwen2.5-vl")
    init_run.add_argument("--rules-version", default="rules_v1")
    init_run.add_argument("--thresholds-version", default="th_v1")
    init_run.add_argument("--note", action="append", default=[])
    init_run.add_argument("--overwrite", action="store_true")

    return parser


def _handle_show_layout() -> int:
    print(render_layout_table())
    return 0


def _handle_init_run(args: argparse.Namespace) -> int:
    manifest = RunManifest(
        run_id=args.run_id,
        dataset_version=args.dataset_version,
        class_map_version=args.class_map_version,
        prelabel_source=args.prelabel_source,
        source_formats=args.source_formats or list(DEFAULT_SOURCE_FORMATS),
        primary_model_version=args.primary_model_version,
        secondary_detector_version=args.secondary_detector_version,
        vlm_version=args.vlm_version,
        rules_version=args.rules_version,
        thresholds_version=args.thresholds_version,
        notes=args.note,
    )
    initialize_run_directory(
        output_dir=Path(args.output_dir),
        manifest=manifest,
        overwrite=args.overwrite,
    )
    print(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "show-layout":
        return _handle_show_layout()
    if args.command == "init-run":
        return _handle_init_run(args)

    parser.error(f"unknown command: {args.command}")
    return 2
