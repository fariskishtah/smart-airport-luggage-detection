# Multi-Video Counting Benchmark

## 1. Overview and Methodology

Counting performance cannot be measured solely by bounding-box mean Average Precision (mAP). In video analytics, a high-mAP detector can fail downstream if tracks fragment, while a fast, stable detector coupled with persistent multi-object tracking can deliver zero counting error.

This benchmark evaluates the end-to-end detection, tracking, and counting pipeline across three legally licensed video sequences depicting baggage handling, carousels, and conveyor operations:
- **Clip 1:** `demo/input_airport_luggage.mp4` (Raphael Kim / Pexels, CC0/free to use)
- **Clip 2:** `demo/benchmark/pexels_1169854_source.mp4` (Pexels, free to use)
- **Clip 3:** `demo/benchmark/pexels_27778466_source.mp4` (Pexels, free to use)

For each video:
1. Ground-truth physical crossings were established through manual human verification.
2. The virtual counting line / gate was configured to intersect the physical flow of luggage.
3. The deployment model (`YOLO11n COCO`, 640px) was executed with `ByteTrack`.
4. Predicted crossings, direction, track IDs, and absolute errors were recorded.

---

## 2. Benchmark Results

| Video | Resolution & FPS | Frames | Ground Truth (GT) | Predicted Count | Absolute Error | Counting Accuracy | Model | Tracker | Mode & Geometry |
|---|---|---|:---:|:---:|:---:|:---:|---|---|---|
| **Carousel Demo** (`input_airport_luggage.mp4`) | 960×540, 30.0 fps | 447 | **4** | **4** | **0** | **100.0%** | YOLO11n COCO | ByteTrack | Line: `[0.55, 0.20]` → `[0.55, 0.92]` |
| **Traveler & Belt** (`pexels_1169854_source.mp4`) | 1920×1080, 29.97 fps | 505 | **3** | **3** | **0** | **100.0%** | YOLO11n COCO | ByteTrack | Line: `[0.55, 0.20]` → `[0.55, 0.92]` |
| **Conveyor Feed** (`pexels_27778466_source.mp4`) | 2560×1440, 25.0 fps | 316 | **3** | **3** | **0** | **100.0%** | YOLO11n COCO | ByteTrack | Line: `[0.20, 0.55]` → `[0.75, 0.55]` |

### Summary Statistics

- **Total Ground Truth Crossings:** 10
- **Total Predicted Crossings:** 10
- **Total Absolute Error:** 0
- **Mean Per-Video Counting Accuracy:** **100.0%**
- **Aggregate Counting Accuracy:** **100.0%**

---

## 3. Detailed Per-Video Crossing Ledger

### Video 1: `input_airport_luggage.mp4`
- **Track IDs Counted:** 2, 1, 9, 41
- **Event 1:** Frame 80 (2.667s), Track 2, suitcase, confidence 0.4487, direction: positive
- **Event 2:** Frame 120 (4.000s), Track 1, suitcase, confidence 0.9227, direction: negative
- **Event 3:** Frame 161 (5.367s), Track 9, suitcase, confidence 0.7138, direction: positive
- **Event 4:** Frame 334 (11.133s), Track 41, suitcase, confidence 0.4797, direction: positive
- **Analysis:** Clean 4/4 detection without false positives or double counts.

### Video 2: `pexels_1169854_source.mp4`
- **Track IDs Counted:** 2, 3, 19
- **Event 1:** Frame 83 (2.769s), Track 2, suitcase, confidence 0.7514, direction: positive
- **Event 2:** Frame 304 (10.143s), Track 3, suitcase, confidence 0.8392, direction: positive
- **Event 3:** Frame 340 (11.345s), Track 19, suitcase, confidence 0.4102, direction: positive
- **Analysis:** Accurately separates background passenger motion from rolling luggage items.

### Video 3: `pexels_27778466_source.mp4`
- **Track IDs Counted:** 1, 2, 49
- **Event 1:** Frame 31 (1.240s), Track 1, suitcase, confidence 0.8736, direction: negative
- **Event 2:** Frame 135 (5.400s), Track 2, suitcase, confidence 0.6107, direction: negative
- **Event 3:** Frame 205 (8.200s), Track 49, suitcase, confidence 0.4460, direction: negative
- **Analysis:** Luggage travels diagonally upward along an inclined conveyor belt. A horizontal gate across the belt at `y=0.55` reliably captures all three physical items that traverse the plane. Trailing items entering near the end of the clip (e.g., Track 100) do not reach the gate before video conclusion and are correctly excluded.

---

## 4. Model Comparison on Carousel Demo Video

To evaluate the effect of domain shift on actual counting accuracy, the identical carousel demo video (`demo/input_airport_luggage.mp4`) was evaluated with all four trained model checkpoints under identical tracking settings:

| Model Checkpoint | Role | Demo Predicted Count | Demo GT Count | Absolute Error | Counting Accuracy | Throughput (FPS) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **YOLO11n COCO (Pretrained)** | **Deployment** | **4** | **4** | **0** | **100.0%** | **39.3–42.2** |
| YOLO11n Fine-Tuned (Open Images) | Research | 1 | 4 | 3 | 25.0% | 44.5 |
| YOLO11s Fine-Tuned (Open Images) | Research | 1 | 4 | 3 | 25.0% | 36.8 |
| YOLO11n Conservative Fine-Tuned | Research | 1 | 4 | 3 | 25.0% | 48.0 |

### Scientific Significance
The fine-tuned models excel on high-resolution static product and street images (held-out mAP up to 0.465), but miss distant moving suitcases on the carousel belt because the Open Images training subset had substantial class imbalance (56% handbags, only 21% suitcases) and product-centric framing. The COCO-pretrained weights preserve strong general suitcase priors that detect moving suitcases consistently across various conveyor scales.
