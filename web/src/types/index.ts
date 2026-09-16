export interface AnalysisEvent {
  event_id: string;
  event_number: number;
  frame: number;
  timestamp: number;
  track_id: number;
  class: string;
  class_name?: string;
  confidence: number;
  direction: string;
  event_type: string;
  centroid_x: number;
  centroid_y: number;
  snapshot?: string;
}

export interface AnalysisResult {
  mode: "tracking" | "counting";
  count_mode: "line" | "zone" | "none";
  frames: number;
  source_fps: number;
  elapsed_seconds: number;
  processing_fps: number;
  average_latency_ms: number;
  total_count: number;
  in_count: number;
  out_count: number;
  class_counts: Record<string, number>;
  events: AnalysisEvent[];
  events_count: number;
  video_width: number;
  video_height: number;
  model: string;
  tracker: string;
  output_video_url: string;
  events_csv_url?: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  current_step?: string;
  error?: string | null;
  result?: AnalysisResult | null;
}

export interface SystemHealth {
  status: string;
  service: string;
  model: string;
  tracker: string;
  device: string;
  concurrency_limit: number;
}
