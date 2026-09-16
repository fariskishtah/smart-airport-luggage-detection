import argparse
from pathlib import Path

from ultralytics import YOLO

from utils import ROOT, choose_device, save_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=str(ROOT / "models/best.pt"))
    parser.add_argument("--data", default=str(ROOT / "data.yaml"))
    parser.add_argument("--split", default="test", choices=["val", "test"])
    parser.add_argument("--device", default="auto")
    parser.add_argument("--name", default="held_out")
    parser.add_argument("--output", default=None)
    parser.add_argument("--imgsz", type=int, default=512)
    args = parser.parse_args()
    model = YOLO(args.model)
    metrics = model.val(data=args.data, split=args.split, imgsz=args.imgsz, device=choose_device(args.device), project=str(ROOT / "outputs/evaluation"), name=args.name, plots=True)
    image_count = len(list((ROOT / "data/processed" / args.split / "images").glob("*")))
    output = {"model": args.model, "split": args.split, "images": image_count, "precision": float(metrics.box.mp), "recall": float(metrics.box.mr), "map50": float(metrics.box.map50), "map50_95": float(metrics.box.map), "class_names": model.names, "per_class_map50_95": {model.names[i]: float(value) for i, value in enumerate(metrics.box.maps)}, "speed_ms_per_image": {key: float(value) for key, value in metrics.speed.items()}}
    output_path = Path(args.output) if args.output else ROOT / "outputs/evaluation" / f"{args.name}_metrics.json"
    save_json(output_path, output)
    print(output)


if __name__ == "__main__": main()
