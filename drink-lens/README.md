# Stories Drink Lens

A camera-based menu discovery prototype: photograph a drink, find a similar Stories drink family, confirm a menu item, then explore food pairings for your branch.

## Implemented

- Camera capture with rear-camera preference, permission-denial feedback, and camera track shutdown after capture or closing.
- JPG/PNG/WebP upload, 12 MB limit, maximum decoded dimensions, and client-side resizing.
- Real pretrained CLIP inference in a dedicated browser worker using Transformers.js 3.0.2 and `Xenova/clip-vit-base-patch32` (q8 ONNX, WASM).
- Twelve visual classes, including an out-of-scope class, top alternatives, an uncertain state, cancel/timeout handling and explicit menu confirmation.
- Branch-specific historical menu prices and product-level food pairings exported from January–May transactions, with three choices and basket previews.
- Optional download of session feedback; no photos or customer identifiers in the log, no server-side analytics, and no orders/payments.

Image inference runs on the device after downloading model code and weights from jsDelivr and Hugging Face. Initial download is substantial and may take minutes. A browser with enough memory, WebAssembly and worker support is required. Camera access needs HTTPS or localhost; camera access in an embedded preview may be blocked, in which case open the deployed page directly or upload an image. No API key is required.

The interface uses CSS illustrations, not generated drink photos. There is no simulated recognition mode. Manual menu selection is marked as manual, and a failed vision download remains a visible error rather than producing fabricated recognition output.

## Run locally

From this directory:

```sh
python3 -m http.server 8000 --directory dist --bind 127.0.0.1
```

Open `http://127.0.0.1:8000`. Do not open `index.html` using `file://` because modules, workers and menu loading need HTTP.

To regenerate the aggregate catalog from the repository root:

```sh
python3 src/export_drink_lens.py --data /path/to/stories_transactions.csv
```

Only `dist/` is served by the hosted Site. The source CSV and ML artifact directory are not bundled. The catalog contains aggregate co-purchase counts and branch menu prices, not individual transaction/customer records.

## What the models mean

**Vision:** this is zero-shot transfer from a pretrained vision-language model. It has not been fine-tuned or evaluated on a labelled Stories drink-image dataset. It matches broad appearance, not a known SKU, brand, flavor, ingredients or allergens. Two menu items can look identical. The score is a relative image/text similarity distribution across the fixed label descriptions, not calibrated correctness probability. Abstention cutoffs (`top < .22` or `top − second < .035`, or top class `other`) are uncalibrated heuristics. Always ask the user to confirm the item.

**Pairings:** use smoothed historical product co-purchases given drink and branch, ranked by `estimated co-purchase rate × branch-specific unit margin`. Thirty pseudo-baskets smooth the rate toward branch-level product frequency. No customer history or photo enters the pairing rule. This product-level extension is a new prototype rule; it is not the category XGBoost classifier, has not been evaluated as a product recommender, and does not inherit its 0.745 AUC. Broad drink-family recognition does not change the previously reported transaction-model metrics.

**Business objective:** reduce menu-search friction and test whether relevant, optional food suggestions improve total basket gross profit. Co-purchase prediction cannot establish recommendation uplift. Historical prices are for demonstration, not a current ordering menu.

## Evaluation before making accuracy or revenue claims

1. Collect consented, real drink photos with verified drink-family labels. Include non-drinks, different lighting/cups, multiple drinks, occlusion and drinks outside this menu. Do not use the scan-session correction log as a representative test set.
2. Split by physical drink/photo session and location/customer when available. Keep near-duplicate photos out of different partitions. Fix class descriptions and calibrate abstention on validation images only; preserve a separate test set.
3. Compare CLIP to the majority-class baseline and, when sufficient data exists, a trained classifier on frozen image embeddings. Report top-1 and top-3 family accuracy, macro F1, per-family precision/recall, confusion matrix, out-of-scope false acceptance and acceptance coverage with accuracy among accepted results. For ROC AUC, report one-vs-rest class AUC only when each class has both positive and negative test examples; it is not a substitute for identification accuracy.
4. Report latency, cold/warm model download behavior and memory/browser failures on real target phones. A successful desktop inference smoke test is not an accuracy benchmark or a phone compatibility guarantee.
5. Separately randomize no food prompt, a simple popular-item prompt and the new pairing rule. Log actual exposures and completed purchases. Measure net gross profit per assigned basket, accounting for cannibalization, availability and prompt cost. Keep camera/manual journeys as separate reporting strata.

## Checks

```sh
npm install
npm test
npm run check
npx playwright install chromium
node tests/browser.mjs
```

The browser suite uses a temporary localhost server, a fake camera, and temporary screenshots. It verifies the manual path, branch changes, historical pairing previews, invalid uploads, accessible dialog, camera track cleanup and mobile layout. To exercise real network-backed CLIP inference as well, set `RUN_VISION=1` and place a drink image at `/tmp/stories-vision-coffee.jpg`; it is a functionality smoke test, not an accuracy test. Tests do not buy anything, send photos to a recognition server, or publish data.

## References

- [Transformers.js zero-shot image pipeline](https://huggingface.co/docs/transformers.js/api/pipelines#module_pipelines.ZeroShotImageClassificationPipeline)
- [CLIP model converted for browser inference](https://huggingface.co/Xenova/clip-vit-base-patch32)

Static hosting settings are in `.openai/hosting.json`. The Site starts private to its owner.

## Two independent matching modes

1. **Menu descriptions (default):** photo → CLIP image/text comparison → drink family → existing CSV menu names → customer confirmation. This path does not fetch or need the optional photo gallery.
2. **Reference photos (optional experiment):** photo → CLIP image embedding → cosine similarity against separately stored reference-photo embeddings → nearest example families → existing menu names → customer confirmation. This is image-to-image retrieval, not retraining or a calibrated classifier. Scores are cosine similarities, not probabilities. The small gallery covers only five families, so unsupported drinks and non-drinks may still have a nearest image. Low similarity or a small gap uses a heuristic uncertain state; confirmation is always required.

Reference photos live only in `dist/assets/references/`. They are **outside visual examples, not verified Stories photos**. Sources, authors, licenses, transformations and image fingerprints are in [the manifest](dist/assets/references/manifest.json), [attributions](dist/assets/references/ATTRIBUTION.md), and the optional in-app gallery. Source images retain their listed CC0 or CC BY-SA licenses. Photos do not alter, append to, or relabel the transaction CSV. Our historical transaction-model scores do not measure this new visual retrieval feature.

Choose either radio option before scanning. Switching modes clears the previous result. Only one model pipeline is retained at a time to limit memory, and reference vectors stay in the worker's memory after their first calculation. Switching models may take time even when weights are cached.

To hide the reference mode, open the app with `?references=off`. To create a standalone copy **without any external reference-photo files**, run from the repository root:

```sh
python3 src/package_description_demo.py --out artifacts/drink-lens-descriptions-only
```

The exported HTML disables the photo mode even if someone removes the URL parameter. Serve that directory with a local HTTP server or deploy its files. This preserves a photo-free option if the hackathon excludes added reference images; check the actual rules separately. Both modes still use a pretrained vision model.

To redownload the collection and its source metadata, run `python3 src/fetch_drink_references.py` from the root. It requires internet access and fetches only openly licensed files. Missing candidate files are skipped. Do not treat a photo used in this gallery as a held-out test image; matching a reference to itself does not establish generalization accuracy.


## Offer Studio

Open `bundles.html` or use the Offer Studio link in Drink Lens. It provides branch/hour demand and revenue forecasts, a busy-hour exclusion policy, two/three-item bundle candidates, margin-safe discounts, shared redemption limits, scenario sliders (new baskets, add-on purchases and would-buy-anyway customers), a conservative break-even check and JSON export. Prices and planning dates are historical. No live offers are activated.

Reproduce with `python3 src/bundle_planner.py` from the repository root. The aggregate plan is `dist/assets/bundle-plan.json`; the source CSV stays unchanged. Implementation, assumptions, measured forecast results and pilot design are in `reports/BUNDLE_PLANNER.md` at the repository root. Product selection, sizes, caps and discounts are disclosed pilot policies, not learned causal optima. The browser does not train a model; it loads locally generated forecast outputs and runs scenario accounting.

Additional checks: `node --test tests/bundles.test.mjs` and `node tests/bundle-browser.mjs`.

## Profit Lab — seven additional modules

Open `/profit-lab.html` from the same server for Ideas 9–15: basket completion, the one-dollar price challenge, menu alternatives, profit-risk alerts, discount review, portfolio attention and crisis menu/stock planning. Branch selectors, scenario/sensitivity controls and an aggregate evidence download are implemented. This page uses `dist/assets/profit-lab.json`; it does not run Python models in the browser or create live offers, orders or stock movements.

[Full report](../reports/profit_lab/REPORT.md) · [Executed notebook](../notebooks/04_profit_lab.ipynb). July 1, 2026 planning examples are historical, from data through June 30. This evaluated basket model is separate from Drink Lens's original pairing rule; the latter does not inherit its results. The conditional margin model loses to the simple popularity margin baseline. Profit-risk alerts have many false positives. Discount exposure and portfolio captured GP are not incremental gains. Crisis scenarios use assumed ingredient groups, procurement budgets and capacity; they are not validated wartime predictions.

Regenerate from the repository root after preparing `daily_demand_features.csv`, `artifacts/demand_predictions.csv` and `artifacts/next_day_forecast.csv` using the existing preparation/forecast scripts:

```sh
python3 src/profit_lab.py --data /path/to/stories_transactions.csv --features daily_demand_features.csv
python3 src/build_profit_lab_report.py
python3 src/build_profit_lab_notebook.py
python3 src/verify_profit_lab.py
```

Run `npm test` and `npm run check` in this directory. `tests/profit-lab-browser.mjs` uses Playwright to check all seven panels, controls, JSON export, existing navigation and mobile layouts. Backend verification checks financial identities, source immutability and optimizer feasibility, including closed-branch and unavailable-resource cases. Only aggregate web assets are published; no serialized model, source CSV or individual predictions are served.
