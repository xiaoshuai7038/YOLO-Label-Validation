from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import threading

import pytest

from yolo_label_validation.artifact_io import load_run_artifact
from yolo_label_validation.cli import main
from yolo_label_validation.vlm import (
    _resolve_codex_cli_command,
    build_vlm_requests,
    parse_vlm_reviews,
    run_vlm_for_directory,
)

from .support import build_risk_ready_run, build_risk_ready_zero_annotation_run, write_json


ROOT = Path(__file__).resolve().parents[1]


def _legacy_runtime_config_payload(*, base_url: str) -> dict[str, object]:
    return {
        "version": "runtime_integration_v1",
        "defaults_file": "configs/defaults.json",
        "thresholds_file": "configs/thresholds.example.yaml",
        "vlm": {
            "mode": "live",
            "provider": "openai_compatible",
            "base_url": base_url,
            "endpoint_path": "/chat/completions",
            "api_key_env": "TEST_VLM_API_KEY",
            "model": "mock-live-vlm",
            "timeout_seconds": 15,
            "max_retries": 0,
            "temperature": 0.0,
            "response_format": "json_object",
            "max_tokens": 256,
            "image_transport": "data_url",
            "system_prompt": "Return JSON only.",
        },
        "detector": {
            "mode": "proxy",
            "family": "ultralytics",
            "weights_path": "artifacts/models/yolo11n.pt",
            "device": "cpu",
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_det": 100,
            "refine_match_iou": 0.1,
            "missing_match_iou": 0.1,
        },
    }


def _openai_responses_runtime_config_payload(*, base_url: str) -> dict[str, object]:
    return {
        "version": "runtime_integration_v1",
        "defaults_file": "configs/defaults.json",
        "thresholds_file": "configs/thresholds.example.yaml",
        "vlm": {
            "mode": "live",
            "provider": "openai_responses",
            "base_url": base_url,
            "endpoint_path": "/responses",
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-5.4",
            "timeout_seconds": 15,
            "max_retries": 0,
            "temperature": 0.0,
            "reasoning_effort": "none",
            "response_format": "json_object",
            "max_tokens": 256,
            "image_transport": "data_url",
            "system_prompt": "Return JSON only.",
        },
        "detector": {
            "mode": "proxy",
            "family": "ultralytics",
            "weights_path": "artifacts/models/yolo11n.pt",
            "device": "cpu",
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_det": 100,
            "refine_match_iou": 0.1,
            "missing_match_iou": 0.1,
        },
    }


def _codex_cli_runtime_config_payload() -> dict[str, object]:
    return {
        "version": "runtime_integration_v1",
        "defaults_file": "configs/defaults.json",
        "thresholds_file": "configs/thresholds.example.yaml",
        "vlm": {
            "mode": "live",
            "provider": "codex_cli",
            "base_url": None,
            "endpoint_path": None,
            "api_key_env": None,
            "command": "codex",
            "profile": "label-review",
            "model": None,
            "timeout_seconds": 15,
            "max_retries": 0,
            "temperature": None,
            "reasoning_effort": None,
            "response_format": "json_object",
            "max_tokens": None,
            "image_transport": "file_path",
            "sandbox": "read-only",
            "system_prompt": "Return JSON only.",
        },
        "detector": {
            "mode": "proxy",
            "family": "ultralytics",
            "weights_path": "artifacts/models/yolo11n.pt",
            "device": "cpu",
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_det": 100,
            "refine_match_iou": 0.1,
            "missing_match_iou": 0.1,
        },
    }


@contextmanager
def _mock_vlm_server(response_payload: dict[str, object]):
    captured_requests: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            captured_requests.append(
                {
                    "path": self.path,
                    "headers": dict(self.headers),
                    "payload": json.loads(body),
                }
            )
            encoded = json.dumps(response_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", captured_requests
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_build_vlm_requests_and_parse_reviews_are_deterministic(tmp_path) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    review_candidates = load_run_artifact(run_dir, "review_candidates")
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    class_map = load_run_artifact(run_dir, "class_map")
    risk_scores = load_run_artifact(run_dir, "risk_scores")
    rule_issues = load_run_artifact(run_dir, "rule_issues")

    requests = build_vlm_requests(
        review_candidates,
        normalized_annotations,
        image_index,
        class_map,
        risk_scores,
        rule_issues,
        model="gpt-5.4",
        decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
        image_decision_enum=["keep", "add_missing", "uncertain"],
    )
    reviews = parse_vlm_reviews(
        [
            {
                "request_id": requests[0]["request_id"],
                "response": {
                    "decision": "relabel",
                    "class_ok": False,
                    "box_ok": True,
                    "new_class_name": "dog",
                    "need_refine_box": False,
                    "need_add_missing": False,
                    "missing_candidates": [],
                    "reason": "outline matches dog better",
                    "reason_code": "VLM_RELABEL_DOG",
                    "confidence": 0.97,
                },
            }
        ],
        requests,
        class_map,
        decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
    )

    assert len(requests) == 1
    assert requests[0]["review_scope"] == "annotation"
    assert requests[0]["annotation_context"]["rule_issues"] == []
    assert requests[0]["image_level_context"] is None
    assert requests[0]["allowed_decisions"][1] == "relabel"
    assert reviews[0]["decision"] == "relabel"
    assert reviews[0]["review_scope"] == "annotation"
    assert reviews[0]["reason_code"] == "VLM_RELABEL_DOG"
    assert reviews[0]["metric_kind"] == "proxy"


def test_parse_vlm_reviews_rejects_invalid_enum(tmp_path) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    requests = build_vlm_requests(
        load_run_artifact(run_dir, "review_candidates"),
        load_run_artifact(run_dir, "normalized_annotations"),
        load_run_artifact(run_dir, "image_index"),
        load_run_artifact(run_dir, "class_map"),
        load_run_artifact(run_dir, "risk_scores"),
        load_run_artifact(run_dir, "rule_issues"),
        model="gpt-5.4",
        decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
        image_decision_enum=["keep", "add_missing", "uncertain"],
    )

    with pytest.raises(ValueError, match="allowed enum"):
        parse_vlm_reviews(
            [
                {
                    "request_id": requests[0]["request_id"],
                    "response": {
                        "decision": "explode",
                        "class_ok": True,
                        "box_ok": True,
                        "new_class_name": None,
                        "need_refine_box": False,
                        "need_add_missing": False,
                        "missing_candidates": [],
                        "reason": "bad response",
                        "reason_code": "VLM_BAD",
                        "confidence": 0.1,
                    },
                }
            ],
            requests,
            load_run_artifact(run_dir, "class_map"),
            decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
        )


def test_build_vlm_requests_support_image_level_review_scope(tmp_path) -> None:
    run_dir = build_risk_ready_zero_annotation_run(tmp_path)
    review_candidates = load_run_artifact(run_dir, "review_candidates")
    requests = build_vlm_requests(
        review_candidates,
        load_run_artifact(run_dir, "normalized_annotations"),
        load_run_artifact(run_dir, "image_index"),
        load_run_artifact(run_dir, "class_map"),
        load_run_artifact(run_dir, "risk_scores"),
        load_run_artifact(run_dir, "rule_issues"),
        model="gpt-5.4",
        decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
        image_decision_enum=["keep", "add_missing", "uncertain"],
    )
    reviews = parse_vlm_reviews(
        [
            {
                "request_id": requests[0]["request_id"],
                "response": {
                    "decision": "add_missing",
                    "class_ok": True,
                    "box_ok": True,
                    "new_class_name": None,
                    "need_refine_box": False,
                    "need_add_missing": True,
                    "missing_candidates": [
                        {
                            "class_name": "dog",
                            "bbox_xyxy": [55.0, 8.0, 90.0, 42.0],
                            "confidence": 0.94,
                            "reason": "a carton stack is visible even though the image has no prelabels",
                            "reason_code": "VLM_IMAGE_LEVEL_MISSING",
                        }
                    ],
                    "reason": "the image contains an unlabeled object",
                    "reason_code": "VLM_IMAGE_REVIEW_MISSING",
                    "confidence": 0.94,
                },
            }
        ],
        requests,
        load_run_artifact(run_dir, "class_map"),
        decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
    )

    assert len(requests) == 1
    assert requests[0]["review_scope"] == "image"
    assert requests[0]["ann_id"] is None
    assert requests[0]["annotation_context"] is None
    assert requests[0]["image_level_context"]["annotation_count"] == 0
    assert requests[0]["allowed_decisions"] == ["keep", "add_missing", "uncertain"]
    assert reviews[0]["review_scope"] == "image"
    assert reviews[0]["ann_id"] is None
    assert reviews[0]["missing_candidates"][0]["reason_code"] == "VLM_IMAGE_LEVEL_MISSING"


def test_resolve_codex_cli_command_falls_back_to_cmd_suffix(monkeypatch) -> None:
    resolved_codex = r"C:\Users\tester\AppData\Roaming\npm\codex.cmd"

    def fake_which(command: str) -> str | None:
        if command == "codex.cmd":
            return resolved_codex
        return None

    monkeypatch.setattr("yolo_label_validation.vlm.shutil.which", fake_which)

    assert _resolve_codex_cli_command("codex") == resolved_codex


def test_run_vlm_for_directory_writes_artifacts(tmp_path) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    responses_file = tmp_path / "responses.json"
    write_json(
        responses_file,
        [
            {
                "decision": "relabel",
                "class_ok": False,
                "box_ok": True,
                "new_class_name": "dog",
                "need_refine_box": False,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "outline matches dog better",
                "reason_code": "VLM_RELABEL_DOG",
                "confidence": 0.97,
            }
        ],
    )

    outputs = run_vlm_for_directory(
        run_dir,
        responses_file=responses_file,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )

    assert (run_dir / "vlm_requests.jsonl").exists()
    assert (run_dir / "vlm_raw_responses.jsonl").exists()
    assert (run_dir / "vlm_review.json").exists()
    assert len(outputs["vlm_requests"]) == 1
    assert outputs["vlm_review"][0]["new_class_name"] == "dog"


def test_cli_run_vlm_writes_review_outputs(tmp_path, capsys) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    responses_file = tmp_path / "responses.json"
    write_json(
        responses_file,
        [
            {
                "decision": "keep",
                "class_ok": True,
                "box_ok": True,
                "new_class_name": None,
                "need_refine_box": False,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "label and geometry are acceptable",
                "reason_code": "VLM_KEEP_OK",
                "confidence": 0.95,
            }
        ],
    )

    exit_code = main(
        [
            "run-vlm",
            "--run-dir",
            str(run_dir),
            "--responses-file",
            str(responses_file),
            "--defaults-file",
            str(ROOT / "configs" / "defaults.json"),
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["request_count"] == 1
    assert payload["review_count"] == 1
    assert (run_dir / "vlm_review.json").exists()


def test_run_vlm_for_directory_supports_live_http(tmp_path, monkeypatch) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    monkeypatch.setenv("TEST_VLM_API_KEY", "fixture-secret")
    server_response = {
        "id": "chatcmpl-test",
        "model": "mock-live-vlm",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "decision": "keep",
                            "class_ok": True,
                            "box_ok": True,
                            "new_class_name": None,
                            "need_refine_box": False,
                            "need_add_missing": False,
                            "missing_candidates": [],
                            "reason": "live endpoint accepted the current label",
                            "reason_code": "VLM_LIVE_KEEP",
                            "confidence": 0.98,
                        }
                    ),
                },
                "finish_reason": "stop",
            }
        ],
    }

    with _mock_vlm_server(server_response) as (base_url, captured_requests):
        outputs = run_vlm_for_directory(
            run_dir,
            defaults_file=ROOT / "configs" / "defaults.json",
            runtime_config_payload=_legacy_runtime_config_payload(base_url=base_url),
            overwrite=True,
        )

    assert len(captured_requests) == 1
    request_payload = captured_requests[0]["payload"]
    assert request_payload["model"] == "mock-live-vlm"
    assert captured_requests[0]["headers"]["Authorization"] == "Bearer fixture-secret"
    assert any(
        part["type"] == "image_url" and part["image_url"]["url"].startswith("data:image/png;base64,")
        for part in request_payload["messages"][1]["content"]
    )
    assert outputs["vlm_review"][0]["metric_kind"] == "measured"
    manifest = load_run_artifact(run_dir, "run_manifest")
    assert manifest["runtime_context"]["vlm"]["mode"] == "live"
    assert manifest["vlm_version"] == "mock-live-vlm"


def test_run_vlm_for_directory_supports_openai_responses(tmp_path, monkeypatch) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-openai-secret")
    response_json = json.dumps(
        {
            "decision": "keep",
            "class_ok": True,
            "box_ok": True,
            "new_class_name": None,
            "need_refine_box": False,
            "need_add_missing": False,
            "missing_candidates": [],
            "reason": "responses api accepted the current label",
            "reason_code": "OPENAI_RESPONSES_KEEP",
            "confidence": 0.99,
        }
    )
    server_response = {
        "id": "resp-test",
        "model": "gpt-5.4",
        "output_text": response_json,
        "output": [
            {
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": response_json,
                    }
                ],
            }
        ],
    }

    with _mock_vlm_server(server_response) as (base_url, captured_requests):
        outputs = run_vlm_for_directory(
            run_dir,
            defaults_file=ROOT / "configs" / "defaults.json",
            runtime_config_payload=_openai_responses_runtime_config_payload(base_url=base_url),
            overwrite=True,
        )

    assert len(captured_requests) == 1
    request_payload = captured_requests[0]["payload"]
    assert captured_requests[0]["path"] == "/responses"
    assert captured_requests[0]["headers"]["Authorization"] == "Bearer fixture-openai-secret"
    assert request_payload["model"] == "gpt-5.4"
    assert request_payload["text"]["format"]["type"] == "json_object"
    assert request_payload["reasoning"]["effort"] == "none"
    assert request_payload["input"][0]["content"][0]["type"] == "input_text"
    assert any(
        part["type"] == "input_image" and part["image_url"].startswith("data:image/png;base64,")
        for part in request_payload["input"][0]["content"]
    )
    assert outputs["vlm_review"][0]["reason_code"] == "OPENAI_RESPONSES_KEEP"
    assert outputs["vlm_review"][0]["metric_kind"] == "measured"
    manifest = load_run_artifact(run_dir, "run_manifest")
    assert manifest["runtime_context"]["vlm"]["provider"] == "openai_responses"
    assert manifest["runtime_context"]["vlm"]["reasoning_effort"] == "none"
    assert manifest["vlm_version"] == "gpt-5.4"


def test_run_vlm_for_directory_rejects_invalid_openai_responses_payload(tmp_path, monkeypatch) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-openai-secret")
    server_response = {
        "id": "resp-test",
        "model": "gpt-5.4",
        "output_text": "not-json",
        "output": [],
    }

    with _mock_vlm_server(server_response) as (base_url, _captured_requests):
        with pytest.raises(ValueError, match="invalid JSON VLM response"):
            run_vlm_for_directory(
                run_dir,
                defaults_file=ROOT / "configs" / "defaults.json",
                runtime_config_payload=_openai_responses_runtime_config_payload(base_url=base_url),
                overwrite=True,
            )


def test_run_vlm_for_directory_supports_codex_cli(tmp_path, monkeypatch) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    captured: dict[str, object] = {}
    resolved_codex = r"C:\Users\tester\AppData\Roaming\npm\codex.cmd"
    response_json = json.dumps(
        {
            "decision": "keep",
            "class_ok": True,
            "box_ok": True,
            "new_class_name": None,
            "need_refine_box": False,
            "need_add_missing": False,
            "missing_candidates": [],
            "reason": "codex cli accepted the current label",
            "reason_code": "CODEX_KEEP_OK",
            "confidence": 0.96,
        }
    )

    def fake_run(
        command: list[str],
        *,
        input: str,
        text: bool,
        capture_output: bool,
        timeout: float,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["input"] = input
        captured["timeout"] = timeout
        captured["text"] = text
        captured["capture_output"] = capture_output
        captured["check"] = check
        schema_path = Path(command[command.index("--output-schema") + 1])
        output_path = Path(command[command.index("--output-last-message") + 1])
        schema_payload = json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema_payload["properties"]["decision"]["enum"] == [
            "keep",
            "relabel",
            "refine",
            "delete",
            "add_missing",
            "uncertain",
        ]
        output_path.write_text(response_json, encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    def fake_which(command: str) -> str | None:
        if command == "codex":
            return resolved_codex
        return None

    monkeypatch.setattr("yolo_label_validation.vlm.shutil.which", fake_which)
    monkeypatch.setattr("yolo_label_validation.vlm.subprocess.run", fake_run)

    outputs = run_vlm_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        runtime_config_payload=_codex_cli_runtime_config_payload(),
        overwrite=True,
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert command[:2] == [resolved_codex, "exec"]
    assert "--image" in command
    assert "--output-schema" in command
    assert "--output-last-message" in command
    assert "--profile" in command
    assert "--model" not in command
    assert "--sandbox" in command
    assert "Return JSON only." in str(captured["input"])
    assert outputs["vlm_review"][0]["reason_code"] == "CODEX_KEEP_OK"
    assert outputs["vlm_review"][0]["metric_kind"] == "measured"
    manifest = load_run_artifact(run_dir, "run_manifest")
    assert manifest["runtime_context"]["vlm"]["provider"] == "codex_cli"
    assert manifest["runtime_context"]["vlm"]["command"] == "codex"
    assert manifest["runtime_context"]["vlm"]["profile"] == "label-review"
    assert manifest["vlm_version"] == "codex-profile:label-review"


def test_run_vlm_for_directory_rejects_invalid_codex_cli_payload(tmp_path, monkeypatch) -> None:
    run_dir = build_risk_ready_run(tmp_path)

    def fake_run(
        command: list[str],
        *,
        input: str,
        text: bool,
        capture_output: bool,
        timeout: float,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text("not-json", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("yolo_label_validation.vlm.subprocess.run", fake_run)

    with pytest.raises(ValueError, match="invalid JSON VLM response"):
        run_vlm_for_directory(
            run_dir,
            defaults_file=ROOT / "configs" / "defaults.json",
            runtime_config_payload=_codex_cli_runtime_config_payload(),
            overwrite=True,
        )
