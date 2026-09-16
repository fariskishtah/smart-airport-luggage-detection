# Graduation defense questions and concise answers

1. **Why YOLO?** It provides one-stage detection with a strong speed/accuracy tradeoff, pretrained weights, Apple MPS support, and a stable training/export ecosystem. This project measures two YOLO11 sizes rather than assuming one is best.
2. **Why transfer learning?** Starting from COCO features reduces the data and training time needed for 396 luggage images. Fine-tuning adapts the output head and features to three target categories.
3. **Why Open Images?** It directly labels backpack, handbag, and suitcase with human-produced/verified boxes, normalized coordinates, public metadata, and CC BY 4.0 annotations. Its airport-domain limitations are explicitly reported.
4. **Why not count detections per frame?** One physical bag appears in many frames. Per-frame box counts would multiply-count it; tracking supplies temporal identity and the crossing event converts that identity into one count.
5. **What is IoU?** Intersection over Union is overlap area divided by union area. It is used for detection evaluation, non-maximum suppression, and tracker association.
6. **What is precision?** `TP / (TP + FP)`: among predicted bags, the fraction that matches ground truth.
7. **What is recall?** `TP / (TP + FN)`: among labelled bags, the fraction detected.
8. **What is mAP@0.5?** Mean average precision across classes where a detection is correct at IoU at least 0.5.
9. **Why also mAP@0.5:0.95?** Averaging AP over stricter IoUs from 0.50 to 0.95 penalizes poorly localized boxes and is more demanding than mAP50.
10. **Why a held-out test set?** Validation metrics influence checkpoint selection. The 40-image test split is evaluated only afterward to estimate generalization without that selection bias.
11. **How is leakage prevented?** A unique Open Images ID is assigned to exactly one seeded split, and SHA-256 duplicate checks found no byte-identical images across the dataset.
12. **Why ByteTrack?** It associates both high- and lower-confidence detections, which can preserve luggage trajectories through partial occlusion while remaining lightweight.
13. **What is an ID switch?** The tracker incorrectly changes the identity assigned to the same bag or transfers an ID between bags. It can cause fragmented or duplicate events.
14. **Did you measure MOTA or IDF1?** No. Those require frame-level ground-truth trajectories. Tracker comparison is explicitly qualitative plus speed/count behavior, not a fabricated formal tracking score.
15. **How do you prevent duplicate counting?** Each accepted event inserts the persistent track ID into a permanent registry. Later crossings by that ID are ignored.
16. **How is line jitter handled?** Points inside a configurable deadband do not change the stable side. A count requires stable positions on opposite sides plus the minimum track age.
17. **How does direction work?** For a line, the sign change of oriented distance gives positive/negative movement and maps to IN/OUT. For a polygon, outside→inside is IN and inside→outside is OUT.
18. **Why use the bottom-center of a box?** It approximates contact with the conveyor/floor more consistently than the box center, especially when bags vary in height.
19. **What does minimum track age do?** It rejects one-frame or very short noisy tracks before they can trigger an event.
20. **What happens during occlusion?** The tracker can maintain or recover a trajectory within its buffer, but long/full occlusion may create a new ID. That remains a duplicate-count risk and is documented.
21. **Why MPS?** This host has Apple M2 graphics and no CUDA GPU. MPS materially accelerates supported PyTorch operations; automatic selection safely falls back to CPU.
22. **Why train at 512 pixels?** It fits 8 GB unified memory for both model candidates and shortens experiments. Small distant bags may benefit from larger images on stronger hardware.
23. **Why is the dataset imbalanced?** The exhaustive selected Open Images pools naturally contain 293 handbags versus 121 backpacks and 108 suitcases. Augmentation helps, but per-class AP exposes the remaining effect.
24. **Is 396 images enough for deployment?** No. It is enough to demonstrate a real reproducible transfer-learning experiment, not certify operational airport performance. Multi-airport labelled data is future work.
25. **What is counting accuracy here?** For each video it is `max(0, 1 - |prediction-GT|/GT)`. It evaluates configured crossing totals, not object detection localization or class AP.
26. **Why save CSV and crops?** They create an audit trail containing when, where, which track, which class/confidence, and the visual evidence for every increment.
27. **How do you know the MP4 is browser-compatible?** OpenCV first writes frames, then FFmpeg converts to H.264 with `faststart`; codec probing is included in final verification.
28. **Why no face recognition?** Passenger identity is unnecessary for luggage flow counts and would add privacy, fairness, and governance risks.
29. **How would this scale to an airport?** Use fixed calibrated cameras, per-camera services, health monitoring, a message/event store, centralized dashboards, and continuous validation for camera drift and domain shift.
30. **How could RFID integrate?** A crossing event could be time-correlated with RFID reads; video supplies location/visual evidence while RFID supplies a baggage identifier. Conflict rules would need operational validation.
31. **How would multi-camera tracking work?** Calibrated transition zones, time constraints, and appearance embeddings could associate tracklets, but privacy and identity-error auditing become more important.
32. **What are the main privacy controls?** Process locally where possible, retain aggregate/event data briefly, blur people if stored, restrict access, document purpose, and never infer passenger identity.
33. **What is the biggest current failure mode?** Domain shift: product-style Open Images training data does not fully represent crowded, reflective, motion-blurred airport conveyors.
34. **What would you improve first?** Collect licensed, multi-airport conveyor footage with box and track annotations, then re-balance classes and evaluate detection, tracking, and counting on separate sites.
