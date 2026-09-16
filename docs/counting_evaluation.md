# Counting evaluation

Counting correctness has two levels:

1. Unit-level geometry: automated tests cover one crossing, no crossing, repeated appearances, multiple tracks, direction filtering and jitter inside the deadband.
2. Video-level accuracy: a human watches the fixed demo clip and records each physical bag crossing the displayed line, then compares that total with `outputs/demo_output.json`.

The selected 14.9-second Pexels clip was reviewed manually at the configured vertical line. Four physical suitcases cross: two smaller bags on the rear belt section, then the tan and silver foreground cases. Their timestamps are recorded in `docs/counting_ledger.csv`. The exact tracker events were independently written by inference to `outputs/demo_output.json`.

## Measured result (17 September 2026)

- Ground truth count: **4**
- Predicted unique count: **4** (`track_id` 2, 1, 9 and 41)
- Absolute error: **0**
- Counting accuracy: **100%** on this clip
- Events: 2.667 s, 4.000 s, 5.367 s and 11.133 s

This is a single short demonstration, not a statistically representative airport benchmark. The result validates that the implemented counter matches the manually observed crossings in this clip; it does not establish general deployment accuracy.

For additional clips, use `docs/counting_ledger.csv` to record `bag_number`, approximate crossing timestamp and notes. Then report:

- Ground truth count: number of ledger rows
- Predicted count: `total_count` in the JSON sidecar
- Absolute error: `abs(predicted - ground_truth)`
- Counting accuracy: `max(0, 1 - absolute_error / ground_truth) × 100%`

If errors occur, inspect whether they came from missed detection, an ID switch, an incorrect line placement or direction. Tune confidence, line position and ByteTrack buffer on a calibration clip—not on the final evaluation clip.
