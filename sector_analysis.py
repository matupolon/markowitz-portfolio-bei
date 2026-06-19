# =============================================================================
# ANALISIS KINERJA 11 SEKTOR BEI — Periode Juni 2024 – Mei 2026
# Metode : Equal-weighted basket dari 3-5 saham terliquid per sektor (IDX80/LQ45)
# Output : tabel CSV + figure PNG untuk paper
# =============================================================================

import warnings
warnings.filterwarnings('ignore')
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import yfinance as yf
import pandas as pd
import numpy as np
import os

# ── Konfigurasi ──────────────────────────────────────────────────────────────
START_DATE   = '2024-06-03'
END_DATE     = '2026-05-30'
RF_ANNUAL    = 0.0575
TRADING_DAYS = 252
OUTPUT_DIR   = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Basket saham representatif per sektor (IDX80/LQ45, 3-5 saham terliquid) ─
# Setiap sektor direpresentasikan oleh saham dengan market cap & likuiditas
# tertinggi dalam kategori GICS/IDX yang setara.
SECTOR_BASKETS = {
    'IDXEnergy'  : ['ADRO.JK', 'PTBA.JK', 'ITMG.JK'],
    'IDXBasic'   : ['ANTM.JK', 'MDKA.JK', 'INCO.JK', 'TINS.JK'],
    'IDXIndust'  : ['ASII.JK', 'SMGR.JK', 'BRIS.JK'],
    'IDXNonCyc'  : ['INDF.JK', 'ICBP.JK', 'UNVR.JK'],
    'IDXCyclic'  : ['MAPI.JK', 'ACES.JK', 'ERAA.JK'],
    'IDXHealth'  : ['KLBF.JK', 'MIKA.JK', 'SIDO.JK'],
    'IDXFinance' : ['BMRI.JK', 'BBCA.JK', 'BBRI.JK', 'BBNI.JK'],
    'IDXPropert' : ['BSDE.JK', 'CTRA.JK', 'SMRA.JK'],
    'IDXTechno'  : ['GOTO.JK', 'EMTK.JK', 'DNET.JK'],
    'IDXInfra'   : ['TLKM.JK', 'JSMR.JK', 'EXCL.JK'],
    'IDXTrans'   : ['GIAA.JK', 'BIRD.JK', 'SMDR.JK'],
}

# Label display untuk tabel/gambar
SECTOR_LABELS = {
    'IDXEnergy'  : 'Energy',
    'IDXBasic'   : 'Basic Materials',
    'IDXIndust'  : 'Industrials',
    'IDXNonCyc'  : 'Consumer Non-Cyc.',
    'IDXCyclic'  : 'Consumer Cyc.',
    'IDXHealth'  : 'Healthcare',
    'IDXFinance' : 'Financials',
    'IDXPropert' : 'Property & RE',
    'IDXTechno'  : 'Technology',
    'IDXInfra'   : 'Infrastructure',
    'IDXTrans'   : 'Transportation',
}

# Saham pilihan paper → sektor
SELECTED_STOCKS = {
    'IDXEnergy'  : 'ADRO.JK',
    'IDXBasic'   : 'ANTM.JK, MDKA.JK',
    'IDXIndust'  : 'ASII.JK',
    'IDXNonCyc'  : 'INDF.JK',
    'IDXFinance' : 'BMRI.JK',
}

# ── Unduh semua saham sekaligus ───────────────────────────────────────────────
all_tickers = sorted({t for basket in SECTOR_BASKETS.values() for t in basket})
all_tickers += ['^JKSE']

print(f"Mengunduh {len(all_tickers)} ticker …")
raw = yf.download(all_tickers, start=START_DATE, end=END_DATE,
                  auto_adjust=True, progress=False)
prices_all  = raw['Close'].copy()
volumes_all = raw['Volume'].copy()

# IHSG terpisah
ihsg_price = prices_all['^JKSE'].dropna()
ihsg_ret   = ihsg_price.pct_change().dropna()

# ── Bangun sektor index (equal-weighted) dan hitung metrik ───────────────────
def compute_mdd(price_series):
    roll_max = price_series.cummax()
    return ((price_series - roll_max) / roll_max).min()

def compute_sharpe(ret_series, rf_daily):
    excess = ret_series - rf_daily
    sd = excess.std()
    if sd == 0 or np.isnan(sd):
        return np.nan
    return (excess.mean() / sd) * np.sqrt(TRADING_DAYS)

rf_daily = RF_ANNUAL / TRADING_DAYS

records = []
for sector_key, basket in SECTOR_BASKETS.items():
    # Ambil saham yang berhasil didownload
    avail = [t for t in basket if t in prices_all.columns and
             prices_all[t].dropna().shape[0] > 100]
    if not avail:
        print(f"  [!] {sector_key}: tidak ada data valid")
        continue

    # Equal-weighted: normalisasi harga ke 1 pada hari pertama bersama
    px = prices_all[avail].dropna(how='all')
    # Rebase ke 1 pada titik awal observasi bersama
    px = px.divide(px.iloc[0])
    sector_price = px.mean(axis=1)                  # equal-weighted index
    sector_ret   = sector_price.pct_change().dropna()

    # Volume tahunan: rata-rata harian × 252, dalam miliar IDR
    # (proxy: sum volume saham basket dalam unit lot)
    vol_basket = volumes_all[[t for t in avail if t in volumes_all.columns]].dropna(how='all')
    vol_annual  = vol_basket.mean().mean() * TRADING_DAYS / 1e9  # miliar unit

    # Return kumulatif periode penuh
    cumret = sector_price.iloc[-1] - 1

    # Sharpe & MDD
    sr  = compute_sharpe(sector_ret, rf_daily)
    mdd = compute_mdd(sector_price)

    records.append({
        'sector_key'       : sector_key,
        'Sektor'           : SECTOR_LABELS[sector_key],
        'Basket (n saham)' : f"{len(avail)} saham",
        'Return Kumulatif' : cumret,
        'Vol Tahunan (M lot)' : vol_annual * 1e3,   # tampilkan juta lot
        'Sharpe Ratio'     : sr,
        'MDD'              : mdd,
        'Saham Dipilih'    : SELECTED_STOCKS.get(sector_key, '—'),
    })
    print(f"  {SECTOR_LABELS[sector_key]:22s}  Ret={cumret*100:+7.2f}%  SR={sr:+6.3f}  MDD={mdd*100:6.2f}%  basket={avail}")

df = pd.DataFrame(records)
df_sorted = df.sort_values('Return Kumulatif', ascending=False).reset_index(drop=True)

# ── IHSG benchmark ────────────────────────────────────────────────────────────
ihsg_aligned = ihsg_price.loc[ihsg_price.index >= prices_all.dropna(how='all').index[0]]
ihsg_cumret  = (ihsg_aligned.iloc[-1] / ihsg_aligned.iloc[0]) - 1
ihsg_sr      = compute_sharpe(ihsg_ret.loc[ihsg_ret.index >= prices_all.dropna(how='all').index[0]], rf_daily)
ihsg_mdd     = compute_mdd(ihsg_aligned)

# ── Cetak tabel lengkap ───────────────────────────────────────────────────────
print("\n" + "="*80)
print("TABEL KINERJA SEKTOR BEI  |  Juni 2024 – Mei 2026  |  Rf = 5,75%/thn")
print("="*80)
print(f"{'Rank':<4} {'Sektor':<22} {'Kum. Ret':>10} {'Sharpe':>8} {'MDD':>8}  {'Saham Dipilih'}")
print("-"*80)
for i, row in df_sorted.iterrows():
    flag = " ◄" if row['Saham Dipilih'] != '—' else ""
    print(f"{i+1:<4} {row['Sektor']:<22} {row['Return Kumulatif']*100:>+9.2f}% "
          f"{row['Sharpe Ratio']:>8.4f} {row['MDD']*100:>7.2f}%  {row['Saham Dipilih']}{flag}")
print("-"*80)
print(f"{'':4} {'IHSG (benchmark)':<22} {ihsg_cumret*100:>+9.2f}%  "
      f"{ihsg_sr:>7.4f} {ihsg_mdd*100:>7.2f}%")

# ── Simpan CSV ────────────────────────────────────────────────────────────────
df_sorted.to_csv(os.path.join(OUTPUT_DIR, 'sector_metrics.csv'), index=False)
print(f"\nCSV → {OUTPUT_DIR}/sector_metrics.csv")

# ── Cetak baris LaTeX untuk copy-paste ───────────────────────────────────────
print("\n" + "="*80)
print("BARIS LaTeX UNTUK TABEL (copy siap pakai):")
print("="*80)
for i, row in df_sorted.iterrows():
    cr  = row['Return Kumulatif'] * 100
    sr  = row['Sharpe Ratio']
    mdd = abs(row['MDD'] * 100)
    saham = row['Saham Dipilih']
    bold_open  = r'\textbf{' if saham != '—' else ''
    bold_close = '}'         if saham != '—' else ''
    print(
        f"{bold_open}{row['Sektor']}{bold_close} & "
        f"{bold_open}{cr:+.2f}\\%{bold_close} & "
        f"{bold_open}{sr:.4f}{bold_close} & "
        f"{bold_open}{mdd:.2f}\\%{bold_close} & "
        f"{bold_open}{saham}{bold_close} \\\\"
    )
print(f"\\midrule")
print(f"IHSG & {ihsg_cumret*100:+.2f}\\% & {ihsg_sr:.4f} & {abs(ihsg_mdd*100):.2f}\\% & --- \\\\")
