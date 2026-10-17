"""Independent source, coefficient, selection and error-arithmetic audit.

This module deliberately does not import the forecasting implementation.
It validates exported computations; it does not prove prospective accuracy.
"""
import csv
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json
import math

import numpy as np

from .paths import REFERENCE_REPORTS


def _read(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def reconstruct(stored, day, branch):
    """Evaluate saved coefficients independently of model design code."""
    fitted = stored["fit"]
    origin = date.fromisoformat(stored["origin"][:10])
    day = date.fromisoformat(day)
    if fitted.get("kind") == "baseline":
        labels = list(fitted["category_labels"])
        label = f"{branch}_{day.weekday()}"
        value = float(fitted["intercept"])
        if label in labels:
            value += fitted["coefficients"][labels.index(label)]
        for index, column in enumerate(fitted["numeric_columns"]):
            raw = (day - origin).days / 30 if column == "trend_" + branch else 0.0
            standardized = (raw - fitted["numeric_mean"][index]) / fitted["numeric_scale"][index]
            value += fitted["coefficients"][len(labels) + index] * standardized
        return math.exp(value)

    config = stored["config"]
    start = date.fromisoformat(fitted["start"][:10])
    time = (day - origin).days / 30
    if config["basis"] == "log90":
        time = math.log((day - start).days + 90) - math.log((origin - start).days + 90)
    value = 0.0
    for name, coefficient in zip(fitted["names"], fitted["beta"]):
        if name.startswith("intercept_"):
            feature = float(name.removeprefix("intercept_") == branch)
        elif name == "common_trend":
            feature = time
        elif name == "curvature":
            feature = time * time
        elif name.startswith("trend_deviation_"):
            feature = time * float(name.removeprefix("trend_deviation_") == branch)
        elif name.startswith("weekday_deviation_"):
            label, weekday = name.removeprefix("weekday_deviation_").rsplit("_", 1)
            feature = float(label == branch and day.weekday() == int(weekday))
        elif name.startswith("weekday_growth_"):
            feature = time * float(day.weekday() == int(name.removeprefix("weekday_growth_")))
        elif name.startswith("weekday_"):
            feature = float(day.weekday() == int(name.removeprefix("weekday_")))
        else:
            raise ValueError("Unknown coefficient: " + name)
        value += coefficient * feature
    return math.exp(value)


def validate(data_path, output, reference=REFERENCE_REPORTS):
    checks_run = 0
    failures = []

    def check(label, passed):
        nonlocal checks_run
        checks_run += 1
        if not passed:
            failures.append(label)

    def close(a, b):
        return math.isclose(float(a), float(b), rel_tol=1e-8, abs_tol=1e-8)

    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    selection = json.loads((output / "selection.json").read_text(encoding="utf-8"))
    protocol = json.loads((output / "protocol.json").read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(data_path.read_bytes()).hexdigest()
    check("source hash", summary["source_sha256"] == source_hash)
    check("protocol hash", selection["protocol_sha256"] == hashlib.sha256((output / "protocol.json").read_bytes()).hexdigest())
    check("bounded candidate search", len(protocol["candidates"]) == 25)

    baskets = defaultdict(set)
    for row in _read(data_path):
        baskets[row["Date"], row["Branch"]].add(row["Transaction ID"])
    branches = sorted({branch for _, branch in baskets})
    first_date = min(day for day, _ in baskets)
    predictions = _read(output / "tables/predictions.csv")
    groups = defaultdict(list)
    lookup = {}
    for row in predictions:
        day, branch = row["date"], row["branch"]
        origin = date.fromisoformat(row["origin"])
        check("source target", close(row["actual"], len(baskets[day, branch])))
        check("weekly horizon", 0 <= (date.fromisoformat(day) - origin).days <= 6)
        check("declared stage origin", row["origin"] in protocol["evaluation_periods"][row["stage"]])
        check("finite nonnegative prediction", math.isfinite(float(row["predicted"])) and float(row["predicted"]) >= 0)
        groups[row["stage"], row["method"]].append(row)
        lookup[row["stage"], row["method"], day, branch] = row

    computed = {}
    for metric in _read(output / "tables/metrics.csv"):
        key = metric["stage"], metric["method"]
        rows = groups[key]
        actual = np.array([float(row["actual"]) for row in rows])
        predicted = np.array([float(row["predicted"]) for row in rows])
        error = np.abs(actual - predicted)
        values = {
            "n": len(rows), "actual_sum": actual.sum(),
            "wape": error.sum() / actual.sum(), "mae": error.mean(),
            "rmse": np.sqrt(np.mean(error**2)),
            "bias": (predicted - actual).sum() / actual.sum(),
        }
        for field, value in values.items():
            check(f"metric/{key}/{field}", close(metric[field], value))
        computed[key] = values

    ranked = sorted(
        (values["wape"], method)
        for (stage, method), values in computed.items()
        if stage == "development" and method != "baseline"
    )
    check("development-only shortlist", [method for _, method in ranked[:3]] == selection["development_shortlist"])
    validation_rank = sorted(
        (values["wape"], method)
        for (stage, method), values in computed.items() if stage == "validation"
    )
    check("May-only selection", validation_rank[0][1] == selection["selected_method"] == summary["selected_method"])
    recipe = summary["selected_recipe"]
    check("selected recipe", recipe == selection["validation_recipes"][selection["selected_method"]])
    check("blend weights", close(sum(recipe.values()), 1.0) and all(weight >= 0 for weight in recipe.values()))
    for (stage, method), rows in groups.items():
        expected = {
            ((date.fromisoformat(origin) + timedelta(days=offset)).isoformat(), branch)
            for origin in protocol["evaluation_periods"][stage]
            for offset in range(7) for branch in branches
            if stage != "june" or date.fromisoformat(origin) + timedelta(days=offset) <= date(2026, 6, 30)
        }
        check(f"same complete evaluation rows/{stage}/{method}", len(rows) == len(expected) and {(row["date"], row["branch"]) for row in rows} == expected)

    fit_cache = {}

    def point(method, origin, day, branch):
        key = method, origin
        if key not in fit_cache:
            stored = json.loads((output / "model_fits" / f"{method}_{origin}.json").read_text(encoding="utf-8"))
            fitted = stored["fit"]
            expected_rows = (date.fromisoformat(origin) - date.fromisoformat(first_date)).days * len(branches)
            check("strictly past fit row count", fitted["training_rows"] == expected_rows)
            if fitted.get("kind") == "pooled":
                check("optimizer convergence", fitted["converged"] and fitted["max_abs_gradient"] < 1e-3)
            fit_cache[key] = stored
        return reconstruct(fit_cache[key], day, branch)

    for method in ["baseline", "selected"]:
        weights = {"baseline": 1.0} if method == "baseline" else recipe
        for row in groups["june", method]:
            prediction = sum(
                weight * point(component, row["origin"], row["date"], row["branch"])
                for component, weight in weights.items()
            )
            check("independent forecast formula", close(prediction, row["predicted"]))
        for field, value in computed["june", method].items():
            check(f"summary/{method}/{field}", close(summary[method][field], value))

    before, after = computed["june", "baseline"], computed["june", "selected"]
    check("error reduction claim", close(summary["wape_reduction_percentage_points"], 100 * (before["wape"] - after["wape"])))
    check("better flag", summary["better_in_june"] == (after["wape"] < before["wape"]))
    blocks = defaultdict(lambda: [0.0, 0.0])
    daily = defaultdict(list)
    for row in groups["june", "selected"]:
        control = lookup["june", "baseline", row["date"], row["branch"]]
        actual = float(row["actual"])
        gain = abs(actual - float(control["predicted"])) - abs(actual - float(row["predicted"]))
        blocks[row["origin"]][0] += gain
        blocks[row["origin"]][1] += actual
        daily[row["date"]].append(gain)
    block = np.array([value for _, value in sorted(blocks.items())])
    indices = np.random.default_rng(490).integers(0, len(block), size=(10000, len(block)))
    interval = np.quantile(block[indices, 0].sum(axis=1) / block[indices, 1].sum(axis=1), [0.025, 0.975])
    check("bootstrap arithmetic", all(close(a, b) for a, b in zip(interval, summary["bootstrap95_wape_reduction"])))
    difference = np.array([sum(value) / len(value) for _, value in sorted(daily.items())])
    centered, count = difference - difference.mean(), len(difference)
    variance = float(centered @ centered / count)
    for offset in range(1, 7):
        variance += 2 * (1 - offset / 7) * float(centered[offset:] @ centered[:-offset] / count)
    statistic = float(difference.mean() / math.sqrt(variance / count)) if variance > 0 else 0.0
    check("DM/HAC arithmetic", close(statistic, summary["dm"]["dm_statistic"]) and close(math.erfc(abs(statistic) / math.sqrt(2)), summary["dm"]["p_value_two_sided"]))
    for row in _read(output / "tables/optimizer_checks.csv"):
        check("development optimizer convergence", float(row["max_abs_gradient"]) < 1e-3)

    next_rows = _read(output / "tables/forecast_next_7_days.csv")
    check("next seven-day grid", len(next_rows) == 7 * len(branches) and len({(row["date"], row["branch"]) for row in next_rows}) == len(next_rows))
    for row in next_rows:
        prediction = sum(
            weight * point(component, row["origin"], row["date"], row["branch"])
            for component, weight in recipe.items()
        )
        check("next forecast formula", close(prediction, row["predicted"]))
        check("next source period", row["date"] > summary["source_end"] and row["origin"] == summary["next_forecast_origin"])

    reference_status = "not applicable to this source file"
    reference_summary = reference / "expected_summary.json"
    if reference_summary.exists():
        previous = json.loads(reference_summary.read_text(encoding="utf-8"))
        if previous["source_sha256"] == source_hash:
            reference_status = "checked against pre-cleanup predictions"
            for row in _read(reference / "previous_june_forecasts.csv"):
                current = lookup["june", row["method"], row["date"], row["branch"]]
                check("pre-cleanup prediction parity", close(current["predicted"], row["predicted"]))
            future = {(row["date"], row["branch"]): row for row in next_rows}
            for row in _read(reference / "previous_next7_forecast.csv"):
                key = row["date"], row["branch"]
                check("pre-cleanup next-forecast parity", key in future and close(future[key]["predicted"], row["predicted"]))
            for row in _read(reference / "baseline_next7.csv"):
                baseline_value = point("baseline", row["origin"], row["date"], row["branch"])
                check("pre-cleanup baseline future parity", close(baseline_value, row["transactions"]))

    result = {
        "status": "PASS" if not failures else "FAIL",
        "checks_run": checks_run,
        "failures": failures,
        "cleanup_regression_reference": reference_status,
        "scope": "Source targets, selection, coefficients, blend weights, score arithmetic, issue cutoffs, bootstrap/DM and pre-cleanup prediction parity. No independent parameter optimization or prospective accuracy guarantee.",
    }
    (output / "validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
