from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Optional
import urllib.request

from backend.utils.security import MAX_UPLOAD_MB, is_allowed_file_extension, validate_remote_url

LOG = logging.getLogger("backend.storage")

BACKEND_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIR = BACKEND_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
OUTPUTS_DIR = STORAGE_DIR / "outputs"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

BLOB_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN", "")


class StorageService:
    @staticmethod
    def get_job_output_dir(job_id: str) -> Path:
        job_dir = OUTPUTS_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    @staticmethod
    def download_video(url: str, job_id: str) -> Path:
        """Download remote video with streaming, size limits, and security validation."""
        validate_remote_url(url)
        target_path = UPLOADS_DIR / f"{job_id}_input.mp4"

        LOG.info("Downloading remote video for job %s from %s", job_id, url)
        max_bytes = MAX_UPLOAD_MB * 1024 * 1024

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SmartAirportLuggage-Backend/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                total_downloaded = 0
                with target_path.open("wb") as out_file:
                    while True:
                        chunk = response.read(64 * 1024)
                        if not chunk:
                            break
                        total_downloaded += len(chunk)
                        if total_downloaded > max_bytes:
                            target_path.unlink(missing_ok=True)
                            raise ValueError(f"Video file exceeds maximum allowed size of {MAX_UPLOAD_MB} MB")
                        out_file.write(chunk)
        except Exception as exc:
            target_path.unlink(missing_ok=True)
            raise RuntimeError(f"Failed to download video: {exc}") from exc

        return target_path

    @staticmethod
    def save_uploaded_file(file_obj, filename: str, job_id: str) -> Path:
        """Save a directly uploaded file safely with size validation."""
        if not is_allowed_file_extension(filename):
            raise ValueError(f"Unsupported file extension in '{filename}'. Allowed: .mp4, .mov, .avi, .mkv")

        ext = Path(filename).suffix.lower() or ".mp4"
        target_path = UPLOADS_DIR / f"{job_id}_input{ext}"
        max_bytes = MAX_UPLOAD_MB * 1024 * 1024
        total_bytes = 0

        with target_path.open("wb") as buffer:
            while True:
                chunk = file_obj.read(64 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    target_path.unlink(missing_ok=True)
                    raise ValueError(f"Upload exceeds maximum allowed size of {MAX_UPLOAD_MB} MB")
                buffer.write(chunk)

        return target_path

    @staticmethod
    def upload_to_vercel_blob(local_path: Path, blob_pathname: str) -> Optional[str]:
        """Upload a processed file to Vercel Blob if token is configured."""
        if not BLOB_TOKEN:
            return None

        try:
            import requests
            url = f"https://blob.vercel-storage.com/{blob_pathname}"
            headers = {
                "Authorization": f"Bearer {BLOB_TOKEN}",
                "x-api-version": "7",
            }
            with local_path.open("rb") as f:
                resp = requests.put(url, data=f, headers=headers, timeout=60)
            if resp.status_code in (200, 201):
                data = resp.json()
                return data.get("url")
            else:
                LOG.warning("Vercel Blob upload failed with status %d: %s", resp.status_code, resp.text)
        except Exception as exc:
            LOG.warning("Vercel Blob upload exception: %s", exc)

        return None

    @staticmethod
    def cleanup_input(job_id: str) -> None:
        """Clean up raw uploaded input video after processing."""
        for f in UPLOADS_DIR.glob(f"{job_id}_input*"):
            try:
                f.unlink(missing_ok=True)
            except Exception as exc:
                LOG.warning("Could not delete input file %s: %s", f, exc)

    @staticmethod
    def cleanup_job(job_id: str) -> None:
        """Remove all files associated with a job."""
        StorageService.cleanup_input(job_id)
        job_out = OUTPUTS_DIR / job_id
        if job_out.exists():
            shutil.rmtree(job_out, ignore_errors=True)
