# Drink Lens implementation and verification

A working browser app now implements the camera idea. Journey: camera or upload → pretrained image/text matching → drink-family alternatives → explicit menu-item confirmation → historical branch-specific food pairings → basket preview.

This feature is independent of the transaction prediction models. The previously reported 0.745 category AUC does not apply to computer vision or to the new product-level pairing rule.

## Verification performed

- Five Node tests passed: abstention/invalid score handling, visual-class menu coverage, branch pricing/pairing integrity, and exclusion of transaction/customer identifiers from the catalog.
- JavaScript syntax checks passed for the app and vision worker.
- Chromium browser checks passed: manual drink selection, branch switching, three real-data pairings, preview-only behavior, invalid file feedback, keyboard dismissal of the explanation dialog, fake-camera capture, camera-track release and mobile layout without horizontal overflow.
- Real CLIP inference completed in Chromium on a downloaded iced-coffee photo. The image was passed to a browser worker, not an image-recognition API. The model's top family was iced black coffee; iced milk coffee appeared in the top three, although the photo showed visible milk. This is a known ambiguity from the smoke test, not an accuracy success. Menu confirmation is mandatory.
- No uncaught browser errors occurred during the end-to-end test. An initial favicon 404 was fixed before packaging.

The browser test used desktop Chromium with a fake camera. Phone hardware cameras, iOS/Safari, cold-start behavior on low-memory phones and accuracy on representative drinks have not been validated. First use downloads a substantial model. Internet/CDN failures produce a visible error; manual menu exploration remains available.

## Business use and limits

Customers can find a similar Stories drink after seeing a drink elsewhere and discover an optional food pairing. The pairing rule uses January–May product co-purchases weighted by branch-specific gross margin, with smoothing. It is not the category XGBoost model. Product-level retrieval quality and causal purchase uplift have not been established.

Current prototype prices come from historical transactions, not a live POS. There is no ordering/payment integration. Photos do not persist and session feedback stays in memory unless the visitor downloads it. Test feedback records are not automatically collected or used for retraining.

Before any accuracy claim: collect verified real drink images; split by drink/photo session; calibrate abstention on validation images; report untouched test top-1/top-3 accuracy, macro F1, out-of-scope false acceptance and acceptance coverage. Before a profit claim: randomize recommendation exposure and measure completed-basket gross profit, not pairing clicks.

Source and setup: [app README](../drink-lens/README.md). Catalog exporter: [Python source](../src/export_drink_lens.py). App source: `drink-lens/dist/`.

## Two-mode update

The app now offers description-to-menu matching (default) and optional image-to-image retrieval against five separately stored Wikimedia photos. Both require menu confirmation. The original CSV SHA-256 was rechecked against the initial audit and is unchanged. No photo rows or labels were inserted into it.

Seven core tests passed. Chromium verified that default mode does not fetch reference assets; the optional gallery has attribution; real CLIP description inference and real image-to-image inference complete; switching back works; `?references=off` hides the optional mode without fetching its assets. A standalone ZIP excludes reference assets and permanently disables the mode through HTML configuration.

A real iced-coffee photo with visible milk was a smoke-test input. The description model ranked iced black coffee first, and the five-photo image retrieval ranked the espresso example first. These demonstrate functioning pipelines but also incorrect top matches; neither establishes useful accuracy. No prompts, thresholds or photo labels were tuned to claim success on that image. The separate collection is a small exploratory gallery, not a held-out benchmark.

Image source/author/license metadata: `drink-lens/dist/assets/references/manifest.json`. Individual photos retain their CC0 or CC BY-SA licenses. Setup and limits: `drink-lens/README.md`. Photo-free package: `artifacts/drink-lens-descriptions-only.zip`.
