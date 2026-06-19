"""
calculation.py - Cetak seluruh angka kunci paper (bukti perhitungan).

Semua perhitungan diambil dari common.py (satu sumber kebenaran). Skrip ini
hanya MENCETAK hasil; pembuatan grafik ditangani figures.py.
"""
import common as c

# ---- Ambil data & hitung (lewat common) ----
px = c.load_prices()
ret = c.daily_returns(px)
R, Rm = ret[c.TICKERS], ret[c.MARKET]
mu, sigma = c.annual_stats(R)
Sigma, corr = c.cov_corr(R)
capm_df, E_RM_EMP = c.compute_capm(R, Rm)
capm_df = c.classify_zones(capm_df, E_RM_EMP)
beta = capm_df['Beta'].values.astype(float)

w_lo = c.gmvp_long_only(mu, Sigma)
w_uc = c.gmvp_unconstrained(Sigma)
m_lo = c.metrics(w_lo, mu, Sigma, beta)
m_uc = c.metrics(w_uc, mu, Sigma, beta)

def baris(lab, *vals):
    print("  " + lab.ljust(10) + "".join(f"{v:>12}" for v in vals))

# ---- Laporan ----
print("\n=== KONDISI PASAR (IHSG) ===")
print(f"  E(Rm) empiris   : {E_RM_EMP*100:+.2f}%")
print(f"  ERP empiris     : {(E_RM_EMP-c.RF)*100:+.2f}%   (E(Rm) - Rf, Rf={c.RF*100:.2f}%)")

print("\n=== STATISTIK & CAPM / DUAL SML ===")
baris("Saham", "Beta", "Ret(%)", "Vol(%)", "E(Ri)E%", "R^2", "Zona")
for i, t in enumerate(c.LABELS):
    baris(t, f"{beta[i]:.3f}", f"{mu.iloc[i]*100:+.2f}", f"{sigma.iloc[i]*100:.2f}",
          f"{capm_df['E(Ri)E'].iloc[i]*100:+.2f}", f"{capm_df['R2'].iloc[i]:.3f}",
          capm_df['Zona'].iloc[i].replace('Zona ', ''))

print("\n=== KORELASI (ANTM-MDKA & ADRO-INDF dipakai di narasi) ===")
print(f"  ANTM-MDKA = {corr.loc['ANTM.JK','MDKA.JK']:.3f}   "
      f"ADRO-INDF = {corr.loc['ADRO.JK','INDF.JK']:.3f}")

print("\n=== GMVP: LONG-ONLY vs UNCONSTRAINED ===")
baris("Metrik", "Long-Only", "Unconstr.")
baris("E(Rp)%",  f"{m_lo['ret']*100:+.3f}",   f"{m_uc['ret']*100:+.3f}")
baris("sigma%",  f"{m_lo['sigma']*100:.3f}",  f"{m_uc['sigma']*100:.3f}")
baris("Sharpe",  f"{m_lo['sharpe']:.4f}",     f"{m_uc['sharpe']:.4f}")
baris("Treynor", f"{m_lo['treynor']:.4f}",    f"{m_uc['treynor']:.4f}")
baris("Beta_p",  f"{m_lo['beta']:.4f}",       f"{m_uc['beta']:.4f}")
baris("MDKA w%", f"{w_lo[3]*100:.2f}",        f"{w_uc[3]*100:.2f}")
print(f"  Break-even Rf* = {m_lo['ret']*100:.2f}%")

print("\n=== ALOKASI GMVP LONG-ONLY (Rp100.000.000) ===")
for i, t in enumerate(c.LABELS):
    print(f"  {t:<6} {w_lo[i]*100:6.2f}%   Rp {int(round(w_lo[i]*c.CAPITAL)):>12,}")

print("\n=== BIAYA KENDALA LONG-ONLY (Delta-sigma) ===")
baris("Target", "sigmaLO%", "sigmaUC%", "Dsig(pp)")
baris("GMVP", f"{m_lo['sigma']*100:.2f}", f"{m_uc['sigma']*100:.2f}",
      f"{(m_lo['sigma']-m_uc['sigma'])*100:.2f}")
for tr in c.TARGETS:
    lo, uc, d = c.delta_sigma(mu, Sigma, tr)
    baris(f"{int(tr*100)}%", f"{lo:.2f}", f"{uc:.2f}", f"{d:.2f}")

print("\n=== SENSITIVITAS BI RATE (bobot GMVP-LO tetap) ===")
baris("Rf(%)", "Sharpe", "Treynor")
for rf in c.RF_SCENARIOS:
    m = c.metrics(w_lo, mu, Sigma, beta, rf)
    baris(f"{rf*100:.2f}", f"{m['sharpe']:.4f}", f"{m['treynor']:.4f}")
print(f"  d(Sharpe)/d(Rf) = -1/sigma_p = {-1/m_lo['sigma']:.2f}")

oos, oos_dates = c.oos_backtest(R, Rm)
print(f"\n=== VALIDASI OUT-OF-SAMPLE ({oos_dates[0].date()} s/d {oos_dates[-1].date()}) ===")
baris("Strategi", "Ret(%)", "Vol(%)", "Sharpe", "MDD(%)")
for k in ['GMVP', '1/N', 'IHSG']:
    ar, av, sh, mdd = c.oos_metrics(oos[k])
    baris(k, f"{ar:+.2f}", f"{av:.2f}", f"{sh:.3f}", f"{mdd:.2f}")
print()
