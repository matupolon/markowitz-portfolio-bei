"""
common.py - Mesin perhitungan bersama (single source of truth).

Semua skrip lain (figures.py, calculation.py) mengimpor fungsi dari sini,
sehingga perhitungan inti hanya ditulis SATU kali (DRY). Data diunduh sekali lalu
di-cache ke CSV (_prices_cache.csv) agar tidak mengunduh berulang antar-skrip.
"""
import os
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize
from scipy import stats

# ============================ KONFIGURASI ==============================
TICKERS       = ['ASII.JK', 'ADRO.JK', 'ANTM.JK', 'MDKA.JK', 'BMRI.JK', 'INDF.JK']
MARKET        = '^JKSE'
START, END    = '2024-06-01', '2026-06-01'
TRADING_DAYS  = 252
RF            = 0.0575                      # baseline BI Rate (risk-free)
RF_SCENARIOS  = [0.0450, 0.0575, 0.0700]   # retrospektif, baseline, stress
E_RM_TEORITIS = 0.10                       # benchmark pasar normal jangka panjang
CAPITAL       = 100_000_000                # modal awal Rp100 juta
TARGETS       = [0.20, 0.30, 0.40]         # target return utk biaya frontier
LABELS        = [t.replace('.JK', '') for t in TICKERS]
_CACHE        = os.path.join('data', 'prices_cache.csv')  # data ter-pin (reproduktibilitas)

# ============================ DATA (unduh sekali) ======================
def load_prices(use_cache=True):
    """Harga adjusted-close harian (6 saham + IHSG). Di-cache ke CSV."""
    if use_cache and os.path.exists(_CACHE):
        px = pd.read_csv(_CACHE, index_col=0, parse_dates=True)
    else:
        px = yf.download(TICKERS + [MARKET], start=START, end=END,
                         auto_adjust=True, progress=False)['Close'].dropna()
        px = px[TICKERS + [MARKET]]
        os.makedirs(os.path.dirname(_CACHE), exist_ok=True)
        px.to_csv(_CACHE)
    return px

def daily_returns(px):
    """Return harian (simple return)."""
    return px.pct_change().dropna()

# ============================ STATISTIK ================================
def annual_stats(R):
    """Return & volatilitas tahunan (Series, indeks ticker)."""
    return R.mean() * TRADING_DAYS, R.std() * np.sqrt(TRADING_DAYS)

def cov_corr(R):
    """Matriks kovarians tahunan (DataFrame) & korelasi (DataFrame)."""
    return R.cov() * TRADING_DAYS, R.corr()

# ============================ CAPM / DUAL SML ==========================
def compute_capm(R, Rm, rf=RF):
    """capm_df (Beta, E(Ri)E, Actual, R2 - semua desimal) & E(Rm) empiris."""
    e_rm = Rm.mean() * TRADING_DAYS
    rows = {}
    for t in R.columns:
        slope, _, rval, _, _ = stats.linregress(Rm.values, R[t].values)
        rows[t] = {'Beta': slope,
                   'E(Ri)E': rf + slope * (e_rm - rf),
                   'Actual': R[t].mean() * TRADING_DAYS,
                   'R2': rval ** 2}
    return pd.DataFrame(rows).T, e_rm

def classify_zones(capm_df, e_rm_empiris, rf=RF, e_rm_teoritis=E_RM_TEORITIS):
    """Tambahkan kolom 'Zona' (I/II/III) ke capm_df."""
    z = []
    for t in capm_df.index:
        b = float(capm_df.loc[t, 'Beta']); act = float(capm_df.loc[t, 'Actual'])
        et = rf + b * (e_rm_teoritis - rf)
        ee = rf + b * (e_rm_empiris  - rf)
        z.append('Zona I' if act > et else ('Zona III' if act < ee else 'Zona II'))
    out = capm_df.copy(); out['Zona'] = z
    return out

# ============================ PORTOFOLIO / GMVP ========================
def port_perf(w, mu, Sigma):
    """(E(Rp), sigma_p) tahunan untuk bobot w."""
    w = np.asarray(w, dtype=float)
    r = float(w @ np.asarray(mu))
    s = float(np.sqrt(max(w @ np.asarray(Sigma) @ w, 0.0)))
    return r, s

def min_var(mu, Sigma, target=None, long_only=True):
    """Bobot varians-minimum (SLSQP); opsional kendala target return & w>=0."""
    mu_v, S_v = np.asarray(mu), np.asarray(Sigma)
    n = len(mu_v)
    cons = [{'type': 'eq', 'fun': lambda w: w.sum() - 1.0}]
    if target is not None:
        cons.append({'type': 'eq', 'fun': lambda w, tr=target: w @ mu_v - tr})
    bnds = [(0.0, 1.0)] * n if long_only else [(-1.0, 1.0)] * n
    res = minimize(lambda w: w @ S_v @ w, np.repeat(1.0 / n, n), method='SLSQP',
                   bounds=bnds, constraints=cons, options={'ftol': 1e-12, 'maxiter': 2000})
    return res.x

def gmvp_long_only(mu, Sigma):
    """GMVP long-only (w>=0) via SLSQP."""
    return min_var(mu, Sigma, target=None, long_only=True)

def gmvp_unconstrained(Sigma):
    """GMVP unconstrained via solusi tutup Merton: w = inv(S).1 / (1'.inv(S).1)."""
    inv = np.linalg.inv(np.asarray(Sigma)); ones = np.ones(len(inv))
    return inv @ ones / (ones @ inv @ ones)

def metrics(w, mu, Sigma, beta, rf=RF):
    """dict: ret, sigma, beta_p, sharpe, treynor."""
    r, s = port_perf(w, mu, Sigma)
    bp = float(np.asarray(w) @ np.asarray(beta))
    return {'ret': r, 'sigma': s, 'beta': bp, 'sharpe': (r - rf) / s, 'treynor': (r - rf) / bp}

def delta_sigma(mu, Sigma, target):
    """Biaya kendala long-only di target tertentu: (sigmaLO%, sigmaUC%, dsig pp)."""
    s_lo = port_perf(min_var(mu, Sigma, target, True),  mu, Sigma)[1]
    s_uc = port_perf(min_var(mu, Sigma, target, False), mu, Sigma)[1]
    return s_lo * 100, s_uc * 100, (s_lo - s_uc) * 100

def efficient_frontier(mu, Sigma, long_only=True, n_points=150):
    """Kurva frontier: (rets, stds, weights) atas grid target return."""
    lo, hi = float(np.min(mu)) * 0.8, float(np.max(mu)) * 1.05
    rets, stds, ws = [], [], []
    for tgt in np.linspace(lo, hi, n_points):
        w = min_var(mu, Sigma, tgt, long_only)
        r, s = port_perf(w, mu, Sigma)
        rets.append(r); stds.append(s); ws.append(w)
    return rets, stds, ws

# ============================ OUT-OF-SAMPLE ============================
def oos_backtest(R, Rm, win=252, step=21):
    """Rolling-window OOS: GMVP-LO vs 1/N vs IHSG. (dict return harian, dates)."""
    Rv, Rmv = R.values, Rm.values
    T, n = Rv.shape
    def gmvp_cov(cov):
        cons = [{'type': 'eq', 'fun': lambda w: w.sum() - 1.0}]
        return minimize(lambda w: w @ cov @ w, np.repeat(1.0 / n, n), method='SLSQP',
                        bounds=[(0.0, 1.0)] * n, constraints=cons,
                        options={'ftol': 1e-12, 'maxiter': 1000}).x
    out = {'GMVP': [], '1/N': [], 'IHSG': []}; w_g = w_e = None
    for t in range(win, T):
        if (t - win) % step == 0:
            w_g = gmvp_cov(np.cov(Rv[t - win:t], rowvar=False, ddof=1))
            w_e = np.repeat(1.0 / n, n)
        out['GMVP'].append(Rv[t] @ w_g)
        out['1/N'].append(Rv[t] @ w_e)
        out['IHSG'].append(Rmv[t])
    return out, R.index[win:]

def oos_metrics(daily, rf=RF):
    """(ret%, vol%, sharpe, maxdd%) dari deret return harian OOS."""
    a = np.array(daily); ar = a.mean() * TRADING_DAYS; av = a.std(ddof=1) * np.sqrt(TRADING_DAYS)
    cum = np.cumprod(1 + a); peak = np.maximum.accumulate(cum)
    return ar * 100, av * 100, (ar - rf) / av, ((cum - peak) / peak).min() * 100
