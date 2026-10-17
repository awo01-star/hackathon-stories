"""Load transaction counts without depending on inventory or accounting code."""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class DemandData:
    daily: pd.DataFrame
    branches: list
    end: pd.Timestamp


def load_data(path: Path) -> DemandData:
    """Count distinct baskets; retain all source lines without treating them as visits."""
    columns = ["Transaction ID", "Date", "Branch"]
    raw = pd.read_csv(path, usecols=columns)
    if raw.empty:
        raise ValueError("The transaction file is empty.")
    if raw[columns].isna().any().any():
        raise ValueError("Transaction ID, Date and Branch must be present.")
    if raw.groupby("Transaction ID")[["Date", "Branch"]].nunique().gt(1).any().any():
        raise ValueError("A transaction ID belongs to conflicting dates or branches.")

    raw["date"] = pd.to_datetime(raw["Date"], format="%Y-%m-%d")
    branches = sorted(raw["Branch"].unique())
    grid = pd.MultiIndex.from_product(
        [pd.date_range(raw.date.min(), raw.date.max()), branches],
        names=["date", "branch"],
    )
    counts = raw.drop_duplicates("Transaction ID").groupby(["date", "Branch"]).size()
    counts.index = counts.index.set_names(grid.names)
    # Match team policy: missing records are unknown, not assumed zero sales.
    counts = counts.reindex(grid)
    if counts.isna().any():
        raise ValueError("Missing branch-days require investigation; no zero imputation is allowed.")
    daily = pd.DataFrame({"transactions": counts.astype(int)}).reset_index()
    return DemandData(daily=daily, branches=branches, end=raw.date.max())
