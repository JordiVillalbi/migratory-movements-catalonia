from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

# ------------------------------------------------------------------
# 1. PATHS
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "demografia" / "estudi_impacte_migracions.csv"
FIGURES_DIR = BASE_DIR / "results" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# 2. STYLE
# One colour = one meaning across ALL figures (Okabe-Ito, colour-blind safe):
#   BLUE   -> immigration / net migration gain
#   ORANGE -> emigration / net migration loss
#   GRAY   -> residents (the population itself)
#   DARK   -> reference lines and observed population
# ------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#444444",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 10.5,
    "axes.labelsize": 9.5,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9,
    "grid.color": "#E6E6E6",
    "grid.linewidth": 0.6,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.2,
    "savefig.facecolor": "white",
})

BLUE = "#0072B2"
LIGHT_BLUE = "#56B4E9"
ORANGE = "#E69F00"
GRAY = "#9AA3AB"
DARK = "#222222"

SOURCE_TEXT = "Source: IDESCAT. Observed data 2012–2024, demographic projections 2025–2026."

AGE_MAP_EN = {
    "De 0 a 14 anys": "0–14",
    "De 15 a 29 anys": "15–29",
    "De 30 a 34 anys": "30–34",
    "De 35 a 44 anys": "35–44",
    "De 45 a 59 anys": "45–59",
    "De 60 anys i més": "60+",
}
AGE_ORDER = list(AGE_MAP_EN.values())

# First age and width (in years) of each bracket. 60+ is drawn as 60–85 by convention.
AGE_START = {"0–14": 0, "15–29": 15, "30–34": 30, "35–44": 35, "45–59": 45, "60+": 60}
INTERVAL_WIDTH = {"0–14": 15, "15–29": 15, "30–34": 5, "35–44": 10, "45–59": 15, "60+": 25}


# ------------------------------------------------------------------
# 3. HELPERS
# ------------------------------------------------------------------
def layout(fig, title, subtitle, top_in=1.0, bottom_in=1.1, footnote=None):
    """Left-aligned title + subtitle on top, source at the bottom (sizes in inches)."""
    h = fig.get_figheight()
    fig.text(0.01, 1 - 0.12 / h, title, fontsize=13, fontweight="bold", ha="left", va="top")
    fig.text(0.01, 1 - 0.50 / h, subtitle, fontsize=9.5, color="#555555", ha="left", va="top")
    fig.subplots_adjust(top=1 - top_in / h, bottom=bottom_in / h)
    text = SOURCE_TEXT if footnote is None else f"{footnote}\n{SOURCE_TEXT}"
    fig.text(0.01, 0.10 / h, text, fontsize=8, color="#666666", ha="left", va="bottom")


def nice_limit(value, step):
    return float(np.ceil(value / step) * step)


def spread_labels(values, gap):
    """Push label positions apart so none overlap (values: dict name -> y)."""
    order = sorted(values, key=values.get)
    pos = {}
    prev = None
    for name in order:
        y = values[name] if prev is None else max(values[name], prev + gap)
        pos[name] = y
        prev = y
    return pos


# ------------------------------------------------------------------
# 4. DATA
# ------------------------------------------------------------------
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df = df[df["Grup_edat"].isin(AGE_MAP_EN)].copy()
    df["Age_group"] = pd.Categorical(
        df["Grup_edat"].map(AGE_MAP_EN), categories=AGE_ORDER, ordered=True
    )
    df = df.sort_values(["Any", "Age_group"]).reset_index(drop=True)
    df["Interval_years"] = df["Age_group"].map(INTERVAL_WIDTH).astype(int)
    # net migration rate = annual net balance / population of the same group and year
    df["Migration_rate_%"] = df["Saldo_migratori_total"] / df["Poblacio_total"] * 100
    return df


# ------------------------------------------------------------------
# FIGURE 1: SHAPE BY AGE. Residents and net migration, in separate panels
#   share_i   = X_i / sum(X) * 100
#   density_i = share_i / width_i     (% of the total per single year of age)
# Bar height = age range, bar length = density -> bar AREA = share of the total.
# Each panel has its own horizontal scale: compare shapes, not bar lengths.
# ------------------------------------------------------------------
def plot_age_structure(df: pd.DataFrame, output_path: Path, year: int = 2024):
    d = df[df["Any"] == year].sort_values("Age_group")
    y0 = d["Age_group"].map(AGE_START).astype(int).values
    w = d["Interval_years"].values

    panels = [
        ("Poblacio_total", "Resident population", GRAY, "#555555"),
        ("Saldo_migratori_total", "Net migration balance", BLUE, BLUE),
    ]
    shares = {}
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), sharey=True)

    for ax, (col, title, color, text_color) in zip(axes, panels):
        share = d[col].values / d[col].sum() * 100
        dens = share / w
        shares[col] = share

        ax.axhspan(15, 35, color="#EEF3F8", zorder=0)
        ax.barh(y0, dens, height=w, align="edge", color=color,
                edgecolor="white", linewidth=1.5, zorder=3)

        xmax = nice_limit(dens.max() * 1.25, 0.5)
        for yi, wi, di, si in zip(y0, w, dens, share):
            label = "<1%" if 0 < si < 1 else f"{si:.0f}%"
            ax.text(di + xmax * 0.02, yi + wi / 2, label, va="center", ha="left",
                    fontsize=9, fontweight="bold", color=text_color)

        ax.set_xlim(0, xmax)
        ax.set_ylim(0, 85)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))
        ax.set_xlabel("% of the total, per single year of age")
        ax.set_title(title, loc="left", fontweight="bold", color=text_color)
        ax.grid(axis="x", zorder=1)
        ax.set_axisbelow(True)

    centers = y0 + w / 2
    for ax in axes:
        ax.set_yticks(centers)
        ax.set_yticklabels(AGE_ORDER)
        ax.tick_params(axis="y", labelleft=True)
    axes[0].set_ylabel("Age group (years)")

    young = d["Age_group"].isin(["15–29", "30–34"]).values
    pop_young = shares["Poblacio_total"][young].sum()
    mig_young = shares["Saldo_migratori_total"][young].sum()

    layout(fig,
           f"Ages 15–34 are {pop_young:.0f}% of residents but {mig_young:.0f}% of net migration",
           f"Age structure of the resident population and of the net migration balance, Catalonia, {year}",
           top_in=1.0, bottom_in=1.2,
           footnote="Bar height = age range, bar area = share of the total (labels). Each panel has its own scale: "
                    "compare shapes, not lengths. 60+ drawn as 60–85 by convention. Shaded: ages 15–34.")
    fig.savefig(output_path)
    plt.close(fig)


# ------------------------------------------------------------------
# FIGURE 2: HOW INTENSE? Net migration rate by age and year (lines)
#   rate = Saldo_migratori_total / Poblacio_total * 100
# ------------------------------------------------------------------
def plot_migration_rate_lines(df: pd.DataFrame, output_path: Path):
    pivot = df.pivot(index="Any", columns="Age_group", values="Migration_rate_%")
    years = pivot.index.values
    colors = {"15–29": BLUE, "30–34": LIGHT_BLUE}

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.axhline(0, color=DARK, linewidth=0.9, zorder=2)
    ax.axvspan(2019.5, 2021.5, color="#000000", alpha=0.06, linewidth=0)
    ax.text(2020.5, pivot.max().max() * 1.02, "COVID-19\nyears", ha="center", va="bottom",
            fontsize=8, color="#555555")
    if years.max() > 2024:
        ax.axvspan(2024.5, years.max(), color="#000000", alpha=0.05, linewidth=0)
        ax.text(2025.5, pivot.min().min(), "proj.", ha="center", va="bottom",
                fontsize=8, color="#555555")

    # draw grey groups first so the highlighted ones sit on top
    for g in [g for g in AGE_ORDER if g not in colors] + list(colors):
        c = colors.get(g, GRAY)
        lw = 2.4 if g in colors else 1.4
        ax.plot(years, pivot[g], color=c, linewidth=lw, zorder=4 if g in colors else 3)

    ends = spread_labels({g: pivot[g].iloc[-1] for g in AGE_ORDER}, gap=0.32)
    for g in AGE_ORDER:
        ax.text(years.max() + 0.25, ends[g], g, color=colors.get(g, "#6B747C"),
                fontsize=9, fontweight="bold" if g in colors else "normal",
                va="center", clip_on=False)

    ax.set_xlim(years.min(), years.max())
    ax.set_xticks(range(int(years.min()), int(years.max()) + 1, 2))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_ylabel("Net migration rate (% of the age group, per year)")
    ax.grid(axis="y")
    ax.set_axisbelow(True)

    layout(fig,
           "Net migration at ages 15–34 rose from 1% or less in 2012–14 to 3–5% a year by 2022–24",
           "Annual net migration balance as a percentage of the age group's population",
           top_in=1.0, bottom_in=0.9)
    fig.savefig(output_path)
    plt.close(fig)


# ------------------------------------------------------------------
# FIGURE 3: WHAT DOES IT CHANGE? Population with vs. without net migration
#   cum_t      = sum of net balance from 2013 to t
#   pop_no_mig = population - cum_t
#   index      = population / population_2012 * 100
# ------------------------------------------------------------------
def plot_population_with_without_migration(df: pd.DataFrame, output_path: Path):
    d = df.copy()
    g = d.groupby("Age_group", observed=False)["Saldo_migratori_total"]
    # migration accumulated from 2013 onwards (2012 is the base year, so it starts at 100)
    d["cum_mig"] = g.cumsum() - g.transform("first")
    d["pop_no_mig"] = d["Poblacio_total"] - d["cum_mig"]

    base = d[d["Any"] == d["Any"].min()].set_index("Age_group")["Poblacio_total"]
    base = base.reindex(d["Age_group"]).values
    d["idx_real"] = d["Poblacio_total"].values / base * 100
    d["idx_no"] = d["pop_no_mig"].values / base * 100

    lo = np.floor((min(d["idx_real"].min(), d["idx_no"].min()) - 4) / 10) * 10
    hi = np.ceil((max(d["idx_real"].max(), d["idx_no"].max()) + 4) / 10) * 10

    fig, axes = plt.subplots(2, 3, figsize=(12, 6.6), sharex=True, sharey=True)
    for ax, group in zip(axes.flat, AGE_ORDER):
        s = d[d["Age_group"] == group].sort_values("Any")
        gain = (s["idx_real"] >= s["idx_no"]).values
        loss = ~gain

        ax.axhline(100, color="#BBBBBB", linewidth=0.8, linestyle=":")
        ax.axvspan(2024.5, s["Any"].max(), color="#000000", alpha=0.05, linewidth=0)
        # each fill only gets a legend label if it actually appears somewhere
        ax.fill_between(s["Any"], s["idx_no"], s["idx_real"], where=gain,
                        color=BLUE, alpha=0.18, linewidth=0, interpolate=True,
                        label="Added by net migration" if gain.any() else None)
        if loss.any():
            ax.fill_between(s["Any"], s["idx_no"], s["idx_real"], where=loss,
                            color=ORANGE, alpha=0.25, linewidth=0, interpolate=True,
                            label="Lost to net emigration")
        ax.plot(s["Any"], s["idx_no"], color=GRAY, linewidth=1.5, linestyle="--",
                label="Without net migration after 2012")
        ax.plot(s["Any"], s["idx_real"], color=DARK, linewidth=2, label="Observed / projected")

        end_real, end_no = s["idx_real"].iloc[-1], s["idx_no"].iloc[-1]
        x_end = s["Any"].max() + 0.3
        ax.text(x_end, end_real, f"{end_real - 100:+.0f}%", color=DARK, fontsize=8.5,
                fontweight="bold", va="center", clip_on=False)
        if abs(end_real - end_no) > 4:
            ax.text(x_end, end_no, f"{end_no - 100:+.0f}%", color="#6B747C", fontsize=8.5,
                    va="center", clip_on=False)

        ax.set_title(f"{group} years", loc="left", fontweight="bold")
        ax.set_xlim(2012, 2026)
        ax.set_ylim(lo, hi)
        ax.set_xticks([2012, 2016, 2020, 2024])
        ax.grid(axis="y")
        ax.set_axisbelow(True)

    for ax in axes[:, 0]:
        ax.set_ylabel("Population index (2012 = 100)")
    axes[0, 0].text(2024.7, lo + 2, "proj.", fontsize=7.5, color="#555555")

    # legend built from every panel, without duplicates
    uniq = {}
    for ax in axes.flat:
        for hdl, lab in zip(*ax.get_legend_handles_labels()):
            uniq.setdefault(lab, hdl)
    fig.legend(list(uniq.values()), list(uniq.keys()), frameon=False, loc="lower center",
               ncol=len(uniq), bbox_to_anchor=(0.5, 0.45 / fig.get_figheight()))
    fig.subplots_adjust(wspace=0.35, hspace=0.3)
    layout(fig,
           "Net migration since 2012 has cut population losses at ages 0–44 and turned them into growth at 15–29",
           "Population index (2012 = 100), with and without the net migration accumulated since 2012",
           top_in=1.0, bottom_in=1.35,
           footnote="Simplified counterfactual: subtracts accumulated net migration from each bracket and does not follow migrants as they age.")
    fig.savefig(output_path)
    plt.close(fig)


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
if __name__ == "__main__":
    data = load_data(DATA_PATH)

    plot_age_structure(data, FIGURES_DIR / "01_estructura_edat.png")
    plot_migration_rate_lines(data, FIGURES_DIR / "02_taxa_migratoria.png")
    plot_population_with_without_migration(data, FIGURES_DIR / "03_evolucio_composicio_edat.png")

    print(f"Charts saved in: {FIGURES_DIR}")