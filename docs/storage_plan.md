# Storage plan

Measured before the upgrade on 17 September 2026: **9.4 GiB free**. A minimum target safety margin of **4 GiB** is retained.

| Item | Planned bound | Rationale |
|---|---:|---|
| Downloader metadata/tooling | 0.3–1.0 GiB | A class-filtered downloader is preferred over retaining the full 2.26 GB train annotation CSV. |
| 900 Open Images JPEGs | 0.5–1.2 GiB | 600 train, 180 validation, 120 test; actual JPEG size varies. |
| YOLO labels and reports | <0.1 GiB | Text labels, plots and contact sheets. |
| Ultralytics caches | <0.2 GiB | Label caches for three splits. |
| Two training runs | 0.5–1.0 GiB | YOLO11n/YOLO11s checkpoints, plots and predictions; training artifacts are bounded. |
| Models and demo outputs | <0.2 GiB | Compact checkpoints and short H.264 clips. |
| Contingency | 1.0 GiB | Temporary files and package overhead. |

The actual acquisition stopped at all **396** qualifying images available in the selected exhaustive pools: 98 MiB annotation metadata plus 107 MiB processed images/labels. This was smaller than the planned cap. Training artifacts and checkpoints were monitored during both runs; temporary logs and generated media remain disposable and Git-ignored. Final free space is recorded after evaluation rather than inferred from these estimates.
