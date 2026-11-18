import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Load files where data is stored
df_immigration = pd.read_csv('data/processed/migration/immigracions_externes.csv')
df_emigration = pd.read_csv('data/processed/migration/emigracions_externes.csv')
df_irpf = pd.read_csv('data/raw/economics/irpf_2000_2024.csv', sep=';')

# Filter only 'base imposable general per declarant (€)'
df_base = df_irpf[df_irpf['concepte'] == 'base imposable general per declarant (€)'].set_index('any')

# Merge the columns for net flux by regions
immigration_agg = df_immigration.groupby(['any', 'procedencia'])['valor'].sum().reset_index()
emigration_agg = df_emigration.groupby(['any', 'destinacio'])['valor'].sum().reset_index()

taula_immigration = immigration_agg.rename(columns={'procedencia': 'regio', 'valor': 'immigracions'})
taula_emigration = emigration_agg.rename(columns={'destinacio': 'regio', 'valor': 'emigracions'})

total_flux = pd.merge(taula_immigration, taula_emigration, on=['any', 'regio'], how='inner')
total_flux['flux_net'] = total_flux['immigracions'] - total_flux['emigracions']

regions = ['Amèrica', 'Resta UE', 'Àfrica', 'Àsia i Oceania', 'Resta Europa', 'No hi consta']
piv = total_flux.pivot(index='any', columns='regio', values='flux_net')[regions].sort_index()

years = piv.index.values
total_net_flux = piv.sum(axis=1).values
base_aligned = df_base.reindex(years)['valor']

universal_colors = {
    'Amèrica': '#0072B2',
    'Resta UE': '#E69F00',
    'Àfrica': '#009E73',
    'Àsia i Oceania': '#CC79A7',
    'Resta Europa': '#D55E00',
    'No hi consta': '#999999'
}

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(14, 9.5), sharex=True,
    gridspec_kw={'height_ratios': [1.6, 1], 'hspace': 0.12}
)

# --- PANEL 1: Net Migration Flux ---
base_pos = np.zeros(len(years))
base_neg = np.zeros(len(years))

for reg in regions:
    values = piv[reg].values
    pos = np.maximum(values, 0)
    neg = np.minimum(values, 0)

    ax1.fill_between(years, base_pos, base_pos + pos, color=universal_colors[reg], alpha=0.65, label=reg)
    base_pos += pos

    ax1.fill_between(years, base_neg, base_neg + neg, color=universal_colors[reg], alpha=0.65)
    base_neg += neg

ax1.plot(years, total_net_flux, color='white', lw=6.5, zorder=9)
ax1.plot(years, total_net_flux, color='#111111', lw=3.8, marker='o', ms=6.5,
         markerfacecolor='white', markeredgewidth=2.2, label='Total net flux', zorder=10)

ax1.axhline(0, color='#333333', lw=1.0)

y_min, y_max = ax1.get_ylim()
ax1.set_ylim(y_min, y_max * 1.18)

events = [
    (2008, '2008 Financial Crisis'),
    (2020, 'COVID-19 Pandemic'),
    (2022, 'Ukraine War')
]

for year, label in events:
    ax1.axvline(x=year, color='#222222', linestyle='--', linewidth=1.5, alpha=0.8, zorder=8)
    ax1.text(year + 0.15, y_max * 1.14, label,
             rotation=90, verticalalignment='top', horizontalalignment='left',
             fontsize=9.5, fontweight='bold', color='#222222', zorder=12,
             bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#CCCCCC', alpha=0.95))

ax1.set_title('Net Migration Flux by Region vs. IRPF General Tax Base (2005–2024)',
              fontsize=15, fontweight='bold', pad=45)
ax1.set_ylabel('Net migration flux (people)', fontsize=11, fontweight='bold')
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.spines[['top', 'right']].set_visible(False)

ax1.legend(loc='upper center', bbox_to_anchor=(0.5, 1.13), ncol=4,
           frameon=True, facecolor='white', edgecolor='#CCCCCC', fontsize=10)

# --- PANEL 2: Base Imposable General ---
y_base_min = base_aligned.min() * 0.92
y_base_max = base_aligned.max() * 1.05

ax2.plot(years, base_aligned, color='#1B4F72', lw=3.2, marker='s', ms=6.5,
         markerfacecolor='white', markeredgewidth=2, label='Base imposable general per declarant (€)')
ax2.fill_between(years, y_base_min, base_aligned, color='#AED6F1', alpha=0.28)
ax2.set_ylim(y_base_min, y_base_max)

for year, _ in events:
    ax2.axvline(x=year, color='#222222', linestyle='--', linewidth=1.5, alpha=0.8, zorder=8)

ax2.set_ylabel('Base imposable (€)', fontsize=11, fontweight='bold')
ax2.set_xlabel('Year', fontsize=11, fontweight='bold')
ax2.set_xticks(range(2005, 2025, 1))
ax2.set_xlim(2004.7, 2024.3)
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,} €'))
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.spines[['top', 'right']].set_visible(False)
ax2.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#CCCCCC', fontsize=10)

plt.savefig('results/figures/net_flux_and_base_imposable.png', dpi=300, bbox_inches='tight')
plt.show()