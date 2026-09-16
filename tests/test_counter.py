from src.counter import LineCounter, ZoneCounter


def counter(direction="any"):
    return LineCounter((0, 50), (100, 50), direction=direction, deadband_px=2, min_track_age=2)


def test_one_object_crosses_once():
    c = counter()
    assert c.update(1, (20, 40), "suitcase") is None
    assert c.update(1, (20, 60), "suitcase") is not None
    assert c.update(1, (20, 40), "suitcase") is None
    assert c.total == 1 and c.class_counts == {"suitcase": 1}


def test_object_staying_above_is_not_counted():
    c = counter()
    for point in [(10, 30), (20, 35), (30, 40)]: c.update(2, point)
    assert c.total == 0


def test_same_id_many_frames_only_counts_once():
    c = counter()
    for y in [30, 35, 45, 55, 60, 45, 55, 70]: c.update(7, (40, y))
    assert c.total == 1


def test_multiple_ids_cross():
    c = counter()
    for track_id in [1, 2, 3]:
        c.update(track_id, (20, 40), "bag")
        c.update(track_id, (20, 60), "bag")
    assert c.total == 3 and c.class_counts["bag"] == 3


def test_direction_filtering():
    c = counter("positive")
    c.update(1, (20, 40)); assert c.update(1, (20, 60)) is not None
    c.update(2, (20, 60)); assert c.update(2, (20, 40)) is None
    assert c.total == 1


def test_deadband_prevents_jitter_count():
    c = counter()
    for y in [49, 50, 51, 49, 51]: c.update(1, (20, y))
    assert c.total == 0


def test_object_touching_line_does_not_cross():
    c = counter()
    c.update(3, (10, 40)); c.update(3, (10, 50)); c.update(3, (10, 51))
    assert c.total == 0


def test_short_lived_track_rejected():
    c = LineCounter((0, 50), (100, 50), deadband_px=2, min_track_age=4)
    c.update(8, (10, 40)); c.update(8, (10, 60))
    assert c.total == 0


def test_bidirectional_counts():
    c = counter()
    c.update(1, (10, 40)); c.update(1, (10, 60))
    c.update(2, (10, 60)); c.update(2, (10, 40))
    assert (c.in_count, c.out_count, c.total) == (1, 1, 2)


def test_multiple_simultaneous_crossings():
    c = counter()
    for track_id in range(10, 15): c.update(track_id, (20, 40))
    events = [c.update(track_id, (20, 60)) for track_id in range(10, 15)]
    assert all(events) and c.total == 5


def test_zone_entry():
    c = ZoneCounter([(10,10),(90,10),(90,90),(10,90)], direction="in")
    c.update(1, (0,50), "suitcase")
    event = c.update(1, (20,50), "suitcase")
    assert event and event.direction == "in" and c.in_count == 1


def test_zone_exit():
    c = ZoneCounter([(10,10),(90,10),(90,90),(10,90)], direction="out")
    c.update(2, (20,50)); event = c.update(2, (100,50))
    assert event and event.direction == "out" and c.out_count == 1


def test_zone_duplicate_id_prevention():
    c = ZoneCounter([(10,10),(90,10),(90,90),(10,90)])
    for point in [(0,50),(20,50),(100,50),(20,50)]: c.update(5, point)
    assert c.total == 1


def test_zone_short_lived_track_rejected():
    c = ZoneCounter([(10,10),(90,10),(90,90),(10,90)], min_track_age=4)
    c.update(8, (0, 50))
    event = c.update(8, (20, 50))
    assert event is None and c.total == 0

