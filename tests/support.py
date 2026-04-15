from __future__ import annotations

import json
from pathlib import Path
import struct
import zlib

from yolo_label_validation.contracts import RunManifest
from yolo_label_validation.decision import run_decision_for_directory
from yolo_label_validation.detector_refine import run_detector_refine_for_directory
from yolo_label_validation.ingest import YoloSource, normalize_sources, write_normalized_run_artifacts
from yolo_label_validation.risk import run_risk_for_directory
from yolo_label_validation.rules import run_rules_for_directory
from yolo_label_validation.vlm import run_vlm_for_directory


ROOT = Path(__file__).resolve().parents[1]


def build_yolo_fixture(
    tmp_path: Path,
    *,
    class_names: tuple[str, ...] = ("cat", "dog"),
    label_lines: tuple[str, ...] | None = ("0 0.5 0.5 0.2 0.4",),
    image_name: str = "img-001.png",
    unlabeled_image_names: tuple[str, ...] = (),
    image_width: int = 100,
    image_height: int = 60,
) -> tuple[Path, Path, Path]:
    images_dir = tmp_path / "yolo-images"
    labels_dir = tmp_path / "yolo-labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    write_png(images_dir / image_name, width=image_width, height=image_height)
    if label_lines is not None:
        (labels_dir / f"{Path(image_name).stem}.txt").write_text(
            "\n".join(label_lines) + "\n",
            encoding="utf-8",
        )
    for unlabeled_image_name in unlabeled_image_names:
        write_png(images_dir / unlabeled_image_name, width=image_width, height=image_height)
    class_names_file = tmp_path / "classes.txt"
    class_names_file.write_text("\n".join(class_names) + "\n", encoding="utf-8")
    return images_dir, labels_dir, class_names_file


def build_normalized_yolo_run(
    tmp_path: Path,
    *,
    label_lines: tuple[str, ...] | None = ("0 0.5 0.5 0.2 0.4",),
    unlabeled_image_names: tuple[str, ...] = (),
    run_id: str = "rules-smoke",
) -> Path:
    images_dir, labels_dir, class_names_file = build_yolo_fixture(
        tmp_path,
        label_lines=label_lines,
        unlabeled_image_names=unlabeled_image_names,
    )
    result = normalize_sources(
        [
            YoloSource(
                images_dir=images_dir,
                labels_dir=labels_dir,
                class_names=tuple(class_names_file.read_text(encoding="utf-8").splitlines()),
                source_id="fixture-yolo",
            )
        ]
    )
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    manifest = RunManifest(
        run_id=run_id,
        dataset_version="ds_m2",
        class_map_version="classes_m2",
        prelabel_source="prelabel_model_v1",
        source_formats=["yolo_txt"],
        created_at="2026-04-10T00:00:00Z",
    )
    write_normalized_run_artifacts(run_dir, manifest, result, overwrite=True)
    return run_dir


def build_rule_ready_run(tmp_path: Path) -> Path:
    run_dir = build_normalized_yolo_run(tmp_path)
    run_rules_for_directory(run_dir, overwrite=True)
    return run_dir


def build_rule_ready_mixed_run(tmp_path: Path) -> Path:
    run_dir = build_normalized_yolo_run(
        tmp_path,
        unlabeled_image_names=("img-empty.png",),
        run_id="rules-smoke-mixed",
    )
    run_rules_for_directory(run_dir, overwrite=True)
    return run_dir


def build_rule_ready_zero_annotation_run(tmp_path: Path) -> Path:
    run_dir = build_normalized_yolo_run(
        tmp_path,
        label_lines=None,
        run_id="rules-smoke-zero",
    )
    run_rules_for_directory(run_dir, overwrite=True)
    return run_dir


def build_risk_ready_run(tmp_path: Path) -> Path:
    run_dir = build_rule_ready_run(tmp_path)
    run_risk_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )
    return run_dir


def build_risk_ready_zero_annotation_run(tmp_path: Path) -> Path:
    run_dir = build_rule_ready_zero_annotation_run(tmp_path)
    run_risk_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )
    return run_dir


def build_vlm_ready_run(
    tmp_path: Path,
    responses_payload: object,
) -> Path:
    run_dir = build_risk_ready_run(tmp_path)
    responses_file = tmp_path / "vlm-responses.json"
    write_json(responses_file, responses_payload)
    run_vlm_for_directory(
        run_dir,
        responses_file=responses_file,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )
    return run_dir


def build_vlm_ready_zero_annotation_run(
    tmp_path: Path,
    responses_payload: object,
) -> Path:
    run_dir = build_risk_ready_zero_annotation_run(tmp_path)
    responses_file = tmp_path / "vlm-responses-zero.json"
    write_json(responses_file, responses_payload)
    run_vlm_for_directory(
        run_dir,
        responses_file=responses_file,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )
    return run_dir


def build_decision_ready_run(
    tmp_path: Path,
    responses_payload: object,
    *,
    with_detector: bool = False,
) -> Path:
    run_dir = build_vlm_ready_run(tmp_path, responses_payload)
    if with_detector:
        run_detector_refine_for_directory(
            run_dir,
            thresholds_file=ROOT / "configs" / "thresholds.example.yaml",
            overwrite=True,
        )
    run_decision_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )
    return run_dir


def write_png(path: Path, *, width: int, height: int) -> None:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw_scanlines = b"".join(
        b"\x00" + (b"\x00\x00\x00" * width)
        for _ in range(height)
    )
    png_bytes = b"".join(
        [
            signature,
            _png_chunk(b"IHDR", ihdr_data),
            _png_chunk(b"IDAT", zlib.compress(raw_scanlines)),
            _png_chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(png_bytes)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return b"".join(
        [
            struct.pack(">I", len(data)),
            chunk_type,
            data,
            struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF),
        ]
    )
