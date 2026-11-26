from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator

def main():
    # 1. Rutes relatives
    base_dir = Path(__file__).resolve().parents[2]
    csv_path = base_dir / "data" / "processed" / "economics" / "migracio_externa_salaris_comarques.csv"
    output_dir = base_dir / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "serie_temporal_provincial_migracio_norm_destacat.png"

    # 2. Càrrega i neteja de dades
    df = pd.read_csv(csv_path).dropna(subset=["saldo_migratori_exterior", "sou_mitja_eur", "any", "comarca"])
    
    # Diccionari complet de comarques a províncies de Catalunya
    provincies_map = {
        # Barcelona
        "Alt Penedès": "Barcelona", "Anoia": "Barcelona", "Bages": "Barcelona", 
        "Baix Llobregat": "Barcelona", "Barcelonès": "Barcelona", "Berguedà": "Barcelona", 
        "Garraf": "Barcelona", "Maresme": "Barcelona", "Moianès": "Barcelona", 
        "Osona": "Barcelona", "Vallès Occidental": "Barcelona", "Vallès Oriental": "Barcelona", 
        "Lluçanès": "Barcelona",
        # Girona
        "Alt Empordà": "Girona", "Baix Empordà": "Girona", "Garrotxa": "Girona", 
        "Gironès": "Girona", "Pla de l'Estany": "Girona", "Ripollès": "Girona", "Selva": "Girona",
        # Lleida
        "Alt Urgell": "Lleida", "Alta Ribagorça": "Lleida", "Cerdanya": "Lleida", 
        "Garrigues": "Lleida", "Noguera": "Lleida", "Pallars Jussà": "Lleida", 
        "Pallars Sobirà": "Lleida", "Pla d'Urgell": "Lleida", "Segarra": "Lleida", 
        "Segrià": "Lleida", "Solsonès": "Lleida", "Urgell": "Lleida", "Val d'Aran": "Lleida",
        # Tarragona
        "Alt Camp": "Tarragona", "Baix Camp": "Tarragona", "Baix Ebre": "Tarragona", 
        "Baix Penedès": "Tarragona", "Conca de Barberà": "Tarragona", "Montsià": "Tarragona", 
        "Priorat": "Tarragona", "Ribera d'Ebre": "Tarragona", "Tarragonès": "Tarragona", 
        "Terra Alta": "Tarragona"
    }

    df["provincia"] = df["comarca"].map(provincies_map)
    df = df.dropna(subset=["provincia"])

    # 3. Calcular la mitjana anual del sou i de la immigració per província
    df_prov = df.groupby(["provincia", "any"], as_index=False).agg({
        "sou_mitja_eur": "mean",
        "saldo_migratori_exterior": "mean"
    })

    # 4. Normalitzar el saldo migratori RESPECTE A CADA PROVÍNCIA (Min-Max per grup)
    def normalize_group(group):
        min_v = group["saldo_migratori_exterior"].min()
        max_v = group["saldo_migratori_exterior"].max()
        if max_v - min_v == 0:
            group["saldo_normalitzat"] = 0.0
        else:
            group["saldo_normalitzat"] = (group["saldo_migratori_exterior"] - min_v) / (max_v - min_v)
        return group

    df_prov = df_prov.groupby("provincia", group_keys=False).apply(normalize_group)

    # 5. Construcció del gràfic amb format ample i heatmap molt més visible ('plasma')
    fig, ax = plt.subplots(figsize=(14, 8), dpi=150)

    # Punts grans i colormap 'plasma' per destacar el heatmap
    scatter = ax.scatter(
        df_prov["any"],
        df_prov["saldo_normalitzat"],
        c=df_prov["sou_mitja_eur"],
        cmap="plasma",
        s=220,
        alpha=0.95,
        edgecolors="white",
        linewidth=1.2,
        zorder=3
    )

    # Connectar els punts temporalment per a cada província i afegir etiqueta clara
    for prov in df_prov["provincia"].unique():
        sub = df_prov[df_prov["provincia"] == prov].sort_values("any")
        ax.plot(
            sub["any"],
            sub["saldo_normalitzat"],
            linestyle="--",
            linewidth=1.2,
            alpha=0.35,
            color="#333333",
            zorder=2
        )
        # Etiqueta amb el nom de la província al final de la línia (2024)
        last = sub.iloc[-1]
        ax.annotate(
            prov,
            (last["any"], last["saldo_normalitzat"]),
            xytext=(9, 0),
            textcoords="offset points",
            fontsize=10.5,
            fontweight="bold",
            color="#111111",
            zorder=4
        )

    # Barra de color (heatmap) més destacada
    cbar = plt.colorbar(scatter, ax=ax, pad=0.03, shrink=0.85)
    cbar.set_label("Mitjana del sou provincial (€)", fontsize=11, fontweight="bold")
    cbar.ax.tick_params(labelsize=10)

    # Forçar anys enters a l'eix X
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # Personalització i estètica neta

    ax.set_xlabel("Any", fontsize=11.5, fontweight="bold")
    ax.set_ylabel("Saldo migratori exterior (Escala normalitzada 0–1 per província)", fontsize=11.5, fontweight="bold")
    
    # Marges amplis per evitar talls
    ax.set_xlim(df_prov["any"].min() - 0.5, df_prov["any"].max() + 3.0)
    ax.set_ylim(-0.05, 1.05)
    
    ax.grid(True, which="major", linestyle=":", alpha=0.6, zorder=1)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Sèrie temporal provincial normalitzada guardada a: {output_path}")
    plt.show()

if __name__ == "__main__":
    main()