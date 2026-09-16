from __future__ import annotations

import argparse
import csv
import logging
import platform
import resource
import shutil
import subprocess
import time
from pathlib import Path

import cv2

try:
    from .counter import LineCounter, ZoneCounter
    from .detector import LuggageDetector
    from .tracker import tracks_from_result
    from .utils import ROOT, choose_device, load_config, resolve_path, save_json
    from .visualization import draw_overlay
except ImportError:
    from counter import LineCounter, ZoneCounter
    from detector import LuggageDetector
    from tracker import tracks_from_result
    from utils import ROOT, choose_device, load_config, resolve_path, save_json
    from visualization import draw_overlay

LOG = logging.getLogger("luggage.inference")


def _line_points(config, width: int, height: int):
    start, end = config["line_start"], config["line_end"]
    if config.get("coordinates", "pixels") == "normalized":
        start = (round(start[0] * width), round(start[1] * height))
        end = (round(end[0] * width), round(end[1] * height))
    return tuple(map(int, start)), tuple(map(int, end))


def _portable_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _deep_update(base: dict, changes: dict | None) -> dict:
    for key, value in (changes or {}).items():
        if isinstance(value, dict) and isinstance(base.get(key), dict): _deep_update(base[key], value)
        else: base[key] = value
    return base


def process_video(source: str | Path, output: str | Path, config_path: str | Path = ROOT / "configs/config.yaml", display: bool = False, overrides: dict | None = None, progress_callback=None):
    config = _deep_update(load_config(config_path), overrides)
    source, output = resolve_path(source), resolve_path(output)
    if not source.is_file():
        raise FileNotFoundError(f"Input video not found: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open the video (path or codec issue): {source}")
    width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    mode = config["counting"].get("mode", "line")
    line_start, line_end, zone_points = None, None, None
    if mode == "zone":
        raw_zone = config["counting"].get("zone", [])
        zone_points = [(round(x * width), round(y * height)) for x, y in raw_zone] if config["counting"].get("coordinates") == "normalized" else [tuple(map(int, p)) for p in raw_zone]
        if len(zone_points) < 3: raise ValueError("Zone mode requires at least three polygon points")
        counter = ZoneCounter(zone_points, config["counting"].get("direction", "any"), config["counting"].get("min_track_age", 2))
    else:
        line_start, line_end = _line_points(config["counting"], width, height)
        counter = LineCounter(line_start, line_end, config["counting"].get("direction", "any"), config["counting"].get("deadband_px", 6), config["counting"].get("min_track_age", 2))
    model_path = resolve_path(config["model"]["path"])
    if not model_path.exists() and model_path.name not in {"yolo11n.pt", "yolov8n.pt"}:
        raise FileNotFoundError(f"Model weights not found: {model_path}")
    model_source = model_path if model_path.exists() else model_path.name
    selected_device = choose_device(config["runtime"].get("device", "auto"))
    LOG.info("Selected computation device: %s (requested: %s)", selected_device, config["runtime"].get("device", "auto"))
    detector = LuggageDetector(model_source, config["model"]["confidence"], config["model"]["iou"], config["model"]["image_size"], selected_device)
    class_ids = detector.class_ids(config["model"]["allowed_classes"])
    if not class_ids:
        raise ValueError("None of the configured luggage classes exist in the model label map")
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), source_fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Could not create output video: {output}")
    processed, started, smoothed_fps, inference_seconds = 0, time.perf_counter(), 0.0, 0.0
    crossing_events = []
    event_directory = output.parent / "events"
    if config["runtime"].get("save_snapshots", True): event_directory.mkdir(parents=True, exist_ok=True)
    tracker_candidate = resolve_path(config["tracking"]["config"])
    tracker_config = tracker_candidate if tracker_candidate.exists() else Path(config["tracking"]["config"]).name
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            tick = time.perf_counter()
            inference_started = time.perf_counter()
            result = detector.track(frame, tracker_config, class_ids)
            inference_seconds += time.perf_counter() - inference_started
            tracks = tracks_from_result(result)
            for track in tracks:
                anchor = track.bottom_center if config["counting"].get("anchor") == "bottom_center" else track.center
                event = counter.update(track.track_id, anchor, track.class_name)
                if event:
                    event_type = "zone_entry" if (mode == "zone" and event.direction == "in") else ("zone_exit" if mode == "zone" else "line_crossing")
                    ev_idx = len(crossing_events) + 1
                    record = {
                        "event_id": f"event_{ev_idx:03d}",
                        "event_number": ev_idx,
                        "video": _portable_path(source),
                        "frame": processed,
                        "timestamp": round(processed / source_fps, 3),
                        "timestamp_seconds": round(processed / source_fps, 3),
                        "track_id": event.track_id,
                        "class": event.class_name,
                        "class_name": event.class_name,
                        "confidence": round(track.confidence, 4),
                        "direction": event.direction,
                        "event_type": event_type,
                        "centroid_x": anchor[0],
                        "centroid_y": anchor[1],
                        "model": _portable_path(model_path),
                        "tracker": str(config["tracking"].get("tracker", "bytetrack")),
                        "snapshot": ""
                    }
                    if config["runtime"].get("save_snapshots", True):
                        x1, y1, x2, y2 = track.box; pad = 12
                        crop = frame[max(0,y1-pad):min(height,y2+pad), max(0,x1-pad):min(width,x2+pad)]
                        snapshot = event_directory / f"event_{ev_idx:03d}.jpg"
                        if crop.size:
                            cv2.imwrite(str(snapshot), crop)
                            record["snapshot"] = _portable_path(snapshot)
                    crossing_events.append(record)
            instant = 1.0 / max(time.perf_counter() - tick, 1e-6)
            smoothed_fps = instant if processed == 0 else .9 * smoothed_fps + .1 * instant
            draw_overlay(frame, tracks, counter, line_start, line_end, smoothed_fps if config["video"].get("show_fps") else None, zone_points=zone_points)
            writer.write(frame)
            processed += 1
            if progress_callback and (processed % 10 == 0 or processed == frame_count): progress_callback(processed, frame_count)
            if display:
                cv2.imshow("Smart Airport Luggage Detection", frame)
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    break
    finally:
        cap.release()
        writer.release()
        if display:
            cv2.destroyAllWindows()
    elapsed = time.perf_counter() - started
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg and processed:
        browser_output = output.with_name(f"{output.stem}.h264{output.suffix}")
        conversion = subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(output), "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-movflags", "+faststart", "-an", str(browser_output)], capture_output=True, text=True)
        if conversion.returncode == 0:
            browser_output.replace(output)
        else:
            browser_output.unlink(missing_ok=True)
            LOG.warning("FFmpeg H.264 conversion failed; retaining the OpenCV output: %s", conversion.stderr.strip())
    max_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_memory_mb = max_rss / (1024 * 1024) if platform.system() == "Darwin" else max_rss / 1024
    stats = {
        "source": _portable_path(source),
        "output": _portable_path(output),
        "frames": processed,
        "source_frames": frame_count,
        "elapsed_seconds": round(elapsed, 3),
        "processing_fps": round(processed / max(elapsed, 1e-9), 3),
        "average_inference_latency_ms": round(1000 * inference_seconds / max(processed, 1), 3),
        "peak_process_memory_mb": round(peak_memory_mb, 1),
        "model": _portable_path(model_path),
        "tracker": str(config["tracking"].get("tracker", "bytetrack")),
        "counting_mode": mode,
        "total_count": counter.total,
        "in_count": counter.in_count,
        "out_count": counter.out_count,
        "class_counts": counter.class_counts,
        "counted_track_ids": sorted(counter.counted_track_ids),
        "crossing_events": crossing_events
    }
    save_json(output.with_suffix(".json"), stats)
    if config["runtime"].get("save_events", True):
        csv_path = output.parent / "events.csv"
        fields = [
            "event_id", "video", "frame", "timestamp", "track_id",
            "class", "class_name", "confidence", "direction", "event_type",
            "centroid_x", "centroid_y", "model", "tracker", "snapshot"
        ]
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer_csv = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer_csv.writeheader()
            for event in crossing_events:
                writer_csv.writerow(event)
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Smart Airport Luggage Detection, Tracking and Counting System CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--source", default=None, help="Path to input video file")
    parser.add_argument("--output", default=None, help="Path to save annotated output MP4 video")
    parser.add_argument("--config", default=str(ROOT / "configs/config.yaml"), help="Path to YAML configuration file")
    parser.add_argument("--model", default=None, help="Override detector model checkpoint path (e.g., models/deployment/yolo11n_coco.pt)")
    parser.add_argument("--tracker", choices=["bytetrack", "botsort"], default=None, help="Multi-object tracking algorithm")
    parser.add_argument("--count-mode", "--mode", dest="count_mode", choices=["line", "zone"], default=None, help="Counting geometry mode (line or zone)")
    parser.add_argument("--conf", type=float, default=None, help="Confidence threshold (0.05 - 1.0)")
    parser.add_argument("--iou", type=float, default=None, help="NMS IoU threshold (0.1 - 1.0)")
    parser.add_argument("--direction", choices=["any", "in", "out", "positive", "negative"], default=None, help="Direction filter")
    parser.add_argument("--device", default=None, help="Computation device override (auto, mps, cpu, 0)")
    parser.add_argument("--min-age", type=int, default=None, help="Minimum track age in frames before counting")
    parser.add_argument("--image-size", type=int, default=None, help="Inference image size (e.g. 512, 640)")
    parser.add_argument("--display", action="store_true", help="Display live OpenCV window during processing")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    cfg = load_config(args.config)
    source = args.source or cfg["video"]["input"]
    output = args.output or cfg["video"]["output"]
    try:
        overrides = {}
        if args.model: overrides.setdefault("model", {})["path"] = args.model
        if args.conf is not None: overrides.setdefault("model", {})["confidence"] = args.conf
        if args.iou is not None: overrides.setdefault("model", {})["iou"] = args.iou
        if args.image_size is not None: overrides.setdefault("model", {})["image_size"] = args.image_size
        if args.tracker:
            overrides.setdefault("tracking", {})["tracker"] = args.tracker
            overrides["tracking"]["config"] = "configs/bytetrack_luggage.yaml" if args.tracker == "bytetrack" else "botsort.yaml"
        if args.count_mode: overrides.setdefault("counting", {})["mode"] = args.count_mode
        if args.direction: overrides.setdefault("counting", {})["direction"] = args.direction
        if args.min_age is not None: overrides.setdefault("counting", {})["min_track_age"] = args.min_age
        if args.device: overrides.setdefault("runtime", {})["device"] = args.device

        stats = process_video(source, output, args.config, args.display, overrides=overrides)
        LOG.info("Processing complete. Total unique luggage counted: %d (IN: %d, OUT: %d)", stats["total_count"], stats["in_count"], stats["out_count"])
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
