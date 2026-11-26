from pathlib import Path
from matplotlib.ticker import ScalarFormatter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


def main():
    # 1. Rutes relatives amb pathlib des de scripts/Image_creation/
    base_dir = Path(__file__).resolve().parents[2]
    csv_path = base_dir / "data" / "processed" / "economics" / "migracio_externa_salaris_comarques.csv"
    output_dir = base_dir / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "mapa_quadrants_tendencia.png"

    # 2. Càrrega i agregació per comarca (2005–2024)
    df = pd.read_csv(csv_path).dropna(subset=["saldo_migratori_exterior", "sou_mitja_eur"])
    df_com = df.groupby("comarca", as_index=False).agg(
        saldo_mitja=("saldo_migratori_exterior", "mean"),
        sou_mitja=("sou_mitja_eur", "mean"),
    )

    med_sou = df_com["sou_mitja"].median()
    med_saldo = df_com["saldo_mitja"].median()
    rho_com, _ = stats.spearmanr(df_com["sou_mitja"], df_com["saldo_mitja"])

    # 3. Classificació en 4 quadrants
    def assigna_quadrant(row):
        if row["sou_mitja"] >= med_sou and row["saldo_mitja"] >= med_saldo:
            return "Sou alt + Atracció alta"
        if row["sou_mitja"] < med_sou and row["saldo_mitja"] >= med_saldo:
            return "Sou baix + Atracció alta"
        if row["sou_mitja"] >= med_sou and row["saldo_mitja"] < med_saldo:
            return "Sou alt + Atracció baixa"
        return "Sou baix + Atracció baixa"

    df_com["quadrant"] = df_com.apply(assigna_quadrant, axis=1)

    palette = {
        "Sou alt + Atracció alta": "#1b9e77",
        "Sou baix + Atracció baixa": "#7570b3",
        "Sou alt + Atracció baixa": "#e7298a",
        "Sou baix + Atracció alta": "#d95f02",
    }

    # 4. Construcció del gràfic
    fig, ax = plt.subplots(figsize=(11, 7), dpi=150)

    # Punts per quadrant
    sns.scatterplot(
        data=df_com,
        x="sou_mitja",
        y="saldo_mitja",
        hue="quadrant",
        palette=palette,
        s=95,
        alpha=0.9,
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
        ax=ax,
    )

    # Recta de tendència log-lineal + interval de confiança 95%
    x_vals = df_com["sou_mitja"].values
    y_log = np.log10(df_com["saldo_mitja"].values)
    slope, intercept, r_log, _, _ = stats.linregress(x_vals, y_log)

    x_grid = np.linspace(x_vals.min() - 200, x_vals.max() + 200, 200)
    y_pred = 10 ** (intercept + slope * x_grid)

    n = len(x_vals)
    dof = n - 2
    t_crit = stats.t.ppf(0.975, dof)
    resid = y_log - (intercept + slope * x_vals)
    s_err = np.sqrt(np.sum(resid**2) / dof)
    ci = t_crit * s_err * np.sqrt(
        1 / n + (x_grid - np.mean(x_vals)) ** 2 / np.sum((x_vals - np.mean(x_vals)) ** 2)
    )

    ax.plot(
        x_grid,
        y_pred,
        color="#222222",
        linewidth=2.2,
        linestyle="-",
        zorder=4,
        label=f"Tendència log-lineal (r = {r_log:.2f}, ρ = {rho_com:.2f})",
    )
    ax.fill_between(
        x_grid,
        10 ** ((intercept + slope * x_grid) - ci),
        10 ** ((intercept + slope * x_grid) + ci),
        color="#222222",
        alpha=0.12,
        zorder=2,
    )

    # Línies divisòries de les medianes i escala logarítmica
    ax.set_yscale("log")
    ax.axvline(med_sou, color="#555555", linestyle="--", linewidth=1, alpha=0.75, zorder=1)
    ax.axhline(med_saldo, color="#555555", linestyle="--", linewidth=1, alpha=0.75, zorder=1)

    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.set_yticks([50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000])

    # Etiquetes de comarques clau amb desplaçament per evitar solapaments
    offsets = {
        "Barcelonès": (-55, -14),
        "Vallès Occidental": (6, 4),
        "Baix Llobregat": (-78, 5),
        "Tarragonès": (6, 3),
        "Gironès": (6, -3),
        "Segrià": (6, 3),
        "Alt Empordà": (-68, 4),
        "Terra Alta": (6, 3),
        "Priorat": (6, 3),
        "Cerdanya": (6, 3),
        "Lluçanès": (-52, 5),
        "Maresme": (6, -8),
        "Garraf": (6, 3),
    }

    for _, row in df_com[df_com["comarca"].isin(offsets.keys())].iterrows():
        dx, dy = offsets[row["comarca"]]
        ax.annotate(
            row["comarca"],
            (row["sou_mitja"], row["saldo_mitja"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=8.5,
            alpha=0.9,
            zorder=5,
        )


    ax.set_xlabel("Sou mitjà comarcal 2005–2024 (€)", fontsize=10.5)
    ax.set_ylabel("Saldo migratori exterior mitjà anual (escala logarítmica)", fontsize=10.5)
    ax.grid(True, which="major", linestyle=":", alpha=0.5)
    ax.legend(
        title="Perfil comarcal i tendència",
        loc="upper left",
        fontsize=9,
        title_fontsize=9.5,
        frameon=True,
    )

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Gràfic guardat a: {output_path}")
    plt.show()


if __name__ == "__main__":
    main()