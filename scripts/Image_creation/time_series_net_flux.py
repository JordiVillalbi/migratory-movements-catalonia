from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ROOT_DIR = Path(__file__).resolve().parents[2]

# Load files where data is stored
df_immigration = pd.read_csv(ROOT_DIR / 'data' / 'processed' / 'migration' / 'immigracions_externes.csv')
df_emigration = pd.read_csv(ROOT_DIR / 'data' / 'processed' / 'migration' / 'emigracions_externes.csv')

# We merge the columns that talk about nationality and gender as we are only interested in the net flux by regions
immigration_agg = df_immigration.groupby(['any', 'procedencia'])['valor'].sum().reset_index()
emigration_agg = df_emigration.groupby(['any', 'destinacio'])['valor'].sum().reset_index()

# We rename the new columns
taula_immigration = immigration_agg.rename(columns={'procedencia': 'regio', 'valor': 'immigracions'})
taula_emigration = emigration_agg.rename(columns={'destinacio': 'regio', 'valor': 'emigracions'})

# We merge the two tables into one
total_flux = pd.merge(taula_immigration, taula_emigration, on=['any', 'regio'], how='inner') #Inner so the colum 'baixes per caducitat' that exists only in one file doesn't get added

# Normalize each series over its own annual total across all regions (%)
total_immig_anual = total_flux.groupby('any')['immigracions'].transform('sum')
total_emig_anual = total_flux.groupby('any')['emigracions'].transform('sum')

total_flux['immigracions_pct'] = (total_flux['immigracions'] / total_immig_anual) * 100
total_flux['emigracions_pct'] = (total_flux['emigracions'] / total_emig_anual) * 100

# Ploting of the fluxes

regions = ['Amèrica', 'Resta UE', 'Àfrica', 'Àsia i Oceania', 'Resta Europa', 'No hi consta']

fig, axes = plt.subplots(2, 3, figsize=(16, 9.5), sharex=True, sharey=True)
axes = axes.flatten()

for idx, reg in enumerate(regions):
    ax = axes[idx]
    
    
    sub = total_flux[total_flux['regio'] == reg].sort_values('any')
    
    anys = sub['any'].values
    immig = sub['immigracions_pct'].values
    emig = sub['emigracions_pct'].values

    # Both emigration and immigration lines
    ax.plot(anys, immig, color='#1f77b4', lw=2.2, marker='o', ms=3.5, label='Immigrations (% over total.)')
    ax.plot(anys, emig, color='#d95f02', lw=2.2, ls='--', marker='s', ms=3.2, label='Emigrations (% over total.)')

    # Fill the gap between both lines
    ax.fill_between(anys, immig, emig, where=(immig >= emig), interpolate=True,
                    color='#2ca02c', alpha=0.22, label='Positive net flux')
    ax.fill_between(anys, immig, emig, where=(immig < emig), interpolate=True,
                    color='#d62728', alpha=0.22, label='Negative net flux')


    ax.set_title(reg, fontsize=12, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.spines[['top', 'right']].set_visible(False)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    ax.set_xticks(range(2005, 2025, 3))


fig.suptitle('Net Migration Fluxes over Time (2005–2024)',
             fontsize=15, fontweight='bold', y=0.97)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.92), ncol=4, frameon=True)

plt.tight_layout(rect=[0, 0, 1, 0.88])
ruta_figura = ROOT_DIR / "results" / "figures" / "flux_migratori_net_regions.png"
ruta_figura.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(ruta_figura, dpi=300, bbox_inches="tight")

plt.show()