from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np


CLASS_NAMES = ["backpack", "handbag", "suitcase"]


def validate(root: Path, class_count: int = 3):
    report = {"images": 0, "labels": 0, "instances": 0, "empty_labels": [], "missing_labels": [], "broken_images": [], "invalid_annotations": [], "duplicate_images": [], "duplicate_annotations": [], "extreme_aspect_ratio_images": [], "class_instances": {}, "split_images": {}, "split_instances": {}}
    hashes, counts = {}, Counter()
    for split in ("train", "valid", "test"):
        split_image_count, split_instance_count = 0, 0
        image_dir, label_dir = root / split / "images", root / split / "labels"
        for image_path in sorted(image_dir.glob("*")) if image_dir.exists() else []:
            if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}: continue
            report["images"] += 1; split_image_count += 1
            raw = image_path.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
            if digest in hashes: report["duplicate_images"].append([str(hashes[digest]), str(image_path)])
            else: hashes[digest] = image_path
            image = cv2.imdecode(np.frombuffer(raw, dtype="uint8"), cv2.IMREAD_COLOR)
            if image is None: report["broken_images"].append(str(image_path))
            else:
                h, w = image.shape[:2]
                if max(w / max(h, 1), h / max(w, 1)) > 4: report["extreme_aspect_ratio_images"].append(str(image_path))
            label = label_dir / f"{image_path.stem}.txt"
            if not label.exists(): report["missing_labels"].append(str(image_path)); continue
            report["labels"] += 1
            lines = [line.strip() for line in label.read_text().splitlines() if line.strip()]
            if not lines: report["empty_labels"].append(str(label))
            if len(lines) != len(set(lines)): report["duplicate_annotations"].append(str(label))
            for line_no, line in enumerate(lines, 1):
                try:
                    values = [float(v) for v in line.split()]
                    class_id, coords = int(values[0]), values[1:]
                    if len(values) != 5 or class_id < 0 or class_id >= class_count or any(v < 0 or v > 1 for v in coords) or coords[2] <= 0 or coords[3] <= 0: raise ValueError
                    counts[class_id] += 1; report["instances"] += 1; split_instance_count += 1
                except (ValueError, IndexError): report["invalid_annotations"].append(f"{label}:{line_no}: {line}")
        report["split_images"][split] = split_image_count
        report["split_instances"][split] = split_instance_count
    report["class_instances"] = {CLASS_NAMES[i]: counts[i] for i in range(class_count)}
    report["valid"] = not any(report[key] for key in ("missing_labels", "broken_images", "invalid_annotations", "duplicate_images", "duplicate_annotations"))
    return report


def create_plots(root: Path, report: dict, distribution_path: Path, samples_path: Path):
    distribution_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7, 4))
    names, values = list(report["class_instances"]), list(report["class_instances"].values())
    bars = plt.bar(names, values, color=["#5CDB95", "#FF9966", "#33CCFF"])
    plt.title("Open Images luggage subset — class distribution"); plt.ylabel("Bounding-box instances")
    for bar, value in zip(bars, values): plt.text(bar.get_x() + bar.get_width()/2, value, str(value), ha="center", va="bottom")
    plt.tight_layout(); plt.savefig(distribution_path, dpi=160); plt.close()
    paths = sorted((root / "train/images").glob("*"))[:16]
    tiles = []
    for image_path in paths:
        image = cv2.imread(str(image_path)); label = root / "train/labels" / f"{image_path.stem}.txt"
        if image is None: continue
        h, w = image.shape[:2]
        for line in label.read_text().splitlines():
            class_id, x, y, bw, bh = map(float, line.split()); x1, y1, x2, y2 = int((x-bw/2)*w), int((y-bh/2)*h), int((x+bw/2)*w), int((y+bh/2)*h)
            cv2.rectangle(image, (x1,y1), (x2,y2), (0,220,255), max(2, w//400)); cv2.putText(image, CLASS_NAMES[int(class_id)], (x1,max(20,y1-5)), cv2.FONT_HERSHEY_SIMPLEX, .6, (0,220,255), 2)
        image = cv2.resize(image, (320, 240)); tiles.append(image)
    if tiles:
        while len(tiles) < 16: tiles.append(np.zeros_like(tiles[0]))
        montage = np.vstack([np.hstack(tiles[i:i+4]) for i in range(0,16,4)])
        cv2.imwrite(str(samples_path), montage)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--root", default="data/processed"); p.add_argument("--output", default="outputs/dataset_quality_report.json"); p.add_argument("--distribution", default="outputs/dataset_class_distribution.png"); p.add_argument("--samples", default="outputs/dataset_samples.jpg"); a = p.parse_args()
    root = Path(a.root); result = validate(root); Path(a.output).parent.mkdir(parents=True, exist_ok=True); Path(a.output).write_text(json.dumps(result, indent=2)); create_plots(root, result, Path(a.distribution), Path(a.samples)); print(json.dumps(result, indent=2))
