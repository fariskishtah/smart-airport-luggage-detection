# Project audit — 17 September 2026

## Environment

- Apple Silicon M2 (`arm64`), 8 GB unified memory
- macOS 26.5.2; Python 3.11.15 virtual environment
- PyTorch 2.14.0 with MPS available; CUDA unavailable
- Ultralytics 8.3.199; OpenCV 4.12.0.88
- Storage before upgrade: 9.4 GiB free; repository 1.5 GiB, almost entirely the virtual environment

## Working components to preserve

- YOLO11n COCO baseline detects the three configured luggage classes.
- Ultralytics ByteTrack integration provides persistent IDs.
- Oriented-line counter uses signed distance, deadband, minimum age, direction filtering and a permanent ID registry.
- Verified Pexels carousel demo produces four unique crossing events for four manually observed bags.
- H.264 MP4 and JSON output; Apple MPS demo throughput measured at 38.8 FPS.
- Streamlit upload/process/download flow starts successfully.
- Six deterministic counter tests pass.
- Dataset validator, training/evaluation entry points, configuration, architecture, demo provenance and presentation outline exist.

## Weaknesses

- No downloaded luggage-specific training set, fine-tuned checkpoint or held-out luggage mAP.
- Dataset validator lacks visual reports, annotation-duplicate/aspect-ratio checks and split leakage checks.
- Only line counting exists; no zone entry/exit mode or optional cooldown.
- Event records omit confidence/centroid, are JSON-only and do not save evidence crops.
- UI exposes few runtime controls and no event analytics.
- ByteTrack has not been compared qualitatively with BoT-SORT.
- Counting evidence is limited to one video; detector baseline test is only a COCO8 smoke test.
- Reproducibility, storage plan, performance benchmark, failure analysis and defense Q&A are absent.

## Upgrade scope

Preserve the existing modules and demo while adding a bounded three-class Open Images dataset, quality/split tooling, real transfer learning for two feasible model sizes, held-out evaluation, baseline comparison, line/zone counting, auditable CSV/snapshots, a configurable dashboard, broader tests and presentation-ready reports. MPS is preferred with a CPU fallback if an operation is unstable.

