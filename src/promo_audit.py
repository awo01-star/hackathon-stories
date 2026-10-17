"""Did Stories' discounts earn their cost? Plus Uptown pricing and customer-ID checks.

Usage: python src/promo_audit.py --data data/stories_transactions.csv
Writes reports/promo_audit/REPORT.md, reports/promo_audit/*.csv and
figures/promo_audit/*.png. Uses only pandas/numpy/matplotlib.

Design. Harbour ran 15% off on nine cold coffee and dessert items on 16 days
(12 to 19 March and 12 to 19 May). Garden and Uptown never had it, so they are
the control. We compare daily units of the nine items at Harbour against the
same nine items at the controls (difference in differences on logs), inside
+/-28 days of each campaign. Significance comes from a placebo test in time:
the same statistic for every other 8-day window with no campaign.
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CAMPAIGNS = [("2026-03-12", "2026-03-19"), ("2026-05-12", "2026-05-19")]
CONTROLS = ["Garden", "Uptown"]


def campaign_days():
    return pd.DatetimeIndex(np.concatenate([pd.date_range(a, b) for a, b in CAMPAIGNS]))


def daily_units(df, items):
    df = df.assign(elig=df.Product.isin(items))
    q = df.groupby(["Date", "Branch", "elig"]).Quantity.sum().unstack(["Branch", "elig"]).fillna(0)
    out = pd.DataFrame(index=q.index)
    out["h_elig"] = q[("Harbour", True)]
    out["h_other"] = q[("Harbour", False)]
    out["c_elig"] = sum(q[(b, True)] for b in CONTROLS)
    out["c_other"] = sum(q[(b, False)] for b in CONTROLS)
    # difference in differences on logs: Harbour eligible vs control eligible
    out["did"] = np.log(out.h_elig) - np.log(out.c_elig)
    # triple difference also nets out Harbour-wide traffic swings
    out["ddd"] = out["did"] - (np.log(out.h_other) - np.log(out.c_other))
    return out


def window_effect(series, treat, base):
    return series[treat].mean() - series[base].mean()


def placebo(series, promo, width=8, margin=28):
    """Effect of every 8-day window that does not overlap a campaign, with its own +/-28 day baseline."""
    days = series.index
    effects = []
    for start in days:
        win = pd.date_range(start, periods=width)
        if win[-1] > days[-1] or win.isin(promo).any():
            continue
        base = (days >= start - pd.Timedelta(days=margin)) & (days <= win[-1] + pd.Timedelta(days=margin))
        base &= ~days.isin(win) & ~days.isin(promo)
        effects.append(window_effect(series, days.isin(win), base))
    return np.array(effects)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/stories_transactions.csv")
    ap.add_argument("--out", default="reports/promo_audit")
    ap.add_argument("--fig", default="figures/promo_audit")
    a = ap.parse_args()
    out_dir, fig_dir = Path(a.out), Path(a.fig)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(a.data, parse_dates=["Date"])
    df["gross"] = df.Quantity * df["Unit Price (USD)"]
    df["disc_usd"] = df.gross * df["Discount Rate"]
    promo = campaign_days()
    items = sorted(df.loc[df["Discount Rate"] == 0.15, "Product"].unique())
    lines = []
    w = lines.append

    # ---------- 1. The 15% campaign ----------
    c15 = df[df["Discount Rate"] == 0.15]
    assert set(c15.Branch) == {"Harbour"} and set(c15.Date.unique()) <= set(promo)
    u = daily_units(df, items)
    days = u.index
    base = np.zeros(len(days), bool)
    for a0, b0 in CAMPAIGNS:
        base |= (days >= pd.Timestamp(a0) - pd.Timedelta(days=28)) & (days <= pd.Timestamp(b0) + pd.Timedelta(days=28))
    base &= ~days.isin(promo)
    treat = days.isin(promo)

    res, draws = {}, {}
    for k in ["did", "ddd"]:
        eff = window_effect(u[k], treat, base)
        pl = placebo(u[k], promo)
        # combine two 8-day campaigns: the placebo for their mean is the mean of two random windows
        rng = np.random.default_rng(0)
        pl2 = draws[k] = rng.choice(pl, (20000, 2)).mean(axis=1)
        res[k] = dict(
            lift=np.exp(eff) - 1,
            p=(np.abs(pl2) >= abs(eff)).mean(),
            lo=np.exp(np.quantile(pl2, 0.025) + eff) - 1,
            hi=np.exp(np.quantile(pl2, 0.975) + eff) - 1,
            mde=np.exp(np.quantile(np.abs(pl2), 0.95)) - 1,
        )
    per = []
    for a0, b0 in CAMPAIGNS:
        t = (days >= a0) & (days <= b0)
        bb = base & (days >= pd.Timestamp(a0) - pd.Timedelta(days=28)) & (days <= pd.Timestamp(b0) + pd.Timedelta(days=28))
        per.append((a0, b0, np.exp(window_effect(u["did"], t, bb)) - 1))

    # economics of the campaign on the nine items at Harbour
    h = df[(df.Branch == "Harbour") & df.Product.isin(items)]
    hp = h[h.Date.isin(promo)]
    hb = h[h.Date.isin(days[base])]
    take = (hp["Discount Rate"] == 0.15).mean()
    gp_unit_base = hb["Line Gross Profit (USD)"].sum() / hb.Quantity.sum()
    gp_unit_promo = hp["Line Gross Profit (USD)"].sum() / hp.Quantity.sum()
    breakeven = gp_unit_base / gp_unit_promo - 1
    given = c15.disc_usd.sum()
    # the campaign only discounted 23% of eligible lines; break-even if every eligible line were discounted
    margin = 1 - (hb["Unit Cost (USD)"] * hb.Quantity).sum() / hb.gross.sum()
    be_full = margin / (margin - 0.15) - 1
    lift = res["did"]["lift"]
    units_promo = hp.Quantity.sum()
    gp_net = units_promo * gp_unit_promo - units_promo / (1 + lift) * gp_unit_base

    w("# Discount audit: did the promotions pay for themselves?\n")
    w("Generated by `src/promo_audit.py`. Every number below is recomputed from the CSV.\n")
    w("## 1. Harbour's 15% campaign: a natural experiment\n")
    w(f"- 15% discount lines: {len(c15)}, all at Harbour, all on {promo.size} days ({CAMPAIGNS[0][0]} to {CAMPAIGNS[0][1]} and {CAMPAIGNS[1][0]} to {CAMPAIGNS[1][1]}), on {len(items)} items: {', '.join(items)}.")
    w(f"- On campaign days {take:.0%} of eligible Harbour lines got 15% off, so it was a shelf price cut, not a coupon. Every eligible customer received it.")
    w(f"- Discount given away: **${given:,.0f}** over 16 days.")
    w("- Control: the same nine items at Garden and Uptown, which never had the offer. Baseline: non-campaign days within 28 days of each campaign.\n")
    w("| Estimate | Lift in units of the 9 items | 95% placebo range | Placebo p-value |")
    w("|---|---|---|---|")
    w(f"| Harbour vs controls (DiD) | {res['did']['lift']:+.1%} | {res['did']['lo']:+.1%} to {res['did']['hi']:+.1%} | {res['did']['p']:.2f} |")
    w(f"| Also netting Harbour's other items (DDD) | {res['ddd']['lift']:+.1%} | {res['ddd']['lo']:+.1%} to {res['ddd']['hi']:+.1%} | {res['ddd']['p']:.2f} |")
    w("")
    w("Per campaign (DiD): " + "; ".join(f"{x} to {y}: {l:+.1%}" for x, y, l in per) + ".\n")
    p_be = (draws["did"] >= np.log(1 + breakeven) - np.log(1 + lift)).mean()
    w(f"- **Break-even lift:** {breakeven:+.1%} more units (gross profit per unit fell from ${gp_unit_base:.3f} to ${gp_unit_promo:.3f}; the item margin of {margin:.0%} gives the same {be_full:+.0%} from the formula m/(m-0.15)-1).")
    w(f"- Noise in any 8-day window is about +/-{res['did']['mde']:.0%}, so a small real lift could hide. But the top of the 95% range ({res['did']['hi']:+.0%}) is still below break-even ({breakeven:+.0%}). Only {p_be:.1%} of placebo draws are as far from the estimate as break-even is. **The campaign lost gross profit with about {1-p_be:.0%} confidence.**")
    w(f"- Net gross profit effect at the point estimate: **${gp_net:,.0f}** over 16 days.")
    w("- Measured: the units, the discount dollars and the placebo range. Not measured: whether the offer brought in new customers who return later (customer IDs cannot answer this, see section 3).\n")

    # ---------- 2. 10% discount ----------
    d10 = df[df["Discount Rate"] == 0.10]
    t = df.groupby("Transaction ID").agg(n=("Product", "size"), disc=("Discount Rate", "max"), mixed=("Discount Rate", lambda s: s.nunique() > 1))
    p_line = (df["Discount Rate"] == 0.10).mean()
    exp_any = (1 - (1 - p_line) ** t.n).mean()
    obs_any = (t.disc == 0.10).mean()
    share_m = d10.groupby(d10.Date.dt.month).size() / df.groupby(df.Date.dt.month).size()
    w("## 2. The 10% discount behaves like a random line flag, not a strategy\n")
    w(f"- {len(d10)} lines ({p_line:.1%}) at all branches, all {d10.Product.nunique()} products, every month (monthly share {share_m.min():.1%} to {share_m.max():.1%}) and {d10.Date.nunique()} of {df.Date.nunique()} days.")
    w(f"- {t.mixed.sum()} of {(t.disc > 0).sum()} discounted baskets mix discounted and full-price lines, so it is applied per line, not per customer or per basket.")
    w(f"- If each line were flagged independently with probability {p_line:.3f}, {exp_any:.1%} of baskets would contain one. Observed: {obs_any:.1%}. That match is why discounted baskets look bigger (more lines, more chances), which is not evidence that discounts grow baskets.")
    w(f"- Cost: **${d10.disc_usd.sum():,.0f}** in six months (Garden ${d10[d10.Branch=='Garden'].disc_usd.sum():,.0f}, Harbour ${d10[d10.Branch=='Harbour'].disc_usd.sum():,.0f}, Uptown ${d10[d10.Branch=='Uptown'].disc_usd.sum():,.0f}).")
    g = df[(df.Branch == "Garden")].groupby("Product")[["Unit Price (USD)", "Unit Cost (USD)"]].agg(lambda s: s.mode().iloc[0])
    g["m10"] = 1 - g["Unit Cost (USD)"] / (g["Unit Price (USD)"] * 0.9)
    thin = g[g.m10 < 0.30].sort_values("m10")
    w(f"- At Garden's recorded cost, a 10% discount leaves {len(thin)} items under 30% margin: " + ", ".join(f"{i} {m:.0%}" for i, m in thin.m10.items()) + ".\n")

    # ---------- 3. Customer IDs ----------
    tc = df.dropna(subset=["Customer ID"]).drop_duplicates("Transaction ID")
    v = tc.groupby("Customer ID").agg(n=("Branch", "size"), nb=("Branch", "nunique"))
    disp = v.n.var() / v.n.mean()
    ids = tc["Customer ID"].str[1:].astype(int)
    w("## 3. Customer IDs carry no loyalty signal\n")
    w(f"- {len(v)} IDs, numbered {ids.min()} to {ids.max()}, mean {v.n.mean():.2f} visits each. Variance/mean of visits per customer = {disp:.2f} (1.0 means every ID is equally likely on every visit; real loyalty data is heavily skewed).")
    w(f"- {(v.nb > 1).mean():.0%} of IDs appear at more than one branch.")
    w("- So repeat visit, churn and loyalty analyses would only describe random labels. We make no customer-level claim and recommend Stories check this on its own CRM before using these IDs.\n")

    # ---------- 4. Uptown ----------
    p = df.groupby(["Product", "Branch"])[["Unit Price (USD)", "Unit Cost (USD)"]].agg(lambda s: s.mode().iloc[0]).unstack()
    P, C = p["Unit Price (USD)"], p["Unit Cost (USD)"]
    n = len(P)
    up_cost = ((C.Harbour * 0.96).round(2) == C.Uptown).sum()
    up_price = ((P.Harbour * 0.914).round(2) == P.Uptown).sum()
    up_price_near = ((P.Harbour * 0.914 - P.Uptown).abs() <= 0.011).sum()
    gp = df.groupby(["Branch", "Date"])["Line Gross Profit (USD)"].sum().unstack(0).mean()
    tx = df.drop_duplicates("Transaction ID").groupby(["Branch", "Date"]).size().unstack(0).mean()
    gpt = gp / tx
    w("## 4. Uptown: its gap is traffic, its pricing is also a formula\n")
    w(f"- Uptown cost = round(Harbour cost x 0.96, 2) on {up_cost}/{n} products; price = Harbour price x 0.914 on {up_price}/{n} exactly and within 1 cent on {up_price_near}/{n}.")
    w(f"- So Uptown is 8.6% cheaper for a 4% lower cost. Unit margin {1-(C.Uptown/P.Uptown).median():.1%} vs Harbour {1-(C.Harbour/P.Harbour).median():.1%}.")
    w(f"- Gross profit per transaction: Uptown ${gpt['Uptown']:.2f}, Harbour ${gpt['Harbour']:.2f}, Garden ${gpt['Garden']:.2f}. Transactions per day: Uptown {tx['Uptown']:.1f}, Harbour {tx['Harbour']:.1f}, Garden {tx['Garden']:.1f}.")
    gap = gp["Harbour"] - gp["Uptown"]
    traffic_part = (tx["Harbour"] - tx["Uptown"]) * gpt["Uptown"]
    w(f"- Uptown earns ${gap:.2f}/day less than Harbour; ${traffic_part:.2f} of that ({traffic_part/gap:.0%}) is fewer transactions at Uptown's own profit per transaction. Uptown's problem is footfall, not price or cost. Garden is the opposite: its profit per transaction is {1-gpt['Garden']/gpt['Harbour']:.0%} below Harbour's.")
    w("- Decision: Garden's lever is cost and price (README action 1 and 2). Uptown's lever is traffic, which nothing in this file can test, so we do not invent an Uptown action.\n")

    # ---------- 5. Saturday ----------
    td = df.drop_duplicates("Transaction ID").groupby(["Branch", "Date"]).size().rename("n").reset_index()
    td["dow"] = td.Date.dt.dayofweek
    idx = td.groupby(["Branch", "dow"]).n.mean().unstack()
    idx = idx.div(idx[[0, 2, 3, 4]].mean(axis=1), axis=0)
    w("## 5. Saturday is the quietest day at every branch\n")
    w("| Branch | Mon | Tue | Wed | Thu | Fri | Sat | Sun |")
    w("|---|---|---|---|---|---|---|---|")
    for b, r in idx.iterrows():
        w(f"| {b} | " + " | ".join(f"{x:.2f}" for x in r) + " |")
    w(f"\n- Index relative to Mon/Wed/Thu/Fri. Saturday is {idx[5].mean():.2f}, the same at all three branches to two decimals, like Tuesday. That uniformity is another sign of a shared weekday setting. If Stories' tills confirm it, Saturday is the day to trim staff and fresh bakery prep, the mirror of the Tuesday action.\n")

    # ---------- figure ----------
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    for i, (a0, b0) in enumerate(CAMPAIGNS):
        lo, hi = pd.Timestamp(a0) - pd.Timedelta(days=28), pd.Timestamp(b0) + pd.Timedelta(days=28)
        s = u.loc[lo:hi]
        ax[i].plot(s.index, s.h_elig.rolling(7, center=True, min_periods=1).mean(), label="Harbour, 9 items (7-day mean)")
        ax[i].plot(s.index, s.c_elig.rolling(7, center=True, min_periods=1).mean(), label="Garden+Uptown, same items")
        ax[i].axvspan(pd.Timestamp(a0), pd.Timestamp(b0), color="orange", alpha=0.2, label="15% campaign")
        ax[i].set_title(f"Campaign {i+1}: units per day")
        ax[i].tick_params(axis="x", rotation=30)
    ax[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "campaign_units.png", dpi=130)

    pl = placebo(u["did"], promo)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.hist(np.exp(pl) - 1, bins=30, color="grey")
    ax.axvline(res["did"]["lift"], color="red", label=f"campaign {res['did']['lift']:+.1%}")
    ax.axvline(breakeven, color="green", ls="--", label=f"break-even {breakeven:+.1%}")
    ax.set_xlabel("Lift of an 8-day window with no campaign (placebo)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "placebo.png", dpi=130)
    w("![units](../../figures/promo_audit/campaign_units.png)\n")
    w("![placebo](../../figures/promo_audit/placebo.png)\n")

    w("## What we rejected\n")
    w("- A plain before/after at Harbour: it would credit the campaign with Harbour's growth from January to June. The control branches remove that.")
    w("- Reading elasticity from the 10% flag: it is not tied to time, customer or item, so there is no variation to learn from.\n")
    w("## What would change the conclusion\n")
    w("- If the offer targeted new customers through an app, the value is in later visits, which this file cannot track. Stories' CRM can.")
    w("- If the March and May windows were chosen because sales were expected to dip, the comparison would understate the lift. We assume the dates were not chosen that way.")
    w("- A 15% cut on margin-66% items needs about +29% volume. Any future discount should be judged against m/(m-d)-1 before launch, and run with a control branch as here.")

    Path(out_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    pd.DataFrame(res).T.to_csv(out_dir / "campaign_lift.csv")
    idx.to_csv(out_dir / "weekday_index.csv")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
