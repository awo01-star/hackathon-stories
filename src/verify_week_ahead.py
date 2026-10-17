"""Independently recompute the extension's scores and hypothetical costs."""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


def verify(root, data):
    public = root / "reports/week_ahead_forecasting"
    private = root / "artifacts/week_ahead_forecasting"
    predictions = pd.read_csv(private / "tables/week_ahead_comparison_predictions.csv")
    costs = pd.read_csv(public / "decision_costs.csv")
    metrics = pd.read_csv(public / "benchmark_metrics.csv").set_index("method")
    source = pd.read_csv(data)
    source["Date"] = pd.to_datetime(source.Date)
    prior = source[source.Date.lt("2026-06-01")].copy()
    prior["cost"] = prior.Quantity * prior["Unit Cost (USD)"]
    counts = prior.groupby("Branch")["Transaction ID"].nunique()
    gp = prior.groupby("Branch")["Line Gross Profit (USD)"].sum() / counts
    input_cost = prior.groupby("Branch").cost.sum() / counts
    checks = 0
    for method, group in predictions.groupby("method"):
        assert len(group) == 90 and not group.duplicated(["date", "branch"]).any()
        actual = source.groupby([source.Date.dt.strftime("%Y-%m-%d"), "Branch"])["Transaction ID"].nunique()
        assert all(row.actual == actual.loc[row.date, row.branch] for row in group.itertuples())
        error = group.predicted - group.actual
        assert np.isclose(metrics.loc[method, "WAPE (%)"], 100*error.abs().sum()/group.actual.sum())
        assert np.isclose(metrics.loc[method, "MAE"], error.abs().mean())
        assert np.isclose(metrics.loc[method, "RMSE"], np.sqrt((error**2).mean()))
        checks += 5
    for row in costs.itertuples():
        frame = predictions[predictions.method.eq(row.method)]
        if row.Branch != "ALL":
            frame = frame[frame.branch.eq(row.Branch)]
        prepared = np.floor(frame.predicted + .5) if row.CapacityPolicy == "integer" else frame.predicted
        shortage, excess = (frame.actual-prepared).clip(lower=0), (prepared-frame.actual).clip(lower=0)
        under = (shortage * row.ShortageFraction * frame.branch.map(gp)).sum()
        over = (excess * row.WasteFraction * frame.branch.map(input_cost)).sum()
        assert np.isclose(row.ShortageTransactions, shortage.sum())
        assert np.isclose(row.ExcessTransactions, excess.sum())
        assert np.isclose(row.ShortageCostUSD, under)
        assert np.isclose(row.OverPreparationCostUSD, over)
        assert np.isclose(row.TotalDecisionCostUSD, under+over)
        checks += 5
    assert len(costs) == 9 * 3 * 2 * 4
    assert json.loads((public / "validation.json").read_text())["status"] == "PASS"
    assert json.loads((public / "decision_provenance.json").read_text())["actual_savings_measured"] is False
    assert not any(public.rglob("*predictions*"))
    assert not (public / "model_fits").exists()
    print(f"PASS: {checks+5} integration checks; scores, paired targets, costs and publication boundary")


if __name__ == "__main__":
    import argparse
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(os.environ.get("STORIES_DATA", str(root / "data/stories_transactions.csv"))))
    args = parser.parse_args()
    verify(root, args.data)
