from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ROOT_DIR = Path(__file__).resolve().parents[2]

# Select the year to plot (available: 2005 to 2022)
YEAR = 2022

# Load files where data is stored
df_saldo = pd.read_csv(ROOT_DIR / 'data' / 'raw' / 'migration' / 'saldo_extern_comarques.csv')
df_rfdb = pd.read_csv(ROOT_DIR / 'data' / 'raw' / 'economics' / 'rfdb_per_habitant_comarques_2005_2023.csv')

# Merge on year and comarca (inner join keeps overlapping years and excludes 'Catalunya' total)
merged = pd.merge(
    df_rfdb,
    df_saldo,
    left_on=['any', 'comarca'],
    right_on=['Any', 'Nom'],
    how='inner'
)

df_year = merged[merged['any'] == YEAR].copy()

# Calculate Catalonia population-weighted averages for the quadrant crosshairs
avg_rfdb = (df_year['rfdb_per_habitant_euros'] * df_year['Poblacio']).sum() / df_year['Poblacio'].sum()
avg_saldo = (df_year['Saldo_ext'].sum() / df_year['Poblacio'].sum()) * 1000

# Assign each comarca to its quadrant
def get_quadrant(row):
    high_inc = row['rfdb_per_habitant_euros'] >= avg_rfdb
    high_mig = row['saldo_ext_per_mil'] >= avg_saldo
    if high_inc and high_mig:
        return 'High Income, High Migration'
    elif high_inc and not high_mig:
        return 'High Income, Lower Migration'
    elif not high_inc and high_mig:
        return 'Lower Income, High Migration'
    else:
        return 'Lower Income, Lower Migration'

df_year['quadrant'] = df_year.apply(get_quadrant, axis=1)

# Use the same universal colorblind-safe palette
universal_colors = {
    'High Income, High Migration': '#0072B2',
    'High Income, Lower Migration': '#009E73',
    'Lower Income, High Migration': '#E69F00',
    'Lower Income, Lower Migration': '#999999'
}

fig, ax = plt.subplots(figsize=(14, 8))

# Plot bubbles quadrant by quadrant (size proportional to population)
for quad_name, color in universal_colors.items():
    sub = df_year[df_year['quadrant'] == quad_name]
    sizes = (sub['Poblacio'] / 1000) * 0.55 + 45
    ax.scatter(
        sub['rfdb_per_habitant_euros'],
        sub['saldo_ext_per_mil'],
        s=sizes,
        color=color,
        alpha=0.75,
        edgecolors='white',
        linewidth=1.2,
        zorder=4
    )

# Quadrant reference crosshairs (Catalonia averages) and zero line if needed
ax.axvline(avg_rfdb, color='#222222', linestyle='--', linewidth=1.6, alpha=0.85, zorder=3)
ax.axhline(avg_saldo, color='#222222', linestyle='--', linewidth=1.6, alpha=0.85, zorder=3)
if df_year['saldo_ext_per_mil'].min() < 0:
    ax.axhline(0, color='#333333', lw=1.0, zorder=2)

# Add axis headroom so bubbles and labels never clip
x_min, x_max = df_year['rfdb_per_habitant_euros'].min(), df_year['rfdb_per_habitant_euros'].max()
y_min, y_max = df_year['saldo_ext_per_mil'].min(), df_year['saldo_ext_per_mil'].max()
x_pad = (x_max - x_min) * 0.10
y_pad = (y_max - y_min) * 0.15
ax.set_xlim(x_min - x_pad, x_max + x_pad)
ax.set_ylim(y_min - y_pad, y_max + y_pad)

# Crosshair average callout boxes
ax.text(avg_rfdb + x_pad * 0.10, y_max + y_pad * 0.85,
        f'Catalonia avg: {avg_rfdb:,.0f} €',
        verticalalignment='top', horizontalalignment='left',
        fontsize=10, fontweight='bold', color='#222222', zorder=8,
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#CCCCCC', alpha=0.95))

ax.text(x_min - x_pad * 0.85, avg_saldo + y_pad * 0.12,
        f'Catalonia avg: {avg_saldo:.1f}‰',
        verticalalignment='bottom', horizontalalignment='left',
        fontsize=10, fontweight='bold', color='#222222', zorder=8,
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#CCCCCC', alpha=0.95))

# Label the most populous comarcas and key outliers automatically
to_label = set(
    pd.concat([
        df_year.nlargest(4, 'Poblacio'),
        df_year.nlargest(3, 'rfdb_per_habitant_euros'),
        df_year.nsmallest(2, 'rfdb_per_habitant_euros'),
        df_year.nlargest(3, 'saldo_ext_per_mil'),
        df_year.nsmallest(3, 'saldo_ext_per_mil')
    ])['comarca']
)

placed = []
for _, row in df_year[df_year['comarca'].isin(to_label)].sort_values('Poblacio', ascending=False).iterrows():
    x0, y0 = row['rfdb_per_habitant_euros'], row['saldo_ext_per_mil']
    dx = -10 if x0 > (x_max - x_pad * 0.5) else 9
    ha = 'right' if dx < 0 else 'left'
    dy = -11 if y0 > (y_max - y_pad * 0.3) else 4

    # Slightly stagger labels if two comarcas sit close together
    nx = (x0 - x_min) / max(x_max - x_min, 1)
    ny = (y0 - y_min) / max(y_max - y_min, 1)
    for px, py, pdy in placed:
        if abs(nx - px) < 0.08 and abs(ny - py) < 0.06:
            dy = pdy - 12 if pdy <= 0 else pdy + 12
    placed.append((nx, ny, dy))

    ax.annotate(
        row['comarca'],
        (x0, y0),
        xytext=(dx, dy),
        textcoords='offset points',
        fontsize=9.5,
        fontweight='bold' if row['comarca'] == 'Barcelonès' else 'normal',
        color='#222222',
        ha=ha,
        va='center',
        zorder=7
    )

# Bottom-right info badge

ax.text(0.98, 0.03, f'Bubble size ∝ population ({YEAR}) ',
        transform=ax.transAxes, fontsize=9.5, color='#222222', ha='right', va='bottom',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#CCCCCC', alpha=0.95))

# Centered top legend and axis formatting
ax.set_title(f'Disposable Household Income (RFDB) vs. Net External Migration by Comarca ({YEAR})',
             fontsize=15, fontweight='bold', pad=45)
ax.set_xlabel('Disposable Household Income per Capita (RFDB, €)', fontsize=11)
ax.set_ylabel('Net External Migration Rate (per 1,000 inhabitants)', fontsize=11)
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,} €'))
ax.grid(True, linestyle=':', alpha=0.6)
ax.spines[['top', 'right']].set_visible(False)

legend_handles = [
    plt.Line2D([0], [0], marker='o', color='w', label=quad_name,
               markerfacecolor=color, markersize=10, alpha=0.85)
    for quad_name, color in universal_colors.items()
]
ax.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, 1.09), ncol=4,
          frameon=True, facecolor='white', edgecolor='#CCCCCC', fontsize=10)

plt.tight_layout()
ruta_figura = ROOT_DIR / 'results' / 'figures' / f'rfdb_vs_migration_{YEAR}.png'
ruta_figura.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(ruta_figura, dpi=300, bbox_inches='tight')
plt.show()