from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import json
from pathlib import Path
import struct
from typing import Any, Iterable, Sequence

from .bootstrap import initialize_run_directory
from .contracts import RunManifest, SourceFormat, build_artifact_layout


FLOAT_PRECISION = 6
SUPPORTED_IMAGE_SUFFIXES = (".bmp", ".gif", ".jpeg", ".jpg", ".png", ".ppm")
SUPPORTED_YOLO_PAIRING_MODES = ("exact_stem", "stem_before_double_underscore")


class NormalizationError(ValueError):
    """Raised when a source dataset cannot be normalized safely."""


class ClassMapError(NormalizationError):
    """Raised when class-map definitions are ambiguous or inconsistent."""


@dataclass(frozen=True, slots=True)
class ClassSourceMapping:
    source_id: str
    source_format: SourceFormat
    source_class_id: int
    source_class_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_format": self.source_format,
            "source_class_id": self.source_class_id,
            "source_class_name": self.source_class_name,
        }


@dataclass(frozen=True, slots=True)
class ClassMapEntry:
    class_id: int
    class_name: str
    name_key: str
    source_mappings: tuple[ClassSourceMapping, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "source_mappings": [mapping.to_dict() for mapping in self.source_mappings],
        }


@dataclass(slots=True)
class ImageIndexEntry:
    image_id: str
    source_id: str
    source_format: SourceFormat
    file_name: str
    relative_path: str
    width: int
    height: int
    source_image_id: str | int | None
    annotation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "source_id": self.source_id,
            "source_format": self.source_format,
            "file_name": self.file_name,
            "relative_path": self.relative_path,
            "width": self.width,
            "height": self.height,
            "source_image_id": self.source_image_id,
            "annotation_count": self.annotation_count,
        }


@dataclass(frozen=True, slots=True)
class PendingAnnotation:
    image_id: str
    source_id: str
    source_format: SourceFormat
    raw_class_id: int
    raw_class_name: str
    bbox_xyxy: tuple[float, float, float, float]
    bbox_xywh: tuple[float, float, float, float]
    bbox_normalized_cxcywh: tuple[float, float, float, float]
    area: float
    iscrowd: bool
    source_annotation_ref: str
    source_annotation_id: str | int | None
    source_image_id: str | int | None
    source_image_path: str
    source_label_path: str | None
    raw_annotation: str | dict[str, Any] | None
    sort_key: tuple[str, str, str]


@dataclass(frozen=True, slots=True)
class NormalizedAnnotation:
    ann_id: str
    image_id: str
    source_id: str
    source_format: SourceFormat
    class_id: int
    class_name: str
    bbox_xyxy: tuple[float, float, float, float]
    bbox_xywh: tuple[float, float, float, float]
    bbox_normalized_cxcywh: tuple[float, float, float, float]
    area: float
    iscrowd: bool
    lineage: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ann_id": self.ann_id,
            "image_id": self.image_id,
            "source_id": self.source_id,
            "source_format": self.source_format,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "bbox_xyxy": list(self.bbox_xyxy),
            "bbox_xywh": list(self.bbox_xywh),
            "bbox_normalized_cxcywh": list(self.bbox_normalized_cxcywh),
            "area": self.area,
            "iscrowd": self.iscrowd,
            "lineage": self.lineage,
        }


@dataclass(frozen=True, slots=True)
class YoloSource:
    images_dir: Path
    labels_dir: Path
    class_names: tuple[str, ...]
    source_id: str = "yolo"
    source_format: SourceFormat = "yolo_txt"
    pairing_mode: str = "exact_stem"


@dataclass(frozen=True, slots=True)
class CocoSource:
    annotation_file: Path
    images_dir: Path | None = None
    source_id: str = "coco"
    source_format: SourceFormat = "coco_json"


@dataclass(slots=True)
class SourceSnapshot:
    source_id: str
    source_format: SourceFormat
    image_entries: list[ImageIndexEntry] = field(default_factory=list)
    annotations: list[PendingAnnotation] = field(default_factory=list)
    class_definitions: list[ClassSourceMapping] = field(default_factory=list)
    input_source: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizationResult:
    annotations: list[NormalizedAnnotation]
    image_entries: list[ImageIndexEntry]
    class_entries: list[ClassMapEntry]
    input_sources: list[dict[str, Any]]
    source_formats: list[SourceFormat]

    def annotation_payloads(self) -> list[dict[str, Any]]:
        return [annotation.to_dict() for annotation in self.annotations]

    def image_index_payload(self, dataset_version: str) -> dict[str, Any]:
        return {
            "dataset_version": dataset_version,
            "images": [entry.to_dict() for entry in self.image_entries],
        }

    def class_map_payload(self, class_map_version: str) -> dict[str, Any]:
        return {
            "class_map_version": class_map_version,
            "source_formats": self.source_formats,
            "classes": [entry.to_dict() for entry in self.class_entries],
        }

    def record_counts(self) -> dict[str, int]:
        return {
            "annotations": len(self.annotations),
            "images": len(self.image_entries),
            "classes": len(self.class_entries),
        }

    def summary_payload(self, manifest: RunManifest) -> dict[str, Any]:
        return {
            "run_id": manifest.run_id,
            "record_counts": self.record_counts(),
            "source_formats": self.source_formats,
            "artifacts": manifest.artifacts,
        }


def load_class_names_file(path: Path) -> tuple[str, ...]:
    if not path.exists():
        raise NormalizationError(f"class-names file does not exist: {path}")
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not lines:
        raise ClassMapError(f"class-names file is empty: {path}")
    return tuple(lines)


def normalize_yolo_source(source: YoloSource) -> SourceSnapshot:
    images_dir = source.images_dir.resolve()
    labels_dir = source.labels_dir.resolve()
    if not images_dir.is_dir():
        raise NormalizationError(f"YOLO images directory does not exist: {images_dir}")
    if not labels_dir.is_dir():
        raise NormalizationError(f"YOLO labels directory does not exist: {labels_dir}")
    pairing_mode = _validated_yolo_pairing_mode(source.pairing_mode)

    class_names = _validated_class_names(
        source.class_names,
        source_id=source.source_id,
        source_format=source.source_format,
    )
    class_definitions = [
        ClassSourceMapping(
            source_id=source.source_id,
            source_format=source.source_format,
            source_class_id=class_id,
            source_class_name=class_name,
        )
        for class_id, class_name in enumerate(class_names)
    ]

    image_lookup = _discover_yolo_images(images_dir, pairing_mode=pairing_mode)
    if not image_lookup:
        raise NormalizationError(f"no supported images found under {images_dir}")

    image_entries: dict[str, ImageIndexEntry] = {}
    for stem_key, image_path in image_lookup.items():
        relative_path = image_path.relative_to(images_dir).as_posix()
        width, height = read_image_size(image_path)
        image_entries[stem_key] = ImageIndexEntry(
            image_id=_build_image_id(source.source_id, relative_path),
            source_id=source.source_id,
            source_format=source.source_format,
            file_name=image_path.name,
            relative_path=relative_path,
            width=width,
            height=height,
            source_image_id=relative_path,
        )

    annotations: list[PendingAnnotation] = []
    for label_path in sorted(labels_dir.rglob("*.txt")):
        relative_label_path = label_path.relative_to(labels_dir).as_posix()
        label_key = _build_yolo_pairing_key(
            label_path,
            labels_dir,
            pairing_mode=pairing_mode,
        )
        image_entry = image_entries.get(label_key)
        if image_entry is None:
            raise NormalizationError(
                f"label file {relative_label_path} has no matching image under {images_dir}"
            )

        for line_number, raw_line in enumerate(
            label_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            stripped = raw_line.strip()
            if not stripped:
                continue
            tokens = stripped.split()
            if len(tokens) != 5:
                raise NormalizationError(
                    f"YOLO label row {relative_label_path}:L{line_number} must have 5 fields"
                )

            class_id = _parse_int_token(
                tokens[0],
                f"YOLO class id at {relative_label_path}:L{line_number}",
            )
            if class_id < 0 or class_id >= len(class_names):
                raise ClassMapError(
                    f"YOLO class id {class_id} at {relative_label_path}:L{line_number} is outside "
                    f"the defined class-name range 0..{len(class_names) - 1}"
                )

            x_center = _parse_float_token(
                tokens[1],
                f"YOLO x_center at {relative_label_path}:L{line_number}",
            )
            y_center = _parse_float_token(
                tokens[2],
                f"YOLO y_center at {relative_label_path}:L{line_number}",
            )
            box_width = _parse_float_token(
                tokens[3],
                f"YOLO width at {relative_label_path}:L{line_number}",
            )
            box_height = _parse_float_token(
                tokens[4],
                f"YOLO height at {relative_label_path}:L{line_number}",
            )

            absolute_width = box_width * image_entry.width
            absolute_height = box_height * image_entry.height
            x_min = (x_center - (box_width / 2.0)) * image_entry.width
            y_min = (y_center - (box_height / 2.0)) * image_entry.height
            x_max = x_min + absolute_width
            y_max = y_min + absolute_height

            annotations.append(
                PendingAnnotation(
                    image_id=image_entry.image_id,
                    source_id=source.source_id,
                    source_format=source.source_format,
                    raw_class_id=class_id,
                    raw_class_name=class_names[class_id],
                    bbox_xyxy=_rounded_box(x_min, y_min, x_max, y_max),
                    bbox_xywh=_rounded_box(
                        x_min,
                        y_min,
                        absolute_width,
                        absolute_height,
                    ),
                    bbox_normalized_cxcywh=_rounded_box(
                        x_center,
                        y_center,
                        box_width,
                        box_height,
                    ),
                    area=_round_float(absolute_width * absolute_height),
                    iscrowd=False,
                    source_annotation_ref=f"{relative_label_path}#L{line_number}",
                    source_annotation_id=f"line-{line_number}",
                    source_image_id=image_entry.source_image_id,
                    source_image_path=image_entry.relative_path,
                    source_label_path=relative_label_path,
                    raw_annotation=stripped,
                    sort_key=(
                        image_entry.image_id,
                        relative_label_path,
                        f"{line_number:09d}",
                    ),
                )
            )

    return SourceSnapshot(
        source_id=source.source_id,
        source_format=source.source_format,
        image_entries=sorted(image_entries.values(), key=lambda entry: entry.image_id),
        annotations=sorted(annotations, key=lambda annotation: annotation.sort_key),
        class_definitions=class_definitions,
        input_source={
            "source_id": source.source_id,
            "source_format": source.source_format,
            "images_dir": images_dir.as_posix(),
            "labels_dir": labels_dir.as_posix(),
            "pairing_mode": pairing_mode,
            "image_count": len(image_entries),
            "annotation_count": len(annotations),
            "class_count": len(class_definitions),
        },
    )


def normalize_coco_source(source: CocoSource) -> SourceSnapshot:
    annotation_file = source.annotation_file.resolve()
    if not annotation_file.exists():
        raise NormalizationError(f"COCO annotation file does not exist: {annotation_file}")

    payload = json.loads(annotation_file.read_text(encoding="utf-8"))
    images = payload.get("images")
    annotations = payload.get("annotations")
    categories = payload.get("categories")
    if not isinstance(images, list) or not isinstance(annotations, list) or not isinstance(categories, list):
        raise NormalizationError(
            f"COCO file {annotation_file} must define array-valued images, annotations, and categories"
        )

    category_names: dict[int, str] = {}
    name_key_to_display_name: dict[str, str] = {}
    class_definitions: list[ClassSourceMapping] = []
    for category in sorted(categories, key=lambda item: str(item.get("id"))):
        raw_category_id = _parse_int_token(category.get("id"), "COCO category id")
        raw_category_name = str(category.get("name", "")).strip()
        name_key = _normalize_name_key(raw_category_name)
        if raw_category_id in category_names:
            raise ClassMapError(f"duplicate COCO category id {raw_category_id} in {annotation_file.name}")
        existing_display_name = name_key_to_display_name.get(name_key)
        if existing_display_name is not None:
            raise ClassMapError(
                f"duplicate COCO class name '{raw_category_name}' in {annotation_file.name}"
            )
        category_names[raw_category_id] = raw_category_name
        name_key_to_display_name[name_key] = raw_category_name
        class_definitions.append(
            ClassSourceMapping(
                source_id=source.source_id,
                source_format=source.source_format,
                source_class_id=raw_category_id,
                source_class_name=raw_category_name,
            )
        )

    images_dir = source.images_dir.resolve() if source.images_dir is not None else None
    image_entries: dict[int, ImageIndexEntry] = {}
    canonical_image_ids: set[str] = set()
    for image in sorted(images, key=lambda item: (_sort_text(item.get("file_name")), _sort_text(item.get("id")))):
        raw_image_id = image.get("id")
        if raw_image_id is None:
            raise NormalizationError(f"COCO image entry in {annotation_file.name} is missing an id")
        raw_file_name = str(image.get("file_name", "")).strip()
        if not raw_file_name:
            raw_file_name = f"image-{raw_image_id}"
        relative_path = Path(raw_file_name).as_posix()
        width = _parse_int_token(image.get("width"), f"COCO width for image {raw_image_id}")
        height = _parse_int_token(image.get("height"), f"COCO height for image {raw_image_id}")

        if images_dir is not None:
            image_path = images_dir / Path(raw_file_name)
            if not image_path.exists():
                raise NormalizationError(
                    f"COCO image '{raw_file_name}' referenced by {annotation_file.name} does not exist under {images_dir}"
                )

        image_id = _build_image_id(source.source_id, relative_path)
        if image_id in canonical_image_ids:
            raise NormalizationError(
                f"COCO canonical image id collision for relative path '{relative_path}'"
            )
        canonical_image_ids.add(image_id)
        image_entries[raw_image_id] = ImageIndexEntry(
            image_id=image_id,
            source_id=source.source_id,
            source_format=source.source_format,
            file_name=Path(raw_file_name).name,
            relative_path=relative_path,
            width=width,
            height=height,
            source_image_id=raw_image_id,
        )

    pending_annotations: list[PendingAnnotation] = []
    for annotation_index, annotation in enumerate(
        sorted(
            annotations,
            key=lambda item: (
                _sort_text(item.get("image_id")),
                _sort_text(item.get("id")),
            ),
        ),
        start=1,
    ):
        raw_image_id = annotation.get("image_id")
        raw_category_id = annotation.get("category_id")
        image_entry = image_entries.get(raw_image_id)
        if image_entry is None:
            raise NormalizationError(
                f"COCO annotation {annotation.get('id')} references unknown image id {raw_image_id}"
            )
        parsed_category_id = _parse_int_token(
            raw_category_id,
            f"COCO category id for annotation {annotation.get('id')}",
        )
        if parsed_category_id not in category_names:
            raise ClassMapError(
                f"COCO annotation {annotation.get('id')} references unknown category id {raw_category_id}"
            )
        bbox = annotation.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise NormalizationError(
                f"COCO annotation {annotation.get('id')} must provide bbox as a 4-item array"
            )

        x_min = _parse_float_token(
            bbox[0],
            f"COCO bbox x for annotation {annotation.get('id')}",
        )
        y_min = _parse_float_token(
            bbox[1],
            f"COCO bbox y for annotation {annotation.get('id')}",
        )
        box_width = _parse_float_token(
            bbox[2],
            f"COCO bbox width for annotation {annotation.get('id')}",
        )
        box_height = _parse_float_token(
            bbox[3],
            f"COCO bbox height for annotation {annotation.get('id')}",
        )
        x_max = x_min + box_width
        y_max = y_min + box_height

        source_annotation_id = annotation.get("id")
        source_annotation_ref = (
            f"ann-{source_annotation_id}"
            if source_annotation_id is not None
            else f"annotations[{annotation_index - 1}]"
        )

        pending_annotations.append(
            PendingAnnotation(
                image_id=image_entry.image_id,
                source_id=source.source_id,
                source_format=source.source_format,
                raw_class_id=parsed_category_id,
                raw_class_name=category_names[parsed_category_id],
                bbox_xyxy=_rounded_box(x_min, y_min, x_max, y_max),
                bbox_xywh=_rounded_box(x_min, y_min, box_width, box_height),
                bbox_normalized_cxcywh=_rounded_box(
                    (x_min + (box_width / 2.0)) / image_entry.width,
                    (y_min + (box_height / 2.0)) / image_entry.height,
                    box_width / image_entry.width,
                    box_height / image_entry.height,
                ),
                area=_round_float(box_width * box_height),
                iscrowd=bool(annotation.get("iscrowd", False)),
                source_annotation_ref=source_annotation_ref,
                source_annotation_id=source_annotation_id,
                source_image_id=raw_image_id,
                source_image_path=image_entry.relative_path,
                source_label_path=annotation_file.name,
                raw_annotation=_sorted_object(annotation),
                sort_key=(
                    image_entry.image_id,
                    source_annotation_ref,
                    f"{annotation_index:09d}",
                ),
            )
        )

    return SourceSnapshot(
        source_id=source.source_id,
        source_format=source.source_format,
        image_entries=sorted(image_entries.values(), key=lambda entry: entry.image_id),
        annotations=sorted(pending_annotations, key=lambda annotation: annotation.sort_key),
        class_definitions=class_definitions,
        input_source={
            "source_id": source.source_id,
            "source_format": source.source_format,
            "annotation_file": annotation_file.as_posix(),
            "images_dir": images_dir.as_posix() if images_dir is not None else None,
            "image_count": len(image_entries),
            "annotation_count": len(pending_annotations),
            "class_count": len(class_definitions),
        },
    )


def merge_class_maps(snapshots: Sequence[SourceSnapshot]) -> list[ClassMapEntry]:
    grouped: dict[str, list[ClassSourceMapping]] = {}
    display_names: dict[str, str] = {}
    for snapshot in snapshots:
        seen_source_ids: set[int] = set()
        seen_name_keys: set[str] = set()
        for definition in snapshot.class_definitions:
            if definition.source_class_id in seen_source_ids:
                raise ClassMapError(
                    f"duplicate class id {definition.source_class_id} in source {snapshot.source_id}"
                )
            seen_source_ids.add(definition.source_class_id)

            name_key = _normalize_name_key(definition.source_class_name)
            if name_key in seen_name_keys:
                raise ClassMapError(
                    f"duplicate class name '{definition.source_class_name}' in source {snapshot.source_id}"
                )
            seen_name_keys.add(name_key)

            if name_key in display_names and display_names[name_key] != definition.source_class_name:
                raise ClassMapError(
                    f"inconsistent class spelling for '{definition.source_class_name}' across sources"
                )

            display_names[name_key] = definition.source_class_name
            grouped.setdefault(name_key, []).append(definition)

    entries: list[ClassMapEntry] = []
    for class_id, name_key in enumerate(sorted(grouped, key=lambda key: display_names[key].casefold())):
        source_mappings = tuple(
            sorted(
                grouped[name_key],
                key=lambda mapping: (
                    mapping.source_format,
                    mapping.source_id,
                    mapping.source_class_id,
                ),
            )
        )
        entries.append(
            ClassMapEntry(
                class_id=class_id,
                class_name=display_names[name_key],
                name_key=name_key,
                source_mappings=source_mappings,
            )
        )
    return entries


def normalize_sources(sources: Sequence[YoloSource | CocoSource]) -> NormalizationResult:
    if not sources:
        raise NormalizationError("at least one source is required for normalization")

    snapshots: list[SourceSnapshot] = []
    for source in sorted(sources, key=lambda item: (item.source_format, item.source_id)):
        if isinstance(source, YoloSource):
            snapshots.append(normalize_yolo_source(source))
            continue
        if isinstance(source, CocoSource):
            snapshots.append(normalize_coco_source(source))
            continue
        raise TypeError(f"unsupported source type: {type(source)!r}")

    class_entries = merge_class_maps(snapshots)
    class_entry_by_name_key = {entry.name_key: entry for entry in class_entries}

    normalized_annotations: list[NormalizedAnnotation] = []
    annotation_count_by_image_id: Counter[str] = Counter()
    for snapshot in snapshots:
        for pending in snapshot.annotations:
            class_entry = class_entry_by_name_key[_normalize_name_key(pending.raw_class_name)]
            normalized_annotations.append(
                NormalizedAnnotation(
                    ann_id=_build_annotation_id(
                        pending.source_id,
                        pending.source_format,
                        pending.source_annotation_ref,
                    ),
                    image_id=pending.image_id,
                    source_id=pending.source_id,
                    source_format=pending.source_format,
                    class_id=class_entry.class_id,
                    class_name=class_entry.class_name,
                    bbox_xyxy=pending.bbox_xyxy,
                    bbox_xywh=pending.bbox_xywh,
                    bbox_normalized_cxcywh=pending.bbox_normalized_cxcywh,
                    area=pending.area,
                    iscrowd=pending.iscrowd,
                    lineage={
                        "source_id": pending.source_id,
                        "source_format": pending.source_format,
                        "source_annotation_ref": pending.source_annotation_ref,
                        "source_annotation_id": pending.source_annotation_id,
                        "source_image_id": pending.source_image_id,
                        "source_image_path": pending.source_image_path,
                        "source_label_path": pending.source_label_path,
                        "source_category_id": pending.raw_class_id,
                        "source_category_name": pending.raw_class_name,
                        "raw_annotation": pending.raw_annotation,
                    },
                )
            )
            annotation_count_by_image_id[pending.image_id] += 1

    normalized_annotations.sort(key=lambda annotation: (annotation.image_id, annotation.ann_id))

    image_entries: list[ImageIndexEntry] = []
    seen_image_ids: set[str] = set()
    for snapshot in snapshots:
        for image_entry in snapshot.image_entries:
            if image_entry.image_id in seen_image_ids:
                raise NormalizationError(
                    f"duplicate canonical image id discovered: {image_entry.image_id}"
                )
            seen_image_ids.add(image_entry.image_id)
            image_entry.annotation_count = annotation_count_by_image_id.get(image_entry.image_id, 0)
            image_entries.append(image_entry)
    image_entries.sort(key=lambda entry: entry.image_id)

    input_sources = [
        snapshot.input_source
        for snapshot in sorted(snapshots, key=lambda item: (item.source_format, item.source_id))
    ]
    source_formats = sorted({snapshot.source_format for snapshot in snapshots})
    return NormalizationResult(
        annotations=normalized_annotations,
        image_entries=image_entries,
        class_entries=class_entries,
        input_sources=input_sources,
        source_formats=source_formats,
    )


def write_normalized_run_artifacts(
    output_dir: Path,
    manifest: RunManifest,
    result: NormalizationResult,
    overwrite: bool = False,
) -> RunManifest:
    layout = build_artifact_layout(output_dir)
    for artifact_name in ("normalized_annotations", "image_index", "class_map"):
        _assert_placeholder_or_missing(layout.path_for(artifact_name), overwrite=overwrite)

    manifest.source_formats = result.source_formats
    manifest.input_sources = result.input_sources
    manifest.record_counts = result.record_counts()

    initialize_run_directory(output_dir=output_dir, manifest=manifest, overwrite=overwrite)

    _write_jsonl(layout.path_for("normalized_annotations"), result.annotation_payloads())
    _write_json(
        layout.path_for("image_index"),
        result.image_index_payload(dataset_version=manifest.dataset_version),
    )
    _write_json(
        layout.path_for("class_map"),
        result.class_map_payload(class_map_version=manifest.class_map_version),
    )
    _write_json(layout.path_for("run_manifest"), manifest.to_dict())
    return manifest


def read_image_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(32)

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = struct.unpack(">II", header[16:24])
        return int(width), int(height)

    if header.startswith((b"GIF87a", b"GIF89a")):
        width, height = struct.unpack("<HH", header[6:10])
        return int(width), int(height)

    if header.startswith(b"BM"):
        width, height = struct.unpack("<ii", header[18:26])
        return abs(int(width)), abs(int(height))

    if header[:2] == b"\xff\xd8":
        return _read_jpeg_size(path)

    if header.startswith((b"P3", b"P6")):
        return _read_ppm_size(path)

    raise NormalizationError(f"unsupported image format for size detection: {path}")


def _read_jpeg_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        handle.read(2)
        while True:
            marker_start = handle.read(1)
            if not marker_start:
                break
            if marker_start != b"\xff":
                continue
            marker_code = handle.read(1)
            if not marker_code or marker_code == b"\xda":
                break
            while marker_code == b"\xff":
                marker_code = handle.read(1)
            if not marker_code:
                break
            if marker_code in {b"\xd8", b"\xd9"}:
                continue

            segment_length = struct.unpack(">H", handle.read(2))[0]
            if marker_code in {
                b"\xc0",
                b"\xc1",
                b"\xc2",
                b"\xc3",
                b"\xc5",
                b"\xc6",
                b"\xc7",
                b"\xc9",
                b"\xca",
                b"\xcb",
                b"\xcd",
                b"\xce",
                b"\xcf",
            }:
                handle.read(1)
                height = struct.unpack(">H", handle.read(2))[0]
                width = struct.unpack(">H", handle.read(2))[0]
                return int(width), int(height)
            handle.seek(segment_length - 2, 1)
    raise NormalizationError(f"unable to read JPEG dimensions from {path}")


def _read_ppm_size(path: Path) -> tuple[int, int]:
    tokens: list[str] = []
    with path.open("rb") as handle:
        while len(tokens) < 4:
            line = handle.readline()
            if not line:
                break
            cleaned = line.split(b"#", 1)[0].strip()
            if not cleaned:
                continue
            tokens.extend(cleaned.decode("ascii").split())
    if len(tokens) < 4:
        raise NormalizationError(f"unable to read PPM dimensions from {path}")
    return int(tokens[1]), int(tokens[2])


def _discover_yolo_images(
    images_dir: Path,
    *,
    pairing_mode: str = "exact_stem",
) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for image_path in sorted(images_dir.rglob("*")):
        if not image_path.is_file():
            continue
        if image_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            continue
        stem_key = _build_yolo_pairing_key(
            image_path,
            images_dir,
            pairing_mode=pairing_mode,
        )
        if stem_key in mapping:
            raise NormalizationError(
                f"ambiguous image stem '{stem_key}' under {images_dir} for pairing mode "
                f"'{pairing_mode}'; keep only one image extension per resolved label stem"
            )
        mapping[stem_key] = image_path
    return mapping


def _build_yolo_pairing_key(
    path: Path,
    root: Path,
    *,
    pairing_mode: str,
) -> str:
    resolved_mode = _validated_yolo_pairing_mode(pairing_mode)
    relative_stem = path.relative_to(root).with_suffix("")
    file_stem = relative_stem.name
    if resolved_mode == "stem_before_double_underscore":
        file_stem = _strip_trailing_hash_suffix(file_stem)

    parent = relative_stem.parent.as_posix()
    if parent in {"", "."}:
        return file_stem
    return f"{parent}/{file_stem}"


def _validated_yolo_pairing_mode(pairing_mode: str) -> str:
    normalized = str(pairing_mode).strip() or "exact_stem"
    if normalized not in SUPPORTED_YOLO_PAIRING_MODES:
        raise NormalizationError(
            f"unsupported YOLO pairing_mode '{normalized}'; expected one of "
            f"{', '.join(SUPPORTED_YOLO_PAIRING_MODES)}"
        )
    return normalized


def _strip_trailing_hash_suffix(stem: str) -> str:
    left, separator, right = stem.rpartition("__")
    if separator and left and right and "_" not in right:
        return left
    return stem


def _validated_class_names(
    class_names: Sequence[str],
    *,
    source_id: str,
    source_format: SourceFormat,
) -> tuple[str, ...]:
    names: list[str] = []
    seen_name_keys: set[str] = set()
    for class_name in class_names:
        display_name = str(class_name).strip()
        name_key = _normalize_name_key(display_name)
        if name_key in seen_name_keys:
            raise ClassMapError(
                f"duplicate class name '{display_name}' in {source_format} source {source_id}"
            )
        seen_name_keys.add(name_key)
        names.append(display_name)
    if not names:
        raise ClassMapError(f"{source_format} source {source_id} does not define any class names")
    return tuple(names)


def _normalize_name_key(name: str) -> str:
    cleaned = str(name).strip()
    if not cleaned:
        raise ClassMapError("class name cannot be empty")
    return cleaned.casefold()


def _build_image_id(source_id: str, relative_path: str) -> str:
    return f"{source_id}:{Path(relative_path).as_posix()}"


def _build_annotation_id(
    source_id: str,
    source_format: SourceFormat,
    source_annotation_ref: str,
) -> str:
    return f"{source_id}:{source_format}:{source_annotation_ref}"


def _parse_int_token(value: Any, context: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise NormalizationError(f"{context} must be an integer") from exc


def _parse_float_token(value: Any, context: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise NormalizationError(f"{context} must be a number") from exc


def _round_float(value: float) -> float:
    return round(float(value), FLOAT_PRECISION)


def _rounded_box(*values: float) -> tuple[float, float, float, float]:
    return tuple(_round_float(value) for value in values)  # type: ignore[return-value]


def _sort_text(value: Any) -> str:
    return "" if value is None else str(value)


def _sorted_object(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload[key] for key in sorted(payload)}


def _assert_placeholder_or_missing(path: Path, *, overwrite: bool) -> None:
    if overwrite or not path.exists():
        return
    existing = path.read_text(encoding="utf-8").strip()
    if existing in {"", "{}", "[]"}:
        return
    raise FileExistsError(f"refusing to overwrite populated artifact without --overwrite: {path}")


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True)
        for record in records
    ]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    path.write_text(payload, encoding="utf-8")
