"""Descriptive, auditable evidence. These checks never confer trading approval."""

import hashlib
import time

import numpy as np
import pandas as pd
from sklearn.base import clone

from .statistics import hac_t, ic_series


def fit_candidate(model, train, target, features):
    """Fit solely on the supplied past training rows; never fit on target data."""
    if train.empty or target.empty:
        raise ValueError("Training and prediction frames must be nonempty")
    if train.index.get_level_values("datetime").max() >= target.index.get_level_values("datetime").min():
        raise ValueError("Training must strictly precede prediction timestamps")
    fitted = clone(model)
    started = time.monotonic()
    fitted.fit(train[features], train.label)
    fit_seconds = time.monotonic() - started
    started = time.monotonic()
    prediction = pd.Series(fitted.predict(target[features]), index=target.index)
    inference_seconds = time.monotonic() - started
    fingerprint = hashlib.sha256(
        pd.util.hash_pandas_object(train[features + ["label"]], index=True).values.tobytes()
    ).hexdigest()
    return (
        prediction,
        fitted,
        {
            "fit_seconds": fit_seconds,
            "inference_seconds": inference_seconds,
            "training_frame_sha256": fingerprint,
            "training_rows": len(train),
        },
    )


def select_model(validation):
    """Selection accepts validation evidence only; all-unavailable scores fail."""
    available = {
        name: value for name, value in validation.items() if value is not None and np.isfinite(value)
    }
    if not available:
        raise ValueError("No model has a usable validation IC; do not select arbitrarily")
    return max(available, key=available.get)


def performance(portfolio):
    net = portfolio["return"] - portfolio.cost
    wealth = (1 + net).cumprod()
    annual = float(wealth.iloc[-1] ** (252 / len(net)) - 1)
    drawdown = float((wealth / wealth.cummax().clip(lower=1.0) - 1).min())
    sd = net.std(ddof=1)
    downside = float(np.sqrt(np.mean(np.minimum(net, 0.0) ** 2)))
    benchmark = float((1 + portfolio.bench).prod() - 1)
    return {
        "sessions": len(net),
        "total_return_net": float(wealth.iloc[-1] - 1),
        "annualized_return_net": annual,
        "annualized_volatility": float(sd * np.sqrt(252)) if len(net) > 1 else None,
        "max_drawdown": drawdown,
        "sharpe_zero_rf": float(net.mean() / sd * np.sqrt(252)) if sd > 0 else None,
        "sortino_zero_target": float(net.mean() / downside * np.sqrt(252)) if downside > 0 else None,
        "calmar": annual / abs(drawdown) if drawdown < 0 else None,
        "positive_session_fraction": float((net > 0).mean()),
        "benchmark_total_return": benchmark,
        "excess_return_difference": float(wealth.iloc[-1] - 1 - benchmark),
        "mean_daily_turnover": float(portfolio.turnover.mean()),
    }


def factor_evidence(frame, horizon=1):
    daily = ic_series(frame)
    spread = []
    for _, group in frame.dropna(subset=["prediction", "label"]).groupby(level="datetime"):
        if len(group) < 5 or group.prediction.nunique() < 2:
            continue
        group = group.sort_values("prediction", kind="stable")
        n = max(1, len(group) // 5)
        spread.append(float(group.label.iloc[-n:].mean() - group.label.iloc[:n].mean()))
    sd = daily.std(ddof=1)
    return {
        "rank_ic": float(daily.mean()) if len(daily) else None,
        "icir_unannualized": float(daily.mean() / sd) if sd > 0 else None,
        "ic_hac_t": hac_t(daily, lag=max(5, horizon)),
        "ic_sessions": len(daily),
        "gross_top_minus_bottom_quintile_label_spread": float(np.mean(spread)) if spread else None,
        "label_coverage": float(frame.label.notna().mean()),
    }


def fold_dispersion(folds):
    ics = [f["rank_ic"] for f in folds if f.get("rank_ic") is not None]
    returns = [f["total_return_net"] for f in folds if f.get("total_return_net") is not None]
    return {
        "folds": len(folds),
        "folds_with_ic": len(ics),
        "positive_ic_fold_fraction": sum(v > 0 for v in ics) / len(folds) if folds else None,
        "positive_ic_60pct_screen": len(folds) > 1
        and len(ics) == len(folds)
        and sum(v > 0 for v in ics) / len(folds) >= 0.6,
        "ic_min": min(ics) if ics else None,
        "ic_max": max(ics) if ics else None,
        "ic_std": float(np.std(ics, ddof=1)) if len(ics) > 1 else None,
        "return_min": min(returns) if returns else None,
        "return_max": max(returns) if returns else None,
        "candidate_status": "NOT_ASSESSED: independently dated regime evidence and broader research checks are required",
    }


def quality_panel(bars, calendar):
    missing, longest, zero = 0, 0, 0
    for _, group in bars.groupby("symbol"):
        expected = calendar[(calendar >= group.date.min()) & (calendar <= group.date.max())]
        missing += len(expected) - group.date.nunique()
        run = 0
        for value in group.set_index("date").close.reindex(expected).diff().eq(0):
            run = run + 1 if value else 0
            longest = max(longest, run)
        zero += int((group.volume == 0).sum())
    return {
        "scope": "Accepted input only; invalid/duplicate/nonpositive OHLC rows fail before research",
        "internal_missing_instrument_sessions": int(missing),
        "zero_volume_rows_including_benchmark": zero,
        "longest_unchanged_close_streak_sessions": longest,
        "listing_or_delisting_coverage_verified": False,
        "note": "Coverage between each supplied instrument's first and last bar cannot reveal missing delisted names",
    }


def validity_panel(synthetic, membership, assumed, evaluation, statistics):
    flags = []
    if synthetic:
        flags.append(
            {
                "severity": "INFO",
                "code": "SYNTHETIC",
                "message": "Fictional software test; no investment evidence",
            }
        )
    if not membership:
        flags.append(
            {
                "severity": "WARNING",
                "code": "FIXED_UNIVERSE",
                "message": "EXPLORATORY ONLY: supplied fixed cohort cannot establish historical index performance",
            }
        )
    elif assumed:
        flags.append(
            {
                "severity": "WARNING",
                "code": "ASSUMED_AVAILABILITY",
                "message": "Effective-date knowledge was assumed, not independently established",
            }
        )
    if evaluation != "walk-forward":
        flags.append(
            {"severity": "WARNING", "code": "SINGLE_HOLDOUT", "message": "No repeated out-of-sample folds"}
        )
    if statistics["terminal_writeoff"] > 0:
        flags.append(
            {
                "severity": "WARNING",
                "code": "TERMINAL_WRITEOFF",
                "message": "Unresolved holdings written off; settlement evidence is missing",
            }
        )
    flags.append(
        {
            "severity": "EXECUTION_BLOCKED",
            "code": "NO_LIVE_PATH",
            "message": "Research output is not approval or support for live orders",
        }
    )
    return {
        "status": "SYNTHETIC_ONLY" if synthetic else "EXPLORATORY_ONLY",
        "dated_membership_applied": bool(membership),
        "availability_assumed": bool(membership and assumed),
        "walk_forward": evaluation == "walk-forward",
        "label_boundary_purge": True,
        "external_trials_count": None,
        "prior_test_access": "UNKNOWN",
        "sector_marketcap_factor_exposure": "UNAVAILABLE: dated classifications not supplied",
        "flags": flags,
    }
