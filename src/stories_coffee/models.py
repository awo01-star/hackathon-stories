"""Pooled count models used by the latest validated point-forecast experiment.

The candidate grid and optimization are unchanged by the folder cleanup.
Penalties, recency weights and trend shapes are model assumptions.
"""
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from .baseline import fit_predict as fit_baseline


def candidates():
    configs = {"baseline": {"baseline": True}}
    for tau in [0.0, 0.05, 0.15, 0.4]:
        for basis in ["linear", "log90"]:
            for half in [None, 56]:
                name = f"pooled_{tau:g}_{basis}_half{half or 'all'}"
                configs[name] = {
                    "baseline": False,
                    "weekday_deviation_sd": tau,
                    "basis": basis,
                    "half_life_days": half,
                    "weekday_trends": False,
                }
        configs[f"pooled_{tau:g}_quadratic"] = {
            "baseline": False,
            "weekday_deviation_sd": tau,
            "basis": "quadratic",
            "half_life_days": None,
            "weekday_trends": False,
        }
    for tau in [0.0, 0.15]:
        for half in [None, 56]:
            configs[f"pooled_{tau:g}_weekdaygrowth_half{half or 'all'}"] = {
                "baseline": False,
                "weekday_deviation_sd": tau,
                "basis": "linear",
                "half_life_days": half,
                "weekday_trends": True,
            }
    return configs


def design(frame, origin, start, branches, config):
    origin, start = pd.Timestamp(origin), pd.Timestamp(start)
    time = (frame.date - origin).dt.days.to_numpy(float) / 30
    if config["basis"] == "log90":
        time = np.log((frame.date - start).dt.days.to_numpy() + 90)
        time -= np.log((origin - start).days + 90)
    indicators = [frame.branch.eq(branch).to_numpy(float) for branch in branches]
    weekday = frame.date.dt.dayofweek.to_numpy()
    columns = list(indicators)
    penalties = [1e-7] * len(branches)
    names = ["intercept_" + branch for branch in branches]

    for day in range(1, 7):
        columns.append((weekday == day).astype(float))
        penalties.append(1e-7)
        names.append("weekday_" + str(day))
    columns.append(time)
    penalties.append(1e-5)
    names.append("common_trend")
    for branch, indicator in zip(branches, indicators):
        columns.append(time * indicator)
        penalties.append(1 / 0.15**2)
        names.append("trend_deviation_" + branch)

    tau = config["weekday_deviation_sd"]
    if tau:
        for branch, indicator in zip(branches, indicators):
            for day in range(7):
                columns.append(indicator * (weekday == day))
                penalties.append(1 / tau**2)
                names.append(f"weekday_deviation_{branch}_{day}")
    if config["basis"] == "quadratic":
        columns.append(time * time)
        penalties.append(1 / 0.05**2)
        names.append("curvature")
    if config["weekday_trends"]:
        for day in [1, 5]:
            columns.append(time * (weekday == day))
            penalties.append(1 / 0.05**2)
            names.append("weekday_growth_" + str(day))
    return np.column_stack(columns), np.array(penalties), names


def objective(beta, features, target, weights, penalties):
    log_mean = features @ beta
    if np.max(np.abs(log_mean)) > 40:
        return np.inf, None, None
    mean = np.exp(log_mean)
    value = float(
        np.sum(weights * (mean - target * log_mean))
        + 0.5 * np.dot(penalties, beta**2)
    )
    gradient = features.T @ (weights * (mean - target)) + penalties * beta
    hessian = features.T @ ((weights * mean)[:, None] * features)
    hessian += np.diag(penalties)
    return value, gradient, hessian


def fit(history, origin, branches, config):
    history = history[history.date.lt(origin)].copy()
    if history.empty:
        raise ValueError("No history before forecast origin.")
    features, penalties, names = design(
        history, origin, history.date.min(), branches, config
    )
    target = history.transactions.to_numpy(float)
    if config["half_life_days"] is None:
        weights = np.ones(len(target))
    else:
        weights = np.exp2(
            (history.date - origin).dt.days.to_numpy() / config["half_life_days"]
        )
    beta = np.zeros(features.shape[1])
    for index, branch in enumerate(branches):
        mask = history.branch.eq(branch).to_numpy()
        beta[index] = np.log(max(0.1, np.average(target[mask], weights=weights[mask])))

    with threadpool_limits(limits=1):
        converged = False
        for iteration in range(100):
            value, gradient, hessian = objective(beta, features, target, weights, penalties)
            if np.max(np.abs(gradient)) < 1e-5:
                converged = True
                break
            step = np.linalg.solve(hessian, gradient)
            scale = 1.0
            while scale > 1e-10:
                proposed = beta - scale * step
                updated = objective(proposed, features, target, weights, penalties)[0]
                if updated <= value - 1e-4 * scale * float(gradient @ step):
                    break
                scale *= 0.5
            if scale <= 1e-10:
                converged = np.max(np.abs(gradient)) < 1e-3
                break
            beta = proposed
        if not converged:
            gradient = objective(beta, features, target, weights, penalties)[1]
            if np.max(np.abs(gradient)) >= 1e-3:
                raise RuntimeError("Pooled Poisson optimizer did not converge.")
    return {
        "kind": "pooled",
        "beta": beta,
        "start": history.date.min(),
        "names": names,
        "training_rows": len(history),
        "max_abs_gradient": float(np.max(np.abs(gradient))),
        "iterations": iteration + 1,
        "converged": True,
        "penalties": penalties,
        "effective_weight": float(weights.sum()),
    }


def predict(data, origin, config):
    origin = pd.Timestamp(origin)
    if config.get("baseline"):
        return fit_baseline(data, origin)
    fitted = fit(data.daily, origin, data.branches, config)
    grid = pd.MultiIndex.from_product(
        [pd.date_range(origin, periods=7), data.branches], names=["date", "branch"]
    )
    future = grid.to_frame(index=False)
    features, _, _ = design(future, origin, fitted["start"], data.branches, config)
    future["predicted"] = np.exp(features @ fitted["beta"])
    future["origin"] = origin
    return future, fitted
