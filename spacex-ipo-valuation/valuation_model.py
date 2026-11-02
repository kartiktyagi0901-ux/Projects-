"""
SpaceX (SPCX) IPO valuation model: scenarios, multiples and a reverse valuation.

All inputs are as of the IPO pricing date (12 June 2026) and come from public
sources (S-1 filing, Morningstar, Morgan Stanley / Goldman Sachs research as
reported in the press). Change them in INPUTS and re-run:

    python valuation_model.py

Outputs: tables printed to the console and written to results.md, and charts in charts/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
CHARTS = HERE / "charts"
CHARTS.mkdir(exist_ok=True)

# --------------------------------------------------------------------------
# INPUTS (USD)
# --------------------------------------------------------------------------
INPUTS = {
    "offer_price": 135.0,
    "market_cap_at_offer": 1.75e12,
    "revenue_2024": 14.1e9,
    "revenue_2025": 18.7e9,
    "revenue_2026e": 22.0e9,
    "ebitda_2025": 6.58e9,
    "net_income_2025": -4.9e9,
    "ipo_shares_sold": 556.6e6,
}
# Implied share count (market cap / price). Published fair-value market caps
# may use a slightly different diluted share count.
INPUTS["shares_outstanding"] = INPUTS["market_cap_at_offer"] / INPUTS["offer_price"]

SCENARIOS = {  # value per share
    "Bear (Morningstar fair value)": 63.0,
    "Base (IPO offer price)": 135.0,
    "Bull (Morningstar upside case)": 154.0,
}

STREET_2030_REVENUE = {  # long-horizon forecasts
    "Morgan Stanley": 330e9,
    "Goldman Sachs": 470e9,
}

# Reverse-valuation grid
EXIT_EV_SALES = [5, 8, 10, 15, 20]       # exit multiple on 2030 revenue
DISCOUNT_RATES = [0.09, 0.11, 0.13]      # cost of equity
YEARS_TO_2030 = 4                        # mid-2026 to mid-2030

COLORS = {"bear": "#B23A3A", "base": "#005288", "bull": "#2E8B6E", "ink": "#17323F", "muted": "#A7A9AC"}


def headline_multiples(i):
    cap = i["market_cap_at_offer"]
    return pd.DataFrame(
        {
            "Metric": ["EV/Sales 2025 (x)", "EV/Sales 2026E (x)", "EV/EBITDA 2025 (x)",
                       "Revenue growth 2025 (%)", "IPO proceeds ($bn)"],
            "Value": [cap / i["revenue_2025"], cap / i["revenue_2026e"], cap / i["ebitda_2025"],
                      (i["revenue_2025"] / i["revenue_2024"] - 1) * 100,
                      i["ipo_shares_sold"] * i["offer_price"] / 1e9],
        }
    ).round(1)


def scenario_table(i):
    rows = []
    for name, px in SCENARIOS.items():
        cap = px * i["shares_outstanding"]
        rows.append({
            "Scenario": name,
            "Value / share ($)": px,
            "vs. offer (%)": round((px / i["offer_price"] - 1) * 100, 1),
            "Implied equity value ($bn)": round(cap / 1e9),
            "Implied EV/Sales 2025 (x)": round(cap / i["revenue_2025"], 1),
        })
    return pd.DataFrame(rows)


def street_forward_multiples(i):
    rows = []
    for bank, rev in STREET_2030_REVENUE.items():
        cagr = (rev / i["revenue_2025"]) ** (1 / 5) - 1
        rows.append({
            "Forecast": bank,
            "2030 revenue ($bn)": round(rev / 1e9),
            "Implied CAGR 2025-30 (%)": round(cagr * 100, 1),
            "Offer cap / 2030 revenue (x)": round(i["market_cap_at_offer"] / rev, 1),
        })
    return pd.DataFrame(rows)


def reverse_valuation(i):
    """2030 revenue needed for today's price to earn the cost of equity, given an
    exit EV/Sales multiple, and the 2025-30 revenue CAGR that requires.
    Simplification: no dividends, net cash or dilution, and EV ≈ equity value."""
    cagr = pd.DataFrame(index=[f"{m}x" for m in EXIT_EV_SALES],
                        columns=[f"{r:.0%}" for r in DISCOUNT_RATES], dtype=float)
    req_rev = cagr.copy()
    for m in EXIT_EV_SALES:
        for r in DISCOUNT_RATES:
            future_value = i["market_cap_at_offer"] * (1 + r) ** YEARS_TO_2030
            rev_needed = future_value / m
            req_rev.loc[f"{m}x", f"{r:.0%}"] = rev_needed / 1e9
            cagr.loc[f"{m}x", f"{r:.0%}"] = ((rev_needed / i["revenue_2025"]) ** (1 / 5) - 1) * 100
    req_rev.index.name = cagr.index.name = "Exit EV/Sales \\ Cost of equity"
    return req_rev.round(0), cagr.round(1)


def chart_scenarios(df, i):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cols = [COLORS["bear"], COLORS["base"], COLORS["bull"]]
    labels = [s.split(" (")[0] for s in df["Scenario"]]
    bars = ax.bar(labels, df["Value / share ($)"], color=cols, width=0.55)
    ax.axhline(i["offer_price"], color=COLORS["ink"], ls="--", lw=1)
    ax.text(-0.42, i["offer_price"] + 3, f"Offer ${i['offer_price']:.0f}", ha="left", color=COLORS["ink"], fontsize=9)
    for b, chg in zip(bars, df["vs. offer (%)"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() / 2,
                f"${b.get_height():.0f}\n{chg:+.0f}%", ha="center", color="white", fontweight="bold")
    ax.set_ylabel("Value per share ($)")
    ax.set_title("SPCX: value per share by scenario vs. $135 offer", loc="left", fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / "scenarios.png", dpi=160)
    plt.close(fig)


def chart_reverse(cagr):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    data = cagr.values.astype(float)
    im = ax.imshow(data, cmap="RdYlGn_r", aspect="auto", vmin=20, vmax=110)
    ax.set_xticks(range(len(cagr.columns)), cagr.columns)
    ax.set_yticks(range(len(cagr.index)), cagr.index)
    ax.set_xlabel("Cost of equity")
    ax.set_ylabel("Exit EV/Sales on 2030 revenue")
    for (r, c), v in np.ndenumerate(data):
        ax.text(c, r, f"{v:.0f}%", ha="center", va="center", fontsize=10, fontweight="bold")
    ax.set_title("Revenue CAGR 2025-30 needed to justify the $1.75T offer value", loc="left", fontweight="bold", fontsize=11)
    fig.colorbar(im, ax=ax, label="Required CAGR (%)")
    fig.tight_layout()
    fig.savefig(CHARTS / "reverse_valuation.png", dpi=160)
    plt.close(fig)


def main():
    i = INPUTS
    mult = headline_multiples(i)
    scen = scenario_table(i)
    street = street_forward_multiples(i)
    req_rev, cagr = reverse_valuation(i)

    chart_scenarios(scen, i)
    chart_reverse(cagr)

    sections = [
        ("Headline multiples at the offer price", mult),
        ("Scenario valuation", scen),
        ("Street 2030 forecasts", street),
        ("Reverse valuation: required 2030 revenue ($bn)", req_rev),
        ("Reverse valuation: required revenue CAGR 2025-30 (%)", cagr),
    ]
    md = [f"# Model output\n\nImplied shares outstanding: {i['shares_outstanding'] / 1e9:.2f}bn\n"]
    for title, df in sections:
        print(f"\n== {title} ==\n{df.to_string()}")
        md.append(f"## {title}\n\n{df.to_markdown(index=title.startswith('Reverse'))}\n")
    (HERE / "results.md").write_text("\n".join(md))


if __name__ == "__main__":
    main()
