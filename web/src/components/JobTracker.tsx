"use client";

import React from "react";
import { Loader2, AlertCircle, CheckCircle2, Clock } from "lucide-react";
import { JobStatusResponse } from "@/types";

interface JobTrackerProps {
  job: JobStatusResponse | null;
  onReset?: () => void;
}

export function JobTracker({ job, onReset }: JobTrackerProps) {
  if (!job) return null;

  const isFailed = job.status === "failed";
  const isCompleted = job.status === "completed";
  const progressPct = Math.round((job.progress || 0) * 100);

  const stages = [
    { label: "Queued", active: job.progress >= 0.05 },
    { label: "Detection & Tracking", active: job.progress >= 0.20 },
    { label: "Geometric Counting", active: job.progress >= 0.70 },
    { label: "H.264 Encoding", active: job.progress >= 0.90 },
    { label: "Completed", active: isCompleted },
  ];

  return (
    <div className="bg-surface rounded-2xl border border-surfaceBorder p-5 shadow-xl">
      <div className="flex items-center justify-between border-b border-surfaceBorder/60 pb-3 mb-4">
        <div className="flex items-center space-x-2">
          {isFailed ? (
            <AlertCircle className="w-4 h-4 text-red-400" />
          ) : isCompleted ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <Loader2 className="w-4 h-4 text-brandCyan animate-spin" />
          )}
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
            {isFailed
              ? "Analysis Failed"
              : isCompleted
              ? "Analysis Complete"
              : "Inference In Progress"}
          </h3>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-400 font-mono">Job ID: {job.job_id}</span>
          {isFailed && onReset && (
            <button
              onClick={onReset}
              className="text-brandCyan hover:underline font-medium ml-2"
            >
              Retry
            </button>
          )}
        </div>
      </div>

      {isFailed ? (
        <div className="bg-red-950/40 border border-red-800/60 rounded-xl p-4 text-xs text-red-200">
          <p className="font-semibold mb-1">Error executing pipeline:</p>
          <p className="font-mono text-slate-300">{job.error || "Unknown analysis failure"}</p>
        </div>
      ) : (
        <div>
          {/* Progress Bar */}
          <div className="mb-3">
            <div className="flex justify-between text-xs text-slate-300 font-medium mb-1.5">
              <span>{job.current_step || "Processing…"}</span>
              <span className="font-mono text-brandCyan font-bold">{progressPct}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-brandRed via-amber-500 to-brandCyan transition-all duration-300 rounded-full"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>

          {/* Pipeline Stage Indicators */}
          <div className="grid grid-cols-5 gap-1.5 pt-2">
            {stages.map((stage, idx) => (
              <div
                key={idx}
                className={`text-center py-1 px-1 rounded-md text-[10px] font-medium border transition-colors ${
                  stage.active
                    ? "bg-slate-800 text-slate-200 border-slate-700 font-semibold"
                    : "bg-slate-900/40 text-slate-500 border-slate-900"
                }`}
              >
                {stage.label}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
