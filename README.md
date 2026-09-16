# Smart Airport Luggage Detection, Tracking and Counting System

A robust, real-time Computer Vision system for automated baggage monitoring, tracking, and directional counting on airport carousels and conveyor belts.

---

## 1. Overview

In airport baggage logistics and security surveillance, traditional per-frame object detection cannot accurately measure luggage throughput: a single suitcase traveling along a conveyor is visible across hundreds of frames. Simply summing detection boxes results in massive over-counting.

This system integrates **YOLO11 object detection**, **ByteTrack / BoT-SORT multi-object tracking**, and **vector geometric crossing algorithms** to assign persistent spatial IDs, track trajectories over time, and uniquely count each physical bag upon crossing user-configured virtual lines or polygonal zones. It generates auditable CSV event ledgers, evidence crops, H.264 video overlays, and an interactive Streamlit dashboard.

---

## 2. Problem Statement

Airports process thousands of passenger bags per hour across interconnected conveyor systems. Manual monitoring is labor-intensive and prone to human error. Developing an automated vision-based counting system presents key technical hurdles:
1. **Temporal Redundancy:** Objects persist across frames; counting detections per frame leads to catastrophic over-counting.
2. **Boundary Jitter:** Luggage items hovering near a counting threshold can repeatedly cross back and forth, generating duplicate counts.
3. **Short-Lived False Positives:** Transient detector false positives must not increment physical throughput metrics.
4. **Visual Domain Shift:** Classifiers trained on static consumer web photos encounter small, motion-blurred, rolling luggage on metallic airport conveyors.

---

## 3. Features

- **Luggage Object Detection:** Detects `backpack`, `handbag`, and `suitcase` categories using Ultralytics YOLO11.
- **Persistent Multi-Object Tracking:** Temporal track association using ByteTrack (default) or BoT-SORT to maintain continuous identity.
- **Directional Line Counting:** 2D signed line-distance geometry with configurable deadbands (`deadband_px`) to prevent boundary jitter.
- **Polygonal Zone Counting:** Ray-casting point-in-polygon ROI monitoring to detect `ENTER` and `EXIT` state transitions.
- **False-Track Filtering:** Minimum track age requirement (`min_track_age`) ensures short-lived detector noise is ignored.
- **Permanent ID Registry:** Guarantees that each physical track ID is counted at most once per session.
- **Auditable Event Logging:** Generates `outputs/events.csv` with timestamp, track ID, class, confidence, coordinates, and bounding-box evidence crops (`event_XXX.jpg`).
- **Interactive Streamlit UI:** Full web dashboard for uploading video, toggling models, adjusting thresholds, viewing real-time analytics, and downloading reports.
- **Production H.264 Encoding:** Automated FFmpeg post-processing ensures browser and QuickTime compatibility.
- **Hardware Acceleration:** Native Apple Silicon Metal Performance Shaders (MPS), NVIDIA CUDA, and verified real-time CPU fallback.

---

## 4. Architecture

```text
Input Video / Stream
        │
        ▼
[ Frame Decoding ] (OpenCV / FFmpeg, source FPS & aspect ratio retained)
        │
        ▼
[ Object Detection ] (YOLO11n / YOLO11s, confidence & IoU thresholding)
        │
        ▼
[ Multi-Object Tracking ] (ByteTrack / BoT-SORT: Kalman state & identity association)
        │
        ▼
[ Trajectory Analysis & Anchor ] (Bottom-center footprint tracking)
        │
        ▼
[ Counting Engine ] ──► [ Line Gate: Signed 2D Distance + Deadband ]
                   ──► [ Zone Gate: Point-in-Polygon State Transition ]
                   ──► [ Temporal Gate: Minimum Track Age Rejection ]
                   ──► [ Registry Gate: Permanent ID Deduplication ]
        │
        ▼
[ Outputs & Downstream Analytics ]
   ├── Annotated H.264 MP4 Video
   ├── Machine-Readable Summary JSON (`final_demo.json`)
   ├── Auditable Event Ledger (`events.csv`)
   ├── Visual Evidence Crops (`outputs/events/event_XXX.jpg`)
   └── Interactive Streamlit Web UI (`app/app.py`)
```

See [docs/architecture.md](docs/architecture.md) for detailed module documentation.

---

## 5. Dataset

- **Source:** Open Images V7 luggage subset (`backpack`, `handbag`, `suitcase`).
- **Dataset Size:** 396 unique images, 522 annotated bounding boxes.
  - Backpack: 121 instances (23.2%)
  - Handbag: 293 instances (56.1%)
  - Suitcase: 108 instances (20.7%)
- **Data Partitioning (Disjoint 70/20/10 Split, Seed 42):**
  - **Train:** 277 images (354 instances)
  - **Validation:** 79 images (123 instances)
  - **Test (Held-Out):** 40 images (45 instances: 7 backpacks, 24 handbags, 14 suitcases)
- **Quality Assurance:** 0 broken images, 0 duplicate annotations, 0 label leakage across splits (`outputs/dataset_quality_report.json`).
- **Licensing:** Open Images annotations are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Image pixels retain individual author licenses.

See [docs/dataset_selection.md](docs/dataset_selection.md) for full dataset provenance.

---

## 6. Model Training

Transfer learning was executed using Ultralytics YOLO11 on Apple Silicon MPS:

| Experiment | Base Architecture | Epochs | Batch | Optimizer | Training Time | Checkpoint Path | Size |
|---|---|:---:|:---:|:---:|:---:|---|:---:|
| **YOLO11n Fine-Tuned** | YOLO11n COCO | 15 | 8 | AdamW | 544.7 s (9.08 min) | `models/research/yolo11n_finetuned_best.pt` | 5.44 MB |
| **YOLO11s Fine-Tuned** | YOLO11s COCO | 15 | 8 | AdamW | 986.4 s (16.44 min) | `models/research/yolo11s_finetuned_best.pt` | 19.14 MB |
| **YOLO11n Conservative** | YOLO11n COCO | 8 | 8 | AdamW | 144.1 s (2.40 min) | `models/research/yolo11n_conservative_best.pt` | 5.44 MB |

---

## 7. Model Evaluation & Comparison

All checkpoints were evaluated against the **exact same 40-image held-out test split** (45 ground-truth objects) using un-truncated single-image inference and 101-point interpolated AP:

| Model | Checkpoint | Precision (@0.25) | Recall (@0.25) | mAP@0.50 | mAP@0.50:0.95 | Parameters | Size |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **COCO Baseline YOLO11n** | `models/deployment/yolo11n_coco.pt` | 0.441 | 0.333 | 0.395 | 0.285 | 2.62M | 5.61 MB |
| **YOLO11n Fine-Tuned (Best Research)** | `models/research/yolo11n_finetuned_best.pt` | **0.591** | 0.578 | **0.579** | **0.465** | 2.58M | **5.44 MB** |
| **YOLO11s Fine-Tuned** | `models/research/yolo11s_finetuned_best.pt` | 0.529 | **0.600** | 0.482 | 0.386 | 9.41M | 19.14 MB |
| **YOLO11n Conservative** | `models/research/yolo11n_conservative_best.pt` | **0.618** | 0.467 | **0.653** | **0.480** | 2.58M | **5.44 MB** |

### Per-Class Held-Out Test mAP50-95
- **Backpack:** Baseline: 0.153 → Fine-Tuned: **0.361** (+136% relative gain)
- **Handbag:** Baseline: 0.144 → Fine-Tuned: **0.700** (+386% relative gain)
- **Suitcase:** Baseline: **0.558** → Fine-Tuned: 0.335

See [docs/baseline_vs_finetuned.md](docs/baseline_vs_finetuned.md) and [docs/model_results.md](docs/model_results.md).

---

## 8. Domain Shift Finding & Deployment Model Selection

A critical empirical discovery made in this project is the **visual domain shift** between web/product photography and airport conveyor video:
- Fine-tuning on Open Images produced large mAP improvements on static test photos (0.285 → 0.465).
- However, on real airport carousel video (`demo/input_airport_luggage.mp4`), COCO-pretrained YOLO11n correctly detected moving, small suitcases and counted **4/4 (100%)** crossings, whereas the fine-tuned detector counted only **1/4 (25%)**.
- **Root Cause:** Open Images luggage data is 56% handbags and contains close-up product photos. The COCO pretraining preserves generalized suitcase priors that perform robustly under motion blur and metallic reflections.

Therefore, this graduation project maintains a rigorous, honest separation:
- **Best Research Model:** Fine-Tuned YOLO11n (`models/research/yolo11n_finetuned_best.pt`) — proves transfer learning capability on custom luggage benchmarks.
- **Best Deployment Model:** Pretrained YOLO11n COCO (`models/deployment/yolo11n_coco.pt`) — proves robust operational capability on real airport video.

See [docs/failure_analysis.md](docs/failure_analysis.md) for detailed visual error breakdown.

---

## 9. Tracking Engine Comparison

Evaluated on the 447-frame airport carousel footage:

| Tracker | Counting Accuracy | Throughput (FPS) | Inference Latency | Memory RSS | Selected? |
|---|:---:|:---:|:---:|:---:|:---:|
| **ByteTrack** | **4 / 4 (100.0%)** | **42.23 FPS** | **20.82 ms** | 494.5 MB | **Yes (Primary)** |
| **BoT-SORT** | **4 / 4 (100.0%)** | 32.65 FPS | 27.63 ms | 457.5 MB | Configurable alternative |

ByteTrack is **29.3% faster** with zero duplicate counts and zero identity switches on counted objects. See [docs/tracker_comparison.md](docs/tracker_comparison.md).

---

## 10. Multi-Video Counting Benchmark

Evaluated across three distinct video sequences with verified manual ground-truth counts:

| Video Sequence | Resolution & FPS | Frames | Ground Truth (GT) | System Count | Absolute Error | Counting Accuracy | Mode |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| **Carousel Demo** (`input_airport_luggage.mp4`) | 960×540, 30.0 fps | 447 | **4** | **4** | **0** | **100.0%** | Line |
| **Traveler & Belt** (`pexels_1169854_source.mp4`) | 1920×1080, 29.97 fps | 505 | **3** | **3** | **0** | **100.0%** | Line |
| **Conveyor Feed** (`pexels_27778466_source.mp4`) | 2560×1440, 25.0 fps | 316 | **3** | **3** | **0** | **100.0%** | Line |

- **Total Ground Truth:** 10
- **Total Predicted Count:** 10
- **Total Absolute Error:** 0
- **Mean Per-Video Accuracy:** **100.0%**

See [docs/counting_benchmark.md](docs/counting_benchmark.md).

---

## 11. Performance and Latency Benchmark

Measured on Apple Silicon M2 (arm64, 8 GB RAM):

| Processing Mode | Throughput | Average Latency | Elapsed Time (447 Frames) | Count Accuracy |
|---|:---:|:---:|:---:|:---:|
| **GPU (Apple Silicon MPS)** | **39.26 – 42.23 FPS** | **20.82 – 22.52 ms** | **10.58 – 11.39 s** | **4 / 4 (100%)** |
| **CPU Fallback** | **29.85 FPS** | **30.53 ms** | **14.97 s** | **4 / 4 (100%)** |

Both GPU and CPU modes achieve real-time throughput relative to 30 FPS video input. See [docs/performance_benchmark.md](docs/performance_benchmark.md).

---

## 12. Automated Test Suite

The test suite contains **17 passing automated unit and integration tests** (`pytest`):
- Line crossing detection (single, multiple, bidirectional)
- Boundary jitter suppression inside deadband (`deadband_px`)
- Permanent Track-ID deduplication
- Short-lived false-track rejection (`min_track_age`)
- Polygonal zone entry and exit state transitions
- Invalid configuration and nonexistent video error handling
- End-to-end synthetic pipeline execution (decode → mock tracking → counting → H.264 encode → CSV/JSON output)

Run tests:
```bash
pytest -v
```

---

## 13. Installation & Quick Start

### Prerequisites
- Python 3.11 recommended
- FFmpeg (optional, recommended for fast H.264 encoding)

### Setup
```bash
# 1. Clone repository
git clone https://github.com/your-username/smart-airport-luggage-system.git
cd "luggage detection"

# 2. Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 14. Usage

### Command-Line Video Inference
Run the deployment pipeline on the primary airport carousel demo:
```bash
python src/inference_video.py --source demo/input_airport_luggage.mp4
```

CLI Options:
```bash
python src/inference_video.py \
  --source demo/input_airport_luggage.mp4 \
  --output outputs/demo/final_demo.mp4 \
  --model models/deployment/yolo11n_coco.pt \
  --tracker bytetrack \
  --count-mode line \
  --conf 0.25 \
  --iou 0.50 \
  --device auto
```

### Streamlit Web Dashboard
Launch the interactive web UI:
```bash
streamlit run app/app.py
```
The interface allows:
- Selecting between Deployment and Research models
- Real-time video playback and H.264 download
- Real-time metrics: Total Count, IN/OUT, Class Counts, FPS, Latency
- Auditable event table and CSV export
- Visual evidence crops gallery

### Model Evaluation & Training
```bash
# Compare models on held-out test set
python scripts/compare_models.py --baseline models/deployment/yolo11n_coco.pt --finetuned models/research/yolo11n_finetuned_best.pt

# Run fine-tuning (if desired)
python src/train.py --config configs/train_small.yaml
```

---

## 15. Repository Structure

```text
├── app/
│   └── app.py                      # Streamlit interactive dashboard
├── configs/
│   ├── config.yaml                 # Central system configuration
│   ├── bytetrack_luggage.yaml      # ByteTrack tracker parameters
│   ├── train_small.yaml            # YOLO11n fine-tuning configuration
│   ├── train_medium.yaml           # YOLO11s fine-tuning configuration
│   └── train_conservative.yaml     # Conservative fine-tuning configuration
├── demo/
│   ├── input_airport_luggage.mp4   # Primary carousel demo (447 frames)
│   └── benchmark/                  # Additional Pexels test clips
├── docs/
│   ├── antigravity_handoff_audit.md # Complete system handoff audit
│   ├── baseline_vs_finetuned.md    # Held-out detector comparison
│   ├── counting_benchmark.md       # Multi-video counting evaluation
│   ├── tracker_comparison.md       # ByteTrack vs BoT-SORT evaluation
│   ├── performance_benchmark.md    # Latency, FPS, GPU vs CPU benchmark
│   ├── model_results.md            # Checkpoint inventory & metrics
│   ├── failure_analysis.md         # Domain shift and visual error analysis
│   ├── reproducibility.md          # Environment & reproduction guide
│   └── dataset_selection.md        # Open Images subset provenance
├── models/
│   ├── deployment/                 # Production checkpoints (yolo11n_coco.pt)
│   └── research/                   # Fine-tuned checkpoints (*_best.pt)
├── outputs/
│   ├── demo/                       # Canonical demo MP4, JSON, CSV, and events
│   ├── benchmarks/                 # Video benchmark outputs
│   └── evaluation/                 # Test set confusion matrices and PR curves
├── src/
│   ├── counter.py                  # LineCounter & ZoneCounter geometric logic
│   ├── detector.py                 # LuggageDetector YOLO wrapper
│   ├── tracker.py                  # Multi-object tracking integration
│   ├── visualization.py            # Overlay rendering and HUD panel
│   ├── inference_video.py          # Video processing pipeline & CLI
│   └── utils.py                    # Config, device selection, I/O helpers
└── tests/
    ├── test_counter.py             # Geometric counting unit tests
    └── test_end_to_end.py          # End-to-end integration tests
```

---

## 16. Engineering Challenges & Solutions

1. **Conveyor Line Jitter:** Luggage wobbling near the virtual gate caused duplicate counts.
   - *Solution:* Implemented signed perpendicular distance with a deadband buffer (`deadband_px=8`). Bags must clearly enter from one half-plane and exit into the other.
2. **Transient False Tracks:** Passing airport personnel or shadows generated single-frame boxes.
   - *Solution:* Implemented minimum track maturity filtering (`min_track_age=3`). Tracks must persist across consecutive frames before crossing validation.
3. **Domain Shift Discrepancy:** The fine-tuned model scored higher on test photos but lower on conveyor footage.
   - *Solution:* Diagnosed class imbalance (handbags dominated the Open Images subset) and maintained the COCO-pretrained model as the operational deployment engine.

---

## 17. Project Limitations

1. **Dataset Class Imbalance:** Open Images contains significantly more handbags than suitcases or backpacks, causing representation skew.
2. **Single Camera Boundary:** The system monitors a fixed calibrated gate; it does not perform multi-camera passenger-to-bag re-identification.
3. **Dense Piles & Severe Occlusion:** When bags are stacked directly on top of one another on a carousel, standard 2D bounding boxes can merge.
4. **Camera Geometry Dependency:** Virtual counting lines must be oriented perpendicular to luggage travel.

---

## 18. Future Work

- **Conveyor-Specific Dataset:** Annotate video sequences collected directly from airport security checkpoints and carousel feeds.
- **Baggage Damage / Anomaly Detection:** Classify broken handles, open zippers, and tears during conveyor transit.
- **RFID / Barcode Fusion:** Cross-reference vision-based counts with physical baggage tag scans.
- **Multi-Camera Association:** Track bags from check-in through sorting belts to carousel retrieval without facial recognition.

---

## 19. Privacy and Ethical Considerations

This system is strictly designed for **luggage monitoring and baggage logistics**. It explicitly does not perform facial recognition, passenger profiling, biometric tracking, or personal identity association.

---

## 20. License

This graduation project codebase is licensed under the [MIT License](LICENSE). Source video clips are credited to Pexels creators under free-use licenses.
