from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    video_url: Optional[str] = Field(default=None, description="Direct URL to input video in object storage")
    mode: Literal["tracking", "counting"] = Field(
        default="counting",
        description="Analysis mode: 'tracking' (boxes & IDs only) or 'counting' (directional line/zone gate)"
    )
    count_mode: Literal["line", "zone"] = Field(
        default="line",
        description="Counting geometry type: 'line' or 'zone'"
    )
    confidence: float = Field(default=0.25, ge=0.01, le=1.0, description="Detection confidence threshold")
    iou: float = Field(default=0.50, ge=0.10, le=1.0, description="NMS IoU threshold")
    line_start: Optional[List[float]] = Field(
        default=[0.55, 0.20],
        description="Normalized line start coordinate [x, y] in range 0.0 - 1.0"
    )
    line_end: Optional[List[float]] = Field(
        default=[0.55, 0.92],
        description="Normalized line end coordinate [x, y] in range 0.0 - 1.0"
    )
    zone: Optional[List[List[float]]] = Field(
        default=None,
        description="Normalized polygon points [[x1, y1], [x2, y2], ...] for zone mode"
    )
    direction: Literal["any", "in", "out", "positive", "negative"] = Field(
        default="any",
        description="Crossing direction filter"
    )
    min_track_age: int = Field(
        default=3,
        ge=1,
        le=30,
        description="Minimum consecutive frames a track must persist before crossing validation"
    )
    tracker: Literal["bytetrack", "botsort"] = Field(
        default="bytetrack",
        description="Multi-object tracking algorithm"
    )
    image_size: int = Field(
        default=640,
        description="Detector input image resolution"
    )
    model_name: Optional[str] = Field(
        default="yolo11n_coco",
        description="Model checkpoint key: 'yolo11n_coco', 'yolo11n_finetuned', 'yolo11s', 'yolo11n_conservative'"
    )


class JobSubmitResponse(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    message: str = "Job submitted successfully"


class JobResult(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    current_step: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
