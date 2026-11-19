from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ROOT_DIR = Path(__file__).resolve().parents[2]

# Load files where data is stored
df_immigration = pd.read_csv(ROOT_DIR / 'data' / 'processed' / 'migration' / 'immigracions_externes.csv')
df_emigration = pd.read_csv(ROOT_DIR / 'data' / 'processed' / 'migration' / 'emigracions_externes.csv')

# We merge the columns that talk about nationality and gender as we are only interested in the net flux by regions
immigration_agg = df_immigration.groupby(['any', 'procedencia'])['valor'].sum().reset_index()
emigration_agg = df_emigration.groupby(['any', 'destinacio'])['valor'].sum().reset_index()  

# Rename the new columns
taula_immigration = immigration_agg.rename(columns={'procedencia': 'regio', 'valor': 'immigracions'})
taula_emigration = emigration_agg.rename(columns={'destinacio': 'regio', 'valor': 'emigracions'})   

# Calculate the total flux
total_flux = pd.merge(taula_immigration, taula_emigration, on=['any', 'regio'], how='inner') #Inner so the colum 'baixes per caducitat' that exists only in one file doesn't get added  
total_flux['flux_net'] = total_flux['immigracions'] - total_flux['emigracions']

regions = ['Amèrica', 'Resta UE', 'Àfrica', 'Àsia i Oceania', 'Resta Europa', 'No hi consta']
piv = total_flux.pivot(index='any', columns='regio', values='flux_net')[regions].sort_index()

years = piv.index.values
total_net_flux = piv.sum(axis=1).values

# We are going to use a universal color palette
universal_colors = {
    'Amèrica': '#0072B2',
    'Resta UE': '#E69F00',
    'Àfrica': '#009E73',
    'Àsia i Oceania': '#CC79A7',
    'Resta Europa': '#D55E00',
    'No hi consta': '#999999'}


fig, ax = plt.subplots(figsize=(14, 8))


# Positive areas upwards and negative downwards
base_pos = np.zeros(len(years))
base_neg = np.zeros(len(years))

for reg in regions:
    values = piv[reg].values
    pos = np.maximum(values, 0)
    neg = np.minimum(values, 0)

    ax.fill_between(years, base_pos, base_pos + pos, color=universal_colors[reg], alpha=0.65, label=reg)
    base_pos += pos

    ax.fill_between(years, base_neg, base_neg + neg, color=universal_colors[reg], alpha=0.65)
    base_neg += neg

# 5. Highlight the total net flux line (white halo + thick line with markers)
ax.plot(years, total_net_flux, color='white', lw=6.5, zorder=9)
ax.plot(years, total_net_flux, color='#111111', lw=3.8, marker='o', ms=6.5,
        markerfacecolor='white', markeredgewidth=2.2, label='Total net flux', zorder=10)

ax.axhline(0, color='#333333', lw=1.0)

# Add vertical headroom and event lines
y_min, y_max = ax.get_ylim()
ax.set_ylim(y_min, y_max * 1.15)

events = [
    (2008, '2008 Financial Crisis'),
    (2020, 'COVID-19 Pandemic'),
    (2022, 'Ukraine War')
]

for year, label in events:
    ax.axvline(x=year, color='#222222', linestyle='--', linewidth=1.6, alpha=0.85, zorder=8)
    ax.text(year + 0.15, y_max * 1.12, label,
            rotation=90, verticalalignment='top', horizontalalignment='left',
            fontsize=10, fontweight='bold', color='#222222', zorder=12,
            bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#CCCCCC', alpha=0.95))

# 6. Centered top legend and axis formatting
ax.set_title('Total Net Migration Flux and Regional Contribution (2005–2024)',
             fontsize=15, fontweight='bold', pad=45)
ax.set_xlabel('Year', fontsize=11)
ax.set_ylabel('Net migration flux (people)', fontsize=11)
ax.set_xticks(range(2005, 2025, 1))
ax.set_xlim(2004.7, 2024.3)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.grid(True, linestyle=':', alpha=0.6)
ax.spines[['top', 'right']].set_visible(False)

ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.09), ncol=4,
          frameon=True, facecolor='white', edgecolor='#CCCCCC', fontsize=10)

plt.tight_layout()
ruta_figura = ROOT_DIR / 'results' / 'figures' / 'net_flux_stacked_regions.png'
ruta_figura.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(ruta_figura, dpi=300, bbox_inches='tight')
plt.show()