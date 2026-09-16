import argparse
import tempfile
from pathlib import Path

import cv2

from counter import LineCounter
from detector import LuggageDetector
from tracker import tracks_from_result
from utils import ROOT, choose_device, load_config, resolve_path
from visualization import draw_overlay


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--config", default=str(ROOT / "configs/config.yaml"))
    args = parser.parse_args()
    cfg = load_config(args.config)
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        parser.exit(2, f"error: camera {args.camera} is unavailable\n")
    width, height = int(cap.get(3)), int(cap.get(4))
    start = tuple(round(v * d) for v, d in zip(cfg["counting"]["line_start"], (width, height)))
    end = tuple(round(v * d) for v, d in zip(cfg["counting"]["line_end"], (width, height)))
    counter = LineCounter(start, end, cfg["counting"]["direction"], cfg["counting"]["deadband_px"], cfg["counting"]["min_track_age"])
    detector = LuggageDetector(resolve_path(cfg["model"]["path"]), cfg["model"]["confidence"], cfg["model"]["iou"], cfg["model"]["image_size"], choose_device(cfg["runtime"]["device"]))
    ids = detector.class_ids(cfg["model"]["allowed_classes"])
    while True:
        ok, frame = cap.read()
        if not ok: break
        tracks = tracks_from_result(detector.track(frame, resolve_path(cfg["tracking"]["config"]), ids))
        for track in tracks: counter.update(track.track_id, track.bottom_center, track.class_name)
        cv2.imshow("Smart Airport Luggage Detection", draw_overlay(frame, tracks, counter, start, end))
        if cv2.waitKey(1) & 0xFF in (27, ord("q")): break
    cap.release(); cv2.destroyAllWindows()


if __name__ == "__main__": main()

