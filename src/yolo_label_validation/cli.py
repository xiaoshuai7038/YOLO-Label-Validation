from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .bootstrap import initialize_run_directory, render_layout_table
from .contracts import DEFAULT_SOURCE_FORMATS, RunManifest, utc_now_iso
from .decision import run_decision_for_directory
from .detector_refine import run_detector_refine_for_directory
from .ingest import (
    CocoSource,
    SUPPORTED_YOLO_PAIRING_MODES,
    YoloSource,
    load_class_names_file,
    normalize_sources,
    write_normalized_run_artifacts,
)
from .materialize import run_export_yolo_for_directory, run_materialize_for_directory
from .risk import run_risk_for_directory
from .rules import run_rules_for_directory
from .vlm import run_vlm_for_directory


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
    _add_manifest_arguments(init_run)
    init_run.add_argument("--note", action="append", default=[])
    init_run.add_argument("--overwrite", action="store_true")

    normalize_yolo = subparsers.add_parser(
        "normalize-yolo",
        help="Normalize a YOLO txt dataset into canonical run artifacts.",
    )
    _add_manifest_arguments(normalize_yolo)
    normalize_yolo.add_argument("--images-dir", required=True)
    normalize_yolo.add_argument("--labels-dir", required=True)
    normalize_yolo.add_argument(
        "--pairing-mode",
        default=SUPPORTED_YOLO_PAIRING_MODES[0],
        choices=SUPPORTED_YOLO_PAIRING_MODES,
        help="How image and label stems are matched inside normalize-yolo.",
    )
    normalize_yolo.add_argument("--source-id", default=None)
    normalize_yolo.add_argument("--class-names-file", default=None)
    normalize_yolo.add_argument(
        "--class-name",
        action="append",
        default=None,
        dest="class_names",
        help="May be repeated. Use instead of --class-names-file.",
    )
    normalize_yolo.add_argument("--note", action="append", default=[])
    normalize_yolo.add_argument("--overwrite", action="store_true")

    normalize_coco = subparsers.add_parser(
        "normalize-coco",
        help="Normalize a COCO JSON dataset into canonical run artifacts.",
    )
    _add_manifest_arguments(normalize_coco)
    normalize_coco.add_argument("--annotation-file", required=True)
    normalize_coco.add_argument("--images-dir", default=None)
    normalize_coco.add_argument("--source-id", default=None)
    normalize_coco.add_argument("--note", action="append", default=[])
    normalize_coco.add_argument("--overwrite", action="store_true")

    run_rules = subparsers.add_parser(
        "run-rules",
        help="Run threshold loading, golden-set contracts, and explicit rule checks for a normalized run directory.",
    )
    run_rules.add_argument("--run-dir", required=True)
    run_rules.add_argument("--thresholds-file", default=None)
    run_rules.add_argument("--golden-set-version", default="golden_v1")
    run_rules.add_argument(
        "--golden-image-id",
        action="append",
        default=None,
        dest="golden_image_ids",
    )
    run_rules.add_argument("--overwrite", action="store_true")

    run_risk = subparsers.add_parser(
        "run-risk",
        help="Build deterministic risk scores and review candidates for a run directory.",
    )
    run_risk.add_argument("--run-dir", required=True)
    run_risk.add_argument("--defaults-file", default=None)
    run_risk.add_argument("--overwrite", action="store_true")

    run_vlm = subparsers.add_parser(
        "run-vlm",
        help="Build review requests and parse fixture responses, local Codex CLI outputs, or legacy HTTP-based review-provider responses.",
    )
    run_vlm.add_argument("--run-dir", required=True)
    run_vlm.add_argument("--responses-file", default=None)
    run_vlm.add_argument("--defaults-file", default=None)
    run_vlm.add_argument("--runtime-config", default=None)
    run_vlm.add_argument("--overwrite", action="store_true")

    run_decision = subparsers.add_parser(
        "run-decision",
        help="Merge rules, risk, VLM, and detector evidence into decisions, patches, and manual review items.",
    )
    run_decision.add_argument("--run-dir", required=True)
    run_decision.add_argument("--defaults-file", default=None)
    run_decision.add_argument("--overwrite", action="store_true")

    run_detector_refine = subparsers.add_parser(
        "run-detector-refine",
        help="Build detector-backed refine and missing-object proposals from either proxy logic or live Ultralytics inference.",
    )
    run_detector_refine.add_argument("--run-dir", required=True)
    run_detector_refine.add_argument("--thresholds-file", default=None)
    run_detector_refine.add_argument("--runtime-config", default=None)
    run_detector_refine.add_argument("--overwrite", action="store_true")

    run_materialize = subparsers.add_parser(
        "run-materialize",
        help="Materialize a patch-applied dataset view and write run-level summary artifacts.",
    )
    run_materialize.add_argument("--run-dir", required=True)
    run_materialize.add_argument("--output-subdir", default="materialized_dataset")
    run_materialize.add_argument("--overwrite", action="store_true")

    export_yolo = subparsers.add_parser(
        "export-yolo",
        help="Export a materialized run into a YOLO-format dataset directory with copied images and labels.",
    )
    export_yolo.add_argument("--run-dir", required=True)
    export_yolo.add_argument("--materialized-subdir", default="materialized_dataset")
    export_yolo.add_argument("--output-subdir", default="materialized_yolo")
    export_yolo.add_argument("--overwrite", action="store_true")

    return parser


def _add_manifest_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dataset-version", default="ds_bootstrap")
    parser.add_argument("--class-map-version", default="classes_v1")
    parser.add_argument("--prelabel-source", default="prelabel_model_v1")
    parser.add_argument(
        "--source-format",
        action="append",
        dest="source_formats",
        default=None,
        help="May be repeated. Defaults to the relevant source format for normalization commands.",
    )
    parser.add_argument("--normalization-version", default="ingest_v1")
    parser.add_argument("--primary-model-version", default="prelabel_model_v1")
    parser.add_argument("--secondary-detector-version", default="detector_b_v0")
    parser.add_argument("--vlm-version", default="codex-config-default")
    parser.add_argument("--rules-version", default="rules_v1")
    parser.add_argument("--thresholds-version", default="th_v1")
    parser.add_argument("--created-at", default=None)


def _handle_show_layout() -> int:
    print(render_layout_table())
    return 0


def _handle_init_run(args: argparse.Namespace) -> int:
    manifest = _build_manifest(args)
    initialize_run_directory(
        output_dir=Path(args.output_dir),
        manifest=manifest,
        overwrite=args.overwrite,
    )
    print(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False))
    return 0


def _handle_normalize_yolo(args: argparse.Namespace) -> int:
    class_names = _resolve_yolo_class_names(args)
    source = YoloSource(
        images_dir=Path(args.images_dir),
        labels_dir=Path(args.labels_dir),
        class_names=class_names,
        source_id=args.source_id or Path(args.labels_dir).name,
        pairing_mode=args.pairing_mode,
    )
    manifest = _build_manifest(args, default_source_formats=["yolo_txt"])
    result = normalize_sources([source])
    write_normalized_run_artifacts(
        output_dir=Path(args.output_dir),
        manifest=manifest,
        result=result,
        overwrite=args.overwrite,
    )
    print(json.dumps(result.summary_payload(manifest), indent=2, ensure_ascii=False))
    return 0


def _handle_normalize_coco(args: argparse.Namespace) -> int:
    source = CocoSource(
        annotation_file=Path(args.annotation_file),
        images_dir=Path(args.images_dir) if args.images_dir else None,
        source_id=args.source_id or Path(args.annotation_file).stem,
    )
    manifest = _build_manifest(args, default_source_formats=["coco_json"])
    result = normalize_sources([source])
    write_normalized_run_artifacts(
        output_dir=Path(args.output_dir),
        manifest=manifest,
        result=result,
        overwrite=args.overwrite,
    )
    print(json.dumps(result.summary_payload(manifest), indent=2, ensure_ascii=False))
    return 0


def _handle_run_rules(args: argparse.Namespace) -> int:
    outputs = run_rules_for_directory(
        Path(args.run_dir),
        thresholds_file=Path(args.thresholds_file) if args.thresholds_file else None,
        golden_set_version=args.golden_set_version,
        selected_image_ids=args.golden_image_ids,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(
            {
                "golden_set_version": outputs["golden_set_manifest"]["golden_set_version"],
                "rule_issue_count": len(outputs["rule_issues"]),
                "class_count": outputs["class_stats"]["total_classes"],
                "thresholds_version": outputs["class_stats"]["thresholds_version"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _handle_run_risk(args: argparse.Namespace) -> int:
    outputs = run_risk_for_directory(
        Path(args.run_dir),
        defaults_file=Path(args.defaults_file) if args.defaults_file else None,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(
            {
                "risk_score_count": len(outputs["risk_scores"]),
                "candidate_image_count": len(outputs["review_candidates"]),
                "top_image_id": outputs["review_candidates"][0]["image_id"] if outputs["review_candidates"] else None,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _handle_run_vlm(args: argparse.Namespace) -> int:
    outputs = run_vlm_for_directory(
        Path(args.run_dir),
        responses_file=Path(args.responses_file) if args.responses_file else None,
        defaults_file=Path(args.defaults_file) if args.defaults_file else None,
        runtime_config_file=Path(args.runtime_config) if args.runtime_config else None,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(
            {
                "request_count": len(outputs["vlm_requests"]),
                "raw_response_count": len(outputs["vlm_raw_responses"]),
                "review_count": len(outputs["vlm_review"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _handle_run_decision(args: argparse.Namespace) -> int:
    outputs = run_decision_for_directory(
        Path(args.run_dir),
        defaults_file=Path(args.defaults_file) if args.defaults_file else None,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(
            {
                "decision_count": len(outputs["decision_results"]),
                "patch_count": len(outputs["patches"]),
                "manual_review_count": len(outputs["manual_review_queue"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _handle_run_detector_refine(args: argparse.Namespace) -> int:
    outputs = run_detector_refine_for_directory(
        Path(args.run_dir),
        thresholds_file=Path(args.thresholds_file) if args.thresholds_file else None,
        runtime_config_file=Path(args.runtime_config) if args.runtime_config else None,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(
            {
                "refine_count": len(outputs["refine_results"]),
                "missing_count": len(outputs["missing_results"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _handle_run_materialize(args: argparse.Namespace) -> int:
    outputs = run_materialize_for_directory(
        Path(args.run_dir),
        output_subdir=args.output_subdir,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(
            {
                "materialized_output_dir": outputs["materialized"]["output_dir"],
                "summary_run_id": outputs["run_summary"]["run_id"],
                "patch_count": outputs["run_summary"]["record_counts"]["patches"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _handle_export_yolo(args: argparse.Namespace) -> int:
    outputs = run_export_yolo_for_directory(
        Path(args.run_dir),
        materialized_subdir=args.materialized_subdir,
        output_subdir=args.output_subdir,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(
            {
                "yolo_output_dir": str(Path(args.run_dir) / args.output_subdir),
                "image_count": outputs["yolo_export"]["image_count"],
                "annotation_count": outputs["yolo_export"]["annotation_count"],
                "class_count": outputs["yolo_export"]["class_count"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _build_manifest(
    args: argparse.Namespace,
    default_source_formats: list[str] | None = None,
) -> RunManifest:
    return RunManifest(
        run_id=args.run_id,
        dataset_version=args.dataset_version,
        class_map_version=args.class_map_version,
        prelabel_source=args.prelabel_source,
        source_formats=args.source_formats or default_source_formats or list(DEFAULT_SOURCE_FORMATS),
        normalization_version=args.normalization_version,
        primary_model_version=args.primary_model_version,
        secondary_detector_version=args.secondary_detector_version,
        vlm_version=args.vlm_version,
        rules_version=args.rules_version,
        thresholds_version=args.thresholds_version,
        created_at=args.created_at or utc_now_iso(),
        notes=args.note,
    )


def _resolve_yolo_class_names(args: argparse.Namespace) -> tuple[str, ...]:
    class_names_from_cli = tuple(args.class_names or [])
    if args.class_names_file and class_names_from_cli:
        raise SystemExit("use either --class-names-file or --class-name, not both")
    if args.class_names_file:
        return load_class_names_file(Path(args.class_names_file))
    if class_names_from_cli:
        return class_names_from_cli
    raise SystemExit("YOLO normalization requires --class-names-file or at least one --class-name")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "show-layout":
        return _handle_show_layout()
    if args.command == "init-run":
        return _handle_init_run(args)
    if args.command == "normalize-yolo":
        return _handle_normalize_yolo(args)
    if args.command == "normalize-coco":
        return _handle_normalize_coco(args)
    if args.command == "run-rules":
        return _handle_run_rules(args)
    if args.command == "run-risk":
        return _handle_run_risk(args)
    if args.command == "run-vlm":
        return _handle_run_vlm(args)
    if args.command == "run-decision":
        return _handle_run_decision(args)
    if args.command == "run-detector-refine":
        return _handle_run_detector_refine(args)
    if args.command == "run-materialize":
        return _handle_run_materialize(args)
    if args.command == "export-yolo":
        return _handle_export_yolo(args)

    parser.error(f"unknown command: {args.command}")
    return 2
