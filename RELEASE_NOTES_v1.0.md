# v1.0-production

Stable graduation-project production release for the **Smart Airport Luggage Detection, Tracking, Counting & Analytics System**.

---

## 1. Core Features
- **Object Detection:** Ultralytics YOLO11n optimized for luggage classes (`suitcase`, `backpack`, `handbag`).
- **Multi-Object Tracking:** Temporal association via ByteTrack maintaining persistent spatial identities across conveyor travel.
- **Persistent Spatial IDs:** Prevents temporal counting redundancy; each physical piece of luggage is counted at most once per session.
- **Directional Line Counting:** 2D signed distance vector geometry with calibrated deadband (`3.0px`) to prevent boundary jitter.
- **Polygonal Zone Counting:** Point-in-polygon ray casting detecting discrete `ENTER` and `EXIT` events across user-defined ROIs.
- **Directional Metrics:** IN / OUT classification, net throughput, and per-category breakdown.
- **Duplicate-Count Prevention:** False-track rejection via minimum track age filtering (`min_track_age=2`) and permanent ID deduplication registers.
- **Browser-Playable Video Output:** H.264 `yuv420p` MP4 encoding with `+faststart` metadata for instant web streaming.
- **Auditable Event CSV:** Timestamped ledger recording event ID, frame number, timestamp, track ID, category, confidence, and centroid coordinates.
- **Evidence Snapshots:** High-resolution bounding-box image crops (`event_XXX.jpg`) generated for every validated crossing event.
- **Local Application:** Full-featured interactive Streamlit dashboard (`app/app.py`) with MPS / CUDA hardware acceleration.
- **Cloud Web Application:** Next.js 14 App Router application deployed on Vercel Edge with modern Airport Operations glassmorphism UI.

---

## 2. AI Results & Model Strategy
- **Dataset Provenance:** Curated Open Images V7 subset of 396 images and 522 bounding boxes partitioned into a 70/20/10 split (277 train / 79 val / 40 test).
- **Fine-Tuned Research Models:**
  - `YOLO11n Fine-Tuned`: mAP50 = 0.589, mAP50-95 = 0.443
  - `YOLO11s Fine-Tuned`: mAP50 = 0.596, mAP50-95 = 0.457
- **Domain Shift Finding:** While custom transfer learning improved static held-out test metrics, real-world airport conveyor footage exhibits significant domain shift (motion blur, metallic reflections, severe angle tilts).
- **Operational Deployment Model:** Ultralytics YOLO11n COCO Pretrained (`models/deployment/yolo11n_coco.pt`) was selected as the deployment default due to superior cross-domain generalization on industrial baggage carousels.

---

## 3. Counting & Tracking Verification
- **Primary Carousel Benchmark Demo (`demo/input_airport_luggage.mp4`):**
  - Total frames: 447 frames (30 FPS)
  - Ground Truth: 4 luggage items
  - Automated Prediction: **4 / 4 items counted (100% precision & recall)**
  - Directional Breakdown: 2 IN, 2 OUT
  - Track IDs: `[1, 8, 10, 37]`
- **Multi-Video Benchmark Verification:**
  - High-resolution airport corridor benchmark (`pexels_1169854_source.mp4`, 1080p): **100% verified**
  - High-resolution airport passenger benchmark (`pexels_27778466_source.mp4`, 1440p): **100% verified**

---

## 4. Production Architecture
- **Frontend (Vercel):** [https://smart-airport-luggage-web.vercel.app](https://smart-airport-luggage-web.vercel.app)
  - Autonomous Next.js 14 App Router
  - Transparent reverse proxy rewrites (`/api/backend/*` -> Cloud AI Backend) eliminating client CORS friction
- **Backend (Railway Cloud):** [https://smart-airport-luggage-backend-production.up.railway.app](https://smart-airport-luggage-backend-production.up.railway.app)
  - Containerized FastAPI application running CPU-optimized PyTorch
  - Asynchronous single-worker queue (`concurrency_limit: 1`) preventing cloud OOM crashes
- **Direct Health Monitoring:** `/health` endpoint reporting system, model, tracker, and hardware state.

---

## 5. Reliability & Memory Engineering
- **Real-Time Streaming FFmpeg Pipe:** Completely eliminated intermediate uncompressed video files on disk. Piped frames directly to an active single-threaded FFmpeg subprocess (`stdin=subprocess.PIPE`, `-threads 1`, `-preset ultrafast`), reducing encoding RAM from $>350\text{ MB}$ to $<35\text{ MB}$.
- **1080p Processing Canvas Bound:** Scaled high-resolution inputs (> 1080p) to a maximum bounding canvas of 1920×1080, preventing memory ballooning while preserving aspect ratio.
- **PyTorch Inference Mode & Thread Bounding:** Enforced `torch.inference_mode()` and restricted CPU OpenMP threads to 2 (`torch.set_num_threads(2)`).
- **Disk-Persisted Job Status & Stale Recovery:** Job records are persisted to disk (`backend/storage/jobs/{job_id}.json`). On container restarts, interrupted jobs are automatically recovered and marked with clear user guidance.
- **Frontend Watchdog:** Client-side polling watchdog detects network stalls or timeouts (> 90s) and transitions gracefully to an error card with a retry button.
- **Zero Ephemeral Tunnel Dependencies:** Cloudflare temporary tunnels have been fully retired; all communication routes over permanent HTTPS infrastructure.

---

## 6. Known Limitations
- **Single Camera Viewpoint:** Designed for calibrated entry/exit conveyor gates; does not perform cross-camera passenger-to-bag re-identification.
- **Calibrated Gate Alignment:** Counting accuracy depends on orienting the virtual gate perpendicular to baggage velocity.
- **Dense Stacking / Piling:** Severe overlapping bags on crowded carousels can cause temporary bounding box merges.
- **Concurrency Limit:** Production deployment enforces single-job concurrency (`concurrency_limit: 1`) to guarantee operation within free/trial cloud memory tiers.
- **Maximum Input Resolution:** Capped at 2560 × 1440 (1440p); 4K uploads are rejected upfront to protect cloud compute stability.
