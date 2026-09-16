from __future__ import annotations

import cv2


COLORS = {"suitcase": (51, 204, 255), "backpack": (92, 220, 92), "handbag": (255, 153, 102)}


def draw_overlay(frame, tracks, counter, line_start=None, line_end=None, fps=None, title="SMART LUGGAGE AI", zone_points=None):
    if zone_points:
        import numpy as np
        polygon = np.array(zone_points, dtype=np.int32)
        overlay = frame.copy(); cv2.fillPoly(overlay, [polygon], (0, 180, 255)); cv2.addWeighted(overlay, .14, frame, .86, 0, frame)
        cv2.polylines(frame, [polygon], True, (0, 220, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, "COUNTING ZONE", tuple(polygon[0]), cv2.FONT_HERSHEY_SIMPLEX, .55, (0,220,255), 2, cv2.LINE_AA)
    elif line_start is not None and line_end is not None:
        cv2.line(frame, line_start, line_end, (0, 220, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, "COUNTING LINE", (line_start[0] + 8, max(24, line_start[1] - 12)), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 220, 255), 2, cv2.LINE_AA)
    for track in tracks:
        x1, y1, x2, y2 = track.box
        color = COLORS.get(track.class_name.lower(), (0, 200, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"ID {track.track_id} | {track.class_name} {track.confidence:.2f}"
        cv2.rectangle(frame, (x1, max(0, y1 - 25)), (x1 + max(150, len(label) * 8), y1), color, -1)
        cv2.putText(frame, label, (x1 + 4, y1 - 7), cv2.FONT_HERSHEY_SIMPLEX, .48, (20, 20, 20), 1, cv2.LINE_AA)
        cv2.circle(frame, track.bottom_center, 4, color, -1)
    panel_h = 94 + 23 * len(counter.class_counts)
    cv2.rectangle(frame, (12, 12), (290, panel_h), (20, 28, 38), -1)
    cv2.putText(frame, title, (24, 36), cv2.FONT_HERSHEY_SIMPLEX, .55, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"TOTAL CROSSED: {counter.total}", (24, 64), cv2.FONT_HERSHEY_SIMPLEX, .68, (0, 220, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"IN: {counter.in_count}   OUT: {counter.out_count}", (24, 87), cv2.FONT_HERSHEY_SIMPLEX, .5, (230,235,240), 1, cv2.LINE_AA)
    y = 111
    for name, value in sorted(counter.class_counts.items()):
        cv2.putText(frame, f"{name.title()}: {value}", (24, y), cv2.FONT_HERSHEY_SIMPLEX, .5, (230, 235, 240), 1, cv2.LINE_AA)
        y += 23
    if fps is not None:
        cv2.putText(frame, f"{fps:.1f} FPS", (frame.shape[1] - 115, 32), cv2.FONT_HERSHEY_SIMPLEX, .55, (255, 255, 255), 2, cv2.LINE_AA)
    return frame
