from __future__ import annotations

import cv2
import json
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from backend.schemas.job import AnalysisRequest, JobResult, JobSubmitResponse
from backend.services.job_manager import job_manager
from backend.services.storage_service import StorageService

LOG = logging.getLogger("backend.api")
router = APIRouter()

ROOT = Path(__file__).resolve().parents[2]


@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Health monitoring endpoint reporting system, model, and tracker status."""
    import torch
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    return {
        "status": "ok",
        "service": "Smart Airport Luggage Detection API",
        "model": "YOLO11n COCO Pretrained (Deployment Default)",
        "tracker": "bytetrack",
        "device": device,
        "concurrency_limit": 1
    }


@router.post("/api/analyze", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_analysis(request: AnalysisRequest):
    """Submit a video analysis job referencing a remote video URL."""
    if not request.video_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="video_url is required when submitting to /api/analyze. Use /api/analyze/upload for direct file uploads."
        )

    job_id = await job_manager.submit_job(request)
    return JobSubmitResponse(
        job_id=job_id,
        status="queued",
        message="Video analysis job queued successfully."
    )


@router.post("/api/analyze/upload", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_and_analyze(
    file: UploadFile = File(...),
    mode: str = Form("counting"),
    count_mode: str = Form("line"),
    confidence: float = Form(0.20),
    iou: float = Form(0.50),
    line_start: Optional[str] = Form(None),
    line_end: Optional[str] = Form(None),
    direction: str = Form("any"),
    min_track_age: int = Form(2),
    tracker: str = Form("bytetrack"),
):
    """Upload video directly and submit analysis job without requiring third-party storage."""
    temp_job_id = "temp"
    try:
        # Parse coordinates
        s = json.loads(line_start) if line_start else [0.55, 0.20]
        e = json.loads(line_end) if line_end else [0.55, 0.92]
    except Exception:
        s = [0.55, 0.20]
        e = [0.55, 0.92]

    req = AnalysisRequest(
        mode=mode,  # type: ignore
        count_mode=count_mode,  # type: ignore
        confidence=confidence,
        iou=iou,
        line_start=s,
        line_end=e,
        direction=direction,  # type: ignore
        min_track_age=min_track_age,
        tracker=tracker,  # type: ignore
    )

    import uuid
    actual_job_id = str(uuid.uuid4())[:8]
    try:
        local_path = StorageService.save_uploaded_file(file.file, file.filename, actual_job_id)
        # Validate video integrity, duration, and resolution
        probe_cap = cv2.VideoCapture(str(local_path))
        if not probe_cap.isOpened():
            probe_cap.release()
            local_path.unlink(missing_ok=True)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is not a readable video.")

        probe_width = int(probe_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        probe_height = int(probe_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        probe_fps = probe_cap.get(cv2.CAP_PROP_FPS) or 25.0
        probe_frames = int(probe_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        probe_cap.release()

        probe_duration = probe_frames / max(probe_fps, 1.0)
        if probe_duration > 180.0:
            local_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video duration ({round(probe_duration)}s) exceeds maximum allowed 180s (3 minutes). Please upload a shorter clip."
            )
        if probe_width > 2560 or probe_height > 1440:
            local_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video resolution ({probe_width}x{probe_height}) exceeds maximum input resolution: 2560 × 1440. Please upload a 1440p, 1080p, or 720p video."
            )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {exc}")

    # Enqueue job with pre-saved local file
    out_dir = StorageService.get_job_output_dir(actual_job_id)
    out_video = out_dir / "annotated.mp4"

    from backend.services.job_manager import JobRecord
    record = JobRecord(
        job_id=actual_job_id,
        status="queued",
        progress=0.05,
        current_step="Uploaded. Queued for analysis.",
        request=req,
        input_file_path=local_path,
        output_dir=out_dir,
        output_video_path=out_video,
    )
    job_manager.jobs[actual_job_id] = record
    record.save_to_disk()
    await job_manager.queue.put(actual_job_id)

    return JobSubmitResponse(
        job_id=actual_job_id,
        status="queued",
        message="Video uploaded and analysis job queued successfully."
    )


@router.post("/api/analyze/demo", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_demo_clip():
    """Instantly trigger analysis on the verified carousel demo video (demo/input_airport_luggage.mp4)."""
    demo_video = ROOT / "demo/input_airport_luggage.mp4"
    if not demo_video.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo video not found on server.")

    req = AnalysisRequest(
        mode="counting",
        count_mode="line",
        confidence=0.20,
        iou=0.50,
        line_start=[0.55, 0.20],
        line_end=[0.55, 0.92],
        direction="any",
        min_track_age=2,
        tracker="bytetrack",
        image_size=640,
        model_name="yolo11n_coco",
    )

    import uuid, shutil
    demo_job_id = f"demo_{str(uuid.uuid4())[:6]}"
    out_dir = StorageService.get_job_output_dir(demo_job_id)
    out_video = out_dir / "annotated.mp4"

    # Copy demo video to storage input
    input_copy = out_dir.parent.parent / "uploads" / f"{demo_job_id}_input.mp4"
    shutil.copyfile(demo_video, input_copy)

    from backend.services.job_manager import JobRecord
    record = JobRecord(
        job_id=demo_job_id,
        status="queued",
        progress=0.05,
        current_step="Loaded demo carousel video. Queued for analysis.",
        request=req,
        input_file_path=input_copy,
        output_dir=out_dir,
        output_video_path=out_video,
    )
    job_manager.jobs[demo_job_id] = record
    await job_manager.queue.put(demo_job_id)

    return JobSubmitResponse(
        job_id=demo_job_id,
        status="queued",
        message="Primary airport carousel demo queued for analysis."
    )


@router.get("/api/jobs/{job_id}", response_model=JobResult)
async def get_job_status(job_id: str):
    """Retrieve current status, progress, and results for a job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")
    return job


@router.api_route("/api/jobs/{job_id}/video", methods=["GET", "HEAD"])
async def get_job_video(job_id: str):
    """Stream the processed H.264 MP4 video."""
    out_dir = StorageService.get_job_output_dir(job_id)
    video_path = out_dir / "annotated.mp4"
    if not video_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output video not ready or missing.")
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"luggage_analysis_{job_id}.mp4"
    )


@router.api_route("/api/jobs/{job_id}/events.csv", methods=["GET", "HEAD"])
async def get_job_csv(job_id: str):
    """Download the auditable events CSV."""
    out_dir = StorageService.get_job_output_dir(job_id)
    csv_path = out_dir / "events.csv"
    if not csv_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Events CSV not ready or missing.")
    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=f"events_{job_id}.csv"
    )


@router.api_route("/api/jobs/{job_id}/events/{filename}", methods=["GET", "HEAD"])
async def get_event_snapshot(job_id: str, filename: str):
    """Retrieve an event snapshot crop image."""
    out_dir = StorageService.get_job_output_dir(job_id)
    snapshot_path = out_dir / "events" / filename
    if not snapshot_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found.")
    return FileResponse(
        path=str(snapshot_path),
        media_type="image/jpeg"
    )
