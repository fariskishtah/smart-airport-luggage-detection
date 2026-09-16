"use client";

import React, { useState } from "react";
import { Sliders, Shield, Crosshair, ArrowRightLeft, Settings2, ChevronDown, ChevronUp } from "lucide-react";

export interface SettingsState {
  mode: "tracking" | "counting";
  count_mode: "line" | "zone";
  geometryPreset: "carousel_vertical" | "conveyor_horizontal" | "custom";
  line_start: number[];
  line_end: number[];
  direction: "any" | "positive" | "negative";
  confidence: number;
  iou: number;
  min_track_age: number;
  tracker: "bytetrack" | "botsort";
}

interface SettingsPanelProps {
  settings: SettingsState;
  onChange: (newSettings: SettingsState) => void;
  disabled?: boolean;
}

export function SettingsPanel({ settings, onChange, disabled }: SettingsPanelProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleModeChange = (mode: "tracking" | "counting") => {
    onChange({ ...settings, mode });
  };

  const handlePresetChange = (preset: "carousel_vertical" | "conveyor_horizontal" | "custom") => {
    let s = [0.55, 0.20];
    let e = [0.55, 0.92];
    if (preset === "conveyor_horizontal") {
      s = [0.20, 0.55];
      e = [0.75, 0.55];
    }
    onChange({
      ...settings,
      geometryPreset: preset,
      line_start: s,
      line_end: e,
    });
  };

  return (
    <div className="bg-surface rounded-2xl border border-surfaceBorder p-5 shadow-xl">
      <div className="flex items-center justify-between border-b border-surfaceBorder/60 pb-3 mb-4">
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-brandCyan" />
          <h2 className="text-sm font-semibold text-white tracking-wide uppercase">
            Inference & Counting Mode
          </h2>
        </div>
        <span className="text-[11px] text-slate-400">YOLO11n · ByteTrack</span>
      </div>

      {/* Mode A vs Mode B Tabs */}
      <div className="mb-5">
        <label className="text-xs font-medium text-slate-300 mb-2 block">
          Operating Mode
        </label>
        <div className="grid grid-cols-2 gap-2 bg-slate-900/80 p-1.5 rounded-xl border border-surfaceBorder">
          <button
            type="button"
            disabled={disabled}
            onClick={() => handleModeChange("counting")}
            className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all ${
              settings.mode === "counting"
                ? "bg-brandRed text-white shadow-md shadow-brandRed/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Crosshair className="w-3.5 h-3.5" />
            <span>Mode B: Count Crossings</span>
          </button>
          <button
            type="button"
            disabled={disabled}
            onClick={() => handleModeChange("tracking")}
            className={`py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all ${
              settings.mode === "tracking"
                ? "bg-brandCyan text-slate-950 shadow-md shadow-brandCyan/30 font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Mode A: Tracking Only</span>
          </button>
        </div>
        <p className="text-[11px] text-slate-400 mt-1.5">
          {settings.mode === "counting"
            ? "Applies geometric virtual gate + directional deadband + unique ID counting."
            : "Tracks all visible luggage with persistent IDs and trajectory without a virtual gate."}
        </p>
      </div>

      {/* Geometry Settings (when in Counting Mode) */}
      {settings.mode === "counting" && (
        <div className="space-y-4 mb-4 bg-slate-900/40 p-3.5 rounded-xl border border-slate-800/80">
          <div>
            <label className="text-xs font-medium text-slate-300 mb-1.5 block">
              Virtual Gate Geometry
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                disabled={disabled}
                onClick={() => handlePresetChange("carousel_vertical")}
                className={`py-1.5 px-2 rounded-lg text-xs font-medium border text-center transition-all ${
                  settings.geometryPreset === "carousel_vertical"
                    ? "bg-brandRed/15 border-brandRed text-brandRed font-bold"
                    : "border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                Carousel Gate (x=0.55)
              </button>
              <button
                type="button"
                disabled={disabled}
                onClick={() => handlePresetChange("conveyor_horizontal")}
                className={`py-1.5 px-2 rounded-lg text-xs font-medium border text-center transition-all ${
                  settings.geometryPreset === "conveyor_horizontal"
                    ? "bg-brandRed/15 border-brandRed text-brandRed font-bold"
                    : "border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                Conveyor Gate (y=0.55)
              </button>
              <button
                type="button"
                disabled={disabled}
                onClick={() => handlePresetChange("custom")}
                className={`py-1.5 px-2 rounded-lg text-xs font-medium border text-center transition-all ${
                  settings.geometryPreset === "custom"
                    ? "bg-brandRed/15 border-brandRed text-brandRed font-bold"
                    : "border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                Custom Coordinates
              </button>
            </div>
          </div>

          {settings.geometryPreset === "custom" && (
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-400 block mb-1">Start [X, Y]:</span>
                <div className="flex space-x-1.5">
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={settings.line_start[0]}
                    onChange={(e) =>
                      onChange({
                        ...settings,
                        line_start: [parseFloat(e.target.value) || 0, settings.line_start[1]],
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100"
                  />
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={settings.line_start[1]}
                    onChange={(e) =>
                      onChange({
                        ...settings,
                        line_start: [settings.line_start[0], parseFloat(e.target.value) || 0],
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100"
                  />
                </div>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">End [X, Y]:</span>
                <div className="flex space-x-1.5">
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={settings.line_end[0]}
                    onChange={(e) =>
                      onChange({
                        ...settings,
                        line_end: [parseFloat(e.target.value) || 0, settings.line_end[1]],
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100"
                  />
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={settings.line_end[1]}
                    onChange={(e) =>
                      onChange({
                        ...settings,
                        line_end: [settings.line_end[0], parseFloat(e.target.value) || 0],
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100"
                  />
                </div>
              </div>
            </div>
          )}

          <div>
            <label className="text-xs font-medium text-slate-300 mb-1 block">
              Count Direction Filter
            </label>
            <select
              disabled={disabled}
              value={settings.direction}
              onChange={(e) =>
                onChange({ ...settings, direction: e.target.value as "any" | "positive" | "negative" })
              }
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brandRed"
            >
              <option value="any">Bidirectional (Count Any Valid Crossing)</option>
              <option value="positive">Positive Vector Only (IN Flow)</option>
              <option value="negative">Negative Vector Only (OUT Flow)</option>
            </select>
          </div>
        </div>
      )}

      {/* Collapsible Advanced Settings */}
      <div className="border-t border-surfaceBorder/60 pt-3">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-between w-full text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
        >
          <div className="flex items-center space-x-1.5">
            <Settings2 className="w-3.5 h-3.5 text-slate-400" />
            <span>Advanced Pipeline Settings</span>
          </div>
          {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showAdvanced && (
          <div className="space-y-3.5 mt-3 pt-2 text-xs">
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Confidence Threshold:</span>
                <span className="font-mono text-brandCyan">{settings.confidence.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.90"
                step="0.05"
                disabled={disabled}
                value={settings.confidence}
                onChange={(e) => onChange({ ...settings, confidence: parseFloat(e.target.value) })}
                className="w-full accent-brandCyan cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>NMS IoU Threshold:</span>
                <span className="font-mono text-brandCyan">{settings.iou.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.90"
                step="0.05"
                disabled={disabled}
                value={settings.iou}
                onChange={(e) => onChange({ ...settings, iou: parseFloat(e.target.value) })}
                className="w-full accent-brandCyan cursor-pointer"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Min Track Age:</label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  disabled={disabled}
                  value={settings.min_track_age}
                  onChange={(e) => onChange({ ...settings, min_track_age: parseInt(e.target.value) || 3 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Tracker:</label>
                <select
                  disabled={disabled}
                  value={settings.tracker}
                  onChange={(e) => onChange({ ...settings, tracker: e.target.value as "bytetrack" | "botsort" })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200"
                >
                  <option value="bytetrack">ByteTrack (Fastest)</option>
                  <option value="botsort">BoT-SORT</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
