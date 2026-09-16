# 18-slide graduation presentation (~20 minutes)

## 1. Title — 0:30

**Smart Airport Luggage Detection, Tracking, Counting and Analytics System**  
Team, supervisor, department, date.

Speaker notes: Introduce the operational problem and state the key distinction: this is not only object detection; it produces auditable unique crossing events over time.

## 2. Problem — 0:55

- Manual video monitoring is slow and inconsistent.
- Counting boxes per frame repeatedly counts the same bag.
- Occlusion, motion blur, reflections, and similar-looking luggage make the task difficult.

Speaker notes: Use one bag visible for 100 frames as the intuitive counterexample to frame-based counting.

## 3. Motivation and responsible scope — 0:50

- Aggregate baggage-flow visibility
- Evidence for operational review
- No face recognition or passenger identification

Speaker notes: Emphasize privacy by design. The goal is bag-flow analytics, not surveillance of identities.

## 4. Target users — 0:40

- Baggage operations teams
- Airport analytics and quality teams
- System integrators and researchers

Speaker notes: Explain that this prototype exposes video, events, and metrics that a larger airport system could consume.

## 5. Proposed solution — 0:55

`Detect → Filter → Track → Analyze trajectory → Cross line/zone → Count ID once → Log evidence`

Speaker notes: Detection answers “what and where”; tracking answers “which bag”; geometry answers “did it cross?”

## 6. Implemented features — 0:55

- Three luggage classes; selectable detector and tracker
- ByteTrack and BoT-SORT; line and polygon-zone modes
- IN/OUT/TOTAL, per-class counts, deadband, minimum track age
- H.264 output, JSON/CSV events, evidence crops, Streamlit analytics

Speaker notes: Distinguish implemented features from future work. Mention that command line and UI use the same pipeline.

## 7. Dataset decision — 1:10

- Compared Open Images, COCO, MVB, Roboflow, and Kaggle candidates
- Selected bounded Open Images boxes for provenance and exact class match
- 396 images, 522 objects: 121 backpack, 293 handbag, 108 suitcase

Speaker notes: Explain why MVB is domain-relevant but a re-identification dataset, and why unclear community licensing was rejected.

## 8. Quality and split — 1:00

- Seed 42; 277 train / 79 validation / 40 held-out test
- No corrupt/missing/invalid/duplicate samples found
- Group boxes and depictions excluded
- Documented handbag imbalance and product-photo bias

Speaker notes: Show `dataset_samples.jpg` and the class distribution. Say explicitly that dataset quality includes limitations, not just zero parser errors.

## 9. Training design — 1:05

- Transfer learning from COCO YOLO11 weights
- YOLO11n and YOLO11s, 15 epochs, 512 px, AdamW
- Batch 8/4, early stopping patience 5, warmup, augmentation
- Apple M2 MPS; full configs and metadata saved

Speaker notes: Report measured durations: 544.7 s for nano and 986.4 s for small. Mention the conservative anti-forgetting run as an engineering response to video domain shift.

## 10. Held-out detector results — 1:20

| Model | Precision | Recall | mAP50 | mAP50-95 | Size |
|---|---:|---:|---:|---:|---:|
| YOLO11n fine-tuned | 0.853 | 0.403 | 0.574 | 0.446 | 5.44 MB |
| YOLO11s fine-tuned | 0.594 | 0.501 | 0.511 | 0.357 | 19.14 MB |

Speaker notes: These are official Ultralytics metrics on 40 untouched images/45 objects. Nano wins precision, mAP, latency, and size; small wins recall. Do not overstate confidence because the test set is small.

## 11. Baseline versus fine-tuning — 1:15

- Common mapped-class protocol: COCO baseline mAP50-95 0.285
- Fine-tuned nano mAP50-95 0.465; small 0.386
- Fine-tuning strongly improves handbags but airport video exposes domain forgetting

Speaker notes: Explain the fair class mapping and per-image low-confidence evaluation. Then show the crucial external result: a better in-domain still-image metric did not guarantee the best conveyor count.

## 12. Tracking — 0:55

- ByteTrack associates high- and lower-confidence detections
- Track buffer helps temporary occlusion
- BoT-SORT is supported and compared qualitatively
- No MOTA/IDF1 claim without trajectory ground truth

Speaker notes: Define an ID switch and explain how it can create duplicate counts. This honesty is a research strength.

## 13. Counting algorithm — 1:20

- Bottom-center anchor and previous/current stable side
- Deadband suppresses boundary jitter
- Minimum age rejects short tracks
- Direction filter maps positive/negative or zone entry/exit to IN/OUT
- Permanent ID registry enforces at most one accepted event per track

Speaker notes: Walk through a two-frame crossing. Mention the 13 focused geometry tests plus one end-to-end artifact test.

## 14. Architecture and outputs — 1:05

Show `docs/architecture.md` Mermaid diagram.

Speaker notes: Follow a frame from OpenCV through YOLO, tracker, trajectory engine, unique registry, logger, overlay, and Streamlit. Point out replaceable module boundaries.

## 15. UI and analytics — 0:55

- Upload and model/tracker/threshold controls
- Line or zone mode and direction
- Progress, video playback, count cards, FPS/time
- Event table, class/time charts, CSV and MP4 download

Speaker notes: The UI is not a second algorithm; it configures the same tested `process_video` function.

## 16. Demo and counting benchmark — 2:00

Play the prepared primary clip, highlight persistent IDs and increments, then show the event table/crops and multi-video table.

Speaker notes: Clearly label manual crossing ground truth versus predicted count. Never call counting accuracy “mAP.” Mention exact model/threshold/line used.

## 17. Failures and lessons — 1:15

- Handbag imbalance; backpack/suitcase confusion
- Dog/bed hard-negative false positives
- Missed overlapping, antique, dark, and small bags
- Fine-tuned still-image gains did not fully transfer to stock airport video

Speaker notes: Show the prediction montage and confusion matrix. Discuss airport-specific sequence data, class balancing, and external-site validation as remedies.

## 18. Conclusion and future work — 0:55

- Delivered a reproducible detection→tracking→event pipeline
- Metrics, artifacts, tests, and limitations are auditable
- Next: multi-airport box/track annotations, RFID fusion, calibrated multi-camera association, deployment monitoring

Speaker notes: Close with the central contribution: temporal identity and explicit geometry convert visual detections into operational events. Invite questions.

Suggested pacing totals about 18 minutes plus a two-minute live/pre-recorded demonstration. Keep two additional minutes available for transitions or questions.
