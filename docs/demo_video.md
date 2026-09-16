# Demo and benchmark video provenance

All three clips were obtained from Pexels on 17 September 2026. Pexels marks its photos and videos free to download, use, and modify under the [Pexels License](https://www.pexels.com/license/); attribution is not required, but creator credit is retained here. The license prohibits selling unaltered copies or implying endorsement.

| Local role | Pexels asset | Creator | Duration / relevance |
|---|---|---|---|
| Primary demo | [Suitcases on airport baggage carousel during daytime](https://www.pexels.com/video/luggage-on-airport-baggage-carousel-36017327/) | Raphael Kim | 14.9 s; multiple suitcases, rear/foreground belts, partial overlap |
| Benchmark B | [Passengers collecting luggage at airport carousel](https://www.pexels.com/video/passengers-collecting-luggage-at-airport-carousel-27778466/) | Martyn Day | ~12 s; crowded carousel, retrieval, occlusion, camera motion |
| Benchmark C | [Smooth and seamless luggage movement on airport conveyor belt](https://www.pexels.com/video/smooth-and-seamless-luggage-movement-on-airport-conveyor-belt-1169854/) | Michael Manning | ~17 s; chute entry, dark luggage, reflective metal, motion blur |

The source and generated MP4 files are Git-ignored. `scripts/download_demo.sh` retrieves the primary clip; the two benchmark files are stored locally under `demo/benchmark/`. If a direct CDN URL changes, download the HD variant from the linked asset page and preserve the asset ID in the filename.

These are stock clips, not operational CCTV. They are suitable for visible end-to-end and manually checked crossing demonstrations, but they do not represent different airports, seasons, camera heights, or full operational load. No stock video frame is included in the Open Images train/validation/test set.
