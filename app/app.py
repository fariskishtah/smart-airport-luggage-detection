from pathlib import Path
import sys
import tempfile

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.inference_video import process_video

st.set_page_config(page_title="Smart Airport Luggage Analytics", page_icon="🧳", layout="wide")
st.title("Smart Airport Luggage Detection & Analytics")
st.caption("YOLO11 Detection · ByteTrack/BoT-SORT · Persistent Unique-ID Counting · Auditable Event Ledger")

# Explicit Model Choices for Graduation Defense
models = {
    "Deployment Model — YOLO11n COCO (Recommended: 4/4 on Carousel Demo)": "models/deployment/yolo11n_coco.pt",
    "Research Model — YOLO11n Fine-Tuned (Held-Out mAP: 0.465)": "models/research/yolo11n_finetuned_best.pt",
    "Research Model — YOLO11s Fine-Tuned (19.1 MB Checkpoint)": "models/research/yolo11s_finetuned_best.pt",
    "Research Model — YOLO11n Conservative (Balanced Weights)": "models/research/yolo11n_conservative_best.pt",
}

# Fallback for paths if symlinks are not resolved
for label, p in list(models.items()):
    if not (ROOT / p).exists():
        fallback_p = "models/yolo11n.pt" if "COCO" in label else "models/yolo11n_luggage_best.pt"
        models[label] = fallback_p

with st.sidebar:
    st.header("Analysis Configuration")
    model_label = st.selectbox("Model Checkpoint", list(models.keys()))
    tracker = st.selectbox("Tracking Algorithm", ["bytetrack", "botsort"])
    confidence = st.slider("Confidence Threshold", 0.05, 0.90, 0.25, 0.05)
    iou = st.slider("NMS IoU Threshold", 0.10, 0.90, 0.50, 0.05)
    mode = st.radio("Counting Geometry", ["line", "zone"], horizontal=True)
    directions = ["any", "positive", "negative"] if mode == "line" else ["any", "in", "out"]
    direction = st.selectbox("Count Direction", directions)
    min_age = st.number_input("Minimum Track Age (frames)", min_value=1, max_value=30, value=3)
    save_snapshots = st.checkbox("Save Event Evidence Crops", value=True)

st.subheader("Video Source")
source_mode = st.radio("Choose Input Source:", ["Primary Airport Carousel Demo", "Upload Custom Video"], horizontal=True)

source_path = None
uploaded_name = None

if source_mode == "Primary Airport Carousel Demo":
    demo_file = ROOT / "demo/input_airport_luggage.mp4"
    if demo_file.is_file():
        source_path = demo_file
        uploaded_name = "input_airport_luggage.mp4"
        st.info("Primary Demo Loaded: `demo/input_airport_luggage.mp4` (447 frames, 30 FPS, Carousel).")
    else:
        st.warning("Demo file not found at demo/input_airport_luggage.mp4")
else:
    uploaded = st.file_uploader("Upload an MP4, MOV, AVI or MKV video", type=["mp4", "mov", "avi", "mkv"])
    if uploaded:
        uploaded_name = uploaded.name

if (source_path or source_mode == "Upload Custom Video") and st.button("Start Analysis", type="primary", use_container_width=True):
    if source_mode == "Upload Custom Video" and not uploaded:
        st.warning("Please upload a video file first.")
    else:
        with tempfile.TemporaryDirectory(prefix="luggage_demo_") as temp:
            temp_dir = Path(temp)
            if source_mode == "Primary Airport Carousel Demo":
                source = source_path
            else:
                source = temp_dir / uploaded.name
                source.write_bytes(uploaded.getbuffer())

            output = temp_dir / "processed.mp4"
            tracker_config = "configs/bytetrack_luggage.yaml" if tracker == "bytetrack" else "botsort.yaml"
            overrides = {
                "model": {"path": models[model_label], "confidence": confidence, "iou": iou, "image_size": 640},
                "tracking": {"tracker": tracker, "config": tracker_config},
                "counting": {"mode": mode, "direction": direction, "min_track_age": int(min_age)},
                "runtime": {"save_snapshots": save_snapshots, "save_events": True}
            }
            progress = st.progress(0, "Preparing detector and tracker…")

            def update_progress(done, total):
                progress.progress(min(done / max(total, 1), 1.0), f"Processing frame {done:,} / {total:,}")

            try:
                stats = process_video(source, output, overrides=overrides, progress_callback=update_progress)
                progress.progress(1.0, "Analysis complete!")

                st.success(f"Processing finished successfully in {stats['elapsed_seconds']:.2f} s ({stats['processing_fps']:.1f} FPS)!")

                cols = st.columns(6)
                values = [
                    stats["total_count"],
                    stats["in_count"],
                    stats["out_count"],
                    stats["class_counts"].get("suitcase", 0),
                    stats["class_counts"].get("backpack", 0),
                    stats["class_counts"].get("handbag", 0)
                ]
                for col, label, value in zip(cols, ["Total Count", "IN", "OUT", "Suitcases", "Backpacks", "Handbags"], values):
                    col.metric(label, value)

                perf = st.columns(2)
                perf[0].metric("Processing Throughput", f"{stats['processing_fps']:.1f} FPS")
                perf[1].metric("Detector Latency", f"{stats['average_inference_latency_ms']:.1f} ms/frame")

                video_bytes = output.read_bytes()
                st.subheader("Annotated Video Playback")
                st.video(video_bytes)
                st.download_button("Download Annotated H.264 Video", video_bytes, "luggage_analysis.mp4", "video/mp4")

                events = pd.DataFrame(stats["crossing_events"])
                st.subheader("Auditable Event Ledger")
                if events.empty:
                    st.info("No crossing event met the configured geometric and temporal criteria.")
                else:
                    display_cols = [c for c in ["event_id", "frame", "timestamp", "track_id", "class", "confidence", "direction", "event_type", "centroid_x", "centroid_y"] if c in events.columns]
                    st.dataframe(events[display_cols], use_container_width=True, hide_index=True)
                    csv_data = events.to_csv(index=False)
                    st.download_button("Download Events CSV", csv_data, "events.csv", "text/csv")

                    chart_col1, chart_col2 = st.columns(2)
                    if "class" in events.columns:
                        chart_col1.subheader("Luggage by Class")
                        chart_col1.bar_chart(events["class"].value_counts())
                    if "timestamp" in events.columns:
                        chart_col2.subheader("Cumulative Count Timeline")
                        timeline = events.set_index("timestamp").assign(cumulative_count=range(1, len(events) + 1))
                        chart_col2.line_chart(timeline["cumulative_count"])

                    # Display Evidence Crops Gallery
                    evidence_dir = temp_dir / "events"
                    if save_snapshots and evidence_dir.is_dir():
                        snapshots = sorted(evidence_dir.glob("*.jpg"))
                        if snapshots:
                            st.subheader("Event Evidence Crops")
                            img_cols = st.columns(min(len(snapshots), 4))
                            for i, snap in enumerate(snapshots):
                                with img_cols[i % len(img_cols)]:
                                    st.image(str(snap), caption=snap.name, use_container_width=True)

            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                st.exception(exc)
else:
    st.info("Select a video source above, adjust detection and tracking settings in the sidebar, and click 'Start Analysis'.")
