from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


ArtifactKind = Literal["json_array", "json_object", "jsonl"]
SourceFormat = Literal["yolo_txt", "coco_json"]


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    name: str
    filename: str
    kind: ArtifactKind
    description: str
    required: bool = True


CANONICAL_ARTIFACTS: tuple[ArtifactSpec, ...] = (
    ArtifactSpec(
        name="normalized_annotations",
        filename="normalized_annotations.jsonl",
        kind="jsonl",
        description="normalized internal annotation contract",
    ),
    ArtifactSpec(
        name="image_index",
        filename="image_index.json",
        kind="json_object",
        description="image-level metadata index",
    ),
    ArtifactSpec(
        name="class_map",
        filename="class_map.json",
        kind="json_object",
        description="versioned class dictionary snapshot",
    ),
    ArtifactSpec(
        name="run_manifest",
        filename="run_manifest.json",
        kind="json_object",
        description="run-level version and artifact manifest",
    ),
    ArtifactSpec(
        name="golden_set_manifest",
        filename="golden_set_manifest.json",
        kind="json_object",
        description="golden set selection and version metadata",
    ),
    ArtifactSpec(
        name="golden_eval_report",
        filename="golden_eval_report.json",
        kind="json_object",
        description="evaluation summary against the golden set",
    ),
    ArtifactSpec(
        name="rule_issues",
        filename="rule_issues.json",
        kind="json_array",
        description="static validation issues",
    ),
    ArtifactSpec(
        name="class_stats",
        filename="class_stats.json",
        kind="json_object",
        description="class-level size, count, and ratio statistics",
    ),
    ArtifactSpec(
        name="risk_scores",
        filename="risk_scores.json",
        kind="json_array",
        description="risk ranking output from model-based QA",
    ),
    ArtifactSpec(
        name="review_candidates",
        filename="review_candidates.json",
        kind="json_array",
        description="review queue candidates before VLM review",
    ),
    ArtifactSpec(
        name="vlm_requests",
        filename="vlm_requests.jsonl",
        kind="jsonl",
        description="serialized VLM requests",
    ),
    ArtifactSpec(
        name="vlm_raw_responses",
        filename="vlm_raw_responses.jsonl",
        kind="jsonl",
        description="raw VLM responses for replay and audit",
    ),
    ArtifactSpec(
        name="vlm_review",
        filename="vlm_review.json",
        kind="json_array",
        description="parsed structured VLM decisions",
    ),
    ArtifactSpec(
        name="decision_results",
        filename="decision_results.json",
        kind="json_array",
        description="merged routing results after all evidence",
    ),
    ArtifactSpec(
        name="refine_results",
        filename="refine_results.json",
        kind="json_array",
        description="detector-backed box refinement results",
    ),
    ArtifactSpec(
        name="missing_results",
        filename="missing_results.json",
        kind="json_array",
        description="detector-backed missing-object proposals",
    ),
    ArtifactSpec(
        name="manual_review_queue",
        filename="manual_review_queue.json",
        kind="json_array",
        description="tasks that must be reviewed manually",
    ),
    ArtifactSpec(
        name="cvat_export_manifest",
        filename="cvat_export_manifest.json",
        kind="json_object",
        description="export metadata for CVAT-bound tasks",
        required=False,
    ),
    ArtifactSpec(
        name="cvat_import_patch",
        filename="cvat_import_patch.json",
        kind="json_object",
        description="CVAT round-trip patch import summary",
        required=False,
    ),
    ArtifactSpec(
        name="cvat_quality_report",
        filename="cvat_quality_report.json",
        kind="json_object",
        description="downloaded or transformed CVAT quality report",
        required=False,
    ),
    ArtifactSpec(
        name="patches",
        filename="patches.json",
        kind="json_array",
        description="patch-first annotation edits",
    ),
    ArtifactSpec(
        name="run_summary",
        filename="run_summary.json",
        kind="json_object",
        description="run-level counts and action summary",
    ),
    ArtifactSpec(
        name="metrics_dashboard_source",
        filename="metrics_dashboard_source.json",
        kind="json_object",
        description="flattened metrics source for dashboards",
        required=False,
    ),
)

DEFAULT_SOURCE_FORMATS: tuple[SourceFormat, ...] = ("yolo_txt", "coco_json")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def artifact_specs() -> tuple[ArtifactSpec, ...]:
    return CANONICAL_ARTIFACTS


@dataclass(slots=True)
class ArtifactLayout:
    root: Path
    files: dict[str, Path]

    def path_for(self, artifact_name: str) -> Path:
        return self.files[artifact_name]

    def as_dict(self) -> dict[str, str]:
        return {name: str(path) for name, path in self.files.items()}


def build_artifact_layout(output_dir: Path) -> ArtifactLayout:
    return ArtifactLayout(
        root=output_dir,
        files={
            spec.name: output_dir / spec.filename
            for spec in artifact_specs()
        },
    )


@dataclass(slots=True)
class RunManifest:
    run_id: str
    dataset_version: str
    class_map_version: str
    prelabel_source: str
    source_formats: list[SourceFormat] = field(
        default_factory=lambda: list(DEFAULT_SOURCE_FORMATS)
    )
    normalization_version: str = "ingest_v1"
    primary_model_version: str = "prelabel_model_v1"
    secondary_detector_version: str = "detector_b_v0"
    vlm_version: str = "qwen2.5-vl"
    rules_version: str = "rules_v1"
    thresholds_version: str = "th_v1"
    created_at: str = field(default_factory=utc_now_iso)
    artifacts: dict[str, str] = field(default_factory=dict)
    input_sources: list[dict[str, Any]] = field(default_factory=list)
    record_counts: dict[str, int] = field(default_factory=dict)
    runtime_context: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "dataset_version": self.dataset_version,
            "class_map_version": self.class_map_version,
            "prelabel_source": self.prelabel_source,
            "source_formats": self.source_formats,
            "normalization_version": self.normalization_version,
            "primary_model_version": self.primary_model_version,
            "secondary_detector_version": self.secondary_detector_version,
            "vlm_version": self.vlm_version,
            "rules_version": self.rules_version,
            "thresholds_version": self.thresholds_version,
            "created_at": self.created_at,
            "artifacts": self.artifacts,
            "input_sources": self.input_sources,
            "record_counts": self.record_counts,
            "runtime_context": self.runtime_context,
            "notes": self.notes,
        }
