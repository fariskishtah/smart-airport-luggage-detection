from __future__ import annotations

import csv
import json
import logging
import platform
import resource
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import cv2

# Ensure project root is accessible
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.counter import LineCounter, ZoneCounter
from src.detector import LuggageDetector
from src.tracker import tracks_from_result
from src.utils import choose_device, resolve_path, save_json
from src.visualization import draw_overlay

LOG = logging.getLogger("backend.inference")

MODEL_REGISTRY = {
    "yolo11n_coco": ROOT / "models/deployment/yolo11n_coco.pt",
    "yolo11n_finetuned": ROOT / "models/research/yolo11n_finetuned_best.pt",
    "yolo11s": ROOT / "models/research/yolo11s_finetuned_best.pt",
    "yolo11n_conservative": ROOT / "models/research/yolo11n_conservative_best.pt",
}


def _resolve_model_path(model_name: Optional[str]) -> Path:
    if model_name and model_name in MODEL_REGISTRY:
        p = MODEL_REGISTRY[model_name]
        if p.exists():
            return p
    # Fallback to local yolo11n.pt
    fallback = ROOT / "models/yolo11n.pt"
    if fallback.exists():
        return fallback
    return ROOT / "yolo11n.pt"


def run_video_analysis(
    input_path: Path,
    output_video_path: Path,
    mode: str = "counting",
    count_mode: str = "line",
    confidence: float = 0.25,
    iou: float = 0.50,
    line_start_norm: Optional[List[float]] = None,
    line_end_norm: Optional[List[float]] = None,
    zone_norm: Optional[List[List[float]]] = None,
    direction: str = "any",
    min_track_age: int = 3,
    tracker_name: str = "bytetrack",
    image_size: int = 640,
    model_name: str = "yolo11n_coco",
    device: str = "auto",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, Any]:
    """
    Execute end-to-end detection, tracking, and optional line/zone counting.
    Works for Mode A (detection & tracking) and Mode B (detection + tracking + counting).
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Input video does not exist: {input_path}")

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open video: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    events_dir = output_video_path.parent / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    # Resolve geometry
    line_start, line_end, zone_points = None, None, None
    counter = None

    if mode == "counting":
        if count_mode == "zone" and zone_norm and len(zone_norm) >= 3:
            zone_points = [(round(x * width), round(y * height)) for x, y in zone_norm]
            counter = ZoneCounter(zone_points, direction=direction if direction in ("any", "in", "out") else "any", min_track_age=min_track_age)
        else:
            s = line_start_norm or [0.55, 0.20]
            e = line_end_norm or [0.55, 0.92]
            line_start = (round(s[0] * width), round(s[1] * height))
            line_end = (round(e[0] * width), round(e[1] * height))
            counter = LineCounter(line_start, line_end, direction=direction if direction in ("any", "positive", "negative") else "any", deadband_px=8.0, min_track_age=min_track_age)

    # Initialize model
    model_path = _resolve_model_path(model_name)
    selected_device = choose_device(device)
    LOG.info("Initializing detector with model %s on %s", model_path, selected_device)
    detector = LuggageDetector(model_path, confidence, iou, image_size, selected_device)
    class_ids = detector.class_ids(["suitcase", "backpack", "handbag"])
    if not class_ids:
        class_ids = [0, 1, 2]

    # Tracker config
    tracker_config = ROOT / "configs/bytetrack_luggage.yaml" if tracker_name == "bytetrack" else "botsort.yaml"

    # Temporary uncompressed video writer
    raw_output_path = output_video_path.with_name(f"temp_raw_{output_video_path.name}")
    writer = cv2.VideoWriter(str(raw_output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not open VideoWriter for {raw_output_path}")

    processed_frames = 0
    start_time = time.perf_counter()
    total_inference_time = 0.0
    all_seen_track_ids = set()
    all_seen_classes = {}
    crossing_events = []

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            t0 = time.perf_counter()
            result = detector.track(frame, str(tracker_config), class_ids)
            total_inference_time += time.perf_counter() - t0
            tracks = tracks_from_result(result)

            for track in tracks:
                all_seen_track_ids.add(track.track_id)
                all_seen_classes[track.class_name] = all_seen_classes.get(track.class_name, 0) + 1

                if counter is not None:
                    anchor = track.bottom_center
                    event = counter.update(track.track_id, anchor, track.class_name)
                    if event:
                        ev_num = len(crossing_events) + 1
                        event_type = "zone_entry" if (count_mode == "zone" and event.direction == "in") else ("zone_exit" if count_mode == "zone" else "line_crossing")
                        record = {
                            "event_id": f"event_{ev_num:03d}",
                            "event_number": ev_num,
                            "frame": processed_frames,
                            "timestamp": round(processed_frames / fps, 3),
                            "track_id": event.track_id,
                            "class": event.class_name,
                            "class_name": event.class_name,
                            "confidence": round(track.confidence, 4),
                            "direction": event.direction,
                            "event_type": event_type,
                            "centroid_x": anchor[0],
                            "centroid_y": anchor[1],
                            "snapshot": ""
                        }
                        # Save evidence crop
                        x1, y1, x2, y2 = track.box
                        pad = 12
                        crop = frame[max(0, y1 - pad):min(height, y2 + pad), max(0, x1 - pad):min(width, x2 + pad)]
                        snapshot_file = events_dir / f"event_{ev_num:03d}.jpg"
                        if crop.size:
                            cv2.imwrite(str(snapshot_file), crop)
                            record["snapshot"] = f"events/{snapshot_file.name}"
                        crossing_events.append(record)

            # Draw HUD
            instant_fps = 1.0 / max(time.perf_counter() - t0, 1e-5)
            if counter is not None:
                draw_overlay(frame, tracks, counter, line_start, line_end, instant_fps, zone_points=zone_points)
            else:
                # Mode A: Tracking only display
                class DummyCounter:
                    total = len(all_seen_track_ids)
                    in_count = 0
                    out_count = 0
                    class_counts = {k: 1 for k in all_seen_classes}
                draw_overlay(frame, tracks, DummyCounter(), None, None, instant_fps, title="SMART LUGGAGE TRACKER")

            writer.write(frame)
            processed_frames += 1

            if progress_callback and total_frames > 0 and (processed_frames % 15 == 0 or processed_frames == total_frames):
                pct = min(0.1 + 0.75 * (processed_frames / total_frames), 0.85)
                progress_callback(pct, f"Processing frame {processed_frames:,} / {total_frames:,}")

    finally:
        cap.release()
        writer.release()

    elapsed = time.perf_counter() - start_time
    effective_fps = processed_frames / max(elapsed, 1e-9)

    # Encode to H.264
    if progress_callback:
        progress_callback(0.90, "Encoding browser-compatible H.264 MP4 video…")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg and raw_output_path.is_file():
        conversion = subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-i", str(raw_output_path),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-movflags", "+faststart", "-an",
            str(output_video_path)
        ], capture_output=True, text=True)

        if conversion.returncode == 0:
            raw_output_path.unlink(missing_ok=True)
        else:
            LOG.warning("FFmpeg conversion returned error: %s. Using raw output.", conversion.stderr)
            raw_output_path.replace(output_video_path)
    else:
        raw_output_path.replace(output_video_path)

    # Write events.csv
    csv_path = output_video_path.parent / "events.csv"
    fields = [
        "event_id", "frame", "timestamp", "track_id",
        "class", "confidence", "direction", "event_type",
        "centroid_x", "centroid_y", "snapshot"
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        w = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for ev in crossing_events:
            w.writerow(ev)

    if progress_callback:
        progress_callback(1.0, "Analysis complete!")

    if counter is not None:
        total_count = counter.total
        in_count = counter.in_count
        out_count = counter.out_count
        class_counts = counter.class_counts
    else:
        total_count = len(all_seen_track_ids)
        in_count = 0
        out_count = 0
        class_counts = {k: v for k, v in all_seen_classes.items()}

    return {
        "mode": mode,
        "count_mode": count_mode if mode == "counting" else "none",
        "frames": processed_frames,
        "source_fps": round(fps, 2),
        "elapsed_seconds": round(elapsed, 2),
        "processing_fps": round(effective_fps, 1),
        "average_latency_ms": round(1000 * total_inference_time / max(processed_frames, 1), 2),
        "total_count": total_count,
        "in_count": in_count,
        "out_count": out_count,
        "class_counts": class_counts,
        "events": crossing_events,
        "events_count": len(crossing_events),
        "video_width": width,
        "video_height": height,
        "model": model_name,
        "tracker": tracker_name,
    }
