"use client";

import React, { useState } from "react";
import {
  Download,
  FileSpreadsheet,
  CheckCircle2,
  Luggage,
  Clock,
  Gauge,
  ArrowDownRight,
  ArrowUpRight,
  Search,
  Maximize2
} from "lucide-react";
import { AnalysisResult } from "@/types";
import { resolveMediaUrl } from "@/lib/api";

interface ResultsViewProps {
  result: AnalysisResult;
}

export function ResultsView({ result }: ResultsViewProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSnapshot, setSelectedSnapshot] = useState<string | null>(null);

  const videoUrl = resolveMediaUrl(result.output_video_url);
  const csvUrl = resolveMediaUrl(result.events_csv_url);

  const filteredEvents = (result.events || []).filter((ev) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      ev.class.toLowerCase().includes(term) ||
      ev.track_id.toString().includes(term) ||
      ev.event_id.toLowerCase().includes(term) ||
      ev.direction.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Total Count */}
        <div className="bg-surface rounded-2xl border border-surfaceBorder p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Count</span>
            <Luggage className="w-4 h-4 text-brandCyan" />
          </div>
          <div className="text-3xl font-black text-white tracking-tight">
            {result.total_count}
          </div>
          <span className="text-[11px] text-brandCyan/90 font-medium mt-1">Unique Physical Bags</span>
        </div>

        {/* IN Count */}
        <div className="bg-surface rounded-2xl border border-surfaceBorder p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">IN Flow</span>
            <ArrowDownRight className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black text-emerald-400 tracking-tight">
            {result.in_count}
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Entering Terminal</span>
        </div>

        {/* OUT Count */}
        <div className="bg-surface rounded-2xl border border-surfaceBorder p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">OUT Flow</span>
            <ArrowUpRight className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-black text-amber-400 tracking-tight">
            {result.out_count}
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Exiting Terminal</span>
        </div>

        {/* Suitcases */}
        <div className="bg-surface rounded-2xl border border-surfaceBorder p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Suitcases</span>
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
          </div>
          <div className="text-3xl font-black text-white tracking-tight">
            {result.class_counts?.suitcase || 0}
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Rolling Luggage</span>
        </div>

        {/* Backpacks & Handbags */}
        <div className="bg-surface rounded-2xl border border-surfaceBorder p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Packs / Bags</span>
            <span className="w-2 h-2 rounded-full bg-amber-400" />
          </div>
          <div className="text-3xl font-black text-white tracking-tight">
            {(result.class_counts?.backpack || 0) + (result.class_counts?.handbag || 0)}
          </div>
          <span className="text-[11px] text-slate-400 mt-1">
            {result.class_counts?.backpack || 0} BP · {result.class_counts?.handbag || 0} HB
          </span>
        </div>

        {/* Processing FPS */}
        <div className="bg-surface rounded-2xl border border-surfaceBorder p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Throughput</span>
            <Gauge className="w-4 h-4 text-brandCyan" />
          </div>
          <div className="text-3xl font-black text-white tracking-tight font-mono">
            {result.processing_fps}
          </div>
          <span className="text-[11px] text-slate-400 mt-1">
            FPS · {result.elapsed_seconds}s total
          </span>
        </div>
      </div>

      {/* Video Player & Analytics Container */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main Video Playback (7 cols) */}
        <div className="lg:col-span-7 bg-surface rounded-2xl border border-surfaceBorder p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-surfaceBorder/60 pb-3 mb-4">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                  Annotated H.264 Video Playback
                </h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                {result.video_width}×{result.video_height} · {result.frames} frames
              </span>
            </div>

            <div className="relative rounded-xl overflow-hidden bg-black aspect-video border border-surfaceBorder/80 mb-4">
              <video
                src={videoUrl}
                controls
                autoPlay
                loop
                playsInline
                className="w-full h-full object-contain"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-surfaceBorder/60">
            <div className="text-xs text-slate-400 font-medium">
              Model: <span className="text-slate-200">{result.model}</span> · Tracker:{" "}
              <span className="text-slate-200">{result.tracker}</span>
            </div>
            <a
              href={videoUrl}
              download="luggage_analysis.mp4"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-brandRed hover:bg-brandRed/90 text-white text-xs font-bold transition-all shadow-md shadow-brandRed/20"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download MP4</span>
            </a>
          </div>
        </div>

        {/* Auditable Event Ledger (5 cols) */}
        <div className="lg:col-span-5 bg-surface rounded-2xl border border-surfaceBorder p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-surfaceBorder/60 pb-3 mb-4">
              <div className="flex items-center space-x-2">
                <FileSpreadsheet className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                  Auditable Event Ledger
                </h3>
              </div>
              {csvUrl && (
                <a
                  href={csvUrl}
                  download="events.csv"
                  className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700"
                >
                  <Download className="w-3 h-3" />
                  <span>CSV</span>
                </a>
              )}
            </div>

            {/* Filter */}
            <div className="relative mb-3">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Filter by class, track ID, direction…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brandCyan"
              />
            </div>

            {/* Table */}
            <div className="overflow-y-auto max-h-[340px] border border-slate-800/80 rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 sticky top-0 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2 px-3">Event</th>
                    <th className="py-2 px-2">Time</th>
                    <th className="py-2 px-2">ID</th>
                    <th className="py-2 px-2">Class</th>
                    <th className="py-2 px-2">Dir</th>
                    <th className="py-2 px-2 text-right">Conf</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {filteredEvents.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-slate-500 text-xs font-sans">
                        {result.events?.length === 0
                          ? "No crossing events met geometric criteria."
                          : "No events match search query."}
                      </td>
                    </tr>
                  ) : (
                    filteredEvents.map((ev, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-2 px-3 text-slate-300 font-semibold">{ev.event_id}</td>
                        <td className="py-2 px-2 text-slate-400">{ev.timestamp.toFixed(2)}s</td>
                        <td className="py-2 px-2 text-brandCyan">#{ev.track_id}</td>
                        <td className="py-2 px-2 capitalize font-sans text-slate-200">{ev.class}</td>
                        <td className="py-2 px-2 text-[11px]">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              ev.direction === "positive" || ev.direction === "in"
                                ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60"
                                : "bg-amber-950/60 text-amber-400 border border-amber-800/60"
                            }`}
                          >
                            {ev.direction.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-2 px-2 text-right text-slate-400">
                          {(ev.confidence * 100).toFixed(0)}%
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="pt-3 border-t border-surfaceBorder/60 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Total Events: {result.events_count}</span>
            <span>Auditable CSV ready</span>
          </div>
        </div>
      </div>
    </div>
  );
}
