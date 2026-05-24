import base64
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, cast
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import cv2
import numpy as np
from flask import Flask, jsonify, request, send_from_directory


DEFAULT_MODEL_REF = os.getenv("YOLO_MODEL_REF", "yolov8n.pt")
DEFAULT_CONFIDENCE = float(os.getenv("YOLO_FACE_CONF", "0.35"))
DEFAULT_IOU = float(os.getenv("YOLO_FACE_IOU", "0.45"))
MODELS_DIR = Path("models")

MODEL_OPTIONS = {
    "ultralytics_yolov8n": {
        "label": "Ultralytics YOLOv8n (quick start)",
        "type": "model_name",
        "value": "yolov8n.pt",
        "notes": "Auto-download by Ultralytics. Great for a guaranteed working demo.",
    },
    "ultralytics_yolo11n": {
        "label": "Ultralytics YOLO11n (newer, lightweight)",
        "type": "model_name",
        "value": "yolo11n.pt",
        "notes": "Auto-download by Ultralytics.",
    },
    "local_face_model": {
        "label": "Local Face Model (models/yolov8n-face.pt)",
        "type": "local_path",
        "value": "models/yolov8n-face.pt",
        "notes": "Use this for actual face-specific detection.",
    },
    "custom_url": {
        "label": "Custom URL Download",
        "type": "custom_url",
        "value": "",
        "notes": "Paste a direct .pt download URL and apply.",
    },
}


@dataclass
class ModelStatus:
    loaded: bool
    message: str


class Detector:
    def __init__(self, model_ref: str) -> None:
        self.model_source = model_ref
        self.model_obj = None
        self.status = ModelStatus(False, "Model not loaded yet")

    def set_model(self, model_ref: str) -> None:
        self.model_source = model_ref
        self.model_obj = None
        self.status = ModelStatus(False, f"Model switched to {model_ref}; reload pending")

    def _looks_like_path(self, ref: str) -> bool:
        return any(sep in ref for sep in ("/", "\\"))

    def load(self) -> None:
        if self.model_obj is not None:
            return

        if self._looks_like_path(self.model_source) and not os.path.exists(self.model_source):
            self.status = ModelStatus(
                False,
                (
                    f"Model file not found at {self.model_source}. "
                    "Use Model Provider in browser to select/download a model."
                ),
            )
            return

        try:
            from ultralytics import YOLO

            # For names like yolov8n.pt, Ultralytics auto-downloads the weights.
            self.model_obj = YOLO(self.model_source)
            self.status = ModelStatus(True, f"Loaded model: {self.model_source}")
        except Exception as exc:
            self.status = ModelStatus(False, f"Failed to load model: {exc}")

    def detect(
        self,
        frame_bgr: np.ndarray,
        confidence: float,
        iou_threshold: float,
        class_ids: list[int] | None = None,
    ) -> tuple[list[dict[str, Any]], float]:
        self.load()
        if self.model_obj is None:
            raise RuntimeError(self.status.message)

        start = time.perf_counter()
        results = cast(
            list[Any],
            self.model_obj(frame_bgr, conf=confidence, iou=iou_threshold, imgsz=640, verbose=False),
        )
        inference_ms = (time.perf_counter() - start) * 1000.0

        h, w = frame_bgr.shape[:2]
        boxes_out: list[dict[str, Any]] = []
        allowed_classes = set(class_ids) if class_ids else None

        first_result = results[0] if results else None
        if first_result is None:
            return boxes_out, inference_ms

        boxes = getattr(first_result, "boxes", None)
        if boxes is None:
            return boxes_out, inference_ms

        class_names = getattr(first_result, "names", {}) or {}
        class_names = cast(dict[int, str], class_names)

        for box in boxes:
            xyxy = getattr(box, "xyxy", None)
            box_conf = getattr(box, "conf", None)
            box_cls = getattr(box, "cls", None)
            if xyxy is None:
                continue

            x1, y1, x2, y2 = xyxy[0].tolist()
            score = float(box_conf[0]) if box_conf is not None else 0.0
            cls_id = int(box_cls[0]) if box_cls is not None else 0

            if allowed_classes is not None and cls_id not in allowed_classes:
                continue

            boxes_out.append(
                {
                    "left": max(0, min(w, int(x1))),
                    "top": max(0, min(h, int(y1))),
                    "right": max(0, min(w, int(x2))),
                    "bottom": max(0, min(h, int(y2))),
                    "score": score,
                    "label_id": cls_id,
                    "label": str(class_names.get(cls_id, f"class_{cls_id}")),
                }
            )

        return boxes_out, inference_ms


def _clamp_float(value: Any, default: float, min_value: float, max_value: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(min_value, min(max_value, parsed))


def _read_class_ids(value: Any) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, dict)):
        return None

    cleaned: list[int] = []
    for item in cast(Iterable[Any], value):
        try:
            cleaned.append(int(item))
        except (TypeError, ValueError):
            continue

    return cleaned or None


def _download_model(url: str, filename: str | None = None) -> str:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP/HTTPS URLs are supported")

    inferred_name = Path(parsed.path).name or "downloaded_model.pt"
    target_name = filename.strip() if filename else inferred_name
    target_name = target_name.replace("..", "_").replace("/", "_").replace("\\", "_")
    if not target_name.endswith(".pt"):
        target_name = f"{target_name}.pt"

    target_path = MODELS_DIR / target_name

    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=120) as response, open(target_path, "wb") as out_file:
        out_file.write(response.read())

    return str(target_path)


def _benchmark_ms(matrix_size: int = 256, iterations: int = 3) -> float:
    data = np.random.rand(matrix_size, matrix_size).astype(np.float32)
    start = time.perf_counter()
    for _ in range(iterations):
        _ = data @ data
    elapsed = (time.perf_counter() - start) * 1000.0
    return elapsed / max(iterations, 1)


def _auto_tuning_profile() -> dict[str, Any]:
    cpu_count = os.cpu_count() or 1
    try:
        bench_ms = _benchmark_ms()
    except Exception:
        bench_ms = 999.0

    if cpu_count >= 8 and bench_ms < 18:
        tier = "high"
        confidence = 0.30
        iou = 0.45
    elif cpu_count >= 4 and bench_ms < 35:
        tier = "medium"
        confidence = 0.40
        iou = 0.50
    else:
        tier = "low"
        confidence = 0.50
        iou = 0.55

    return {
        "tier": tier,
        "cpu_count": cpu_count,
        "bench_ms": round(bench_ms, 2),
        "confidence": confidence,
        "iou": iou,
    }


app = Flask(__name__, static_folder="web", static_url_path="")
detector = Detector(DEFAULT_MODEL_REF)
AUTO_TUNING = _auto_tuning_profile()

# How it works (short version):
# - Browser sends a JPEG data URL to /detect.
# - Server decodes it, runs the YOLO model, returns simplified boxes.
# - The frontend draws those boxes and shows basic timing stats.


@app.get("/")
def index():
    return send_from_directory("web", "index.html")


@app.get("/health")
def health():
    detector.load()
    return jsonify(
        {
            "ok": detector.status.loaded,
            "message": detector.status.message,
            "model": detector.model_source,
            "auto_tune": AUTO_TUNING,
        }
    )


@app.get("/model/providers")
def model_providers():
    items = [{"id": key, **value} for key, value in MODEL_OPTIONS.items()]
    return jsonify({"ok": True, "providers": items, "current_model": detector.model_source})


@app.post("/model/select")
def model_select():
    payload = cast(dict[str, Any], request.get_json(silent=True) or {})
    provider_id = str(payload.get("provider", "")).strip()

    if provider_id not in MODEL_OPTIONS:
        return jsonify({"ok": False, "error": "Unknown provider"}), 400

    provider = MODEL_OPTIONS[provider_id]
    provider_type = provider["type"]

    try:
        if provider_type == "model_name":
            detector.set_model(provider["value"])
        elif provider_type == "local_path":
            detector.set_model(provider["value"])
        elif provider_type == "custom_url":
            custom_url = str(payload.get("custom_url", "")).strip()
            filename = str(payload.get("filename", "")).strip() or None
            if not custom_url:
                return jsonify({"ok": False, "error": "custom_url is required"}), 400
            local_path = _download_model(custom_url, filename)
            detector.set_model(local_path)
        else:
            return jsonify({"ok": False, "error": "Unsupported provider type"}), 400

        detector.load()
        return jsonify(
            {
                "ok": detector.status.loaded,
                "message": detector.status.message,
                "model": detector.model_source,
            }
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.post("/detect")
def detect_route():
    payload = cast(dict[str, Any], request.get_json(silent=True) or {})
    image_data_url = payload.get("image")

    if not image_data_url or not isinstance(image_data_url, str):
        return jsonify({"ok": False, "error": "Missing image data URL"}), 400

    auto_tune = bool(payload.get("auto_tune"))
    if auto_tune:
        confidence = float(AUTO_TUNING["confidence"])
        iou_threshold = float(AUTO_TUNING["iou"])
    else:
        confidence = _clamp_float(payload.get("conf"), DEFAULT_CONFIDENCE, 0.01, 0.99)
        iou_threshold = _clamp_float(payload.get("iou"), DEFAULT_IOU, 0.01, 0.99)
    class_ids = _read_class_ids(payload.get("class_ids"))

    try:
        b64_data = image_data_url.split(",", 1)[1] if "," in image_data_url else image_data_url
        img_bytes = base64.b64decode(b64_data)
        buffer = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"ok": False, "error": "Invalid image payload"}), 400

        boxes, inference_ms = detector.detect(
            frame,
            confidence=confidence,
            iou_threshold=iou_threshold,
            class_ids=class_ids,
        )
        return jsonify({"ok": True, "detections": boxes, "latency_ms": inference_ms})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
