import csv
import json
from pathlib import Path

import cv2
import numpy as np
import yaml

from src import inference_video
from src.tracker import Track


class _ScriptedDetector:
    """Deterministic detector stand-in; model inference is evaluated separately."""

    frame_index = 0

    def __init__(self, *args, **kwargs):
        type(self).frame_index = 0

    def class_ids(self, allowed_names):
        return [0]

    def track(self, frame, tracker_config, classes):
        index = type(self).frame_index
        type(self).frame_index += 1
        # The bottom-centre moves from above to below the horizontal line.
        bottom = [28, 36, 55, 66][index]
        return [Track(17, 0, "suitcase", 0.91, (25, bottom - 18, 45, bottom))]


def _make_video(path: Path):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (96, 72))
    assert writer.isOpened()
    for value in (25, 50, 75, 100):
        writer.write(np.full((72, 96, 3), value, dtype=np.uint8))
    writer.release()


def test_video_to_annotated_output_json_and_csv(tmp_path, monkeypatch):
    source = tmp_path / "input.mp4"
    output = tmp_path / "output.mp4"
    config_path = tmp_path / "config.yaml"
    _make_video(source)
    config_path.write_text(
        yaml.safe_dump(
            {
                "project": {"name": "integration-test"},
                "model": {
                    "path": "models/yolo11n.pt",
                    "confidence": 0.25,
                    "iou": 0.5,
                    "image_size": 96,
                    "allowed_classes": ["suitcase"],
                },
                "tracking": {"tracker": "bytetrack", "config": "bytetrack.yaml"},
                "counting": {
                    "mode": "line",
                    "line_start": [0.0, 0.5],
                    "line_end": [1.0, 0.5],
                    "coordinates": "normalized",
                    "anchor": "bottom_center",
                    "direction": "any",
                    "deadband_px": 2,
                    "min_track_age": 2,
                },
                "video": {"show_fps": True},
                "runtime": {"device": "cpu", "save_events": True, "save_snapshots": True},
            }
        )
    )
    monkeypatch.setattr(inference_video, "LuggageDetector", _ScriptedDetector)
    monkeypatch.setattr(inference_video, "tracks_from_result", lambda result: result)

    stats = inference_video.process_video(source, output, config_path)

    assert output.is_file() and output.stat().st_size > 0
    assert stats["frames"] == 4
    assert stats["total_count"] == 1
    assert stats["class_counts"] == {"suitcase": 1}
    saved = json.loads(output.with_suffix(".json").read_text())
    assert saved["crossing_events"][0]["track_id"] == 17
    with (tmp_path / "events.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1 and rows[0]["class_name"] == "suitcase"
    assert (tmp_path / "events" / "event_001.jpg").is_file()


def test_nonexistent_video_raises(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        inference_video.process_video(tmp_path / "nonexistent.mp4", tmp_path / "out.mp4")


def test_invalid_zone_points_raises(tmp_path):
    import pytest
    source = tmp_path / "input.mp4"
    output = tmp_path / "output.mp4"
    config_path = tmp_path / "config.yaml"
    _make_video(source)
    config_path.write_text(
        yaml.safe_dump(
            {
                "model": {"path": "models/yolo11n.pt", "confidence": 0.25, "iou": 0.5, "image_size": 96, "allowed_classes": ["suitcase"]},
                "tracking": {"tracker": "bytetrack", "config": "bytetrack.yaml"},
                "counting": {"mode": "zone", "zone": [[0.1, 0.1], [0.5, 0.5]]},  # only 2 points
                "video": {"show_fps": False},
                "runtime": {"device": "cpu"},
            }
        )
    )
    with pytest.raises(ValueError, match="at least three"):
        inference_video.process_video(source, output, config_path)

