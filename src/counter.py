from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Point = tuple[float, float]
Direction = Literal["any", "positive", "negative"]


@dataclass
class CrossingEvent:
    track_id: int
    direction: str
    class_name: str


@dataclass
class LineCounter:
    """Count each track once after a stable crossing of an oriented line."""

    line_start: Point
    line_end: Point
    direction: Direction = "any"
    deadband_px: float = 6.0
    min_track_age: int = 2
    counted_track_ids: set[int] = field(default_factory=set)
    last_stable_side: dict[int, int] = field(default_factory=dict)
    track_age: dict[int, int] = field(default_factory=dict)
    class_counts: dict[str, int] = field(default_factory=dict)
    in_count: int = 0
    out_count: int = 0

    def _signed_distance(self, point: Point) -> float:
        x1, y1 = self.line_start
        x2, y2 = self.line_end
        px, py = point
        length = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 1e-9)
        return ((x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)) / length

    def update(self, track_id: int, point: Point, class_name: str = "luggage") -> CrossingEvent | None:
        self.track_age[track_id] = self.track_age.get(track_id, 0) + 1
        distance = self._signed_distance(point)
        side = 1 if distance > self.deadband_px else -1 if distance < -self.deadband_px else 0
        if side == 0:
            return None
        previous = self.last_stable_side.get(track_id)
        self.last_stable_side[track_id] = side
        if previous is None or previous == side or track_id in self.counted_track_ids:
            return None
        if self.track_age[track_id] < self.min_track_age:
            return None
        crossing_direction = "positive" if previous < side else "negative"
        if self.direction != "any" and self.direction != crossing_direction:
            return None
        self.counted_track_ids.add(track_id)
        self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
        if crossing_direction == "positive":
            self.in_count += 1
        else:
            self.out_count += 1
        return CrossingEvent(track_id, crossing_direction, class_name)

    @property
    def total(self) -> int:
        return len(self.counted_track_ids)


@dataclass
class ZoneCounter:
    """Count a mature track once when it enters or exits a polygonal zone."""

    polygon: list[Point]
    direction: Literal["any", "in", "out"] = "any"
    min_track_age: int = 2
    counted_track_ids: set[int] = field(default_factory=set)
    previous_inside: dict[int, bool] = field(default_factory=dict)
    track_age: dict[int, int] = field(default_factory=dict)
    class_counts: dict[str, int] = field(default_factory=dict)
    in_count: int = 0
    out_count: int = 0

    def _inside(self, point: Point) -> bool:
        x, y = point; inside = False; n = len(self.polygon)
        for i in range(n):
            x1, y1 = self.polygon[i]; x2, y2 = self.polygon[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                x_intersection = (x2 - x1) * (y - y1) / (y2 - y1) + x1
                if x < x_intersection: inside = not inside
        return inside

    def update(self, track_id: int, point: Point, class_name: str = "luggage") -> CrossingEvent | None:
        self.track_age[track_id] = self.track_age.get(track_id, 0) + 1
        inside = self._inside(point); previous = self.previous_inside.get(track_id)
        self.previous_inside[track_id] = inside
        if previous is None or previous == inside or track_id in self.counted_track_ids or self.track_age[track_id] < self.min_track_age:
            return None
        event_direction = "in" if inside else "out"
        if self.direction != "any" and self.direction != event_direction:
            return None
        self.counted_track_ids.add(track_id)
        self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
        if event_direction == "in": self.in_count += 1
        else: self.out_count += 1
        return CrossingEvent(track_id, event_direction, class_name)

    @property
    def total(self) -> int:
        return len(self.counted_track_ids)
