# Multi-Object Tracker Comparison: ByteTrack vs. BoT-SORT

## 1. Objectives and Protocol

In automated luggage counting, the tracker's role is to maintain temporal identity across consecutive video frames so that each physical bag is counted exactly once upon traversing a counting gate.

We evaluated two modern tracking algorithms integrated with Ultralytics YOLO11:
1. **ByteTrack:** Employs low-score detection association with a Kalman filter to recover occluded or motion-blurred objects.
2. **BoT-SORT:** Augments Kalman tracking with Camera Motion Compensation (CMC) and optional visual appearance feature extraction (Re-ID).

Both trackers were tested on the verified primary airport carousel footage (`demo/input_airport_luggage.mp4`, 447 frames, 960×540 at 30 fps) using the deployment model (`models/deployment/yolo11n_coco.pt`) at identical detection settings (`conf=0.25`, `iou=0.50`, `imgsz=640`).

> [!NOTE]
> Because public video footage lacks pixel-level ground-truth trajectory annotations, we do NOT fabricate synthetic MOTA, IDF1, or HOTA scores. Comparison is grounded strictly on measured runtime, system memory, ID continuity, and downstream count accuracy.

---

## 2. Empirical Tracking Benchmark

| Metric | ByteTrack | BoT-SORT | Delta / Difference |
|---|:---:|:---:|:---:|
| **Count Accuracy (4 Bags GT)** | **4 / 4 (100.0%)** | **4 / 4 (100.0%)** | Identical |
| **Total Counts (IN / OUT)** | 3 IN, 1 OUT | 3 IN, 1 OUT | Identical |
| **Duplicate Counting Events** | **0** | **0** | None |
| **Overall Processing FPS** | **42.23 FPS** | **32.65 FPS** | **ByteTrack is +29.3% faster** |
| **Average Inference Latency** | **20.82 ms/frame** | **27.63 ms/frame** | ByteTrack saves 6.81 ms/frame |
| **Elapsed Processing Time** | **10.58 s** | **13.69 s** | ByteTrack saves 3.11 s |
| **Peak Process Memory** | 494.5 MB | 457.5 MB | Comparable |
| **Track IDs Assigned to Counted Bags** | `[1, 2, 9, 41]` | `[1, 2, 13, 39]` | Consistent continuity |
| **ID Stability during Crossing** | Stable (no switches) | Stable (no switches) | Both cross cleanly |

---

## 3. Qualitative and Behavioral Analysis

### Visible ID Stability and Continuity
- **ByteTrack:** Successfully tracked distant, low-contrast suitcases along the rear section of the carousel (Events at 2.67s and 5.37s) by associating low-confidence bounding boxes in its second-stage association step. IDs remained stable throughout line traversal.
- **BoT-SORT:** Maintained equally stable tracks across all four crossing instances. However, slight track fragmentation occurred on distant bags prior to reaching the gate, resulting in higher nominal Track IDs (e.g., ID 13 and 39 vs. ByteTrack's 9 and 41).

### Camera Motion Compensation (CMC) vs. Stationary CCTV
- BoT-SORT computes image feature matches between consecutive frames to estimate camera ego-motion. 
- In airport baggage surveillance, CCTV and carousel monitoring cameras are rigidly mounted and stationary. Running GMC on fixed viewpoints adds ~6.8 ms of CPU/GPU overhead per frame without providing kinematic benefit.

### Re-Identification (Re-ID)
- Luggage items frequently possess similar rectangular geometries and neutral color palettes (black, grey, navy nylon). Without fine-grained visual feature extractors, appearance-based Re-ID can trigger false associations between separate black suitcases. ByteTrack's pure motion-guided association avoids this ambiguity.

---

## 4. Final Tracker Selection

**ByteTrack is selected as the primary tracking engine for the deployment pipeline.**

**Rationale:**
1. **Real-Time Performance:** Achieves **42.2 FPS** on Apple Silicon MPS (exceeding camera frame rate of 30 FPS by 40%), providing ample headroom for edge deployments.
2. **Identical Accuracy:** Delivered 100% counting accuracy (4/4) with zero duplicate counts and zero missed crossings.
3. **No Unnecessary Overhead:** Eliminates GMC computation that provides no utility on fixed surveillance cameras.
4. **BoT-SORT Preservation:** BoT-SORT remains fully supported in the codebase and configuration (`tracker: botsort`) as a user-configurable alternative for handheld or pan-tilt-zoom (PTZ) cameras.
