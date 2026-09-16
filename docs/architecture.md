# System architecture

```mermaid
flowchart TD
    A[Input video / camera] --> B[OpenCV frame decoder]
    B --> C[Fine-tuned YOLO luggage detector]
    C --> D[Confidence, IoU and class filtering]
    D --> E{Tracker selection}
    E -->|Selected| F[ByteTrack]
    E -->|Comparison| G[BoT-SORT]
    F --> H[Persistent track IDs]
    G --> H
    H --> I[Bottom-center trajectory analyzer]
    I --> J{Counting mode}
    J -->|Line| K[Signed-side crossing + deadband]
    J -->|Zone| L[Polygon entry / exit]
    K --> M[Minimum age + direction filter]
    L --> M
    M --> N[Unique-ID registry]
    N --> O[CSV event logger + evidence crop]
    N --> P[Professional overlay]
    O --> Q[JSON / CSV analytics]
    P --> R[H.264 annotated MP4]
    Q --> S[Streamlit dashboard]
    R --> S
```

`detector.py` owns model inference; Ultralytics performs ByteTrack or BoT-SORT association and `tracker.py` normalizes results into a stable `Track` record. `counter.py` contains stateful line and polygon geometry. `visualization.py` owns presentation. Both command-line and Streamlit entry points call the same `process_video` implementation, so controls and exported evidence use the tested pipeline.

A detection is not a count. A track must reach the configured minimum age and its bottom-center must move between stable sides of the line (outside the deadband) or cross the polygon boundary. The accepted direction then enters a permanent counted-ID set, preventing the same tracker ID from incrementing the total twice. CSV and snapshots make every accepted event auditable.
