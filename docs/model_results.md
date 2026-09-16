# Model Results and Checkpoint Inventory

## 1. Executive Summary

This document records the exact physical model checkpoints, empirical training parameters, measured held-out test metrics, and runtime characteristics for all models evaluated in the project.

We explicitly maintain a scientific and architectural distinction between:
- **Research Models:** Evaluated on the held-out Open Images V7 luggage benchmark to test transfer learning and class-specific domain adaptation.
- **Deployment Models:** Evaluated on real-world airport carousel and conveyor footage to deliver reliable, unique bag counts for operational deployment.

---

## 2. Checkpoint Inventory

| Category | Model Name | Checkpoint Path | Parameters | File Size | Training Duration | Epochs | Dataset Split |
|---|---|---|:---:|:---:|:---:|:---:|---|
| **Deployment** | **YOLO11n COCO** | `models/deployment/yolo11n_coco.pt` (symlink to `models/yolo11n.pt`) | 2,616,248 | 5.61 MB | N/A (Pretrained) | 80 classes | COCO Pretrained |
| **Research** | **YOLO11n Fine-Tuned** | `models/research/yolo11n_finetuned_best.pt` (symlink to `models/yolo11n_luggage_best.pt`) | 2,582,737 | 5.44 MB | 544.67 s (9.08 min) | 15 | 277 train / 79 val / 40 test |
| **Research** | **YOLO11s Fine-Tuned** | `models/research/yolo11s_finetuned_best.pt` (symlink to `models/yolo11s_luggage_best.pt`) | 9,413,961 | 19.14 MB | 986.42 s (16.44 min) | 15 | 277 train / 79 val / 40 test |
| **Research** | **YOLO11n Conservative** | `models/research/yolo11n_conservative_best.pt` | 2,582,737 | 5.44 MB | 144.12 s (2.40 min) | 8 | 277 train / 79 val / 40 test |

---

## 3. Training Hyperparameters and Hardware Environment

All fine-tuning runs were performed on Apple Silicon (MPS acceleration):
- **Hardware:** Apple M2 (arm64), 8 GB unified memory, macOS Darwin 26.5.2
- **Frameworks:** PyTorch 2.14.0 (MPS available), Ultralytics 8.3.199
- **Batch Size:** 8
- **Input Image Size:** 512×512
- **Optimizer:** AdamW, initial learning rate `lr0=0.001`, `lrf=0.01`
- **Augmentation (`yolo11n_luggage`, `yolo11s_luggage`):** `mixup=0.05`, `degrees=5`, `translate=0.1`, `scale=0.4`, `fliplr=0.5`
- **Augmentation (`yolo11n_conservative`):** `mixup=0.0`, `degrees=3`, `translate=0.05`, `scale=0.25`, `fliplr=0.5`

---

## 4. Empirical Evaluation on Fixed Held-Out Test Set (40 Images, 45 Ground Truth Objects)

Evaluated via `scripts/compare_models.py` with 101-point interpolated AP, IoU=0.70, confidence=0.001:

| Checkpoint | Precision (@0.25) | Recall (@0.25) | mAP@0.50 | mAP@0.50:0.95 | Inference Latency (MPS) | Peak Memory |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `yolo11n_coco.pt` | 0.441 | 0.333 | 0.395 | 0.285 | 103.2 ms | 494.5 MB |
| `yolo11n_luggage_best.pt` | **0.591** | **0.578** | **0.579** | **0.465** | 161.3 ms | 483.9 MB |
| `yolo11s_luggage_best.pt` | 0.529 | **0.600** | 0.482 | 0.386 | 85.9 ms | 498.7 MB |
| `yolo11n_conservative_best.pt` | **0.618** | 0.467 | **0.653** | **0.480** | 155.8 ms | 531.3 MB |

### Per-Class Test Set Results (mAP50-95)
- **YOLO11n Fine-Tuned:** Backpack: **0.361**, Handbag: **0.700**, Suitcase: **0.335**
- **YOLO11s Fine-Tuned:** Backpack: **0.198**, Handbag: **0.661**, Suitcase: **0.299**
- **YOLO11n Conservative:** Backpack: **0.364**, Handbag: **0.756**, Suitcase: **0.321**
- **COCO Baseline:** Backpack: **0.153**, Handbag: **0.144**, Suitcase: **0.558**

---

## 5. Deployment Selection Rationale

Although `yolo11n_luggage_best.pt` and `yolo11n_conservative_best.pt` achieve higher aggregate test set mAP on Open Images static photos (0.465 and 0.480 vs. 0.285), the **COCO Pretrained YOLO11n (`models/deployment/yolo11n_coco.pt`) is selected as the primary deployment model**.

**Why?**
1. **Conveyor Footage Performance:** On the primary 447-frame airport carousel demo, COCO YOLO11n correctly detected and counted **4/4 (100%)** luggage crossings. Fine-tuned models achieved only **1/4 (25%)** crossings due to domain shift and class imbalance (56% of Open Images training labels were handbags, and suitcase recall dropped from 85.7% to 28.6%).
2. **Multi-Video Generalization:** On three diverse airport video sequences, COCO YOLO11n achieved **10/10 total crossings (100% mean accuracy)**.
3. **Execution Speed:** Processes video at **39.3–48.2 FPS** on Apple Silicon MPS with ByteTrack, well above the real-time threshold of 30 FPS.
