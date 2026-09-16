# Engineering challenges and mitigations

## Bounded storage and memory

The run began with 9.4 GiB free and 8 GB unified memory. Full Open Images/COCO downloads were unsafe, so acquisition was limited to the exhaustive validation/test pools for the three target labels. Training used 512-pixel images, batches of 8 (YOLO11n) and 4 (YOLO11s), zero data-loader workers, and no in-memory image cache. Raw pixels, checkpoints, and generated video remain Git-ignored.

## Domain imbalance

Open Images offers strong boxes and clear provenance but is not an airport dataset. Handbags outnumber each other class by more than two to one, and product-style photos are common. The limitation is shown in the dataset montage and per-class AP rather than hidden. Airport stock videos are external behavioral tests, not mixed into the supervised split.

## Runtime compatibility

The isolated Python 3.11 environment was selected for compatible PyTorch/computer-vision wheels. Automatic device selection is CUDA → MPS → CPU. Training succeeded on Apple M2 MPS; PyTorch warned that one MPS accumulation operation is not deterministically implemented, so seed-based repeatability is strong but bit-for-bit reproducibility across devices is not promised.

## Counting around boundaries

Centroid jitter can resemble repeated side changes. The line counter uses a stable previous side, configurable deadband, minimum track age, direction filtering, and permanent unique-ID registry. Zone mode likewise records only the first accepted entry/exit for an ID. Fourteen tests cover geometry and an end-to-end artifact path.

## Detection and identity errors

No counter can recover a bag the detector never sees. Occlusion can also fragment a trajectory into a new ID, while visually similar handbag/suitcase examples create class confusion. The benchmark therefore separates detection mAP, qualitative tracker observations, and event-count accuracy instead of presenting them as one metric.
