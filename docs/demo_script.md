# Two-minute demonstration script

**0:00–0:15 — Problem.** “Airports move large quantities of baggage. Frame-by-frame detections cannot provide a reliable count because the same bag appears repeatedly.”

**0:15–0:30 — Input.** Show the unannotated licensed Pexels carousel clip and point out several bags and the intended flow direction.

**0:30–1:15 — Analysis.** Start the app or prepared command. Point to luggage-only bounding boxes, confidence labels and persistent IDs. Explain that ByteTrack links detections between frames. When bottom-center markers cross the yellow line, point out that the counter increases once; lingering boxes do not increase it again.

**1:15–1:40 — Results.** Show the total and per-class cards, then the JSON sidecar. Mention the measured processing FPS from this exact run and compare predicted crossings against the manual ledger.

**1:40–2:00 — Close.** “Detection answers what and where; tracking answers which physical bag; geometric crossing converts tracks into a unique operational count. Future work includes airport-specific fine-tuning, multi-camera tracking and RFID integration.”

