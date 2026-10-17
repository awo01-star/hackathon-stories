"""Chronological model selection, evaluation and seven-day point forecasts."""
import hashlib
import json

import numpy as np
import pandas as pd

from . import models
from .data import load_data
from .evaluation import bootstrap_gain, dm_test, scores, write_json
from .reporting import write_report


def evaluation_periods():
    """Frozen 2026 study dates; June remains an exploratory re-evaluation."""
    return {
        "development": list(pd.date_range("2026-03-02", "2026-04-20", freq="7D")),
        "validation": list(pd.date_range("2026-05-04", "2026-05-25", freq="7D")),
        "june": list(pd.date_range("2026-06-01", "2026-06-29", freq="7D")),
    }


def prepare_output(output):
    for folder in [output, output / "tables", output / "model_fits"]:
        folder.mkdir(parents=True, exist_ok=True)


def predict_recipe(data, origin, recipe, configs, save_to=None):
    if not recipe or not np.isclose(sum(recipe.values()), 1.0):
        raise ValueError("Forecast component weights must sum to one.")
    blocks = []
    for method, weight in recipe.items():
        if method not in configs or not np.isfinite(weight) or weight < 0:
            raise ValueError("Unknown model or invalid blend weight.")
        frame, fitted = models.predict(data, origin, configs[method])
        if save_to is not None:
            write_json(
                save_to / f"{method}_{origin:%Y-%m-%d}.json",
                {"origin": origin, "method": method, "config": configs[method], "fit": fitted},
            )
        frame["predicted"] *= weight
        blocks.append(frame)
    return (
        pd.concat(blocks).groupby(["date", "branch", "origin"], as_index=False)
        .predicted.sum()
    )


def _attach_actuals(data, forecast, method, stage):
    actual = data.daily.rename(columns={"transactions": "actual"})
    frame = forecast.merge(actual, on=["date", "branch"], validate="one_to_one")
    frame["method"] = method
    frame["stage"] = stage
    return frame


def _shortlist(development_metrics):
    ranking = pd.DataFrame(development_metrics).sort_values(["wape", "method"])
    return ranking[ranking.method.ne("baseline")].head(3).method.tolist()


def _recipes(shortlist):
    return {
        "baseline": {"baseline": 1.0},
        **{name: {name: 1.0} for name in shortlist},
        "half_baseline_devwinner": {"baseline": 0.5, shortlist[0]: 0.5},
        "average_devtop3": {name: 1 / 3 for name in shortlist},
    }


def _future_forecast(data, output, selected, recipe, configs):
    origin = data.end + pd.Timedelta(days=1)
    forecast = predict_recipe(data, origin, recipe, configs, output / "model_fits")
    forecast["selected_method"] = selected
    forecast.to_csv(output / "tables/forecast_next_7_days.csv", index=False)
    return origin


def train(data_path, output):
    """Search earlier periods, freeze a recipe in May, then score June."""
    prepare_output(output)
    data = load_data(data_path)
    if data.daily.date.min() > pd.Timestamp("2026-01-01") or data.end < pd.Timestamp("2026-06-30"):
        raise ValueError("The frozen study requires January through June 2026. Use predict for later incoming data.")
    configs = models.candidates()
    periods = evaluation_periods()
    protocol = {
        "candidate_count": len(configs),
        "new_candidate_count": len(configs) - 1,
        "candidates": configs,
        "evaluation_periods": {stage: [str(day.date()) for day in days] for stage, days in periods.items()},
        "primary_target": "Daily transactions per branch; seven-day forecast issued weekly",
        "selection": "March/April top three; May minimum WAPE among those, baseline and two fixed blends",
        "june_used_for_selection": False,
        "june_previously_inspected": True,
        "untouched_confirmatory_test": False,
        "prior_assumptions": {
            "branch_growth_basis_coefficient_deviation_sd": 0.15,
            "quadratic_log_curvature_sd": 0.05,
            "weekday_growth_sd": 0.05,
            "log_age_offset_days": 90,
        },
    }
    write_json(output / "protocol.json", protocol)

    summaries, development, diagnostics = [], [], []
    for method, config in configs.items():
        blocks = []
        for origin in periods["development"]:
            forecast, fitted = models.predict(data, origin, config)
            blocks.append(_attach_actuals(data, forecast, method, "development"))
            if fitted["kind"] == "pooled":
                diagnostics.append({
                    "stage": "development", "origin": origin, "method": method,
                    **{key: fitted[key] for key in ["training_rows", "max_abs_gradient", "iterations"]},
                })
        frame = pd.concat(blocks, ignore_index=True)
        development.append(frame)
        summaries.append({"stage": "development", "method": method, **scores(frame)})

    shortlist = _shortlist(summaries)
    recipes = _recipes(shortlist)
    validation = []
    for method, recipe in recipes.items():
        blocks = [
            _attach_actuals(data, predict_recipe(data, origin, recipe, configs), method, "validation")
            for origin in periods["validation"]
        ]
        frame = pd.concat(blocks, ignore_index=True)
        validation.append(frame)
        summaries.append({"stage": "validation", "method": method, **scores(frame)})
    ranking = pd.DataFrame(
        [row for row in summaries if row["stage"] == "validation"]
    ).sort_values(["wape", "method"])
    selected = str(ranking.iloc[0].method)
    recipe = recipes[selected]
    selection = {
        "development_shortlist": shortlist,
        "validation_recipes": recipes,
        "selected_method": selected,
        "selected_recipe": recipe,
        "selected_on": "May WAPE after March/April shortlist",
        "validation_ranking": ranking.to_dict("records"),
        "branches": data.branches,
        "protocol_sha256": hashlib.sha256((output / "protocol.json").read_bytes()).hexdigest(),
    }
    # Save the locked selection before evaluating June.
    write_json(output / "selection.json", selection)

    test_blocks = []
    for origin in periods["june"]:
        for label, component_weights in [("baseline", {"baseline": 1.0}), ("selected", recipe)]:
            forecast = predict_recipe(data, origin, component_weights, configs, output / "model_fits")
            forecast = forecast[forecast.date.le(pd.Timestamp("2026-06-30"))]
            test_blocks.append(_attach_actuals(data, forecast, label, "june"))
    june = pd.concat(test_blocks, ignore_index=True)
    for method, frame in june.groupby("method"):
        summaries.append({"stage": "june", "method": method, **scores(frame)})

    predictions = pd.concat(development + validation + [june], ignore_index=True)
    predictions.to_csv(output / "tables/predictions.csv", index=False, float_format="%.10f")
    pd.DataFrame(summaries).to_csv(output / "tables/metrics.csv", index=False)
    pd.DataFrame(diagnostics).to_csv(output / "tables/optimizer_checks.csv", index=False)
    pd.DataFrame([
        {"method": method, "branch": branch, **scores(frame)}
        for (method, branch), frame in june.groupby(["method", "branch"])
    ]).to_csv(output / "tables/branch_metrics.csv", index=False)

    before = scores(june[june.method.eq("baseline")])
    after = scores(june[june.method.eq("selected")])
    next_origin = _future_forecast(data, output, selected, recipe, configs)
    result = {
        "source_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "source_end": str(data.end.date()),
        "selected_method": selected,
        "selected_recipe": recipe,
        "baseline": before,
        "selected": after,
        "wape_reduction_percentage_points": float(100 * (before["wape"] - after["wape"])),
        "better_in_june": bool(after["wape"] < before["wape"]),
        "relative_absolute_error_reduction": float(1 - after["wape"] / before["wape"]),
        "bootstrap95_wape_reduction": bootstrap_gain(june),
        "dm": dm_test(june),
        "june_previously_inspected": True,
        "is_untouched_confirmatory_test": False,
        "june_used_for_model_selection": False,
        "forecast_horizon_days": 7,
        "forecast_cadence": "weekly",
        "target": "transactions_per_branch_day",
        "does_not_evaluate_inventory_or_product_accuracy": True,
        "next_forecast_origin": str(next_origin.date()),
        "next_forecast_is_current_calendar_date": False,
        "assumptions": [
            "Branches may share weekday patterns and growth while differing in average traffic.",
            "Prior strengths, recency and growth shapes are candidate hypotheses, not known business facts.",
            "All fits exclude target-week sales. Completed earlier weeks may enter later training.",
            "A short development/validation period can overfit model selection.",
            "June has been repeatedly inspected. Confirm the frozen recipe on newly collected dates.",
            "Lower transaction WAPE does not establish calibrated intervals or inventory savings.",
        ],
    }
    write_json(output / "summary.json", result)
    write_report(result, selection, output)
    return result


def predict_next(data_path, output):
    """Refit the saved recipe on available history without rerunning selection."""
    selection = json.loads((output / "selection.json").read_text(encoding="utf-8"))
    protocol = json.loads((output / "protocol.json").read_text(encoding="utf-8"))
    data = load_data(data_path)
    if "branches" in selection and list(data.branches) != selection["branches"]:
        raise ValueError("The branch list changed; rerun training before predicting.")
    prepare_output(output)
    return _future_forecast(
        data, output, selection["selected_method"], selection["selected_recipe"], protocol["candidates"]
    )
