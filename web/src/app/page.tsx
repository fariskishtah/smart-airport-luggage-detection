"use client";

import React, { useState, useEffect, useRef } from "react";
import { Header } from "@/components/Header";
import { SettingsPanel, SettingsState } from "@/components/SettingsPanel";
import { UploadSection } from "@/components/UploadSection";
import { JobTracker } from "@/components/JobTracker";
import { ResultsView } from "@/components/ResultsView";
import { JobStatusResponse } from "@/types";
import {
  submitDirectUpload,
  submitRemoteUrlJob,
  submitDemoJob,
  fetchJobStatus,
} from "@/lib/api";

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [remoteUrl, setRemoteUrl] = useState<string>("");
  const [activeJob, setActiveJob] = useState<JobStatusResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [settings, setSettings] = useState<SettingsState>({
    mode: "counting",
    count_mode: "line",
    geometryPreset: "carousel_vertical",
    line_start: [0.55, 0.20],
    line_end: [0.55, 0.92],
    direction: "any",
    confidence: 0.25,
    iou: 0.50,
    min_track_age: 2,
    tracker: "bytetrack",
  });

  // Polling loop for job progress
  useEffect(() => {
    if (!activeJob || activeJob.status === "completed" || activeJob.status === "failed") {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      return;
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        const updated = await fetchJobStatus(activeJob.job_id);
        setActiveJob(updated);
      } catch (err) {
        console.error("Error polling job status:", err);
      }
    }, 1500);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [activeJob?.job_id, activeJob?.status]);

  const handleStartAnalysis = async () => {
    if (!selectedFile && !remoteUrl.trim()) return;

    setIsSubmitting(true);
    try {
      let submitRes: { job_id: string };

      if (selectedFile) {
        submitRes = await submitDirectUpload(selectedFile, {
          mode: settings.mode,
          count_mode: settings.count_mode,
          confidence: settings.confidence,
          iou: settings.iou,
          line_start: settings.line_start,
          line_end: settings.line_end,
          direction: settings.direction,
          min_track_age: settings.min_track_age,
          tracker: settings.tracker,
        });
      } else {
        submitRes = await submitRemoteUrlJob(remoteUrl.trim(), {
          mode: settings.mode,
          count_mode: settings.count_mode,
          confidence: settings.confidence,
          iou: settings.iou,
          line_start: settings.line_start,
          line_end: settings.line_end,
          direction: settings.direction,
          min_track_age: settings.min_track_age,
          tracker: settings.tracker,
        });
      }

      setActiveJob({
        job_id: submitRes.job_id,
        status: "queued",
        progress: 0.05,
        current_step: "Job submitted to processing queue…",
      });
    } catch (err: any) {
      alert(`Submission error: ${err.message || err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectDemo = async () => {
    setIsSubmitting(true);
    try {
      const res = await submitDemoJob();
      setActiveJob({
        job_id: res.job_id,
        status: "queued",
        progress: 0.05,
        current_step: "Loaded airport carousel demo. Queued for analysis…",
      });
    } catch (err: any) {
      alert(`Demo trigger error: ${err.message || err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetJob = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setActiveJob(null);
  };

  const isProcessing =
    isSubmitting ||
    (activeJob !== null && (activeJob.status === "queued" || activeJob.status === "processing"));

  return (
    <div className="flex-1 flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Top Section: Upload & Settings (side-by-side on desktop) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7">
            <UploadSection
              selectedFile={selectedFile}
              onSelectFile={setSelectedFile}
              remoteUrl={remoteUrl}
              onRemoteUrlChange={setRemoteUrl}
              onSelectDemo={handleSelectDemo}
              onAnalyze={handleStartAnalysis}
              disabled={isProcessing}
              isDemoLoading={isSubmitting}
            />
          </div>

          <div className="lg:col-span-5">
            <SettingsPanel
              settings={settings}
              onChange={setSettings}
              disabled={isProcessing}
            />
          </div>
        </div>

        {/* Middle Section: Active Job Progress Tracker */}
        {activeJob && (
          <div className="transition-all duration-300">
            <JobTracker job={activeJob} onReset={handleResetJob} />
          </div>
        )}

        {/* Results Section: KPI Cards, Video Player, Event Table */}
        {activeJob?.status === "completed" && activeJob.result && (
          <div className="transition-all duration-500">
            <ResultsView result={activeJob.result} />
          </div>
        )}
      </main>

      {/* Academic Disclaimer Footer */}
      <footer className="border-t border-surfaceBorder bg-surface/40 py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-1.5">
          <p className="font-semibold text-slate-400">
            Smart Airport Luggage Detection, Tracking, Counting & Analytics System
          </p>
          <p>
            Developed with YOLO11n, ByteTrack, OpenCV, FastAPI & Next.js.
          </p>
          <p className="text-[11px] text-slate-500 max-w-2xl mx-auto">
            Note: Academic demonstration prototype. Detection and counting performance may vary based on camera viewpoint, lighting, conveyor velocity, luggage scale, and dense multi-bag occlusion.
          </p>
        </div>
      </footer>
    </div>
  );
}
