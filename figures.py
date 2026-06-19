"""
figures.py - Semua figur paper (Gambar 1-6) dibuat di satu tempat.

Mengimpor mesin perhitungan dari common.py (single source of truth) lalu
menggambar keenam figur ke folder outputs/ dengan gaya yang sama persis
seperti versi sebelumnya (grayscale-biru, serif Times, tanpa judul di gambar).

  fig0_ihsg_trend.png         Gambar 1  - tren IHSG & BI Rate
  fig6_normalized_prices.png  Gambar 2  - harga 6 saham + IHSG (ternormalisasi)
  fig3_efficient_frontier.png Gambar 4  - efficient frontier LO vs UC + Delta-sigma
  fig1_correlation_heatmap.png Gambar 3 - heatmap korelasi
  fig2_dual_sml_plot.png      Gambar 5  - dual SML (teoritis vs empiris)
  fig5_oos_equity.png         Gambar 6  - equity curve out-of-sample
"""
import os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

import common as c

OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===================== GAYA GRAFIK (standar paper) =====================
plt.rcParams.update({
    'font.family':       'serif',
    'font.serif':        ['Times New Roman', 'DejaVu Serif'],
    'mathtext.fontset':  'stix',
    'font.size':         10,
    'axes.labelsize':    10,
    'xtick.labelsize':   9,
    'ytick.labelsize':   9,
    'legend.fontsize':   8,
    'axes.linewidth':    0.8,
    'axes.edgecolor':    '#333333',
    'axes.grid':         False,
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'figure.dpi':        150,
    'savefig.dpi':       220,
    'savefig.bbox':      'tight',
    'lines.linewidth':   1.3,
})

GS_BLACK = '#000000'
GS_DARK  = '#2b2b2b'
GS_MID   = '#6e6e6e'
GS_LIGHT = '#b0b0b0'
COL_BLUE = '#08519c'   # aksen utama (biru tua)
COL_RED  = '#4292c6'   # aksen sekunder (biru sedang)
COL_BI   = '#4292c6'
COL_BEAR = '#6baed6'

ZONE_MARKER = {'Zona I': 'o', 'Zona II': '^', 'Zona III': 's'}
ZONE_FACE   = {'Zona I': '#08519c', 'Zona II': '#6baed6', 'Zona III': '#c6dbef'}

# Palet seri harga ternormalisasi (selaras tampilan paper)
SERIES_COL = {'ASII': '#3690c0', 'ADRO': '#1b8a6b', 'ANTM': '#08306b',
              'MDKA': '#8856a7', 'BMRI': '#969696', 'INDF': '#9ecae1'}


# ============================ FIGUR ====================================
def fig0_ihsg_trend(px):
    """Gambar 1 - tren IHSG (poin) + BI Rate (dual axis)."""
    ihsg = px[c.MARKET].dropna()
    bi_dates = np.array(['2024-06-01', '2024-09-01', '2025-01-15', '2025-05-01',
                         '2025-09-15', '2026-01-01', '2026-06-01'], dtype='datetime64')
    bi_vals = [6.25, 6.00, 5.75, 5.75, 5.75, 6.00, 6.00]

    fig, ax1 = plt.subplots(figsize=(7.0, 3.4))
    ax1.plot(ihsg.index, ihsg.values, color=COL_BLUE, linewidth=1.5, label='IHSG')
    ax1.fill_between(ihsg.index, ihsg.values, ihsg.values.min(), alpha=0.10, color='#9e9e9e')

    ath_idx, ath_val = ihsg.idxmax(), ihsg.max()
    last_date, last_val = ihsg.index[-1], ihsg.iloc[-1]
    ax1.scatter([ath_idx, last_date], [ath_val, last_val], s=18, color=GS_DARK,
                zorder=5, clip_on=False)
    ax1.axvspan(ath_idx, last_date, alpha=0.30, color=COL_BEAR, label='Fase Bearish')

    ax1.set_ylabel('IHSG (Poin)', color=COL_BLUE)
    ax1.tick_params(axis='y', labelcolor=COL_BLUE)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=30, ha='right')
    ax1.spines['top'].set_visible(False)

    ax2 = ax1.twinx()
    ax2.step(bi_dates, bi_vals, color=COL_BI, linewidth=1.9, linestyle='--',
             where='post', label='BI Rate (%)')
    ax2.set_ylabel('BI 7-Day RRR (%)', color=COL_BI)
    ax2.set_ylim(4.0, 7.5)
    ax2.tick_params(axis='y', labelcolor=COL_BI)
    ax2.yaxis.set_major_formatter(plt.FormatStrFormatter('%.2f%%'))
    ax2.spines['top'].set_visible(False)

    l1, lb1 = ax1.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lb1 + lb2, loc='lower left', framealpha=0.85)
    ax1.grid(True, alpha=0.18, linestyle=':', linewidth=0.6)
    _save(fig, 'fig0_ihsg_trend.png', facecolor='white')


def fig6_normalized_prices(px):
    """Gambar 2 - harga 6 saham + IHSG ternormalisasi (basis = 100)."""
    norm = px / px.iloc[0] * 100.0
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    handles = {}
    for t, lab in zip(c.TICKERS, c.LABELS):
        h, = ax.plot(norm.index, norm[t].values, color=SERIES_COL[lab], linewidth=1.2, label=lab)
        handles[lab] = h
    h_ihsg, = ax.plot(norm.index, norm[c.MARKET].values, color=GS_BLACK,
                      linestyle='--', linewidth=1.8, label='IHSG')
    handles['IHSG'] = h_ihsg
    ax.axhline(100, color=GS_LIGHT, linewidth=0.8, zorder=1)

    ax.set_ylabel('Harga ternormalisasi (basis = 100)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    # urutan legend kolom-mayor (ncol=4) seperti paper
    order = ['ASII', 'ANTM', 'BMRI', 'IHSG', 'ADRO', 'MDKA', 'INDF']
    ax.legend([handles[k] for k in order], order, loc='upper left',
              ncol=4, framealpha=0.9, handletextpad=0.5, columnspacing=1.2)
    ax.grid(True, alpha=0.18, linewidth=0.6)
    _save(fig, 'fig6_normalized_prices.png')


def fig1_correlation_heatmap(corr):
    """Gambar 3 - heatmap korelasi return harian."""
    fig, ax = plt.subplots(figsize=(6.0, 5.0))
    sns.heatmap(corr, annot=True, fmt='.3f', cmap='Blues', vmin=0, vmax=1,
                xticklabels=c.LABELS, yticklabels=c.LABELS,
                linewidths=0.7, linecolor='white', square=True,
                cbar_kws={'shrink': 0.8, 'label': 'Koefisien Korelasi'},
                ax=ax, annot_kws={'size': 9, 'weight': 'semibold'})
    for text in ax.texts:
        text.set_color('white' if float(text.get_text()) >= 0.45 else '#111111')
    ax.tick_params(length=0)
    plt.setp(ax.get_yticklabels(), rotation=0)
    _save(fig, 'fig1_correlation_heatmap.png')


def fig2_dual_sml(capm_df, e_rm_empiris):
    """Gambar 5 - dual SML (teoritis vs empiris) + 3 zona."""
    betas = capm_df['Beta'].astype(float)
    actual = capm_df['Actual'].astype(float) * 100   # ke persen
    zones = capm_df['Zona']
    rf, e_t = c.RF, c.E_RM_TEORITIS

    brange = np.linspace(float(betas.min()) - 0.4, float(betas.max()) + 0.4, 300)
    sml_t = (rf + brange * (e_t - rf)) * 100
    sml_e = (rf + brange * (e_rm_empiris - rf)) * 100

    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    ax.plot(brange, sml_t, color=COL_BLUE, linestyle='-', linewidth=1.6,
            label=f'SML Teoritis: E(Rm) = {e_t*100:.1f}% p.a.')
    ax.plot(brange, sml_e, color=COL_RED, linestyle='--', linewidth=1.6,
            label=f'SML Empiris: E(Rm) = {e_rm_empiris*100:.2f}% p.a.')

    seen = set()
    for i, lab in enumerate(c.LABELS):
        z = zones.iloc[i]
        zlabel = None
        if z not in seen:
            zlabel = {'Zona I': 'Zona I (di atas kedua SML)',
                      'Zona II': 'Zona II (di antara SML)',
                      'Zona III': 'Zona III (di bawah kedua SML)'}[z]
            seen.add(z)
        ax.scatter(float(betas.iloc[i]), float(actual.iloc[i]), marker=ZONE_MARKER[z],
                   facecolor=ZONE_FACE[z], s=70, zorder=6, edgecolors='black',
                   linewidths=0.8, label=zlabel)
        ax.annotate(lab, (float(betas.iloc[i]), float(actual.iloc[i])),
                    textcoords='offset points', xytext=(7, 4), fontsize=8.5, color=GS_BLACK)

    ax.scatter(0, rf * 100, marker='D', facecolor=GS_DARK, s=42, zorder=7,
               edgecolors='black', linewidths=0.6, label=f'Rf = {rf*100:.2f}%')
    ax.scatter(1, e_t * 100, marker='D', facecolor=COL_BLUE, s=55, zorder=7,
               edgecolors='black', linewidths=0.6)
    ax.scatter(1, e_rm_empiris * 100, marker='D', facecolor=COL_RED, s=55, zorder=7,
               edgecolors='black', linewidths=0.6)
    ax.axhline(y=rf * 100, color=GS_LIGHT, linestyle=':', linewidth=0.9)

    ax.legend(fontsize=7.5, loc='upper left', framealpha=0.9, handletextpad=0.4)
    ax.set_xlabel(r'Beta ($\beta$) — Risiko Sistematis')
    ax.set_ylabel('Return Aktual Tahunan (%)')
    ax.grid(True, alpha=0.18, linewidth=0.6)
    _save(fig, 'fig2_dual_sml_plot.png')


def fig3_efficient_frontier(mu, Sigma):
    """Gambar 4 - efficient frontier LO vs UC + anotasi Delta-sigma."""
    lo_rets, lo_stds, _ = c.efficient_frontier(mu, Sigma, long_only=True)
    uc_rets, uc_stds, _ = c.efficient_frontier(mu, Sigma, long_only=False)
    w_g = c.gmvp_long_only(mu, Sigma)
    g_ret, g_std = c.port_perf(w_g, mu, Sigma)

    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    ax.plot([s * 100 for s in lo_stds], [r * 100 for r in lo_rets],
            color=COL_BLUE, linestyle='-', linewidth=1.8,
            label=r'Frontier Long-Only ($w_i \geq 0$)', zorder=3)
    ax.plot([s * 100 for s in uc_stds], [r * 100 for r in uc_rets],
            color=COL_RED, linestyle='--', linewidth=1.5,
            label='Frontier Unconstrained (short selling)', zorder=4)

    for i, lab in enumerate(c.LABELS):
        ind_std = float(np.sqrt(Sigma.iloc[i, i])) * 100
        ind_ret = float(mu.iloc[i]) * 100
        ax.scatter(ind_std, ind_ret, s=42, facecolor=GS_LIGHT, zorder=5,
                   edgecolors='black', linewidths=0.6)
        ax.annotate(lab, (ind_std, ind_ret), textcoords='offset points',
                    xytext=(6, 3), fontsize=8.5, color=GS_BLACK)

    ax.scatter(g_std * 100, g_ret * 100, marker='D', s=70, facecolor=GS_DARK, zorder=7,
               edgecolors='black', linewidths=0.7,
               label=f'GMVP: $\\sigma$={g_std*100:.2f}%, E(R)={g_ret*100:.2f}%')

    ax.set_xlabel('Risiko — Standar Deviasi Tahunan (%)')
    ax.set_ylabel('Expected Return Tahunan (%)')

    # Anotasi Delta-sigma di dekat target return 40%
    uc_sorted = sorted(zip(uc_rets, uc_stds))
    uc_r = np.array([x[0] for x in uc_sorted]); uc_s = np.array([x[1] for x in uc_sorted])
    lo_r = np.array(lo_rets); lo_s = np.array(lo_stds)
    mask = (lo_r >= uc_r.min()) & (lo_r <= uc_r.max())
    if mask.any():
        r_cand = lo_r[mask]; s_lo_c = lo_s[mask]
        s_uc_c = np.interp(r_cand, uc_r, uc_s)
        gaps = (s_lo_c - s_uc_c) * 100
        k = int(np.argmin(np.abs(r_cand - 0.40)))
        if gaps[k] > 0.10:
            ax.annotate('', xy=(s_lo_c[k] * 100, r_cand[k] * 100),
                        xytext=(s_uc_c[k] * 100, r_cand[k] * 100),
                        arrowprops=dict(arrowstyle='<->', color=GS_DARK, lw=1.4))
            ax.text((s_lo_c[k] + s_uc_c[k]) / 2 * 100, r_cand[k] * 100 + 1.2,
                    f'Δσ = {gaps[k]:.2f} pp\n(biaya larangan short)', ha='center',
                    fontsize=7.5, color=GS_DARK,
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                              alpha=0.9, edgecolor=GS_MID))

    ax.legend(fontsize=7.5, loc='lower right', framealpha=0.92, handletextpad=0.4)
    ax.grid(True, alpha=0.18, linewidth=0.6)
    _save(fig, 'fig3_efficient_frontier.png')


def fig5_oos_equity(R, Rm):
    """Gambar 6 - equity curve out-of-sample (basis = 100)."""
    oos, dates = c.oos_backtest(R, Rm)
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    styles = {'GMVP': (COL_BLUE, '-', 2.0), '1/N': ('#6baed6', '-', 1.5),
              'IHSG': (GS_MID, '--', 1.4)}
    for k in ['GMVP', '1/N', 'IHSG']:
        equity = 100.0 * np.cumprod(1 + np.array(oos[k]))
        col, ls, lw = styles[k]
        ax.plot(dates, equity, color=col, linestyle=ls, linewidth=lw, label=k)
    ax.axhline(100, color=GS_LIGHT, linewidth=0.8, zorder=1)

    ax.set_ylabel('Nilai portofolio (basis = 100)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    ax.legend(loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.18, linewidth=0.6)
    _save(fig, 'fig5_oos_equity.png')


def _save(fig, name, facecolor=None):
    path = os.path.join(OUTPUT_DIR, name)
    fig.tight_layout()
    fig.savefig(path, facecolor=facecolor) if facecolor else fig.savefig(path)
    plt.close(fig)
    print(f"    figur disimpan: {path}")


def main():
    px = c.load_prices()
    R = c.daily_returns(px)
    Rs, Rm = R[c.TICKERS], R[c.MARKET]
    mu, _ = c.annual_stats(Rs)
    Sigma, corr = c.cov_corr(Rs)
    capm_df, e_rm = c.compute_capm(Rs, Rm)
    capm_df = c.classify_zones(capm_df, e_rm)

    print("[figures] membuat 6 figur paper ke outputs/ ...")
    fig0_ihsg_trend(px)
    fig6_normalized_prices(px)
    fig1_correlation_heatmap(corr)
    fig2_dual_sml(capm_df, e_rm)
    fig3_efficient_frontier(mu, Sigma)
    fig5_oos_equity(Rs, Rm)
    print("[figures] selesai.")


if __name__ == '__main__':
    main()
