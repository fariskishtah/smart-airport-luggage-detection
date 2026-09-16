from __future__ import annotations

from pathlib import Path


class LuggageDetector:
    def __init__(self, model_path: str | Path, confidence: float, iou: float, image_size: int, device: str):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("Ultralytics is missing. Run: pip install -r requirements.txt") from exc
        self.model = YOLO(str(model_path))
        self.confidence = confidence
        self.iou = iou
        self.image_size = image_size
        self.device = device
        self.names = self.model.names

    def track(self, frame, tracker_config: str | Path, classes: list[int]):
        return self.model.track(
            frame,
            persist=True,
            tracker=str(tracker_config),
            conf=self.confidence,
            iou=self.iou,
            imgsz=self.image_size,
            classes=classes,
            device=self.device,
            verbose=False,
        )[0]

    def class_ids(self, allowed_names: list[str]) -> list[int]:
        allowed = {name.lower() for name in allowed_names}
        return [idx for idx, name in self.names.items() if name.lower() in allowed]

