import { JobStatusResponse, SystemHealth } from "@/types";

const BACKEND_URL = process.env.NEXT_PUBLIC_AI_BACKEND_URL || "http://127.0.0.1:8001";

export async function fetchHealth(): Promise<SystemHealth | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error("Health check error:", err);
    return null;
  }
}

export async function submitDemoJob(): Promise<{ job_id: string }> {
  const res = await fetch(`${BACKEND_URL}/api/analyze/demo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to trigger demo analysis");
  }
  return await res.json();
}

export async function submitDirectUpload(
  file: File,
  options: {
    mode: "tracking" | "counting";
    count_mode: "line" | "zone";
    confidence: number;
    iou: number;
    line_start?: number[];
    line_end?: number[];
    direction?: string;
    min_track_age?: number;
    tracker?: string;
  }
): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", options.mode);
  formData.append("count_mode", options.count_mode);
  formData.append("confidence", options.confidence.toString());
  formData.append("iou", options.iou.toString());
  if (options.line_start) formData.append("line_start", JSON.stringify(options.line_start));
  if (options.line_end) formData.append("line_end", JSON.stringify(options.line_end));
  if (options.direction) formData.append("direction", options.direction);
  if (options.min_track_age) formData.append("min_track_age", options.min_track_age.toString());
  if (options.tracker) formData.append("tracker", options.tracker);

  const res = await fetch(`${BACKEND_URL}/api/analyze/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to upload video to backend");
  }

  return await res.json();
}

export async function submitRemoteUrlJob(
  videoUrl: string,
  options: {
    mode: "tracking" | "counting";
    count_mode: "line" | "zone";
    confidence: number;
    iou: number;
    line_start?: number[];
    line_end?: number[];
    direction?: string;
    min_track_age?: number;
    tracker?: string;
  }
): Promise<{ job_id: string }> {
  const payload = {
    video_url: videoUrl,
    mode: options.mode,
    count_mode: options.count_mode,
    confidence: options.confidence,
    iou: options.iou,
    line_start: options.line_start,
    line_end: options.line_end,
    direction: options.direction || "any",
    min_track_age: options.min_track_age || 3,
    tracker: options.tracker || "bytetrack",
  };

  const res = await fetch(`${BACKEND_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to submit remote video job");
  }

  return await res.json();
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${BACKEND_URL}/api/jobs/${jobId}`, { cache: "no-store" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Job ${jobId} not found`);
  }
  return await res.json();
}

export function resolveMediaUrl(path: string | undefined): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${BACKEND_URL}${path.startsWith("/") ? "" : "/"}${path}`;
}
