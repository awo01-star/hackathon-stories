### Step 7 — Daily transaction forecasting: first model comparison

Target: next-day unique recorded transactions per branch, using the eight Step 6 features. **Train: Jan 8–Apr 30 (339 rows); validation: May 1–31 (93 rows); test: June 1–30 (90 rows).** Each date stays in one partition. Predictions for May/June use observed prior-day histories as they become available, with no parameter updates during either evaluation month. This is not a June 1 forecast of the whole month.

The search was fixed in advance: **four Random Forest and four XGBoost settings**, seed 490, selected by pooled May MAE. Branch and weekday are one-hot encoded inside training-only pipelines. Numeric features pass through without scaling or imputation. After locking configurations and the overall winner on May, selected ML pipelines and preprocessing refit Jan 8–May 31, then score June. The original transaction CSV and feature CSV are unmodified.

| Model | May MAE | May RMSE | May WAPE | June MAE | June RMSE | June WAPE |
|---|---:|---:|---:|---:|---:|---:|
| Seasonal naive | 8.9355 | 12.3319 | 12.91% | 9.6000 | 11.6113 | 12.51% |
| Random Forest | 9.1987 | 13.1514 | 13.29% | 10.0521 | 13.4934 | 13.10% |
| XGBoost | 8.2523 | 12.4338 | 11.92% | 9.1015 | 12.2786 | 11.86% |

**Selected on validation: XGBoost.** Lowest June MAE (descriptive, not used to switch the choice): XGBoost. The validation-selected method has **5.19% lower June MAE** than seasonal naive. MAE and RMSE are transactions per branch-day. WAPE is total absolute error divided by total transactions, not classification accuracy.

![Actual versus predicted daily transactions](../../figures/demand_forecasting/june_actual_vs_predicted.png)

#### Branch-level results

**Validation**

| Branch | Model | MAE | RMSE | WAPE |
|---|---|---:|---:|---:|
| Harbour | Seasonal naive | 12.2581 | 16.8753 | 12.22% |
| Harbour | Random Forest | 12.2900 | 17.6548 | 12.25% |
| Harbour | XGBoost | 12.1586 | 17.8270 | 12.12% |
| Garden | Seasonal naive | 7.2903 | 9.1933 | 10.62% |
| Garden | Random Forest | 9.1824 | 11.6453 | 13.38% |
| Garden | XGBoost | 6.5507 | 8.7375 | 9.54% |
| Uptown | Seasonal naive | 7.2581 | 9.3239 | 18.73% |
| Uptown | Random Forest | 6.1237 | 8.4600 | 15.81% |
| Uptown | XGBoost | 6.0474 | 8.3458 | 15.61% |

**Test**

| Branch | Model | MAE | RMSE | WAPE |
|---|---|---:|---:|---:|
| Harbour | Seasonal naive | 11.2333 | 13.8263 | 9.95% |
| Harbour | Random Forest | 13.1179 | 18.0624 | 11.62% |
| Harbour | XGBoost | 11.4805 | 16.1115 | 10.17% |
| Garden | Seasonal naive | 10.2333 | 11.8251 | 13.64% |
| Garden | Random Forest | 10.1715 | 12.1595 | 13.56% |
| Garden | XGBoost | 9.3153 | 11.2545 | 12.41% |
| Uptown | Seasonal naive | 7.3333 | 8.5713 | 17.34% |
| Uptown | Random Forest | 6.8668 | 8.4915 | 16.23% |
| Uptown | XGBoost | 6.5088 | 8.1271 | 15.39% |

**Mixed evidence:** June RMSE is lowest for Seasonal naive, so the MAE winner is not the winner on large-error penalties. June per-branch MAE winners are {'Harbour': 'Seasonal naive', 'Garden': 'XGBoost', 'Uptown': 'XGBoost'}. These are descriptive June comparisons; no branch-specific hybrid is selected from June. The paired-date interval includes zero, so this month does not establish a reliable improvement. Random Forest is retained in the report even if it loses to the baseline.

#### Interpretation and limits

The selected model misses by 9.10 transactions per branch-day on average in June, compared with 9.60 for copying the same weekday last week. Better forecasts can guide staffing/preparation planning, but do not establish extra sales, dollars saved, optimum inventory or treatment effects. Transaction counts do not specify products or preparation quantities; product mix and cost/capacity information are needed before converting this target into stocking decisions.

Paired-date bootstrap 95% interval for baseline MAE minus the validation-selected model's MAE: **-0.7294–1.8134** transactions/day (1,000 resamples, three branches kept together within each date). Only 30 June dates exist; serial dependence and explored model families limit generalization. This uncertainty summary is not used for selection.

June was already inspected during earlier EDA and separate model tasks. This run excludes June from tuning, but cannot retroactively make it an unseen external benchmark. Validate on later dates or a prospective shadow pilot. One-hot weekday is known for a forecast date; lag 1 and the rolling mean require the preceding day to have closed. No claim is made for a week-ahead forecast or disruption-specific performance.

Artifacts: [full results](../demand_forecasting/model_results.json), [all eight validation trials](../demand_forecasting/validation_search.csv), [predefined search](../demand_forecasting/search_spec.json), [selection lock](../demand_forecasting/selection_lock.json), [comparison CSV](../demand_forecasting/model_comparison.csv), [saved-model manifest](../demand_forecasting/best_model_manifest.json). The saved model bundle and row-level predictions stay in ignored `artifacts/daily_demand_models/`. Its pipeline is fit through May 31, not June. If the baseline wins, the bundle explicitly stores its Lag7 prediction rule rather than claiming an ML model won.

Reproduce: `python3 src/train_daily_models.py --data daily_demand_features.csv`. Executed notebook: `notebooks/03_ml_demand_models.ipynb`. No original transaction rows or source features are overwritten.
