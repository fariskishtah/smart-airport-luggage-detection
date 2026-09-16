#!/usr/bin/env python3
"""Build a deterministic YOLO luggage subset from exhaustive Open Images splits."""
from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CLASSES = {"/m/01940j": 0, "/m/080hkjn": 1, "/m/01s55n": 2}
NAMES = ["backpack", "handbag", "suitcase"]
ANNOTATION_URLS = {
    "validation": "https://storage.googleapis.com/openimages/v5/validation-annotations-bbox.csv",
    "test": "https://storage.googleapis.com/openimages/v5/test-annotations-bbox.csv",
}
IMAGE_URL = "https://open-images-dataset.s3.amazonaws.com/{source}/{image_id}.jpg"


def fetch(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    urllib.request.urlretrieve(url, partial)
    partial.replace(destination)


def parse_annotations(csv_path: Path, source: str):
    images = defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["LabelName"] not in CLASSES or row.get("IsGroupOf") == "1" or row.get("IsDepiction") == "1":
                continue
            class_id = CLASSES[row["LabelName"]]
            xmin, xmax = float(row["XMin"]), float(row["XMax"])
            ymin, ymax = float(row["YMin"]), float(row["YMax"])
            images[(source, row["ImageID"])].append((class_id, xmin, ymin, xmax, ymax))
    return images


def balanced_select(images: dict, limit: int, seed: int):
    rng = random.Random(seed)
    candidates = list(images)
    rng.shuffle(candidates)
    by_class = {class_id: [] for class_id in range(len(NAMES))}
    for key in candidates:
        for class_id in {box[0] for box in images[key]}:
            by_class[class_id].append(key)
    selected, selected_set = [], set()
    quota = limit // len(NAMES)
    for class_id in range(len(NAMES)):
        for key in by_class[class_id]:
            if key in selected_set:
                continue
            selected.append(key); selected_set.add(key)
            if sum(class_id in {b[0] for b in images[k]} for k in selected) >= quota:
                break
    for key in candidates:
        if len(selected) >= limit:
            break
        if key not in selected_set:
            selected.append(key); selected_set.add(key)
    rng.shuffle(selected)
    return selected[:limit]


def yolo_line(box) -> str:
    class_id, xmin, ymin, xmax, ymax = box
    return f"{class_id} {(xmin+xmax)/2:.6f} {(ymin+ymax)/2:.6f} {xmax-xmin:.6f} {ymax-ymin:.6f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=600)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--root", type=Path, default=Path("data/processed"))
    parser.add_argument("--metadata", type=Path, default=Path("data/raw/openimages_metadata"))
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    for source, url in ANNOTATION_URLS.items():
        fetch(url, args.metadata / f"{source}-annotations-bbox.csv")
    images = {}
    for source in ANNOTATION_URLS:
        images.update(parse_annotations(args.metadata / f"{source}-annotations-bbox.csv", source))
    selected = balanced_select(images, min(args.limit, len(images)), args.seed)
    rng = random.Random(args.seed); rng.shuffle(selected)
    n_train, n_valid = round(len(selected) * .7), round(len(selected) * .2)
    assignments = {}
    for index, key in enumerate(selected):
        assignments[key] = "train" if index < n_train else "valid" if index < n_train + n_valid else "test"
    for split in ("train", "valid", "test"):
        for kind in ("images", "labels"):
            directory = args.root / split / kind
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True)

    def download_one(key):
        source, image_id = key; split = assignments[key]
        image_path = args.root / split / "images" / f"{source}_{image_id}.jpg"
        fetch(IMAGE_URL.format(source=source, image_id=image_id), image_path)
        label_path = args.root / split / "labels" / f"{source}_{image_id}.txt"
        label_path.write_text("\n".join(yolo_line(box) for box in images[key]) + "\n", encoding="utf-8")
        return key

    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download_one, key): key for key in selected}
        for future in as_completed(futures):
            try: future.result()
            except Exception as exc: failures.append({"image": futures[future], "error": str(exc)})
    split_images, instances = Counter(), Counter()
    for key in selected:
        if any(tuple(f["image"]) == key for f in failures): continue
        split_images[assignments[key]] += 1
        for box in images[key]: instances[NAMES[box[0]]] += 1
    manifest = {"dataset": "Open Images V7 annotations / V5 dense split files", "annotation_license": "CC BY 4.0", "seed": args.seed, "requested_images": args.limit, "downloaded_images": sum(split_images.values()), "split_images": dict(split_images), "class_instances": dict(instances), "failures": failures, "source_splits": list(ANNOTATION_URLS)}
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/dataset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
