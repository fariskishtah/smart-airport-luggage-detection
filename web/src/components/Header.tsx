"use client";

import React, { useEffect, useState } from "react";
import { Plane, Cpu, CheckCircle2, AlertCircle, ShieldCheck } from "lucide-react";
import { SystemHealth } from "@/types";
import { fetchHealth } from "@/lib/api";

export function Header() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    fetchHealth().then((h) => {
      if (mounted) {
        setHealth(h);
        setLoading(false);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="border-b border-surfaceBorder bg-surface/70 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brandRed to-amber-500 flex items-center justify-center shadow-lg shadow-brandRed/20">
            <Plane className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight text-white">
                Smart Airport Luggage Detection System
              </h1>
              <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-brandCyan/10 text-brandCyan border border-brandCyan/30">
                Graduation System v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              AI-Powered Detection, Persistent Tracking & Directional Counting
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {loading ? (
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-400">
              <div className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
              <span>Connecting to Backend…</span>
            </div>
          ) : health ? (
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-semibold">AI Engine Online</span>
              <span className="text-slate-400 font-mono text-[11px]">
                ({health.device.toUpperCase()} · {health.tracker})
              </span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-red-950/40 border border-red-800/60 text-xs text-red-300">
              <AlertCircle className="w-3.5 h-3.5 text-red-400" />
              <span>Backend Offline</span>
            </div>
          )}

          <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-800/50 border border-slate-700/50 text-[11px] text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-brandCyan" />
            <span>Academic Prototype</span>
          </div>
        </div>
      </div>
    </header>
  );
}
