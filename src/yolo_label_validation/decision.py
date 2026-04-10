from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any
from pathlib import Path

from .artifact_io import load_run_artifact, write_run_artifact
from .risk import load_defaults_config


def build_decision_results(
    normalized_annotations: list[dict[str, Any]],
    rule_issues: list[dict[str, Any]],
    risk_scores: list[dict[str, Any]],
    vlm_review: list[dict[str, Any]],
    *,
    defaults_config: dict[str, Any],
    refine_results: list[dict[str, Any]] | None = None,
    missing_results: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    decision_thresholds = defaults_config.get("decision_thresholds", {})
    keep_threshold = float(decision_thresholds.get("keep", 0.9))
    relabel_threshold = float(decision_thresholds.get("relabel", 0.92))
    refine_iou_floor = float(decision_thresholds.get("refine_geometry_iou_floor", 0.5))
    delete_requires_detector_absence = bool(
        decision_thresholds.get("delete_requires_detector_absence", True)
    )

    issues_by_ann: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in sorted(
        rule_issues,
        key=lambda item: (item["image_id"], item["ann_id"], item["issue_type"], item.get("related_ann_id") or ""),
    ):
        issues_by_ann[issue["ann_id"]].append(issue)
    risk_by_ann = {
        row["ann_id"]: row
        for row in risk_scores
    }
    review_by_ann = {
        row["ann_id"]: row
        for row in sorted(vlm_review, key=lambda item: (item["image_id"], item["ann_id"]))
    }
    refine_by_ann = {
        row["ann_id"]: row
        for row in sorted(
            refine_results or [],
            key=lambda item: (-item["detector_confidence"], item["image_id"], item["ann_id"]),
        )
    }
    missing_by_source_ann: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(
        missing_results or [],
        key=lambda item: (-item["detector_confidence"], item["image_id"], item["missing_id"]),
    ):
        if row["source_ann_id"] is not None:
            missing_by_source_ann[row["source_ann_id"]].append(row)

    decision_results: list[dict[str, Any]] = []
    for annotation in sorted(normalized_annotations, key=lambda item: (item["image_id"], item["ann_id"])):
        ann_id = annotation["ann_id"]
        issues = issues_by_ann.get(ann_id, [])
        risk_row = risk_by_ann.get(ann_id)
        review = review_by_ann.get(ann_id)
        refine = refine_by_ann.get(ann_id)
        missing_for_ann = missing_by_source_ann.get(ann_id, [])
        has_error_issue = any(issue["severity"] == "error" for issue in issues)

        evidence = {
            "rule_issue_ids": [issue["issue_id"] for issue in issues],
            "risk_score": risk_row["risk_score"] if risk_row is not None else None,
            "risk_tags": risk_row["risk_tags"] if risk_row is not None else [],
            "vlm_request_id": review["request_id"] if review is not None else None,
            "vlm_decision": review["decision"] if review is not None else None,
            "detector_refine_id": refine["refine_id"] if refine is not None else None,
            "missing_result_ids": [row["missing_id"] for row in missing_for_ann],
        }

        if has_error_issue:
            decision_results.append(
                _decision_result(
                    annotation,
                    action="manual_review",
                    status="manual_review",
                    reason="explicit rule errors require a human decision before automatic routing",
                    reason_codes=["DECISION_RULE_ERROR"],
                    confidence=review["confidence"] if review is not None else _baseline_confidence(risk_row),
                    evidence=evidence,
                    review=review,
                )
            )
            continue

        if review is None:
            decision_results.append(
                _decision_result(
                    annotation,
                    action="keep",
                    status="auto",
                    reason="annotation stayed outside the sampled review set and has no blocking rule issue",
                    reason_codes=["DECISION_BASELINE_KEEP"],
                    confidence=_baseline_confidence(risk_row),
                    evidence=evidence,
                )
            )
            continue

        decision = review["decision"]
        if decision == "keep" and review["confidence"] >= keep_threshold:
            action = "keep"
            status = "auto"
            reason = review["reason"]
            reason_codes = [review["reason_code"], "DECISION_VLM_KEEP"]
            new_class_name = None
            new_bbox_xyxy = None
        elif decision == "relabel" and review["confidence"] >= relabel_threshold:
            action = "relabel"
            status = "auto"
            reason = review["reason"]
            reason_codes = [review["reason_code"], "DECISION_VLM_RELABEL"]
            new_class_name = review["new_class_name"]
            new_bbox_xyxy = None
        elif decision == "refine" and refine is not None and refine["iou_with_original"] >= refine_iou_floor:
            action = "refine"
            status = "auto"
            reason = refine["reason"]
            reason_codes = [review["reason_code"], refine["reason_code"], "DECISION_DETECTOR_REFINE"]
            new_class_name = None
            new_bbox_xyxy = refine["proposed_bbox_xyxy"]
        elif decision == "delete" and not delete_requires_detector_absence and review["confidence"] >= keep_threshold:
            action = "delete"
            status = "auto"
            reason = review["reason"]
            reason_codes = [review["reason_code"], "DECISION_VLM_DELETE"]
            new_class_name = None
            new_bbox_xyxy = None
        elif decision == "add_missing" and review["class_ok"] and review["box_ok"]:
            action = "keep"
            status = "auto"
            reason = "existing annotation is kept while separate missing-object proposals are evaluated"
            reason_codes = [review["reason_code"], "DECISION_KEEP_WITH_MISSING_PROPOSAL"]
            new_class_name = None
            new_bbox_xyxy = None
        else:
            action = "manual_review"
            status = "manual_review"
            reason = review["reason"]
            reason_codes = [review["reason_code"], "DECISION_REQUIRES_MANUAL_REVIEW"]
            new_class_name = None
            new_bbox_xyxy = None

        decision_results.append(
            _decision_result(
                annotation,
                action=action,
                status=status,
                reason=reason,
                reason_codes=reason_codes,
                confidence=review["confidence"],
                evidence=evidence,
                review=review,
                new_class_name=new_class_name,
                new_bbox_xyxy=new_bbox_xyxy,
            )
        )

    for missing_row in sorted(
        missing_results or [],
        key=lambda item: (item["image_id"], item["missing_id"]),
    ):
        decision_results.append(
            {
                "decision_id": f"decision:{missing_row['missing_id']}",
                "image_id": missing_row["image_id"],
                "ann_id": None,
                "source_ann_id": missing_row["source_ann_id"],
                "class_id": missing_row["class_id"],
                "class_name": missing_row["class_name"],
                "action": "add" if missing_row["detector_confidence"] >= keep_threshold else "manual_review",
                "status": "auto" if missing_row["detector_confidence"] >= keep_threshold else "manual_review",
                "reason": missing_row["reason"],
                "reason_codes": [missing_row["reason_code"], "DECISION_DETECTOR_ADD"],
                "confidence": missing_row["detector_confidence"],
                "metric_kind": missing_row["metric_kind"],
                "new_class_name": missing_row["class_name"],
                "new_bbox_xyxy": missing_row["proposed_bbox_xyxy"],
                "evidence": {
                    "rule_issue_ids": [],
                    "risk_score": None,
                    "risk_tags": [],
                    "vlm_request_id": None,
                    "vlm_decision": "add_missing",
                    "detector_refine_id": None,
                    "missing_result_ids": [missing_row["missing_id"]],
                },
            }
        )
    return sorted(
        decision_results,
        key=lambda item: (
            item["image_id"],
            item["ann_id"] or "",
            item["decision_id"],
        ),
    )


def build_patch_records(
    decision_results: list[dict[str, Any]],
    normalized_annotations: list[dict[str, Any]],
    *,
    timestamp: str,
) -> list[dict[str, Any]]:
    annotation_lookup = {
        annotation["ann_id"]: annotation
        for annotation in normalized_annotations
    }
    patches: list[dict[str, Any]] = []
    for decision in sorted(decision_results, key=lambda item: (item["image_id"], item["ann_id"] or "", item["decision_id"])):
        if decision["status"] != "auto":
            continue
        if decision["action"] not in {"relabel", "refine", "delete", "add"}:
            continue

        annotation = annotation_lookup.get(decision["ann_id"]) if decision["ann_id"] is not None else None
        patches.append(
            {
                "patch_id": f"patch:{decision['decision_id']}",
                "image_id": decision["image_id"],
                "ann_id": decision["ann_id"],
                "old_class_name": annotation["class_name"] if annotation is not None else None,
                "old_bbox_xyxy": annotation["bbox_xyxy"] if annotation is not None else None,
                "action": decision["action"],
                "new_class_name": decision["new_class_name"],
                "new_bbox_xyxy": decision["new_bbox_xyxy"],
                "reason": decision["reason"],
                "reason_code": decision["reason_codes"][0],
                "review_source": {
                    "decision_id": decision["decision_id"],
                    "reason_codes": decision["reason_codes"],
                },
                "confidence": decision["confidence"],
                "human_reviewed": False,
                "timestamp": timestamp,
                "metric_kind": decision["metric_kind"],
                "evidence": decision["evidence"],
            }
        )
    return patches


def build_manual_review_queue(
    decision_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for decision in sorted(decision_results, key=lambda item: (item["image_id"], item["ann_id"] or "", item["decision_id"])):
        if decision["status"] != "manual_review":
            continue
        risk_score = decision["evidence"].get("risk_score")
        has_rule_issue = bool(decision["evidence"].get("rule_issue_ids"))
        if has_rule_issue or (isinstance(risk_score, (int, float)) and risk_score >= 0.9):
            priority = 1
        elif isinstance(risk_score, (int, float)) and risk_score >= 0.6:
            priority = 2
        else:
            priority = 3
        queue.append(
            {
                "queue_id": f"manual:{decision['decision_id']}",
                "image_id": decision["image_id"],
                "ann_id": decision["ann_id"],
                "requested_action": decision["action"],
                "priority": priority,
                "reason": decision["reason"],
                "reason_codes": decision["reason_codes"],
                "evidence": decision["evidence"],
            }
        )
    return queue


def run_decision_for_directory(
    run_dir: Path,
    *,
    defaults_file: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    defaults_config = load_defaults_config(defaults_file)
    run_manifest = load_run_artifact(run_dir, "run_manifest")
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    rule_issues = load_run_artifact(run_dir, "rule_issues")
    risk_scores = load_run_artifact(run_dir, "risk_scores")
    vlm_review = load_run_artifact(run_dir, "vlm_review")
    refine_results = load_run_artifact(run_dir, "refine_results")
    missing_results = load_run_artifact(run_dir, "missing_results")

    decision_results = build_decision_results(
        normalized_annotations,
        rule_issues,
        risk_scores,
        vlm_review,
        defaults_config=defaults_config,
        refine_results=refine_results,
        missing_results=missing_results,
    )
    patches = build_patch_records(
        decision_results,
        normalized_annotations,
        timestamp=str(run_manifest["created_at"]),
    )
    manual_review_queue = build_manual_review_queue(decision_results)

    write_run_artifact(run_dir, "decision_results", decision_results, overwrite=overwrite)
    write_run_artifact(run_dir, "patches", patches, overwrite=overwrite)
    write_run_artifact(run_dir, "manual_review_queue", manual_review_queue, overwrite=overwrite)
    return {
        "decision_results": decision_results,
        "patches": patches,
        "manual_review_queue": manual_review_queue,
    }


def _baseline_confidence(risk_row: dict[str, Any] | None) -> float:
    if risk_row is None:
        return 0.5
    return round(max(0.0, min(1.0, 1.0 - float(risk_row["risk_score"]))), 6)


def _decision_result(
    annotation: dict[str, Any],
    *,
    action: str,
    status: str,
    reason: str,
    reason_codes: list[str],
    confidence: float,
    evidence: dict[str, Any],
    review: dict[str, Any] | None = None,
    new_class_name: str | None = None,
    new_bbox_xyxy: list[float] | None = None,
) -> dict[str, Any]:
    return {
        "decision_id": f"decision:{annotation['ann_id']}",
        "image_id": annotation["image_id"],
        "ann_id": annotation["ann_id"],
        "source_ann_id": annotation["ann_id"],
        "class_id": annotation["class_id"],
        "class_name": annotation["class_name"],
        "action": action,
        "status": status,
        "reason": reason,
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "confidence": round(float(confidence), 6),
        "metric_kind": review["metric_kind"] if review is not None else "proxy",
        "new_class_name": new_class_name,
        "new_bbox_xyxy": new_bbox_xyxy,
        "evidence": evidence,
    }
