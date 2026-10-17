"""The original log-linear transaction baseline, preserved numerically."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import PoissonRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _features(frame, origin, branches):
    features = pd.DataFrame(index=frame.index)
    features["branch_dow"] = frame.branch + "_" + frame.date.dt.dayofweek.astype(str)
    time = (frame.date - origin).dt.days / 30
    for branch in branches:
        features["trend_" + branch] = time * frame.branch.eq(branch)
    return features


def fit_predict(data, origin):
    """Issue seven daily forecasts using only dates strictly before origin."""
    origin = pd.Timestamp(origin)
    history = data.daily[data.daily.date.lt(origin)].copy()
    if history.empty:
        raise ValueError("No history before forecast origin.")
    grid = pd.MultiIndex.from_product(
        [pd.date_range(origin, periods=7), data.branches], names=["date", "branch"]
    )
    future = grid.to_frame(index=False)
    features = _features(history, origin, data.branches)
    future_features = _features(future, origin, data.branches)
    numeric = [column for column in features if column != "branch_dow"]
    transform = ColumnTransformer([
        ("calendar", OneHotEncoder(handle_unknown="ignore"), ["branch_dow"]),
        ("trend", StandardScaler(), numeric),
    ])
    model = make_pipeline(
        transform, PoissonRegressor(alpha=0.001, max_iter=2000, tol=1e-7)
    )
    model.fit(features, history.transactions)
    future["predicted"] = np.maximum(0, model.predict(future_features))
    future["origin"] = origin
    fitted_transform = model.named_steps["columntransformer"]
    estimator = model.named_steps["poissonregressor"]
    scaler = fitted_transform.named_transformers_["trend"]
    fitted = {
        "kind": "baseline",
        "origin": origin,
        "training_rows": len(history),
        "category_labels": fitted_transform.named_transformers_["calendar"].categories_[0],
        "numeric_columns": numeric,
        "numeric_mean": scaler.mean_,
        "numeric_scale": scaler.scale_,
        "coefficients": estimator.coef_,
        "intercept": estimator.intercept_,
        "iterations": int(estimator.n_iter_),
    }
    return future, fitted


def predict(data, origin):
    return fit_predict(data, origin)[0]
