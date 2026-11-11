"""Seeded, bounded diagnostics; resampling is not proof of an investable edge."""

import numpy as np
import pandas as pd


def ic_series(frame):
    result = {}
    for day, group in frame.dropna(subset=["prediction", "label"]).groupby(level="datetime"):
        if len(group) >= 3 and group.prediction.nunique() > 1 and group.label.nunique() > 1:
            result[day] = group.prediction.corr(group.label, method="spearman")
    return pd.Series(result, dtype=float)


def hac_t(values, lag=5):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 10:
        return None
    centered = x - x.mean()
    variance = np.dot(centered, centered) / len(x)
    for k in range(1, min(lag, len(x) - 1) + 1):
        variance += 2 * (1 - k / (lag + 1)) * np.dot(centered[k:], centered[:-k]) / len(x)
    return float(x.mean() / np.sqrt(variance / len(x))) if variance > 0 else None


def interval(returns, samples=500, block=5, seed=17):
    x = np.asarray(returns, dtype=float)
    rng = np.random.default_rng(seed)
    estimates = []
    annual, sharpes, drawdowns = [], [], []
    for _ in range(samples):
        starts = rng.integers(0, len(x), size=int(np.ceil(len(x) / block)))
        ix = np.concatenate([(start + np.arange(block)) % len(x) for start in starts])[: len(x)]
        sampled = x[ix]
        wealth = np.cumprod(1 + sampled)
        estimates.append(wealth[-1] - 1)
        annual.append(wealth[-1] ** (252 / len(x)) - 1)
        vol = sampled.std(ddof=1)
        if vol > 0:
            sharpes.append(sampled.mean() / vol * np.sqrt(252))
        drawdowns.append(np.min(wealth / np.maximum.accumulate(np.r_[1.0, wealth])[1:] - 1))
    lo, hi = np.quantile(estimates, [0.025, 0.975])
    return {
        "low": float(lo),
        "high": float(hi),
        "metric_intervals": {
            name: [float(v) for v in np.quantile(values, [0.025, 0.975])] if values else None
            for name, values in (
                ("total_return_net", estimates),
                ("annualized_return_net", annual),
                ("sharpe_zero_rf", sharpes),
                ("max_drawdown", drawdowns),
            )
        },
        "samples": samples,
        "block_sessions": block,
        "method": "95% circular moving-block percentile interval, total net return",
    }


def multiple_model_check(frames, draws=199, seed=31, block=5):
    daily = pd.concat({name: ic_series(frame) for name, frame in frames.items()}, axis=1).dropna()
    if len(daily) < 10:
        return {"p_value": None, "reason": "Insufficient common IC observations"}
    values = daily.to_numpy()
    observed = max(hac_t(values[:, j]) or 0.0 for j in range(values.shape[1]))
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(draws):
        signs = np.repeat(rng.choice([-1, 1], size=int(np.ceil(len(values) / block))), block)[: len(values)]
        best = max(hac_t(values[:, j] * signs) or 0.0 for j in range(values.shape[1]))
        hits += best >= observed
    return {
        "p_value": (hits + 1) / (draws + 1),
        "models": len(frames),
        "draws": draws,
        "method": "One-sided block sign-flip max HAC-t of daily rank IC; assumes block sign symmetry; covers only these models",
    }


def paired_return_interval(strategy, baseline, samples=500, block=5, seed=43):
    """Resample matched dates together; difference of compounded returns, not compounded spread."""
    if not strategy.index.equals(baseline.index):
        raise ValueError("Paired return dates must match exactly")
    values = np.column_stack([strategy.to_numpy(), baseline.to_numpy()])
    if len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("Paired interval requires at least two finite matched sessions")
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(samples):
        starts = rng.integers(0, len(values), size=int(np.ceil(len(values) / block)))
        ix = np.concatenate([(start + np.arange(block)) % len(values) for start in starts])[: len(values)]
        returns = np.prod(1 + values[ix], axis=0) - 1
        estimates.append(returns[0] - returns[1])
    point = np.prod(1 + values, axis=0) - 1
    low, high = np.quantile(estimates, [0.025, 0.975])
    return {
        "difference": float(point[0] - point[1]),
        "low": float(low),
        "high": float(high),
        "samples": samples,
        "block_sessions": block,
        "seed": seed,
        "method": "95% paired circular moving-block percentile interval of total net return difference; conditional on observed paths, not refitted models",
    }
