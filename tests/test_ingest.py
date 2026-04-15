from __future__ import annotations

import json
from pathlib import Path
import struct
import zlib

import pytest

from yolo_label_validation.cli import main
from yolo_label_validation.contracts import RunManifest
from yolo_label_validation.ingest import (
    ClassMapError,
    CocoSource,
    NormalizationError,
    YoloSource,
    normalize_sources,
    write_normalized_run_artifacts,
)


def test_normalize_yolo_source_produces_shared_contract(tmp_path) -> None:
    images_dir, labels_dir, class_names_file = _build_yolo_fixture(tmp_path)

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

    assert result.record_counts() == {"annotations": 1, "images": 1, "classes": 2}

    annotation = result.annotations[0].to_dict()
    assert annotation["class_id"] == 0
    assert annotation["class_name"] == "cat"
    assert annotation["bbox_xyxy"] == [40.0, 18.0, 60.0, 42.0]
    assert annotation["bbox_xywh"] == [40.0, 18.0, 20.0, 24.0]
    assert annotation["bbox_normalized_cxcywh"] == [0.5, 0.5, 0.2, 0.4]
    assert annotation["lineage"]["source_label_path"] == "img-001.txt"
    assert annotation["lineage"]["source_annotation_ref"] == "img-001.txt#L1"
    assert annotation["lineage"]["source_category_id"] == 0

    image_entry = result.image_entries[0].to_dict()
    assert image_entry["width"] == 100
    assert image_entry["height"] == 60
    assert image_entry["annotation_count"] == 1


def test_normalize_coco_source_produces_shared_contract(tmp_path) -> None:
    annotation_file, images_dir = _build_coco_fixture(tmp_path)

    result = normalize_sources(
        [
            CocoSource(
                annotation_file=annotation_file,
                images_dir=images_dir,
                source_id="fixture-coco",
            )
        ]
    )

    assert result.record_counts() == {"annotations": 1, "images": 1, "classes": 1}

    annotation = result.annotations[0].to_dict()
    assert annotation["class_id"] == 0
    assert annotation["class_name"] == "cat"
    assert annotation["bbox_xyxy"] == [10.0, 20.0, 40.0, 60.0]
    assert annotation["bbox_xywh"] == [10.0, 20.0, 30.0, 40.0]
    assert annotation["bbox_normalized_cxcywh"] == [0.125, 0.4, 0.15, 0.4]
    assert annotation["lineage"]["source_annotation_id"] == 7
    assert annotation["lineage"]["source_image_id"] == 11
    assert annotation["lineage"]["source_label_path"] == "annotations.json"


def test_normalize_sources_rejects_duplicate_class_names(tmp_path) -> None:
    images_dir, labels_dir, _ = _build_yolo_fixture(tmp_path)

    with pytest.raises(ClassMapError):
        normalize_sources(
            [
                YoloSource(
                    images_dir=images_dir,
                    labels_dir=labels_dir,
                    class_names=("cat", "Cat"),
                    source_id="bad-yolo",
                )
            ]
        )


def test_normalize_yolo_source_rejects_hash_pair_fixture_without_pairing_mode(tmp_path) -> None:
    mixed_dir, class_names_file = _build_yolo_hash_pair_fixture(tmp_path)

    with pytest.raises(
        NormalizationError,
        match="has no matching image",
    ):
        normalize_sources(
            [
                YoloSource(
                    images_dir=mixed_dir,
                    labels_dir=mixed_dir,
                    class_names=tuple(class_names_file.read_text(encoding="utf-8").splitlines()),
                    source_id="hash-yolo",
                )
            ]
        )


def test_normalize_yolo_source_supports_hash_pairing_mode(tmp_path) -> None:
    mixed_dir, class_names_file = _build_yolo_hash_pair_fixture(tmp_path)

    result = normalize_sources(
        [
            YoloSource(
                images_dir=mixed_dir,
                labels_dir=mixed_dir,
                class_names=tuple(class_names_file.read_text(encoding="utf-8").splitlines()),
                source_id="hash-yolo",
                pairing_mode="stem_before_double_underscore",
            )
        ]
    )

    assert result.record_counts() == {"annotations": 1, "images": 2, "classes": 1}
    assert [entry.annotation_count for entry in result.image_entries] == [1, 0]
    assert result.annotations[0].to_dict()["lineage"]["source_label_path"] == "frame-001__lab.txt"
    assert result.input_sources[0]["pairing_mode"] == "stem_before_double_underscore"


def test_write_normalized_run_artifacts_is_deterministic(tmp_path) -> None:
    images_dir, labels_dir, class_names_file = _build_yolo_fixture(tmp_path)
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

    run_dir = tmp_path / "artifacts" / "runs" / "deterministic"
    manifest_one = RunManifest(
        run_id="deterministic",
        dataset_version="ds_m2",
        class_map_version="classes_m2",
        prelabel_source="prelabel_model_v1",
        source_formats=["yolo_txt"],
        created_at="2026-04-10T00:00:00Z",
        notes=["deterministic"],
    )
    write_normalized_run_artifacts(run_dir, manifest_one, result, overwrite=True)

    initial_text = {
        "normalized_annotations": (run_dir / "normalized_annotations.jsonl").read_text(encoding="utf-8"),
        "image_index": (run_dir / "image_index.json").read_text(encoding="utf-8"),
        "class_map": (run_dir / "class_map.json").read_text(encoding="utf-8"),
        "run_manifest": (run_dir / "run_manifest.json").read_text(encoding="utf-8"),
    }

    manifest_two = RunManifest(
        run_id="deterministic",
        dataset_version="ds_m2",
        class_map_version="classes_m2",
        prelabel_source="prelabel_model_v1",
        source_formats=["yolo_txt"],
        created_at="2026-04-10T00:00:00Z",
        notes=["deterministic"],
    )
    write_normalized_run_artifacts(run_dir, manifest_two, result, overwrite=True)

    assert (run_dir / "normalized_annotations.jsonl").read_text(encoding="utf-8") == initial_text["normalized_annotations"]
    assert (run_dir / "image_index.json").read_text(encoding="utf-8") == initial_text["image_index"]
    assert (run_dir / "class_map.json").read_text(encoding="utf-8") == initial_text["class_map"]
    assert (run_dir / "run_manifest.json").read_text(encoding="utf-8") == initial_text["run_manifest"]

    manifest_payload = json.loads(initial_text["run_manifest"])
    assert manifest_payload["record_counts"] == {"annotations": 1, "images": 1, "classes": 2}
    assert manifest_payload["input_sources"][0]["source_format"] == "yolo_txt"


def test_cli_normalize_yolo_writes_manifest_and_artifacts(tmp_path, capsys) -> None:
    images_dir, labels_dir, class_names_file = _build_yolo_fixture(tmp_path)
    output_dir = tmp_path / "cli-yolo-run"

    exit_code = main(
        [
            "normalize-yolo",
            "--run-id",
            "cli-yolo",
            "--output-dir",
            str(output_dir),
            "--images-dir",
            str(images_dir),
            "--labels-dir",
            str(labels_dir),
            "--class-names-file",
            str(class_names_file),
            "--dataset-version",
            "ds_m2",
            "--class-map-version",
            "classes_m2",
            "--prelabel-source",
            "prelabel_model_v1",
            "--created-at",
            "2026-04-10T00:00:00Z",
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["record_counts"] == {"annotations": 1, "images": 1, "classes": 2}
    manifest = json.loads((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["normalization_version"] == "ingest_v1"
    assert manifest["source_formats"] == ["yolo_txt"]
    assert manifest["record_counts"]["annotations"] == 1


def test_cli_normalize_yolo_supports_hash_pairing_mode(tmp_path, capsys) -> None:
    mixed_dir, class_names_file = _build_yolo_hash_pair_fixture(tmp_path)
    output_dir = tmp_path / "cli-yolo-hash-run"

    exit_code = main(
        [
            "normalize-yolo",
            "--run-id",
            "cli-yolo-hash",
            "--output-dir",
            str(output_dir),
            "--images-dir",
            str(mixed_dir),
            "--labels-dir",
            str(mixed_dir),
            "--class-names-file",
            str(class_names_file),
            "--pairing-mode",
            "stem_before_double_underscore",
            "--dataset-version",
            "ds_m8",
            "--class-map-version",
            "classes_m8",
            "--prelabel-source",
            "prelabel_model_v1",
            "--created-at",
            "2026-04-13T00:00:00Z",
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["record_counts"] == {"annotations": 1, "images": 2, "classes": 1}
    manifest = json.loads((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["input_sources"][0]["pairing_mode"] == "stem_before_double_underscore"
    assert manifest["record_counts"]["images"] == 2


def test_cli_normalize_coco_writes_manifest_and_artifacts(tmp_path, capsys) -> None:
    annotation_file, images_dir = _build_coco_fixture(tmp_path)
    output_dir = tmp_path / "cli-coco-run"

    exit_code = main(
        [
            "normalize-coco",
            "--run-id",
            "cli-coco",
            "--output-dir",
            str(output_dir),
            "--annotation-file",
            str(annotation_file),
            "--images-dir",
            str(images_dir),
            "--dataset-version",
            "ds_m2",
            "--class-map-version",
            "classes_m2",
            "--prelabel-source",
            "prelabel_model_v1",
            "--created-at",
            "2026-04-10T00:00:00Z",
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["record_counts"] == {"annotations": 1, "images": 1, "classes": 1}
    manifest = json.loads((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_formats"] == ["coco_json"]
    assert manifest["record_counts"]["annotations"] == 1


def _build_yolo_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    images_dir = tmp_path / "yolo-images"
    labels_dir = tmp_path / "yolo-labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    _write_png(images_dir / "img-001.png", width=100, height=60)
    (labels_dir / "img-001.txt").write_text("0 0.5 0.5 0.2 0.4\n", encoding="utf-8")
    class_names_file = tmp_path / "classes.txt"
    class_names_file.write_text("cat\ndog\n", encoding="utf-8")
    return images_dir, labels_dir, class_names_file


def _build_yolo_hash_pair_fixture(tmp_path: Path) -> tuple[Path, Path]:
    mixed_dir = tmp_path / "mixed-yolo"
    mixed_dir.mkdir()

    _write_png(mixed_dir / "frame-001__img.png", width=120, height=80)
    (mixed_dir / "frame-001__lab.txt").write_text(
        "0 0.5 0.5 0.2 0.4\n",
        encoding="utf-8",
    )
    _write_png(mixed_dir / "frame-002__solo.png", width=120, height=80)

    class_names_file = tmp_path / "hash-classes.txt"
    class_names_file.write_text("cigarette\n", encoding="utf-8")
    return mixed_dir, class_names_file


def _build_coco_fixture(tmp_path: Path) -> tuple[Path, Path]:
    images_dir = tmp_path / "coco-images"
    images_dir.mkdir()
    _write_png(images_dir / "frame-001.png", width=200, height=100)

    annotation_file = tmp_path / "annotations.json"
    annotation_file.write_text(
        json.dumps(
            {
                "images": [
                    {
                        "id": 11,
                        "file_name": "frame-001.png",
                        "width": 200,
                        "height": 100,
                    }
                ],
                "annotations": [
                    {
                        "id": 7,
                        "image_id": 11,
                        "category_id": 3,
                        "bbox": [10, 20, 30, 40],
                        "iscrowd": 0,
                    }
                ],
                "categories": [
                    {
                        "id": 3,
                        "name": "cat",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return annotation_file, images_dir


def _write_png(path: Path, *, width: int, height: int) -> None:
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


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return b"".join(
        [
            struct.pack(">I", len(data)),
            chunk_type,
            data,
            struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF),
        ]
    )
