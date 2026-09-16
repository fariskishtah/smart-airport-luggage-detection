# Dataset directory

The chosen fine-tuning source is a bounded Open Images V7 subset containing `Suitcase`, `Backpack`, and `Handbag`. Large image sets are intentionally Git-ignored. Download with `python scripts/download_dataset.py`, export/convert to YOLO, then normalize with `python scripts/prepare_dataset.py SOURCE` and validate with `python scripts/validate_dataset.py`.

The current repository is configured for a three-class mapping in `data.yaml`. Do not mix datasets until class IDs have been remapped consistently.

