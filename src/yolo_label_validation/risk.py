from __future__ import annotations

from collections import defaultdict
import json
from math import ceil
from pathlib import Path
from typing import Any

from .artifact_io import load_run_artifact, write_run_artifact


def load_defaults_config(
    config_path: Path | None = None,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if payload is not None:
        return payload
    if config_path is None:
        return {
            "candidate_sampling": {
                "image_top_ratio": 0.1,
                "annotation_top_ratio": 0.2,
                "review_all_zero_annotation_images": True,
            },
            "vlm": {
                "image_decision_enum": ["keep", "add_missing", "uncertain"],
            },
        }
    return json.loads(config_path.read_text(encoding="utf-8"))


def build_risk_scores(
    normalized_annotations: list[dict[str, Any]],
    rule_issues: list[dict[str, Any]],
    class_stats: dict[str, Any],
    image_index: dict[str, Any],
) -> list[dict[str, Any]]:
    issue_counts = defaultdict(int)
    for issue in rule_issues:
        issue_counts[issue["ann_id"]] += 1

    class_count_lookup = {
        row["class_id"]: max(row["annotation_count"], 1)
        for row in class_stats.get("classes", [])
    }
    max_class_count = max(class_count_lookup.values(), default=1)
    max_area = max((float(annotation["area"]) for annotation in normalized_annotations), default=1.0)

    image_annotations: dict[str, list[str]] = defaultdict(list)
    risk_scores: list[dict[str, Any]] = []
    for annotation in sorted(normalized_annotations, key=lambda item: (item["image_id"], item["ann_id"])):
        ann_id = annotation["ann_id"]
        class_count = class_count_lookup.get(annotation["class_id"], 1)
        issue_count = issue_counts[ann_id]
        class_rarity = 1.0 - (class_count / max_class_count)
        area_risk = 1.0 - min(1.0, float(annotation["area"]) / max_area)
        risk_score = min(
            1.0,
            0.15 + (0.25 if issue_count else 0.0) + (0.1 * issue_count) + (0.2 * class_rarity) + (0.3 * area_risk),
        )

        risk_tags: list[str] = []
        reason_codes: list[str] = []
        if issue_count:
            risk_tags.append("rule_issue")
            reason_codes.append("RISK_RULE_ISSUE")
        if class_rarity >= 0.5:
            risk_tags.append("rare_class")
            reason_codes.append("RISK_RARE_CLASS")
        if area_risk >= 0.5:
            risk_tags.append("small_box")
            reason_codes.append("RISK_SMALL_BOX")
        if not risk_tags:
            risk_tags.append("baseline_review")
            reason_codes.append("RISK_BASELINE")

        risk_scores.append(
            {
                "review_scope": "annotation",
                "image_id": annotation["image_id"],
                "ann_id": ann_id,
                "class_id": annotation["class_id"],
                "class_name": annotation["class_name"],
                "risk_score": round(risk_score, 6),
                "risk_tags": risk_tags,
                "reason_codes": reason_codes,
                "metric_kind": "proxy",
                "evidence": {
                    "rule_issue_count": issue_count,
                    "class_rarity_score": round(class_rarity, 6),
                    "area_risk_score": round(area_risk, 6),
                    "annotation_count": 1,
                },
            }
        )
        image_annotations[annotation["image_id"]].append(ann_id)

    image_score_lookup: dict[str, float] = {}
    for image_id, annotation_ids in image_annotations.items():
        image_risks = [
            row["risk_score"]
            for row in risk_scores
            if row["review_scope"] == "annotation" and row["ann_id"] in annotation_ids
        ]
        image_score_lookup[image_id] = round(max(image_risks), 6)

    for row in risk_scores:
        row["image_score"] = image_score_lookup[row["image_id"]]

    for image in sorted(image_index.get("images", []), key=lambda item: item["image_id"]):
        if int(image.get("annotation_count", 0)) != 0:
            continue
        risk_scores.append(
            {
                "review_scope": "image",
                "image_id": image["image_id"],
                "ann_id": None,
                "class_id": None,
                "class_name": None,
                "risk_score": 1.0,
                "risk_tags": ["empty_prelabel_image"],
                "reason_codes": ["RISK_EMPTY_PRELABEL_IMAGE"],
                "metric_kind": "proxy",
                "evidence": {
                    "annotation_count": 0,
                    "review_rationale": "zero existing annotations require explicit image-level missing-object review",
                },
                "image_score": 1.0,
            }
        )

    return sorted(
        risk_scores,
        key=lambda row: (
            -row["image_score"],
            -row["risk_score"],
            row["image_id"],
            row["ann_id"] or "",
        ),
    )


def build_review_candidates(
    risk_scores: list[dict[str, Any]],
    defaults_config: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_sampling = defaults_config.get("candidate_sampling", {})
    image_top_ratio = float(candidate_sampling.get("image_top_ratio", 0.1))
    annotation_top_ratio = float(candidate_sampling.get("annotation_top_ratio", 0.2))
    review_all_zero_annotation_images = bool(
        candidate_sampling.get("review_all_zero_annotation_images", True)
    )

    annotation_rows_by_image: dict[str, list[dict[str, Any]]] = defaultdict(list)
    image_level_rows_by_image: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in risk_scores:
        if row["review_scope"] == "annotation":
            annotation_rows_by_image[row["image_id"]].append(row)
            continue
        if row["review_scope"] == "image":
            image_level_rows_by_image[row["image_id"]].append(row)
            continue
        raise ValueError(f"unsupported risk review_scope: {row['review_scope']}")

    annotation_image_rows = sorted(
        (
            {
                "image_id": image_id,
                "image_score": max(item["image_score"] for item in rows),
                "rows": rows,
            }
            for image_id, rows in annotation_rows_by_image.items()
        ),
        key=lambda row: (-row["image_score"], row["image_id"]),
    )
    selected_annotation_image_count = (
        max(1, ceil(len(annotation_image_rows) * image_top_ratio))
        if annotation_image_rows
        else 0
    )
    selected_annotation_image_ids = {
        row["image_id"]
        for row in annotation_image_rows[:selected_annotation_image_count]
    }

    image_level_candidates = {
        image_id: sorted(
            rows,
            key=lambda row: (-row["risk_score"], row["image_id"]),
        )[0]
        for image_id, rows in image_level_rows_by_image.items()
    }
    if review_all_zero_annotation_images:
        selected_image_level_ids = set(image_level_candidates)
    else:
        ordered_image_level_rows = sorted(
            image_level_candidates.values(),
            key=lambda row: (-row["image_score"], row["image_id"]),
        )
        selected_image_level_count = (
            max(1, ceil(len(ordered_image_level_rows) * image_top_ratio))
            if ordered_image_level_rows
            else 0
        )
        selected_image_level_ids = {
            row["image_id"]
            for row in ordered_image_level_rows[:selected_image_level_count]
        }

    selected_image_ids = sorted(
        selected_annotation_image_ids | selected_image_level_ids
    )
    candidates: list[dict[str, Any]] = []
    for image_id in selected_image_ids:
        annotation_rows = sorted(
            annotation_rows_by_image.get(image_id, []),
            key=lambda row: (-row["risk_score"], row["ann_id"] or ""),
        )
        image_level_row = image_level_candidates.get(image_id)
        selected_annotation_count = (
            max(1, ceil(len(annotation_rows) * annotation_top_ratio))
            if annotation_rows
            else 0
        )
        image_score = max(
            [row["image_score"] for row in annotation_rows] +
            ([image_level_row["image_score"]] if image_level_row is not None else [0.0])
        )
        candidates.append(
            {
                "image_id": image_id,
                "image_score": round(float(image_score), 6),
                "candidate_annotations": [
                    {
                        "ann_id": row["ann_id"],
                        "risk_tags": row["risk_tags"],
                        "risk_score": row["risk_score"],
                        "reason_codes": row["reason_codes"],
                        "review_scope": row["review_scope"],
                    }
                    for row in annotation_rows[:selected_annotation_count]
                ],
                "image_level_candidate": (
                    {
                        "risk_tags": image_level_row["risk_tags"],
                        "risk_score": image_level_row["risk_score"],
                        "reason_codes": image_level_row["reason_codes"],
                        "review_scope": image_level_row["review_scope"],
                    }
                    if image_level_row is not None and image_id in selected_image_level_ids
                    else None
                ),
            }
        )
    return sorted(candidates, key=lambda row: (-row["image_score"], row["image_id"]))


def run_risk_for_directory(
    run_dir: Path,
    *,
    defaults_file: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    rule_issues = load_run_artifact(run_dir, "rule_issues")
    class_stats = load_run_artifact(run_dir, "class_stats")
    defaults_config = load_defaults_config(defaults_file)

    risk_scores = build_risk_scores(
        normalized_annotations,
        rule_issues,
        class_stats,
        image_index,
    )
    review_candidates = build_review_candidates(risk_scores, defaults_config)

    write_run_artifact(run_dir, "risk_scores", risk_scores, overwrite=overwrite)
    write_run_artifact(run_dir, "review_candidates", review_candidates, overwrite=overwrite)

    return {
        "risk_scores": risk_scores,
        "review_candidates": review_candidates,
    }
