from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    box: tuple[int, int, int, int]

    @property
    def center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.box
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def bottom_center(self) -> tuple[int, int]:
        x1, _, x2, y2 = self.box
        return ((x1 + x2) // 2, y2)


def tracks_from_result(result) -> list[Track]:
    boxes = result.boxes
    if boxes is None or boxes.id is None:
        return []
    output = []
    for xyxy, track_id, cls, conf in zip(boxes.xyxy.cpu(), boxes.id.int().cpu(), boxes.cls.int().cpu(), boxes.conf.cpu()):
        class_id = int(cls)
        output.append(Track(int(track_id), class_id, result.names[class_id], float(conf), tuple(map(int, xyxy.tolist()))))
    return output

