# Antigravity Handoff Audit — 17 September 2026

## Project
**Smart Airport Luggage Detection, Tracking, Counting and Analytics System**

---

## 1. Executive Summary

This audit assesses the state of the repository as inherited, identifies all verified working components, catalogs measured empirical data, details discrepancies and gaps against the graduation acceptance requirements, and lays out the precise sequence of engineering tasks needed to finalize the project.

---

## 2. Environment & System Verification

- **Host Architecture:** Apple Silicon Mac (arm64, Darwin 26.5.2)
- **Python Environment:** Python 3.11.15 in `.venv` (system Python: 3.14.7)
- **Key Packages:**
  - `torch==2.14.0` (Apple Metal Performance Shaders / MPS verified available)
  - `ultralytics==8.3.199`
  - `opencv-python==4.12.0.88`
  - `streamlit==1.49.1`
  - `pytest==8.4.2`
  - `lap==0.5.12` (Linear assignment for ByteTrack)
  - `pandas==2.3.3`, `matplotlib==3.11.2`, `PyYAML==6.0.2`
- **Available Disk Space:** ~12 GiB free out of 460 GiB. Storage preservation is critical; redundant model training or large file generation must be avoided.
- **Git Status:** Clean local workspace on branch `master`, untracked files staged for project consolidation.

---

## 3. Inventory of Completed Work

1. **Dataset Preparation & Validation:**
   - Source: Open Images V7 luggage classes (`backpack`, `handbag`, `suitcase`).
   - Verified size: 396 images, 522 bounding box annotations (121 backpacks, 293 handbags, 108 suitcases).
   - Strict 70/20/10 split: 277 train (354 instances), 79 val (123 instances), 40 test (45 instances).
   - Quality checks verified: 0 broken images, 0 duplicate images, 0 missing labels, 0 invalid bounding boxes (`outputs/dataset_quality_report.json`).

2. **Model Training Runs (All Verified from Logs & Weights):**
   - **YOLO11n Fine-Tuned (`yolo11n_luggage`):** 15 epochs on MPS, 544.67s training time, 5.44 MB checkpoint size.
   - **YOLO11s Fine-Tuned (`yolo11s_luggage`):** 15 epochs on MPS, 986.42s training time, 19.14 MB checkpoint size.
   - **YOLO11n Conservative Fine-Tuned (`yolo11n_conservative`):** 8 epochs on MPS, 144.12s training time, 5.44 MB checkpoint size.

3. **Rigorous Held-Out Evaluation (40 test images, 45 ground-truth objects):**
   - Evaluated without batch NMS timeout truncation using exact 101-point interpolated AP.
   - Baseline COCO YOLO11n: Precision 0.441, Recall 0.333, mAP50 0.395, mAP50-95 0.285.
   - Research Best (YOLO11n Fine-Tuned): Precision 0.591, Recall 0.578, mAP50 0.579, mAP50-95 0.465 (per-image test metrics: mAP50 0.574, mAP50-95 0.446).
   - YOLO11s Fine-Tuned: Precision 0.529, Recall 0.600, mAP50 0.482, mAP50-95 0.386.
   - YOLO11n Conservative: Precision 0.618, Recall 0.467, mAP50 0.653, mAP50-95 0.480.

4. **Multi-Object Tracking & Counting Core:**
   - `LineCounter`: 2D signed line-distance geometry, configurable deadband (`deadband_px`), minimum track age filter (`min_track_age`), permanent unique-ID counting registry, direction filtering (`any`, `positive`, `negative`).
   - `ZoneCounter`: Ray-casting polygon intersection, enter/exit state transition detection, mature track filtering, duplicate suppression.
   - Modular tracking via ByteTrack and BoT-SORT.

5. **Primary Demo Result:**
   - 447 frames, 960x540 at 30 FPS (`demo/input_airport_luggage.mp4`).
   - Ground truth manually verified: 4 crossing suitcases.
   - Predicted count: 4 unique crossings (Track IDs 1, 2, 9, 41 with ByteTrack; 1, 2, 13, 39 with BoT-SORT).
   - Absolute Error: 0. Clip-level counting accuracy: 100%. Throughput: 38–48 FPS on Apple Silicon MPS.

6. **Automated Test Suite:**
   - 14 passing unit and integration tests covering line crossing, duplicate prevention, jitter deadband, bidirectional counting, zone entry/exit, and end-to-end video synthesis.

---

## 4. Partially Completed Work & Gaps

1. **Documentation Lag & Contradictory Claims:**
   - `README.md` and `docs/model_results.md` still state that luggage-specific training was unmeasured due to disk constraints. In reality, training and evaluation were successfully performed and logged.
   - Missing required comparison documents: `docs/baseline_vs_finetuned.md`, `docs/tracker_comparison.md`, and `docs/counting_benchmark.md`.
2. **Multi-Video Benchmark Execution:**
   - Three Pexels videos exist in `demo/` and `demo/benchmark/`.
   - `pexels_1169854_source.mp4` has benchmark runs (3/3 count).
   - `pexels_27778466_source.mp4` was previously evaluated with default vertical line coordinates that run parallel to the conveyor, resulting in 0 counts. Needs video-specific geometry and manual ground-truth documentation.
3. **CLI Arguments & Configuration:**
   - `src/inference_video.py` lacks `--conf`, `--iou`, `--count-mode`, `--device` command-line overrides.
   - Default `configs/config.yaml` points to `models/best.pt` (research model), which due to domain shift underperforms on conveyor video compared to `models/yolo11n.pt` (deployment model). Default should point to deployment model with 640 image size.
4. **Event Logging Format:**
   - `outputs/events.csv` lacks explicit fields specified in acceptance criteria: `event_id`, `video`, `model`, `tracker`, `event_type`.
5. **Streamlit UI Enhancements:**
   - Needs explicit labeling of Deployment Model vs Research Fine-Tuned models.
   - Needs demo sample loading capability for immediate testing without manual file selection.
6. **Model Organization:**
   - Models currently sit flat in `models/` and root. Should provide organized structure `models/deployment/` and `models/research/` while preserving backward compatibility.
7. **Test Suite Coverage:**
   - Needs tests for zone short-lived track rejection and configuration error handling.

---

## 5. Domain Shift Findings

Empirical evidence proves a strong visual domain shift:
- On Open Images held-out static photos, fine-tuned YOLO11n achieves **mAP50-95 of 0.465** vs COCO baseline's **0.285** (a +63% relative improvement), with handbag mAP reaching 0.700.
- However, on the real airport carousel demo (`demo/input_airport_luggage.mp4`), COCO YOLO11n correctly detects small rolling suitcases and counts **4/4 (100%)**, whereas fine-tuned YOLO11n achieves only **1/4** due to training set class imbalance (56% handbags, 21% suitcases) and product-style framing.
- **Architectural Decision:** Maintain clear scientific separation:
  - **Research Model:** Fine-Tuned YOLO11n (`models/research/yolo11n_finetuned_best.pt`)
  - **Deployment Model:** COCO Pretrained YOLO11n (`models/deployment/yolo11n_coco.pt` / `models/yolo11n.pt`)

---

## 6. Action Plan for Completion

| Phase | Tasks |
|---|---|
| **Phase 1: Core Code & CLI** | Update `src/inference_video.py` with complete CLI args (`--conf`, `--iou`, `--count-mode`, `--device`), standardize event CSV schema (`event_id`, `video`, `event_type`, `model`, `tracker`), update `configs/config.yaml` defaults. |
| **Phase 2: Model Organization** | Create `models/deployment/` and `models/research/` symlinks/copies while keeping legacy paths intact for backward compatibility. |
| **Phase 3: Multi-Video Benchmark** | Establish manual ground truth for all benchmark clips, configure video-specific geometry, execute benchmark runs, generate `docs/counting_benchmark.md`. |
| **Phase 4: Comparative Documentation** | Write `docs/baseline_vs_finetuned.md`, `docs/tracker_comparison.md`, update `docs/model_results.md`, update `docs/reproducibility.md`. |
| **Phase 5: Test Suite Expansion** | Add missing tests in `tests/test_counter.py` and `tests/test_end_to_end.py`, verify all pass. |
| **Phase 6: Streamlit UI Polish** | Refine `app/app.py` with crystal-clear model labels and demo pre-load option. |
| **Phase 7: Final Demo & README** | Generate canonical `outputs/demo/final_demo.mp4` (H.264) and `outputs/demo/final_demo.json`, rewrite `README.md` to reflect verified final metrics. |
