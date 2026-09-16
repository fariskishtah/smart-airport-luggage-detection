# Reproducibility Record

## 1. Experimental Environment

- **Recorded Date:** 17 September 2026
- **Host Architecture:** Apple M2 (`arm64`), 8 CPU cores, 10 GPU cores, 8 GB Unified Memory
- **Operating System:** macOS Darwin 26.5.2 (Kernel Darwin 26.5.2)
- **Python Version:** 3.11.15 (`.venv/bin/python`)
- **PyTorch Version:** 2.14.0 (MPS verified available, CPU fallback verified)
- **Ultralytics Version:** 8.3.199
- **OpenCV Version:** 4.12.0.88
- **Streamlit Version:** 1.49.1
- **Key Dependencies:** `PyYAML==6.0.2`, `lap==0.5.12`, `pytest==8.4.2`, `pandas==2.3.3`, `matplotlib==3.11.2`, `Pillow==11.3.0`, `numpy==2.2.6`

---

## 2. Dataset Provenance and Partitioning

- **Source:** Open Images V7 (Validation and Test bounding-box pools via official AWS mirrors).
- **Target Category MIDs:**
  - Backpack: `/m/01940j` (121 instances)
  - Handbag: `/m/080hkjn` (293 instances)
  - Suitcase: `/m/01s55n` (108 instances)
- **Filters Applied:** Excluded non-photographic depictions, occluded group boxes (`IsGroupOf=1`).
- **Total Dataset:** 396 unique images, 522 bounding-box instances.
- **Random Seed:** 42 (`deterministic: true`).
- **Split Distribution (Disjoint 70/20/10):**
  - **Train:** 277 images, 354 instances (82 backpack, 199 handbag, 73 suitcase)
  - **Validation:** 79 images, 123 instances (32 backpack, 70 handbag, 21 suitcase)
  - **Test (Held-Out):** 40 images, 45 instances (7 backpack, 24 handbag, 14 suitcase)
- **Validation Artifacts:** `outputs/dataset_manifest.json`, `outputs/dataset_quality_report.json` (0 broken images, 0 duplicate annotations).

---

## 3. Training Recipes and Model Checkpoints

Three fine-tuning configurations were executed using Ultralytics YOLO11 with seed 42 on Apple Silicon MPS:

```bash
# Research Run 1: YOLO11n transfer learning (15 epochs, 544.7s)
python src/train.py --config configs/train_small.yaml

# Research Run 2: YOLO11s transfer learning (15 epochs, 986.4s)
python src/train.py --config configs/train_medium.yaml

# Research Run 3: YOLO11n conservative fine-tuning (8 epochs, 144.1s)
python src/train.py --config configs/train_conservative.yaml
```

### Checkpoint Paths
- **Deployment Model:** `models/deployment/yolo11n_coco.pt` (Pretrained COCO, 5.61 MB)
- **Research Best (YOLO11n):** `models/research/yolo11n_finetuned_best.pt` (5.44 MB)
- **Research YOLO11s:** `models/research/yolo11s_finetuned_best.pt` (19.14 MB)
- **Research Conservative:** `models/research/yolo11n_conservative_best.pt` (5.44 MB)

---

## 4. Evaluation and Verification Protocol

```bash
# 1. Run full test suite (17 passed)
pytest -q

# 2. Reproduce held-out model comparison
python scripts/compare_models.py --baseline models/deployment/yolo11n_coco.pt --finetuned models/research/yolo11n_finetuned_best.pt --device mps

# 3. Reproduce primary airport carousel demo (4/4 counted)
python src/inference_video.py --source demo/input_airport_luggage.mp4 --output outputs/demo/final_demo.mp4 --model models/deployment/yolo11n_coco.pt

# 4. Launch Streamlit UI
streamlit run app/app.py
```
