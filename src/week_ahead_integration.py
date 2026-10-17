"""Additive week-ahead analysis using the team's read-only cost formulas."""
from pathlib import Path
import hashlib
from importlib.metadata import version
import itertools
import json
import shutil

import numpy as np
import pandas as pd


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_team_economics_source(root):
    path = root / "src/forecast_business_value.py"
    if not path.is_file():
        raise FileNotFoundError("This extension requires the team's src/forecast_business_value.py")
    return sha(path)


def decision_study(data_path, predictions, root, output):
    # Import pure accounting/loss helpers only. Never call the existing run/write_report.
    from forecast_business_value import transaction_economics, decision_loss
    from forecast_business_value import SHORTAGE_FRACTIONS, WASTE_FRACTIONS

    inputs_before = {"source": sha(data_path),
                     "cost_source": verify_team_economics_source(root)}
    _, transactions, economics = transaction_economics(data_path)
    calibration = economics[economics.Period.eq("Jan-May calibration")].set_index("Branch")
    source = transactions.groupby(["Date", "Branch"]).size()
    predictions = predictions.copy()
    expected = set(itertools.product(pd.date_range("2026-06-01", "2026-06-30"),
                                     ["Garden", "Harbour", "Uptown"]))
    for name, group in predictions.groupby("method"):
        keys = list(zip(group.date, group.branch))
        if len(keys) != 90 or set(keys) != expected or len(set(keys)) != 90:
            raise ValueError("Every forecast must have the identical 90 June branch-days")
        if not (group.actual.to_numpy() == [source.loc[key] for key in keys]).all():
            raise ValueError("Targets do not match distinct source transactions")
        if not np.isfinite(group.predicted).all() or (group.predicted < 0).any():
            raise ValueError("Invalid prediction")
        if not ((group.date >= group.origin) & ((group.date-group.origin).dt.days < 7)).all():
            raise ValueError("Forecast date outside its issue week")
    if set(predictions.method) != {"baseline", "selected", "seasonal_naive_4_weeks"}:
        raise ValueError("Unexpected forecast comparison")
    rows = []
    for shortage_fraction, waste_fraction in itertools.product(SHORTAGE_FRACTIONS, WASTE_FRACTIONS):
        for name, group in predictions.groupby("method"):
            shortage_unit = shortage_fraction * group.branch.map(calibration.GPPerTransactionUSD).to_numpy()
            excess_unit = waste_fraction * group.branch.map(calibration.InputCostPerTransactionUSD).to_numpy()
            for policy in ["integer", "continuous"]:
                prepared = np.floor(group.predicted.to_numpy() + .5) if policy == "integer" else group.predicted.to_numpy()
                shortage, excess, under, over = decision_loss(group.actual, prepared, shortage_unit, excess_unit)
                frame = pd.DataFrame({"Branch": group.branch.to_numpy(),
                                      "ShortageTransactions": shortage, "ExcessTransactions": excess,
                                      "ShortageCostUSD": under, "OverPreparationCostUSD": over})
                frame["TotalDecisionCostUSD"] = under + over
                fields = list(frame.columns[1:])
                summary = frame.groupby("Branch", as_index=False)[fields].sum()
                summary = pd.concat([summary, pd.DataFrame([{"Branch": "ALL", **frame[fields].sum().to_dict()}])])
                for row in summary.to_dict("records"):
                    rows.append({"Scenario": f"S{shortage_fraction:g}_W{waste_fraction:g}",
                                 "ShortageFraction": shortage_fraction, "WasteFraction": waste_fraction,
                                 "CapacityPolicy": policy, "method": name, **row})
    result = pd.DataFrame(rows)
    result.to_csv(output / "tables/week_ahead_decision_costs.csv", index=False)
    predictions.to_csv(output / "tables/week_ahead_comparison_predictions.csv", index=False)
    economics[economics.Period.eq("Jan-May calibration")].to_csv(
        output / "tables/week_ahead_calibration_economics.csv", index=False)
    assert inputs_before == {"source": sha(data_path), "cost_source": verify_team_economics_source(root)}
    (output / "decision_provenance.json").write_text(json.dumps({
        **inputs_before, "training_unchanged_by_cost_study": True,
        "calibration_end": "2026-05-31", "actual_savings_measured": False,
        "selection_based_on_decision_costs": False,
        "helpers": ["forecast_business_value.transaction_economics", "forecast_business_value.decision_loss"],
        "runtime_versions": {name: version(name) for name in ["numpy", "pandas", "scipy", "scikit-learn"]},
    }, indent=2) + "\n", encoding="utf-8")
    return result


def publish(root, output, public, metrics, branches, weekdays, decisions, audit):
    """Allowlist aggregate evidence; keep daily predictions and fits ignored."""
    public.mkdir(parents=True, exist_ok=True)
    for name, frame in [("benchmark_metrics.csv", metrics), ("branch_metrics.csv", branches),
                        ("weekday_metrics.csv", weekdays), ("decision_costs.csv", decisions)]:
        frame.to_csv(public / name, index=False)
    for name in ["summary.json", "protocol.json", "selection.json", "validation.json", "decision_provenance.json"]:
        shutil.copyfile(output / name, public / name)
    shutil.copyfile(output / "tables/week_ahead_calibration_economics.csv", public / "calibration_economics.csv")
    result = json.loads((output / "summary.json").read_text())
    overall = decisions[decisions.Branch.eq("ALL")]
    discussion = []
    for policy in ["integer", "continuous"]:
        pivot = overall[overall.CapacityPolicy.eq(policy)].pivot(
            index="Scenario", columns="method", values="TotalDecisionCostUSD")
        for benchmark in ["baseline", "seasonal_naive_4_weeks"]:
            gain = pivot[benchmark] - pivot["selected"]
            discussion.append(f"- {policy} capacity vs {benchmark}: selected forecast has lower assumed cost "
                              f"in {int((gain > 1e-8).sum())}/9 scenarios; total June cost difference "
                              f"(benchmark minus selected) ranges from ${gain.min():+.2f} to ${gain.max():+.2f}.")
    header = ["method", "WAPE (%)", "100-WAPE (%)", "MAE", "RMSE", "Bias (%)"]
    table = "| " + " | ".join(header) + " |\n|" + "|".join(["---"]*len(header)) + "|\n"
    for row in metrics.to_dict("records"):
        table += "| " + " | ".join(str(row[key]) if key == "method" else f"{row[key]:.3f}" for key in header) + " |\n"
    report = f"""# Week-ahead planning: extension to notebooks 02–05

**Business use:** plan all seven daily branch totals before the week begins.
Notebook 03 addresses next-day updates; this study refits weekly and forecasts
seven days at once. It does not replace the team's profit/root-cause argument.

## Measured historical forecast performance

{table}
June contains 90 matched branch-days. Recipe selection uses March/April and May;
all fits exclude their target week. Previously completed June weeks may enter
later training. June was inspected before this extension: results are exploratory.
100%-WAPE is an error shorthand, not exact-match accuracy or a confidence level.

The descriptive 95% interval for WAPE reduction against the regression baseline is
{100*result['bootstrap95_wape_reduction'][0]:+.3f} to
{100*result['bootstrap95_wape_reduction'][1]:+.3f} percentage points;
approximate DM/HAC p={result['dm']['p_value_two_sided']:.4f}. The gain is not conclusive.
The selected model's RMSE is slightly worse than the regression baseline.

## Hypothetical business decision test

Reuse notebook 04's original Jan–May GP/input-cost accounting and shortage/excess
formulas without rewriting its reports or running its pipeline. All nine penalty
combinations are reported for every weekly model, with integer and continuous
capacity. There is no cost-based retuning or selection from June.

{chr(10).join(discussion)}

These are scenario-dependent penalties, **not measured savings or profit uplift**.
Do not deploy the lowest-WAPE recipe on that score alone. Retain the regression
baseline in the prospective pilot: under the current assumptions it can have
lower preparation penalties despite slightly higher absolute prediction error.
The nine scenarios reuse the same errors. Recorded costs may include allocation;
actual waste, lost sales, salvage, labour, service delays and implementation costs
are unknown. Transaction capacity is a proxy and cannot specify product orders.

## Relationship to the team's existing findings

- Notebook 03's next-day XGBoost and this weekly model have different information
  schedules and refitting rules. Their scores cannot establish a controlled winner.
- Notebook 05's branch hybrid was proposed after inspecting June; this is a global
  May-selected blend, not a retrospective selection of June branch winners.
- Notebook 10's shared weekday rhythm motivates pooling; it does not establish
  that today's real branches follow the same pattern. Check raw POS and promotions.
- Garden cost/price investigation, offers and long-term profit outlook remain
  separate. Forecast accuracy does not validate a promotion or recoverable cash.

**Pilot:** freeze the recipe, store weekly forecasts before sales arrive, compare
with normal planning on newly collected weeks, and measure paid hours, service
delays, availability and waste. Verify opening hours and operational penalties.

## Reproduce and inspect

Set `STORIES_DATA` to the supplied CSV or use `data/stories_transactions.csv`.
Run [notebook 12](../../notebooks/12_week_ahead_demand_forecasting.ipynb), then
[notebook 13](../../notebooks/13_week_ahead_validation.ipynb), each with a fresh
kernel and Run All. Source code is in `src/stories_coffee/` and
`src/week_ahead_integration.py`. Supplemental dependencies are in
`requirements-week-ahead.txt`; the team's original requirements are unchanged.

Published evidence contains aggregate metrics, selection/protocol, source hash,
runtime versions, calibration economics and decision costs. Detailed forecasts,
saved coefficients and the next forecast stay under ignored
`artifacts/week_ahead_forecasting/`. No raw CSV or individual transaction records
are added. Missing branch-days stop fitting rather than being imputed as zero.
The default next forecast starts {result['next_forecast_origin']}, after source
end {result['source_end']}; it is a historical example, not today's forecast.

Audit status: **{audit['status']}** ({audit['checks_run']} computation checks).
This verifies consistency rather than prospective accuracy. Run
`python src/verify_week_ahead.py` after both notebooks to check the integration.
"""
    (public / "README.md").write_text(report, encoding="utf-8")
