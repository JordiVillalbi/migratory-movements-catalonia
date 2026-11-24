from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

# 1. RELATIVE PATHS (from Projecte_Big_Data/scripts/Image_creation/)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "demografia" / "estudi_impacte_migracions.csv"
FIGURES_DIR = BASE_DIR / "results" / "figures"
PIRAMIDES_DIR = FIGURES_DIR / "piramides"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
PIRAMIDES_DIR.mkdir(parents=True, exist_ok=True)

# 2. CLEAN, ACCESSIBLE & PUBLICATION-READY AESTHETICS

plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "grid.color": "#EAEAEA",
    "grid.linestyle": "-",
    "grid.linewidth": 0.6,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.25
})

BLUE = "#0072B2"
VERMILION = "#D55E00"
GRAY = "#8C969E"
DARK = "#1A1A1A"

SOURCE_TEXT = "Source: IDESCAT (Observed data 2012–2024; Demographic projections 2025–2026)"

AGE_MAP_EN = {
    "De 0 a 14 anys": "0–14 years",
    "De 15 a 29 anys": "15–29 years",
    "De 30 a 34 anys": "30–34 years",
    "De 35 a 44 anys": "35–44 years",
    "De 45 a 59 anys": "45–59 years",
    "De 60 anys i més": "60+ years"
}

AGE_ORDER_EN = list(AGE_MAP_EN.values())

INTERVAL_WIDTH = {
    "0–14 years": 15,
    "15–29 years": 15,
    "30–34 years": 5,
    "35–44 years": 10,
    "45–59 years": 15,
    "60+ years": 25
}

def add_footer(fig, y_pos: float = -0.02):
    fig.text(0.01, y_pos, SOURCE_TEXT, fontsize=8, color="#666666", ha="left", style="italic")

# 3. DATA LOADING

def load_data(path: Path, years: list[int] | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    if years is not None:
        df = df[df["Any"].isin(years)].copy()

    df = df[df["Grup_edat"].isin(AGE_MAP_EN.keys())].copy()
    df["Age_group"] = pd.Categorical(df["Grup_edat"].map(AGE_MAP_EN), categories=AGE_ORDER_EN, ordered=True)
    df = df.sort_values(["Any", "Age_group"]).reset_index(drop=True)

    df["Interval_years"] = df["Age_group"].map(INTERVAL_WIDTH).astype(int)
    df["Migration_rate_%"] = (df["Saldo_migratori_total"] / df["Poblacio_total"]) * 100
    return df

# FIGURE 1: ANNUAL MIGRATION FLOWS & NET BALANCE BY AGE (SMALL MULTIPLES)

def plot_migration_flows_by_age(df_historic: pd.DataFrame, output_path: Path, years: list[int] = [2015, 2020, 2024]):
    df_sub = df_historic[df_historic["Any"].isin(years)].copy()

    df_sub["Imm_per_yr"] = df_sub["Immigracions_total"] / df_sub["Interval_years"]
    df_sub["Emi_per_yr"] = df_sub["Emigracions_total"] / df_sub["Interval_years"]
    df_sub["Net_per_yr"] = df_sub["Saldo_migratori_total"] / df_sub["Interval_years"]

    max_imm = df_sub["Imm_per_yr"].max() * 1.15
    max_emi = df_sub["Emi_per_yr"].max() * 1.15

    fig, axes = plt.subplots(1, len(years), figsize=(14, 5.4), sharey=True)
    y = np.arange(len(AGE_ORDER_EN))

    for idx, (ax, year) in enumerate(zip(axes, years)):
        df_y = df_sub[df_sub["Any"] == year].sort_values("Age_group")

        ax.barh(y, -df_y["Emi_per_yr"], color=VERMILION, height=0.55, label="Emigration")
        ax.barh(y, df_y["Imm_per_yr"], color=BLUE, height=0.55, label="Immigration")

        ax.scatter(
            df_y["Net_per_yr"],
            y,
            color=DARK,
            edgecolor="white",
            linewidth=1.2,
            zorder=5,
            s=48,
            label="Net balance"
        )

        if year == 2024:
            peak_row = df_y[df_y["Age_group"] == "30–34 years"].iloc[0]
            peak_y = AGE_ORDER_EN.index("30–34 years")
            ax.annotate(
                f"+{peak_row['Net_per_yr']/1000:.1f}k/yr net",
                xy=(peak_row["Net_per_yr"], peak_y),
                xytext=(peak_row["Net_per_yr"] + 800, peak_y + 0.35),
                fontsize=8,
                fontweight="bold",
                color=DARK,
                arrowprops=dict(arrowstyle="->", color=DARK, lw=0.8)
            )

        ax.axvline(0, color="#333333", linewidth=0.9)
        ax.set_xlim(-max_emi, max_imm)
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(
            lambda x, pos: "0" if x == 0 else (f"{abs(x)/1000:.1f}k" if abs(x) < 1000 else f"{abs(int(x))/1000:.0f}k")
        ))
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        ax.set_title(f"{year}", fontsize=11, fontweight="bold", pad=8)

        if idx == 0:
            ax.set_yticks(y)
            ax.set_yticklabels(AGE_ORDER_EN, fontsize=10)
        if idx == 1:
            ax.set_xlabel("← Emigration   |   People per single year of age (thousands)   |   Immigration →", fontsize=9.5, labelpad=8)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="upper right", ncol=3, fontsize=9.5, bbox_to_anchor=(0.98, 0.96))

    fig.suptitle(
        "Immigration Surged Across All Working Ages by 2024, Peaking Sharply at 30–34",
        fontsize=13,
        fontweight="bold",
        x=0.04,
        y=0.99,
        ha="left"
    )
    fig.text(
        0.04,
        0.935,
        "Annual migration flows and net balance normalized per single year of age (2015, 2020 & 2024)",
        fontsize=9.5,
        color="#555555",
        ha="left"
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    add_footer(fig, y_pos=0.01)
    plt.savefig(output_path)
    plt.close()

# FIGURE 2: POPULATION PYRAMID — ACTUAL VS. NO MIGRATION SCENARIO (2024)

def plot_population_pyramid(df: pd.DataFrame, output_path: Path):
    pop_2024 = df[df["Any"] == 2024][["Age_group", "Poblacio_homes", "Poblacio_dones"]].copy()
    cum_balance = df.groupby("Age_group", observed=False).agg({
        "Saldo_migratori_homes": "sum",
        "Saldo_migratori_dones": "sum",
        "Interval_years": "first"
    }).reset_index()

    data = pd.merge(pop_2024, cum_balance, on="Age_group")

    m_actual = data["Poblacio_homes"] / data["Interval_years"]
    f_actual = data["Poblacio_dones"] / data["Interval_years"]
    m_no_mig = (data["Poblacio_homes"] - data["Saldo_migratori_homes"]) / data["Interval_years"]
    f_no_mig = (data["Poblacio_dones"] - data["Saldo_migratori_dones"]) / data["Interval_years"]

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    y = np.arange(len(data))

    ax.barh(y, -m_actual, color=BLUE, height=0.58, label="Men (Observed 2024)")
    ax.barh(y, f_actual, color=VERMILION, height=0.58, label="Women (Observed 2024)")

    ax.barh(y, -m_no_mig, facecolor="none", edgecolor=DARK, linestyle="--", linewidth=1.3, height=0.58, label="Counterfactual without 2022–24 migration")
    ax.barh(y, f_no_mig, facecolor="none", edgecolor=DARK, linestyle="--", linewidth=1.3, height=0.58)

    ax.axvline(0, color="#333333", linewidth=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(data["Age_group"], fontsize=10)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, pos: "0" if x == 0 else f"{abs(int(x))/1000:.0f}k"))
    ax.set_xlim(-80000, 80000)
    ax.grid(axis="x")
    ax.set_axisbelow(True)

    ax.set_title(
        "2022–2024 Migration Prevented Severe Contraction in Young Adult Cohorts",
        fontsize=12.5,
        fontweight="bold",
        loc="left",
        pad=22
    )
    ax.text(
        0, 1.02,
        "Catalonia population pyramid in 2024 vs. counterfactual without 2022–2024 net migration",
        transform=ax.transAxes, fontsize=9, color="#555555", ha="left"
    )
    ax.set_xlabel("Residents per single year of age (thousands)", fontsize=10)
    ax.legend(frameon=False, loc="lower right", fontsize=9)

    add_footer(fig, y_pos=-0.04)
    plt.savefig(output_path)
    plt.close()

# ==============================================================================
# FIGURE 3: ANNUAL NET MIGRATION RATE HEATMAP (ALL YEARS + PROJECTION LINE)
# ==============================================================================
def plot_migration_rate_heatmap(df_historic: pd.DataFrame, output_path: Path):
    pivot = df_historic.pivot(index="Age_group", columns="Any", values="Migration_rate_%").iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, 5.6))

    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="RdBu",
        vmin=-1.5,
        vmax=5.2,
        center=0,
        cbar_kws={"label": "Net migration rate (%)", "shrink": 0.85},
        linewidths=1.0,
        linecolor="white",
        annot_kws={"size": 8.5},
        ax=ax
    )

    cols = list(pivot.columns)
    if 2024 in cols and 2025 in cols:
        proj_idx = cols.index(2025)
        ax.axvline(proj_idx, color=DARK, linestyle="--", linewidth=1.6)
        ax.text(proj_idx + 0.12, -0.12, "Projections →", fontsize=8.5, fontweight="bold", color=DARK, ha="left")

    ax.set_title(
        "Post-2022 Migration Boom Reversed the 2012–2014 Exodus Among Young Adults",
        fontsize=12.5,
        fontweight="bold",
        loc="left",
        pad=32
    )
    ax.text(
        0,
        1.06,
        "Annual net migration growth rate by age group (%), observed (2012–2024) & projected (2025–2026)",
        transform=ax.transAxes,
        fontsize=9,
        color="#555555",
        ha="left"
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="y", rotation=0, labelsize=10)
    ax.tick_params(axis="x", rotation=45, labelsize=9.5)

    add_footer(fig, y_pos=-0.05)
    plt.savefig(output_path)
    plt.close()

# FIGURE 4: CRYSTAL-CLEAR OVERREPRESENTATION BAR CHART (SELF-EXPLANATORY)

def plot_age_structure_comparison(df_historic: pd.DataFrame, output_path: Path, year: int = 2024):
    df_year = df_historic[df_historic["Any"] == year].groupby("Age_group", observed=False).agg({
        "Poblacio_total": "sum",
        "Saldo_migratori_total": "sum",
        "Interval_years": "first"
    })

    pop_per_yr = df_year["Poblacio_total"] / df_year["Interval_years"]
    mig_per_yr = df_year["Saldo_migratori_total"] / df_year["Interval_years"]

    pct_pop = (pop_per_yr / pop_per_yr.sum()) * 100
    pct_mig = (mig_per_yr / mig_per_yr.sum()) * 100

    fig, ax = plt.subplots(figsize=(10, 5.4))
    y = np.arange(len(AGE_ORDER_EN))
    height = 0.36

    ax.axhspan(0.55, 2.45, color="#EBF3FA", zorder=0)
    ax.text(
        38.5, 1.5,
        "Core Migration Engine (15–34)\n• 32.7% of resident base\n• 66.6% of net migration\n  (>2x overrepresented)",
        fontsize=8.8, color=BLUE, fontweight="bold", va="center", ha="right",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor=BLUE, alpha=0.95, lw=1)
    )

    ax.barh(y - height/2, pct_pop, height, color=GRAY, label=f"Share of resident population ({year})", zorder=3)
    ax.barh(y + height/2, pct_mig, height, color=BLUE, label=f"Share of net migration inflow ({year})", zorder=3)

    for i in range(len(AGE_ORDER_EN)):
        ax.text(pct_pop.iloc[i] + 0.4, y[i] - height/2, f"{pct_pop.iloc[i]:.1f}%", va="center", ha="left", fontsize=8.5, color="#555555")
        ax.text(pct_mig.iloc[i] + 0.4, y[i] + height/2, f"{pct_mig.iloc[i]:.1f}%", va="center", ha="left", fontsize=9, color=BLUE, fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels(AGE_ORDER_EN, fontsize=10)
    ax.set_xlim(0, 40)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.grid(axis="x", zorder=1)

    ax.set_title(
        "Young Adults (15–34) Drive Two-Thirds of Migration Despite Being One-Third of Residents",
        fontsize=12,
        fontweight="bold",
        loc="left",
        pad=24
    )
    ax.text(
        0,
        1.02,
        f"Age distribution of resident population vs. net migration balance in {year} (adjusted for unequal age-bracket widths)",
        transform=ax.transAxes,
        fontsize=8.8,
        color="#555555",
        ha="left"
    )
    ax.set_xlabel("Share across age cohorts (%)", fontsize=9.5, labelpad=6)
    ax.legend(frameon=False, loc="upper right", fontsize=9)

    add_footer(fig, y_pos=-0.04)
    plt.savefig(output_path)
    plt.close()

# FIGURE 5: POPULATION EVOLUTION WITH VS. WITHOUT MIGRATION (SMALL MULTIPLES)

def plot_age_composition_evolution(df_historic: pd.DataFrame, output_path: Path):
    df = df_historic.copy()
    df["Cum_mig"] = df.groupby("Age_group", observed=False)["Saldo_migratori_total"].cumsum()
    df["Pop_no_mig"] = df["Poblacio_total"] - df["Cum_mig"]

    base_2012 = df[df["Any"] == 2012].set_index("Age_group")["Poblacio_total"]
    df["Index_real"] = (df["Poblacio_total"] / df["Age_group"].map(base_2012).astype(float)) * 100
    df["Index_no_mig"] = (df["Pop_no_mig"] / df["Age_group"].map(base_2012).astype(float)) * 100
    df.loc[df["Any"] == 2012, "Index_no_mig"] = 100.0

    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.2), sharex=True, sharey=True)
    axes = axes.flatten()

    for idx, group in enumerate(AGE_ORDER_EN):
        ax = axes[idx]
        sub = df[df["Age_group"] == group].sort_values("Any")

        ax.axhline(100, color="#BBBBBB", linestyle=":", linewidth=0.8, zorder=1)
        ax.axvline(2024, color="#666666", linestyle=":", linewidth=0.9, zorder=1)

        ax.fill_between(
            sub["Any"], sub["Index_no_mig"], sub["Index_real"],
            where=(sub["Index_real"] >= sub["Index_no_mig"]),
            color=BLUE, alpha=0.16, interpolate=True, label="Net migration gain"
        )
        ax.fill_between(
            sub["Any"], sub["Index_no_mig"], sub["Index_real"],
            where=(sub["Index_real"] < sub["Index_no_mig"]),
            color=VERMILION, alpha=0.16, interpolate=True
        )

        ax.plot(sub["Any"], sub["Index_real"], color=BLUE, linewidth=2.2, label="Observed / Projected population")
        ax.plot(sub["Any"], sub["Index_no_mig"], color=DARK, linestyle="--", linewidth=1.4, label="Without migration (since 2012)")

        end_real = sub["Index_real"].iloc[-1]
        end_nomig = sub["Index_no_mig"].iloc[-1]
        gap = end_real - end_nomig

        ax.text(2026.2, end_real, f"{end_real - 100:+.0f}%", color=BLUE, fontsize=8.5, fontweight="bold", va="center")
        if abs(gap) > 3:
            ax.text(2026.2, end_nomig, f"{end_nomig - 100:+.0f}%", color=DARK, fontsize=8, va="center")

        ax.set_title(group, fontsize=10.5, fontweight="bold", loc="left", pad=6)
        ax.set_xlim(2012, 2028.2)
        ax.set_ylim(60, 138)
        ax.grid(axis="y", alpha=0.4)
        ax.tick_params(axis="x", rotation=45, labelsize=8.5)

        if idx % 3 == 0:
            ax.set_ylabel("Population index (2012 = 100)", fontsize=9)
        if idx == 2:
            ax.text(2024.1, 133, "Proj. →", fontsize=7.5, color="#555555", fontweight="bold")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="upper right", ncol=3, fontsize=9, bbox_to_anchor=(0.98, 0.94))

    fig.suptitle(
        "Migration Prevents Youth Collapse (15–34) While 60+ Growth Is Driven by Aging",
        fontsize=13,
        fontweight="bold",
        x=0.04,
        y=0.99,
        ha="left"
    )
    fig.text(
        0.04,
        0.945,
        "Population change indexed to 2012: Observed/Projected vs. Counterfactual without cumulative net migration",
        fontsize=9,
        color="#555555",
        ha="left"
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    add_footer(fig, y_pos=0.01)
    plt.savefig(output_path)
    plt.close()

# EXECUTION

if __name__ == "__main__":
    df_historic = load_data(DATA_PATH)
    df_22_24 = load_data(DATA_PATH, years=[2022, 2023, 2024])

    plot_migration_flows_by_age(df_historic, FIGURES_DIR / "01_fluxos_migratoris_edat.png", years=[2015, 2020, 2024])
    plot_population_pyramid(df_22_24, PIRAMIDES_DIR / "02_piramide_real_vs_sense_migracio.png")
    plot_migration_rate_heatmap(df_historic, FIGURES_DIR / "03_heatmap_taxa_migratoria.png")
    plot_age_structure_comparison(df_historic, FIGURES_DIR / "04_estructura_poblacio_vs_migracio.png", year=2024)
    plot_age_composition_evolution(df_historic, FIGURES_DIR / "05_evolucio_composicio_edat.png")

    print(f"Charts saved in: {FIGURES_DIR}")