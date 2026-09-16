# Dataset selection and final build

Research and acquisition were completed on 17 September 2026. Full-release counts below are publisher figures; the last section contains the exact local subset counts.

| Candidate | Relevance and annotations | License / provenance | Practical assessment |
|---|---|---|---|
| [Open Images V7](https://storage.googleapis.com/openimages/web/download_v7.html) | Direct `Backpack`, `Handbag`, and `Suitcase` bounding boxes; varied resolutions, viewpoints, occlusion, truncation, and multi-object scenes | Annotations are [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); image-level metadata records each Flickr author, landing URL, and license | Best auditable detection source. Class-filtered download is practical, but the subset is dominated by generic/product imagery rather than airport conveyors. |
| [COCO 2017](https://cocodataset.org/#download) | The same three categories and mature pretrained weights | Image licenses vary; COCO annotation terms apply | Excellent general-purpose pretrained baseline, but a full download is large and scenes are not airport-specific. |
| [MVB baggage re-identification](https://arxiv.org/abs/1907.11366) | 22,660 baggage images from two real airports and 4,519 identities | Academic dataset; access/reuse terms must be confirmed with its maintainers | Strong airport domain, but designed for identity/re-identification rather than object-detection boxes/classes, so it is not a drop-in detector training source. |
| [Roboflow Universe luggage search](https://universe.roboflow.com/search?q=luggage) | Some airport and conveyor projects with YOLO exports | License, class definitions, duplicates, and quality vary by project/version | Potential future domain supplement, rejected here because no single candidate offered sufficiently clear, compatible provenance and consistent labels. |
| [Kaggle luggage search](https://www.kaggle.com/datasets?search=luggage+detection) | Mixed classification/detection collections | Terms and source provenance vary; account/API friction | Rejected for this reproducible build because packaging convenience did not outweigh provenance and label consistency risk. |

## Final decision

The project uses a deterministic, class-filtered Open Images subset for fine-tuning and the COCO-pretrained YOLO11n checkpoint as the general baseline. `scripts/build_openimages_subset.py` reads the official dense validation and test bounding-box CSVs, rejects `IsGroupOf` and `IsDepiction` boxes, downloads pixels from the official Open Images AWS mirror, converts normalized boxes to YOLO format, and splits by unique image ID with seed 42.

Only **396** unique images in those two exhaustive source pools met the three-class filters, below the requested cap of 600. The script correctly used all 396 rather than duplicating images or quietly introducing a different source. The fixed split is **277 train / 79 validation / 40 test** (70/20/10 after rounding), with **522 boxes**: 121 backpack, 293 handbag, and 108 suitcase. Because every Open Images ID is assigned once, no image crosses split boundaries; the quality checker also found no byte-identical duplicates.

## Domain relevance and limitations

The sample montage confirms diversity in color, size, background, truncation, and carried bags, but it also reveals a significant handbag/product-photo bias. Airport conveyors and crowded baggage halls are underrepresented. The three Pexels airport videos are therefore used only for external counting/demo checks—not folded into detector training without box annotations. This avoids test leakage and prevents unlabeled stock frames from being presented as supervised data.

Open Images annotation files are CC BY 4.0. The image pixels retain the licenses recorded in Open Images image-level metadata; raw images are intentionally Git-ignored. Anyone redistributing the subset must export and retain the per-image author, landing URL, and license metadata rather than treating the pixels as a single CC BY 4.0 bundle.

Final class mapping: `0 backpack`, `1 handbag`, `2 suitcase`.
