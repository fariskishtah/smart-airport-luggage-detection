"""Download a bounded Open Images subset through FiftyOne when explicitly requested."""
import argparse


def main():
    p = argparse.ArgumentParser(); p.add_argument("--max-samples", type=int, default=1500); p.add_argument("--output", default="data/raw/open-images-luggage"); a = p.parse_args()
    try: import fiftyone.zoo as foz
    except ImportError as exc: raise SystemExit("Install the optional downloader first: pip install fiftyone") from exc
    foz.load_zoo_dataset("open-images-v7", split="train", label_types=["detections"], classes=["Suitcase", "Backpack", "Handbag"], max_samples=a.max_samples, dataset_dir=a.output, shuffle=True, seed=42)


if __name__ == "__main__": main()

