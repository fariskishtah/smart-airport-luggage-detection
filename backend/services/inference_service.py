from __future__ import annotations

import csv
import gc
import json
import logging
import os
import platform
import resource
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import cv2
import torch

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

MAX_CANVAS_WIDTH = 1920
MAX_CANVAS_HEIGHT = 1080


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
    confidence: float = 0.20,
    iou: float = 0.50,
    line_start_norm: Optional[List[float]] = None,
    line_end_norm: Optional[List[float]] = None,
    zone_norm: Optional[List[List[float]]] = None,
    direction: str = "any",
    min_track_age: int = 2,
    tracker_name: str = "bytetrack",
    image_size: int = 640,
    model_name: str = "yolo11n_coco",
    device: str = "auto",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, Any]:
    """
    Memory-efficient stream-based video analysis pipeline.
    Streams frames directly into FFmpeg or VideoWriter to avoid intermediate raw video files
    and avoid multithreaded encoding memory spikes.
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Input video does not exist: {input_path}")

    # Limit PyTorch CPU threads to bound memory allocation on cloud multi-core nodes
    selected_device = choose_device(device)
    if selected_device == "cpu":
        try:
            if torch.get_num_threads() > 2:
                torch.set_num_threads(2)
        except Exception:
            pass

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open video: {input_path}")

    raw_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    raw_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Guard against 0 or invalid frame count
    if total_frames <= 0:
        total_frames = 1

    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    events_dir = output_video_path.parent / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    # Resolution scaling for memory bounding on high-res uploads (1440p / 4K)
    scale = 1.0
    if raw_width > MAX_CANVAS_WIDTH or raw_height > MAX_CANVAS_HEIGHT:
        scale = min(MAX_CANVAS_WIDTH / raw_width, MAX_CANVAS_HEIGHT / raw_height)
        out_width = int(round(raw_width * scale))
        out_height = int(round(raw_height * scale))
        LOG.info("Scaling input video (%dx%d) to (%dx%d) for safe cloud memory", raw_width, raw_height, out_width, out_height)
    else:
        out_width = raw_width
        out_height = raw_height

    # Ensure even dimensions for H.264 yuv420p
    out_width = out_width if out_width % 2 == 0 else out_width - 1
    out_height = out_height if out_height % 2 == 0 else out_height - 1

    # Resolve geometry in canvas coordinates
    line_start, line_end, zone_points = None, None, None
    counter = None

    if mode == "counting":
        if count_mode == "zone" and zone_norm and len(zone_norm) >= 3:
            zone_points = [(round(x * out_width), round(y * out_height)) for x, y in zone_norm]
            counter = ZoneCounter(zone_points, direction=direction if direction in ("any", "in", "out") else "any", min_track_age=min_track_age)
        else:
            s = line_start_norm or [0.55, 0.20]
            e = line_end_norm or [0.55, 0.92]
            line_start = (round(s[0] * out_width), round(s[1] * out_height))
            line_end = (round(e[0] * out_width), round(e[1] * out_height))
            counter = LineCounter(line_start, line_end, direction=direction if direction in ("any", "positive", "negative") else "any", deadband_px=3.0, min_track_age=min_track_age)

    # Initialize model with bounded imgsz
    effective_imgsz = min(image_size, 640)
    model_path = _resolve_model_path(model_name)
    LOG.info("Initializing detector with model %s on %s (imgsz=%d)", model_path, selected_device, effective_imgsz)
    detector = LuggageDetector(model_path, confidence, iou, effective_imgsz, selected_device)
    class_ids = detector.class_ids(["suitcase", "backpack", "handbag"])
    if not class_ids:
        class_ids = [0, 1, 2]

    # Tracker config
    tracker_config = ROOT / "configs/bytetrack_luggage.yaml" if tracker_name == "bytetrack" else "botsort.yaml"

    # Initialize real-time streaming FFmpeg encoder with single thread to minimize RAM
    ffmpeg_bin = shutil.which("ffmpeg")
    ffmpeg_proc: Optional[subprocess.Popen] = None
    cv_writer: Optional[cv2.VideoWriter] = None
    raw_fallback_path: Optional[Path] = None

    if ffmpeg_bin:
        ffmpeg_cmd = [
            ffmpeg_bin,
            "-y",
            "-loglevel", "error",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{out_width}x{out_height}",
            "-pix_fmt", "bgr24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "24",
            "-threads", "1",  # Strictly 1 encoding thread to bound memory to <35MB
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-an",
            str(output_video_path),
        ]
        try:
            ffmpeg_proc = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            LOG.info("Initialized real-time FFmpeg pipe encoder (threads=1, ultrafast)")
        except Exception as exc:
            LOG.warning("Could not launch FFmpeg pipe (%s). Falling back to OpenCV VideoWriter.", exc)
            ffmpeg_proc = None

    if ffmpeg_proc is None:
        raw_fallback_path = output_video_path.with_name(f"temp_raw_{output_video_path.name}")
        cv_writer = cv2.VideoWriter(str(raw_fallback_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (out_width, out_height))
        if not cv_writer.isOpened():
            cap.release()
            raise RuntimeError(f"Could not open VideoWriter for {raw_fallback_path}")

    processed_frames = 0
    start_time = time.perf_counter()
    total_inference_time = 0.0
    all_seen_track_ids = set()
    all_seen_classes = {}
    crossing_events = []

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break

            # Rescale frame if canvas scaling is active
            if scale < 1.0:
                frame = cv2.resize(frame, (out_width, out_height), interpolation=cv2.INTER_AREA)

            t0 = time.perf_counter()
            with torch.inference_mode():
                result = detector.track(frame, str(tracker_config), class_ids)
            total_inference_time += time.perf_counter() - t0

            # Convert result to lightweight primitive dataclasses
            tracks = tracks_from_result(result)
            del result  # Immediately discard the heavyweight Ultralytics Result object

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
                        crop = frame[max(0, y1 - pad):min(out_height, y2 + pad), max(0, x1 - pad):min(out_width, x2 + pad)]
                        snapshot_file = events_dir / f"event_{ev_num:03d}.jpg"
                        if crop.size:
                            cv2.imwrite(str(snapshot_file), crop)
                            record["snapshot"] = f"events/{snapshot_file.name}"
                        crossing_events.append(record)
                        del crop

            # Draw HUD directly on frame
            instant_fps = 1.0 / max(time.perf_counter() - t0, 1e-5)
            if counter is not None:
                draw_overlay(frame, tracks, counter, line_start, line_end, instant_fps, zone_points=zone_points)
            else:
                class DummyCounter:
                    total = len(all_seen_track_ids)
                    in_count = 0
                    out_count = 0
                    class_counts = {k: 1 for k in all_seen_classes}
                draw_overlay(frame, tracks, DummyCounter(), None, None, instant_fps, title="SMART LUGGAGE TRACKER")

            # Stream frame to encoder
            if ffmpeg_proc and ffmpeg_proc.stdin:
                try:
                    ffmpeg_proc.stdin.write(frame.tobytes())
                except (BrokenPipeError, IOError):
                    LOG.warning("FFmpeg pipe broke unexpectedly during frame %d", processed_frames)
            elif cv_writer:
                cv_writer.write(frame)

            del tracks
            del frame
            processed_frames += 1

            # Periodic garbage collection to maintain lean memory footprint
            if processed_frames % 45 == 0:
                gc.collect()

            if progress_callback and total_frames > 0 and (processed_frames % 15 == 0 or processed_frames == total_frames):
                pct = min(0.10 + 0.88 * (processed_frames / total_frames), 0.98)
                progress_callback(pct, f"Processing frame {processed_frames:,} / {total_frames:,}")

    finally:
        cap.release()
        if ffmpeg_proc:
            if ffmpeg_proc.stdin:
                try:
                    ffmpeg_proc.stdin.close()
                except Exception:
                    pass
            try:
                ffmpeg_proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                ffmpeg_proc.kill()
        if cv_writer:
            cv_writer.release()
        gc.collect()

    elapsed = time.perf_counter() - start_time
    effective_fps = processed_frames / max(elapsed, 1e-9)

    # If OpenCV fallback writer was used, transcode using low-thread FFmpeg
    if raw_fallback_path and raw_fallback_path.is_file():
        if progress_callback:
            progress_callback(0.95, "Finalizing H.264 video…")
        if ffmpeg_bin:
            conv = subprocess.run([
                ffmpeg_bin, "-y", "-loglevel", "error",
                "-threads", "1",
                "-i", str(raw_fallback_path),
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24",
                "-movflags", "+faststart", "-an",
                str(output_video_path)
            ], capture_output=True, text=True)
            if conv.returncode == 0:
                raw_fallback_path.unlink(missing_ok=True)
            else:
                raw_fallback_path.replace(output_video_path)
        else:
            raw_fallback_path.replace(output_video_path)

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
        "counted_track_ids": sorted(counter.counted_track_ids) if counter is not None else sorted(all_seen_track_ids),
        "events": crossing_events,
        "events_count": len(crossing_events),
        "video_width": out_width,
        "video_height": out_height,
        "model": model_name,
        "tracker": tracker_name,
    }
