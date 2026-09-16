from __future__ import annotations

import asyncio
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from backend.schemas.job import AnalysisRequest, JobResult
from backend.services.inference_service import run_video_analysis
from backend.services.storage_service import StorageService

LOG = logging.getLogger("backend.jobs")


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


class JobManager:
    def __init__(self, max_concurrent: int = 1):
        self.jobs: Dict[str, JobRecord] = {}
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.worker_task: Optional[asyncio.Task] = None
        self.base_url: str = ""

    def start_worker(self):
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._process_queue())
            LOG.info("JobManager background worker started.")

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
        await self.queue.put(job_id)
        LOG.info("Submitted job %s to queue (queue size: %d)", job_id, self.queue.qsize())
        return job_id

    def get_job(self, job_id: str) -> Optional[JobResult]:
        rec = self.jobs.get(job_id)
        if not rec:
            return None
        return JobResult(
            job_id=rec.job_id,
            status=rec.status,
            progress=rec.progress,
            current_step=rec.current_step,
            error=rec.error_message,
            result=rec.result_data,
        )

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
                rec.current_step = "Downloading / preparing video asset…"

                # If no local file, download from video_url
                if rec.input_file_path is None or not rec.input_file_path.is_file():
                    if not rec.request.video_url:
                        raise ValueError("No video source provided (neither local file nor video_url).")
                    rec.input_file_path = await asyncio.to_thread(
                        StorageService.download_video, rec.request.video_url, job_id
                    )

                rec.current_step = "Executing detection and tracking pipeline…"
                req = rec.request

                def progress_cb(pct: float, step: str):
                    rec.progress = pct
                    rec.current_step = step

                # Run heavy inference in worker thread to prevent event loop blocking
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

                # Check if Vercel Blob or remote storage upload is available
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
                LOG.info("Job %s completed successfully: %d items counted in %.2fs", job_id, stats["total_count"], stats["elapsed_seconds"])

            except Exception as exc:
                LOG.exception("Job %s failed: %s", job_id, exc)
                rec.status = "failed"
                rec.progress = 1.0
                rec.current_step = "Failed"
                rec.error_message = str(exc)
            finally:
                # Always clean up raw input video from disk
                StorageService.cleanup_input(job_id)
                self.queue.task_done()


# Global singleton
job_manager = JobManager(max_concurrent=1)
