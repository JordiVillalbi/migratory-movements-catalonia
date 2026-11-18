import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.animation import FuncAnimation, PillowWriter

# 1. Load and merge
df_saldo = pd.read_csv('data/raw/migration/saldo_extern_comarques.csv')
df_rfdb = pd.read_csv('data/raw/economics/rfdb_per_habitant_comarques_2005_2023.csv')
merged = pd.merge(df_rfdb, df_saldo, left_on=['any', 'comarca'], right_on=['Any', 'Nom'])

years = sorted(merged['any'].unique())

# Keep axes fixed across all years
x_min, x_max = merged['rfdb_per_habitant_euros'].min(), merged['rfdb_per_habitant_euros'].max()
y_min, y_max = merged['saldo_ext_per_mil'].min(), merged['saldo_ext_per_mil'].max()
x_pad, y_pad = (x_max - x_min) * 0.10, (y_max - y_min) * 0.15

colors = {
    'High Income, High Migration': '#0072B2',
    'High Income, Lower Migration': '#009E73',
    'Lower Income, High Migration': '#E69F00',
    'Lower Income, Lower Migration': '#999999'
}

# Fixed-size handles so legend dots never change size across frames
legend_handles = [
    plt.Line2D([0], [0], marker='o', color='w', label=label, markerfacecolor=color, markersize=10)
    for label, color in colors.items()
]

fig, ax = plt.subplots(figsize=(14, 8))

# 2. Draw one frame per year
def update(year):
    ax.clear()
    df = merged[merged['any'] == year].copy()

    avg_x = (df['rfdb_per_habitant_euros'] * df['Poblacio']).sum() / df['Poblacio'].sum()
    avg_y = (df['Saldo_ext'].sum() / df['Poblacio'].sum()) * 1000

    for label, color in colors.items():
        inc_cond = (df['rfdb_per_habitant_euros'] >= avg_x) if 'High Income' in label else (df['rfdb_per_habitant_euros'] < avg_x)
        mig_cond = (df['saldo_ext_per_mil'] >= avg_y) if 'High Migration' in label else (df['saldo_ext_per_mil'] < avg_y)
        sub = df[inc_cond & mig_cond]

        ax.scatter(
            sub['rfdb_per_habitant_euros'], sub['saldo_ext_per_mil'],
            s=(sub['Poblacio'] / 1000) * 0.55 + 45,
            color=color, alpha=0.75, edgecolors='white', linewidth=1.2
        )

    # Crosshairs and labels
    ax.axvline(avg_x, color='#222222', ls='--', lw=1.5)
    ax.axhline(avg_y, color='#222222', ls='--', lw=1.5)
    ax.axhline(0, color='#333333', lw=0.8)

    for _, r in df.nlargest(8, 'Poblacio').iterrows():
        ax.annotate(r['comarca'], (r['rfdb_per_habitant_euros'], r['saldo_ext_per_mil']),
                    xytext=(6, 4), textcoords='offset points', fontsize=9)

    # Formatting
    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_title(f'Disposable Income (RFDB) vs. Net External Migration ({year})', fontsize=15, fontweight='bold', pad=40)
    ax.set_xlabel('Disposable Household Income per Capita (€)')
    ax.set_ylabel('Net External Migration Rate (per 1,000)')
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,} €'))
    ax.grid(True, ls=':', alpha=0.6)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, 1.08), ncol=4, frameon=True)

# 3. Save directly to path
anim = FuncAnimation(fig, update, frames=years, interval=800)
anim.save('results/figures/rfdb_vs_migration_2005_2023.gif', writer=PillowWriter(fps=0.5), dpi=150)
plt.show()
