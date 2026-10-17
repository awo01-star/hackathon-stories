"""Forecast errors, paired uncertainty and JSON output."""
import json

import numpy as np
import pandas as pd
from scipy.stats import norm


def write_json(path, value):
    def convert(item):
        if isinstance(item, pd.Timestamp):
            return item.isoformat()
        if isinstance(item, np.ndarray):
            return item.tolist()
        if isinstance(item, np.generic):
            return item.item()
        raise TypeError(type(item).__name__)

    path.write_text(
        json.dumps(value, indent=2, default=convert, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def scores(frame):
    error = (frame.actual - frame.predicted).abs()
    return {
        "n": len(frame),
        "actual_sum": float(frame.actual.sum()),
        "wape": float(error.sum() / frame.actual.sum()),
        "mae": float(error.mean()),
        "rmse": float(np.sqrt((error**2).mean())),
        "bias": float((frame.predicted - frame.actual).sum() / frame.actual.sum()),
    }


def dm_test(frame, selected="selected", benchmark="baseline"):
    losses = (
        frame.assign(error=(frame.actual - frame.predicted).abs())
        .groupby(["date", "method"]).error.mean().unstack("method")
    )
    difference = (losses[benchmark] - losses[selected]).to_numpy()
    centered = difference - difference.mean()
    count = len(difference)
    lag = min(6, count - 1)
    variance = float(centered @ centered / count)
    for offset in range(1, lag + 1):
        variance += (
            2 * (1 - offset / (lag + 1))
            * float(centered[offset:] @ centered[:-offset] / count)
        )
    statistic = (
        float(difference.mean() / np.sqrt(variance / count)) if variance > 0 else 0.0
    )
    return {
        "selected": selected,
        "benchmark": benchmark,
        "loss": "absolute_error",
        "dates": count,
        "hac_lags": lag,
        "mean_loss_reduction": float(difference.mean()),
        "dm_statistic": statistic,
        "p_value_two_sided": float(2 * norm.sf(abs(statistic))),
        "interpretation": "Approximate normal DM/HAC; reused June, mixed weekly lead times and five issue blocks.",
    }


def bootstrap_gain(frame, repetitions=10000):
    paired = frame.pivot(
        index=["origin", "date", "branch", "actual"],
        columns="method", values="predicted",
    ).reset_index()
    paired["gain"] = (
        (paired.actual - paired.baseline).abs()
        - (paired.actual - paired.selected).abs()
    )
    blocks = paired.groupby("origin")[["gain", "actual"]].sum()
    rng = np.random.default_rng(490)
    indices = rng.integers(0, len(blocks), size=(repetitions, len(blocks)))
    difference = (
        blocks.gain.to_numpy()[indices].sum(axis=1)
        / blocks.actual.to_numpy()[indices].sum(axis=1)
    )
    return [float(value) for value in np.quantile(difference, [0.025, 0.975])]
