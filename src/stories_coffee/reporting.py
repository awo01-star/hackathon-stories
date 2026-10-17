"""Generate the latest report without rewriting project documentation."""
import json

import pandas as pd


def write_report(result, selection, output):
    baseline, selected = result["baseline"], result["selected"]
    lower, upper = result["bootstrap95_wape_reduction"]
    end = pd.Timestamp(result["next_forecast_origin"]) + pd.Timedelta(days=6)
    lines = [
        "# Latest transaction forecast results", "",
        "Daily transaction totals per branch, issued seven days ahead and updated weekly.", "",
        "| June result | Original baseline | Selected blend |",
        "|---|---:|---:|",
        f"| WAPE, lower is better | {baseline['wape']:.4%} | {selected['wape']:.4%} |",
        f"| 100% minus WAPE | {1-baseline['wape']:.4%} | {1-selected['wape']:.4%} |",
        f"| MAE, transactions/day/branch | {baseline['mae']:.3f} | {selected['mae']:.3f} |",
        f"| RMSE | {baseline['rmse']:.3f} | {selected['rmse']:.3f} |",
        f"| Signed bias | {baseline['bias']:.2%} | {selected['bias']:.2%} |", "",
        f"The selected recipe {'reduces' if result['better_in_june'] else 'does not reduce'} June WAPE. "
        f"The error reduction is {result['wape_reduction_percentage_points']:+.3f} percentage points "
        f"({result['relative_absolute_error_reduction']:.1%} relative). "
        "The gain does not establish better performance on every metric or on future data.", "",
        "## How the forecast works", "",
        "The baseline estimates branch, weekday and growth effects. Pooled candidates share "
        "weekday patterns across branches while allowing penalized branch deviations and "
        "alternative growth shapes. The selected recipe is:", "",
        "```json", json.dumps(result["selected_recipe"], indent=2), "```", "",
        "## Chronological evaluation", "",
        "Eight March/April weekly origins shortlist the three best new candidates out of 24. "
        "Four May origins select among that shortlist, the baseline and two fixed blends. "
        "The chosen recipe is saved before June scoring. Five June origins compare it with "
        "the baseline on 90 identical branch-days. Later weeks may use completed earlier "
        "weeks; each forecast excludes its target week. June was inspected in earlier work, "
        "so this is an exploratory evaluation, not an untouched confirmatory test.", "",
        "| May validation recipe | WAPE |", "|---|---:|",
    ]
    lines.extend(
        f"| {row['method']} | {row['wape']:.3%} |"
        for row in selection["validation_ranking"]
    )
    lines.extend([
        "", "## Uncertainty and limits", "",
        f"Descriptive issue-week bootstrap 95% interval for error reduction: "
        f"{100*lower:+.3f} to {100*upper:+.3f} percentage points. "
        f"Approximate DM/HAC p={result['dm']['p_value_two_sided']:.4f}. "
        "The interval includes zero; only five issue blocks and June reuse limit inference.", "",
        "The score 100%-WAPE is a shorthand for volume-weighted absolute error, "
        "not a fraction of exactly correct predictions. Lower WAPE does not automatically "
        "mean better range calibration, lower inventory waste or higher profit. "
        "RMSE and signed bias show remaining tradeoffs. Freeze the recipe and test "
        "new dates before operational adoption.", "",
        "## Inspect the evidence", "",
        "- [Protocol and assumptions](protocol.json)",
        "- [Selection trace](selection.json)",
        "- [Machine-readable result](summary.json)",
        "- [Validation audit](validation.json)",
        "- [All predictions](tables/predictions.csv)",
        "- [All metrics](tables/metrics.csv)",
        "- [Branch metrics](tables/branch_metrics.csv)",
        "- [Optimizer checks](tables/optimizer_checks.csv)",
        "- [Saved coefficients](model_fits)",
        "- [Next seven daily forecasts](tables/forecast_next_7_days.csv)", "",
        f"The next forecast covers {result['next_forecast_origin']} through {end.date()}, "
        "starting after the last source observation. It is not automatically a forecast "
        "for the current calendar date.", "",
        "## Reproduce", "", "From the project root:", "", "```powershell",
        "python run.py", "python -m unittest discover -s tests", "```", "",
        "This main workflow forecasts transaction totals. Earlier probabilistic, product, "
        "inventory and external-factor studies are retained separately in the archive.", "",
        "## Assumptions", "",
    ])
    lines.extend("- " + assumption for assumption in result["assumptions"])
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
