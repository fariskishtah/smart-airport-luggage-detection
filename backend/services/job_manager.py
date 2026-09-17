from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from backend.schemas.job import AnalysisRequest, JobResult
from backend.services.inference_service import run_video_analysis
from backend.services.storage_service import StorageService

LOG = logging.getLogger("backend.jobs")

JOBS_META_DIR = StorageService.STORAGE_DIR / "jobs"
JOBS_META_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class JobRecord:
    job_id: str
    status: str = "queued"  # queued, processing, completed, failed
    progress: float = 0.0
    current_step: str = "Queued"
    request: Optional[AnalysisRequest] = None
    input_file_path: Optional[Path] = None
    output_dir: Optional[Path] = None
    output_video_path: Optional[Path] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    last_saved_at: float = field(default=0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": round(self.progress, 4),
            "current_step": self.current_step,
            "error_message": self.error_message,
            "result_data": self.result_data,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    def save_to_disk(self):
        try:
            target = JOBS_META_DIR / f"{self.job_id}.json"
            target.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        except Exception as exc:
            LOG.warning("Failed to persist job %s metadata: %s", self.job_id, exc)


class JobManager:
    def __init__(self, max_concurrent: int = 1):
        self.jobs: Dict[str, JobRecord] = {}
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.worker_task: Optional[asyncio.Task] = None
        self.base_url: str = ""

    def start_worker(self):
        # Recover stale jobs from disk
        self._recover_stale_jobs()
        # Clean old temporary files and uploads
        try:
            StorageService.cleanup_old_data(max_age_hours=2)
        except Exception as exc:
            LOG.warning("Error cleaning old storage data: %s", exc)

        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._process_queue())
            LOG.info("JobManager background worker started.")

    def _recover_stale_jobs(self):
        """Mark any interrupted jobs from previous container run as failed with clear message."""
        for meta_file in JOBS_META_DIR.glob("*.json"):
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                if data.get("status") in ("queued", "processing"):
                    data["status"] = "failed"
                    data["progress"] = 1.0
                    data["current_step"] = "Server container restarted"
                    data["error_message"] = (
                        "Processing failed due to server resource limits. "
                        "Please try a shorter or lower-resolution video."
                    )
                    meta_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    LOG.info("Recovered stale job %s: marked as failed due to container restart", data.get("job_id"))
            except Exception as exc:
                LOG.warning("Could not read job metadata %s: %s", meta_file, exc)

    async def submit_job(self, request: AnalysisRequest, local_file_path: Optional[Path] = None) -> str:
        job_id = str(uuid.uuid4())[:8]
        out_dir = StorageService.get_job_output_dir(job_id)
        out_video = out_dir / "annotated.mp4"

        record = JobRecord(
            job_id=job_id,
            status="queued",
            progress=0.05,
            current_step="Job queued in processing pipeline",
            request=request,
            input_file_path=local_file_path,
            output_dir=out_dir,
            output_video_path=out_video,
        )
        self.jobs[job_id] = record
        record.save_to_disk()
        await self.queue.put(job_id)
        LOG.info("Submitted job %s to queue (queue size: %d)", job_id, self.queue.qsize())
        return job_id

    def get_job(self, job_id: str) -> Optional[JobResult]:
        rec = self.jobs.get(job_id)
        if rec:
            return JobResult(
                job_id=rec.job_id,
                status=rec.status,
                progress=rec.progress,
                current_step=rec.current_step,
                error=rec.error_message,
                result=rec.result_data,
            )

        # Fallback to persistent disk metadata
        disk_path = JOBS_META_DIR / f"{job_id}.json"
        if disk_path.is_file():
            try:
                data = json.loads(disk_path.read_text(encoding="utf-8"))
                return JobResult(
                    job_id=data["job_id"],
                    status=data["status"],
                    progress=data.get("progress", 0.0),
                    current_step=data.get("current_step", ""),
                    error=data.get("error_message"),
                    result=data.get("result_data"),
                )
            except Exception as exc:
                LOG.warning("Error reading disk job %s: %s", job_id, exc)

        return None

    async def _process_queue(self):
        while True:
            job_id = await self.queue.get()
            rec = self.jobs.get(job_id)
            if not rec:
                self.queue.task_done()
                continue

            try:
                rec.status = "processing"
                rec.progress = 0.10
                rec.current_step = "Preparing video asset for inference…"
                rec.save_to_disk()

                # If no local file, download from video_url
                if rec.input_file_path is None or not rec.input_file_path.is_file():
                    if not rec.request or not rec.request.video_url:
                        raise ValueError("No video source provided (neither local file nor video_url).")
                    rec.input_file_path = await asyncio.to_thread(
                        StorageService.download_video, rec.request.video_url, job_id
                    )

                rec.current_step = "Executing detection, tracking & counting pipeline…"
                rec.save_to_disk()
                req = rec.request

                def progress_cb(pct: float, step: str):
                    rec.progress = pct
                    rec.current_step = step
                    # Throttle disk saves to at most once per 2 seconds
                    now = time.time()
                    if now - rec.last_saved_at >= 2.0:
                        rec.last_saved_at = now
                        rec.save_to_disk()

                # Run inference in worker thread with timeout safety
                stats = await asyncio.to_thread(
                    run_video_analysis,
                    input_path=rec.input_file_path,
                    output_video_path=rec.output_video_path,
                    mode=req.mode,
                    count_mode=req.count_mode,
                    confidence=req.confidence,
                    iou=req.iou,
                    line_start_norm=req.line_start,
                    line_end_norm=req.line_end,
                    zone_norm=req.zone,
                    direction=req.direction,
                    min_track_age=req.min_track_age,
                    tracker_name=req.tracker,
                    image_size=req.image_size,
                    model_name=req.model_name or "yolo11n_coco",
                    progress_callback=progress_cb,
                )

                # Optional Vercel Blob storage
                blob_video_url = await asyncio.to_thread(
                    StorageService.upload_to_vercel_blob,
                    rec.output_video_path,
                    f"jobs/{job_id}/annotated.mp4"
                )
                csv_path = rec.output_dir / "events.csv"
                blob_csv_url = await asyncio.to_thread(
                    StorageService.upload_to_vercel_blob,
                    csv_path,
                    f"jobs/{job_id}/events.csv"
                ) if csv_path.is_file() else None

                stats["output_video_url"] = blob_video_url or f"/api/jobs/{job_id}/video"
                stats["events_csv_url"] = blob_csv_url or f"/api/jobs/{job_id}/events.csv"

                rec.status = "completed"
                rec.progress = 1.0
                rec.current_step = "Completed"
                rec.result_data = stats
                rec.completed_at = time.time()
                rec.save_to_disk()
                LOG.info("Job %s completed successfully: %d items counted in %.2fs", job_id, stats["total_count"], stats["elapsed_seconds"])

            except Exception as exc:
                LOG.exception("Job %s failed: %s", job_id, exc)
                rec.status = "failed"
                rec.progress = 1.0
                rec.current_step = "Failed"
                rec.error_message = str(exc)
                rec.save_to_disk()
            finally:
                # Always clean up raw input video from disk to preserve ephemeral storage
                StorageService.cleanup_input(job_id)
                self.queue.task_done()


# Global singleton with concurrency = 1
job_manager = JobManager(max_concurrent=1)
