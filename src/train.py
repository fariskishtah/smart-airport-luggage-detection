import argparse
import shutil
import time
import json
from pathlib import Path

from ultralytics import YOLO
import yaml

from utils import ROOT, choose_device


def main():
    parser = argparse.ArgumentParser(description="Fine-tune a compact YOLO luggage detector.")
    parser.add_argument("--config", default=None, help="Ultralytics training YAML")
    parser.add_argument("--data", default=str(ROOT / "data.yaml"))
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    if args.config:
        params = yaml.safe_load(Path(args.config).read_text())
        model_name = params.pop("model")
        params["data"] = str(ROOT / params.get("data", "data.yaml"))
        params["project"] = str(ROOT / params.get("project", "outputs/training"))
        params["device"] = choose_device(params.get("device", "auto"))
    else:
        model_name = args.model
        params = dict(data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, device=choose_device(args.device), patience=12, optimizer="auto", project=str(ROOT / "outputs/training"), name="luggage_yolo11n", exist_ok=True, plots=True, seed=42)
    started = time.perf_counter()
    result = YOLO(model_name).train(**params)
    duration = time.perf_counter() - started
    weights = Path(result.save_dir) / "weights"
    (ROOT / "models").mkdir(exist_ok=True)
    prefix = params.get("name", Path(model_name).stem)
    for name in ("best.pt", "last.pt"):
        if (weights / name).exists(): shutil.copy2(weights / name, ROOT / "models" / f"{prefix}_{name}")
    metadata = {"model": model_name, "parameters": params, "duration_seconds": round(duration, 3), "save_dir": str(result.save_dir)}
    (Path(result.save_dir) / "experiment_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__": main()
