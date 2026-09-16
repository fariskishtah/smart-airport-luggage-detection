#!/usr/bin/env python3
"""Fair fixed-test comparison for COCO baseline and fine-tuned YOLO models."""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from ultralytics import YOLO

NAMES = ["backpack", "handbag", "suitcase"]
COCO_MAP = {24: 0, 26: 1, 28: 2}


def iou(box, boxes):
    if not len(boxes): return np.empty(0)
    x1 = np.maximum(box[0], boxes[:,0]); y1 = np.maximum(box[1], boxes[:,1]); x2 = np.minimum(box[2], boxes[:,2]); y2 = np.minimum(box[3], boxes[:,3])
    inter = np.maximum(0,x2-x1) * np.maximum(0,y2-y1)
    return inter / np.maximum((box[2]-box[0])*(box[3]-box[1]) + (boxes[:,2]-boxes[:,0])*(boxes[:,3]-boxes[:,1]) - inter, 1e-9)


def average_precision(recall, precision):
    mrec = np.concatenate(([0.], recall, [1.])); mpre = np.concatenate(([1.], precision, [0.]))
    mpre = np.flip(np.maximum.accumulate(np.flip(mpre)))
    return float(np.trapezoid(np.interp(np.linspace(0,1,101), mrec, mpre), np.linspace(0,1,101)))


def evaluate(model_path: Path, test_root: Path, baseline: bool, device: str):
    model = YOLO(str(model_path)); images = sorted((test_root / "images").glob("*")); ground_truth = defaultdict(lambda: defaultdict(list)); total_gt = defaultdict(int)
    for image_path in images:
        for line in (test_root / "labels" / f"{image_path.stem}.txt").read_text().splitlines():
            cls,x,y,w,h = map(float,line.split()); cls=int(cls); ground_truth[cls][image_path.name].append([x-w/2,y-h/2,x+w/2,y+h/2]); total_gt[cls]+=1
    predictions = defaultdict(list)
    # Exclude model initialization / MPS graph warm-up from steady-state latency.
    for _ in range(3): model.predict(str(images[0]), conf=.001, iou=.7, imgsz=512, device=device, verbose=False)
    started=time.perf_counter()
    # Per-image inference avoids Ultralytics' batch NMS time limit truncating a
    # prediction-heavy model at the very low confidence needed for AP curves.
    results = [model.predict(str(path), conf=.001, iou=.7, imgsz=512, device=device, verbose=False)[0] for path in images]
    elapsed=time.perf_counter()-started
    for image_path, result in zip(images,results):
        height, width = result.orig_shape
        for box, cls, conf in zip(result.boxes.xyxy.cpu().numpy(), result.boxes.cls.int().cpu().numpy(), result.boxes.conf.cpu().numpy()):
            mapped = COCO_MAP.get(int(cls)) if baseline else int(cls)
            if mapped is None or mapped not in range(3): continue
            predictions[mapped].append((float(conf),image_path.name,np.array([box[0]/width,box[1]/height,box[2]/width,box[3]/height])))
    thresholds=np.arange(.5,1.,.05); per_class={}; aggregate_tp=aggregate_fp=0
    for cls,name in enumerate(NAMES):
        ordered=sorted(predictions[cls], reverse=True, key=lambda x:x[0]); aps=[]; fixed_tp=fixed_fp=0
        for threshold in thresholds:
            matched=defaultdict(set); tp=[]; fp=[]
            for conf,image_name,box in ordered:
                boxes=np.array(ground_truth[cls][image_name]); overlaps=iou(box,boxes); best=int(overlaps.argmax()) if len(overlaps) else -1
                correct=best>=0 and overlaps[best]>=threshold and best not in matched[image_name]
                if correct: matched[image_name].add(best)
                tp.append(int(correct)); fp.append(int(not correct))
                if abs(threshold-.5)<1e-9 and conf>=.25:
                    fixed_tp+=int(correct); fixed_fp+=int(not correct)
            ctp=np.cumsum(tp); cfp=np.cumsum(fp); recall=ctp/max(total_gt[cls],1); precision=ctp/np.maximum(ctp+cfp,1); aps.append(average_precision(recall,precision))
        fixed_fn=max(total_gt[cls]-fixed_tp,0); aggregate_tp+=fixed_tp; aggregate_fp+=fixed_fp
        per_class[name]={"ground_truth":total_gt[cls],"predictions_at_conf_0.25":fixed_tp+fixed_fp,"precision_at_0.25":fixed_tp/max(fixed_tp+fixed_fp,1),"recall_at_0.25":fixed_tp/max(total_gt[cls],1),"ap50":aps[0],"map50_95":float(np.mean(aps))}
    total_ground_truth=sum(total_gt.values()); precision=aggregate_tp/max(aggregate_tp+aggregate_fp,1); recall=aggregate_tp/max(total_ground_truth,1)
    return {"model":str(model_path),"images":len(images),"ground_truth_instances":total_ground_truth,"precision_at_conf_0.25":precision,"recall_at_conf_0.25":recall,"map50":float(np.mean([v['ap50'] for v in per_class.values()])),"map50_95":float(np.mean([v['map50_95'] for v in per_class.values()])),"fps":len(images)/elapsed,"latency_ms":elapsed/len(images)*1000,"size_mb":model_path.stat().st_size/1e6,"parameters":sum(p.numel() for p in model.model.parameters()),"per_class":per_class}


def main():
    p=argparse.ArgumentParser(); p.add_argument("--baseline",type=Path,default=Path("models/yolo11n.pt")); p.add_argument("--finetuned",type=Path,required=True); p.add_argument("--device",default="mps"); p.add_argument("--output",type=Path,default=Path("outputs/evaluation/model_comparison.json")); a=p.parse_args()
    payload={"protocol":"Fixed held-out 40-image test set; precision/recall at confidence 0.25; 101-point interpolated AP","baseline":evaluate(a.baseline,Path("data/processed/test"),True,a.device),"finetuned":evaluate(a.finetuned,Path("data/processed/test"),False,a.device)}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,indent=2)); print(json.dumps(payload,indent=2))


if __name__=="__main__": main()
