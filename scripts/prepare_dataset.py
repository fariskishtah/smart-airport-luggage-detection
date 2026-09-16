"""Normalize an already exported YOLO dataset into the repository split layout."""
import argparse
import shutil
from pathlib import Path


def main():
    p = argparse.ArgumentParser(); p.add_argument("source", type=Path); p.add_argument("--destination", type=Path, default=Path("data/processed")); a = p.parse_args()
    aliases = {"train": "train", "valid": "valid", "val": "valid", "test": "test"}
    copied = 0
    for source_name, target_name in aliases.items():
        split = a.source / source_name
        if not split.exists(): continue
        for kind in ("images", "labels"):
            src, dst = split / kind, a.destination / target_name / kind
            dst.mkdir(parents=True, exist_ok=True)
            if src.exists():
                for item in src.iterdir():
                    if item.is_file(): shutil.copy2(item, dst / item.name); copied += 1
    print(f"Copied {copied} files to {a.destination}")


if __name__ == "__main__": main()

