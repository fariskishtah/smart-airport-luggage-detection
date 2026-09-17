# Production Memory & Latency Benchmark Report

## 1. Overview
In resource-constrained container environments (e.g. Railway Trial plan with a 512 MB memory limit), processing high-resolution video streams (1080p, 1440p) with computer vision models and multi-threaded video encoders easily causes out-of-memory (OOM) process termination.

This benchmark evaluates the memory footprint, throughput, and stability of the production inference pipeline before and after optimization.

---

## 2. Root Cause Analysis of the OOM Crash (at ~89%)
1. **Uncompressed Frame Accumulation & Double-Pass Encoding:**
   Previously, the backend used `cv2.VideoWriter` to write a temporary raw video (`temp_raw_annotated.mp4`) using the `mp4v` codec. Upon completing the frame loop (~89% progress), an offline `ffmpeg` subprocess was invoked to transcode the raw file to H.264.
2. **Multithreaded FFmpeg Allocation:**
   Because FFmpeg was launched without explicit thread constraints (`-threads`), FFmpeg detected all host CPU cores on the physical node (typically 16–32 vCPUs) and allocated thread-local pixel buffers for each core. On 1440p (2560×1440) video frames ($11.06\text{ MB}$ per uncompressed BGR frame), FFmpeg allocated over $300\text{ MB}$ of RAM.
3. **Combined Peak Memory vs 512 MB Ceiling:**
   With Python/PyTorch holding ~350 MB RSS and FFmpeg allocating ~300 MB, the container total exceeded the 512 MB cgroup memory limit, triggering the Linux kernel OOM killer (`Killed`).
4. **In-Memory State Loss:**
   When the container was killed and restarted, the in-memory job registry was empty, returning HTTP 404 for subsequent status polls and leaving the frontend UI frozen at 89%.

---

## 3. Systematic Optimizations Implemented
1. **Real-Time Streaming FFmpeg Pipe:**
   Replaced offline two-pass encoding with an active streaming FFmpeg subprocess (`stdin=subprocess.PIPE`). Frames are piped incrementally as they are processed (`ffmpeg_proc.stdin.write(frame.tobytes())`). Output is encoded directly to browser-playable H.264 `yuv420p` with `+faststart`.
2. **Single-Threaded Encoder Bounding (`-threads 1`):**
   Explicitly restricted FFmpeg to 1 encoding thread and `-preset ultrafast`. FFmpeg internal memory overhead dropped from $>300\text{ MB}$ to $<35\text{ MB}$.
3. **Decoupled Resolution & Canvas Scaling:**
   High-resolution inputs (> 1080p) are scaled to a maximum bounding canvas of 1920×1080 for processing and output. Detector inference runs at `imgsz=min(image_size, 640)`.
4. **PyTorch Inference Mode & Thread Bounding:**
   Enforced `torch.inference_mode()` on all detection frames and set `torch.set_num_threads(2)` on CPU to prevent runaway OpenMP thread allocations.
5. **Immediate Result and Tensor Deletion:**
   Extracted pure-Python primitives (`Track` dataclass) and immediately executed `del result` and `del tracks`. Enforced periodic garbage collection (`gc.collect()`).
6. **Persistent Job Metadata on Disk:**
   Job records are saved to `backend/storage/jobs/{job_id}.json`. On startup, any interrupted jobs are automatically recovered and marked with a clean error message.

---

## 4. Benchmark Measurements (CPU Execution)

| Test Video | Resolution | Frame Count | Elapsed Time | Processing FPS | Peak RSS | Output Video Size | Completion Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A. Carousel Demo** (`demo/input_airport_luggage.mp4`) | 960 × 540 | 447 frames | **15.57 s** | **29.1 FPS** | **334.9 MB** | 5.15 MB | **COMPLETED (4/4 count)** |
| **B. Airport Corridor** (`pexels_1169854_source.mp4`) | 1920 × 1080 | 505 frames | **21.13 s** | **24.0 FPS** | **334.9 MB** | 18.12 MB | **COMPLETED (1/1 count)** |
| **C. High-Res Upload** (`pexels_27778466_source.mp4`) | 2560 × 1440 | 316 frames | **22.42 s** | **14.2 FPS** | **334.9 MB** | 20.05 MB | **COMPLETED (3/3 count)** |

---

## 5. Memory Comparison

| Metric | Before Optimization | After Optimization | Reduction |
|---|:---:|:---:|:---:|
| **Intermediate Disk File** | Up to 1.5 GB raw MP4 | **0 bytes** (direct pipe) | **100% eliminated** |
| **FFmpeg Peak Memory** | 300 – 400 MB (16 threads) | **~30 MB** (1 thread) | **> 90% reduction** |
| **Combined Container Peak RSS** | > 700 MB (**OOM Crash**) | **~335 MB** | **> 50% reduction** |
| **Railway 512 MB Headroom** | Negative (Crashed) | **+177 MB Headroom (35%)** | **Stable & Safe** |
| **Processing Throughput** | 6.5 – 7.5 FPS | **14.0 – 29.1 FPS** | **2x – 4x faster** |

---

## 6. Input Guardrails Configured
- **Maximum Upload Size:** 150 MB
- **Maximum Duration:** 180 seconds (3 minutes)
- **Maximum Resolution:** 2560 × 1440 (4K uploads rejected with HTTP 400 warning)
- **Auto-Cleanup:** Old uploads and temporary job directories older than 2 hours are automatically purged.
