"""Independent re-derivation of the headline claims in README.md.

Usage: python src/headline_checks.py --data data/stories_transactions.csv
Writes reports/HEADLINE_CHECKS.md. Uses only pandas/numpy.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/stories_transactions.csv")
    ap.add_argument("--out", default="reports/HEADLINE_CHECKS.md")
    a = ap.parse_args()
    df = pd.read_csv(a.data, parse_dates=["Date"])
    out = []

    # 1. Garden/Uptown vs Harbour cost and price are exact formulas
    p = df.groupby(["Product", "Branch"])[["Unit Cost (USD)", "Unit Price (USD)"]].agg(
        lambda s: s.mode().iloc[0]
    )
    cost = p["Unit Cost (USD)"].unstack()
    price = p["Unit Price (USD)"].unstack()
    n = len(cost.dropna())
    g_cost = ((cost["Harbour"] * 1.43).round(2) == cost["Garden"]).sum()
    g_price = ((price["Harbour"] / 1.05).round(2) == price["Garden"]).sum()
    out.append(f"- Products priced at all 3 branches: {n}")
    out.append(f"- Garden cost == round(Harbour cost x 1.43, 2): {g_cost}/{n}")
    out.append(f"- Garden price == round(Harbour price / 1.05, 2): {g_price}/{n}")
    out.append(f"- Median Garden/Harbour cost ratio: {(cost['Garden']/cost['Harbour']).median():.4f}")

    # 2. Tuesday effect (unique transactions per branch-day)
    d = df.drop_duplicates("Transaction ID")
    t = d.groupby(["Branch", "Date"]).size().rename("n").reset_index()
    t["dow"] = t["Date"].dt.dayofweek
    tue = t[t.dow == 1].n.mean()
    oth = t[t.dow.isin([0, 2, 3, 4])].n.mean()
    out.append(f"- Tuesday / (Mon,Wed,Thu,Fri) transactions per branch-day: {tue/oth:.3f} ({tue:.1f} vs {oth:.1f})")
    bt = t.assign(week=t.Date.dt.to_period("W")).groupby(["Branch", "week", "dow"]).n.sum().unstack()
    bt = bt.dropna(subset=[1])
    wk = (bt[1] > bt[[0, 2, 3, 4]].mean(axis=1)).mean()
    out.append(f"- Share of branch-weeks where Tuesday beats the Mon/Wed/Thu/Fri mean: {wk:.1%}")
    # basket value same?
    bv = df.groupby(["Transaction ID"]).agg(rev=("Line Revenue (USD)", "sum"), date=("Date", "first"))
    bv["dow"] = bv.date.dt.dayofweek
    out.append(f"- Mean basket value Tuesday {bv[bv.dow==1].rev.mean():.2f} vs other weekdays {bv[bv.dow.isin([0,2,3,4])].rev.mean():.2f}")

    # 3. Overdispersion of daily counts (variance / mean after removing weekday x branch mean)
    t["mu"] = t.groupby(["Branch", "dow"]).n.transform("mean")
    t["wk"] = t.Date.dt.to_period("W")
    # remove slow trend with a rolling 28-day mean per branch to be conservative
    t = t.sort_values(["Branch", "Date"])
    t["trend"] = t.groupby("Branch").n.transform(lambda s: s.rolling(28, center=True, min_periods=7).mean())
    t["idx"] = t.mu / t.groupby("Branch").n.transform("mean")
    t["exp"] = t.trend * t.idx
    disp = ((t.n - t.exp) ** 2 / t.exp).mean()
    out.append(f"- Pearson dispersion of daily counts vs weekday x trend expectation (1.0 = Poisson): {disp:.2f}")

    # 4. Garden vs Harbour gross profit gap per day
    gp = df.groupby(["Branch", "Date"])["Line Gross Profit (USD)"].sum().unstack(0)
    out.append(f"- Mean daily gross profit: " + ", ".join(f"{b} ${gp[b].mean():.2f}" for b in gp.columns))
    out.append(f"- Harbour minus Garden daily gross profit gap: ${gp['Harbour'].mean()-gp['Garden'].mean():.2f}")
    tc = d.groupby("Branch").size()
    out.append(f"- Garden transactions / Harbour transactions: {tc['Garden']/tc['Harbour']:.3f}")

    # 5. Data quality
    out.append(f"- Rows {len(df)}, exact duplicate rows {df.duplicated().sum()}, missing Customer ID {df['Customer ID'].isna().sum()}")
    chk = (df["Quantity"] * df["Unit Price (USD)"] * (1 - df["Discount Rate"]) - df["Line Revenue (USD)"]).abs().max()
    out.append(f"- Max |qty*price*(1-disc) - line revenue|: {chk:.4f}")

    Path(a.out).write_text("# Headline checks (auto-generated)\n\n" + "\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
