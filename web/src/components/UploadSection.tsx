"use client";

import React, { useRef, useState } from "react";
import { UploadCloud, Film, PlayCircle, Link2, Sparkles, X } from "lucide-react";

interface UploadSectionProps {
  selectedFile: File | null;
  onSelectFile: (file: File | null) => void;
  remoteUrl: string;
  onRemoteUrlChange: (url: string) => void;
  onSelectDemo: () => void;
  onAnalyze: () => void;
  disabled?: boolean;
  isDemoLoading?: boolean;
}

export function UploadSection({
  selectedFile,
  onSelectFile,
  remoteUrl,
  onRemoteUrlChange,
  onSelectDemo,
  onAnalyze,
  disabled,
  isDemoLoading,
}: UploadSectionProps) {
  const [tab, setTab] = useState<"file" | "url">("file");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith("video/") || file.name.match(/\.(mp4|mov|avi|mkv)$/i)) {
        onSelectFile(file);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onSelectFile(e.target.files[0]);
    }
  };

  return (
    <div className="bg-surface rounded-2xl border border-surfaceBorder p-5 shadow-xl flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between border-b border-surfaceBorder/60 pb-3 mb-4">
          <div className="flex items-center space-x-2">
            <Film className="w-4 h-4 text-brandRed" />
            <h2 className="text-sm font-semibold text-white tracking-wide uppercase">
              Video Source
            </h2>
          </div>

          <div className="flex items-center space-x-1 bg-slate-900/90 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              type="button"
              onClick={() => setTab("file")}
              className={`px-2.5 py-1 rounded font-medium transition-all ${
                tab === "file" ? "bg-slate-800 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Local Video
            </button>
            <button
              type="button"
              onClick={() => setTab("url")}
              className={`px-2.5 py-1 rounded font-medium transition-all ${
                tab === "url" ? "bg-slate-800 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Storage URL
            </button>
          </div>
        </div>

        {tab === "file" ? (
          <div>
            {selectedFile ? (
              <div className="bg-slate-900/80 rounded-xl border border-surfaceBorder p-4 flex flex-col items-center justify-center text-center relative">
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => onSelectFile(null)}
                  className="absolute top-2.5 right-2.5 p-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700"
                >
                  <X className="w-4 h-4" />
                </button>

                <div className="w-12 h-12 rounded-xl bg-brandRed/10 border border-brandRed/30 flex items-center justify-center mb-2 text-brandRed">
                  <Film className="w-6 h-6" />
                </div>
                <p className="text-xs font-bold text-white max-w-[260px] truncate mb-0.5">
                  {selectedFile.name}
                </p>
                <p className="text-[11px] text-slate-400 mb-2 font-mono">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
                  Ready for AI Analysis
                </span>
              </div>
            ) : (
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center ${
                  dragOver
                    ? "border-brandRed bg-brandRed/5 scale-[0.99]"
                    : "border-slate-700/80 bg-slate-900/40 hover:border-slate-500 hover:bg-slate-900/60"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska"
                  onChange={handleFileChange}
                  className="hidden"
                  disabled={disabled}
                />
                <div className="w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center mb-3 text-slate-300">
                  <UploadCloud className="w-6 h-6 text-brandCyan" />
                </div>
                <p className="text-xs font-semibold text-white mb-1">
                  Drag & Drop luggage footage here, or{" "}
                  <span className="text-brandCyan underline">browse</span>
                </p>
                <p className="text-[11px] text-slate-400">
                  Supports MP4, MOV, AVI, MKV (Up to 150 MB · Maximum input resolution: 2560 × 1440)
                </p>
              </div>
            )}

            {/* Quick Demo Pre-load Button */}
            <div className="mt-3.5">
              <button
                type="button"
                disabled={disabled || isDemoLoading}
                onClick={onSelectDemo}
                className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 hover:from-slate-800 hover:to-slate-800 border border-slate-700 text-slate-200 text-xs font-medium flex items-center justify-between group transition-all"
              >
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
                  <span className="text-left">
                    <span className="block font-semibold text-white">Load Carousel Demo Clip</span>
                    <span className="block text-[10px] text-slate-400">447 frames · 4/4 Verified Ground Truth</span>
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                  1-Click Test
                </span>
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-slate-300 mb-1.5 block">
                Direct Video Storage URL (Vercel Blob / S3 / CDN)
              </label>
              <div className="relative">
                <Link2 className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="url"
                  disabled={disabled}
                  placeholder="https://.../airport_baggage.mp4"
                  value={remoteUrl}
                  onChange={(e) => onRemoteUrlChange(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brandRed font-mono"
                />
              </div>
            </div>
            <p className="text-[11px] text-slate-400">
              Directly downloads from object storage into the inference engine, avoiding serverless body size limits.
            </p>
          </div>
        )}
      </div>

      {/* Main Action Button */}
      <div className="mt-5 pt-3 border-t border-surfaceBorder/60">
        <button
          type="button"
          disabled={disabled || (!selectedFile && !remoteUrl.trim())}
          onClick={onAnalyze}
          className={`w-full py-3 px-4 rounded-xl font-bold text-sm flex items-center justify-center space-x-2 transition-all shadow-lg ${
            disabled || (!selectedFile && !remoteUrl.trim())
              ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
              : "bg-brandRed hover:bg-brandRed/90 text-white shadow-brandRed/30 glow-red hover:scale-[1.01]"
          }`}
        >
          <PlayCircle className="w-4 h-4" />
          <span>Start AI Video Analysis</span>
        </button>
      </div>
    </div>
  );
}
