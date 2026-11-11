"""Fixed chronological evaluation using Qlib expressions and portfolio execution."""

import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .data import digest, read_bars, write_qlib
from .evidence import (
    factor_evidence,
    fit_candidate,
    fold_dispersion,
    performance,
    quality_panel,
    select_model,
    validity_panel,
)
from .report import render
from .resources import configure, timeout_seconds

FEATURES = {
    "momentum5": "$close/Ref($close,5)-1",
    "momentum20": "$close/Ref($close,20)-1",
    "volatility20": "Std($close/Ref($close,1)-1,20)",
    "range": "($high-$low)/$close",
    "volume_ratio": "$volume/Mean($volume,20)",
}
LABEL = "Ref($open,-2)/Ref($open,-1)-1"


def split_panel(panel, calendar, horizon=1):
    """Purge labels touching the next segment; no fitted preprocessing crosses boundaries."""
    dates = pd.DatetimeIndex(calendar)
    if len(dates) < 150:
        raise ValueError("At least 150 sessions required for this research recipe")
    validation_start, test_start = dates[int(len(dates) * 0.6)], dates[int(len(dates) * 0.8)]
    end_map = dict(zip(dates[: -(horizon + 1)], dates[horizon + 1 :]))
    timestamp = panel.index.get_level_values("datetime")
    label_end = pd.DatetimeIndex(timestamp.map(end_map))
    train = (timestamp < validation_start) & (label_end < validation_start)
    valid = (timestamp >= validation_start) & (timestamp < test_start) & (label_end < test_start)
    test = (timestamp >= test_start) & label_end.notna()
    return {"train": panel.loc[train], "valid": panel.loc[valid], "test": panel.loc[test]}, {
        "validation_start": str(validation_start.date()),
        "test_signal_start": str(test_start.date()),
        "label": f"open[t+{horizon + 1}] / open[t+1] - 1",
        "purge": "label_end strictly before next segment",
    }


def rank_ic(frame):
    values = []
    for _, group in frame.groupby(level="datetime"):
        if len(group) >= 3 and group.prediction.nunique() > 1 and group.label.nunique() > 1:
            values.append(float(group.prediction.corr(group.label, method="spearman")))
    return float(np.mean(values)) if values else None


def run(
    source,
    output,
    mode="essential",
    benchmark="BENCH",
    synthetic=False,
    calendar_path=None,
    buy_cost=0.001,
    sell_cost=0.0015,
    topk=5,
    capital=1_000_000,
    membership=None,
    index="Nifty500",
    expected_size=None,
    assume_membership_known=False,
    rebalance="daily",
    hold_buffer=0,
    turnover_limit=1.0,
    min_turnover=0.0,
    participation=1.0,
    impact_bps=0.0,
    terminal_policy="error",
    horizon=1,
    feature_set="compact",
    evaluation="holdout",
    train_years=3,
    valid_years=1,
    open_final=False,
    null_draws=19,
    cost_model="proportional",
    broker="zero",
    cost_before_coverage="error",
    timeout_hours=None,
):
    started = time.monotonic()
    profile, workers = configure(mode)
    if not all(math.isfinite(v) for v in [buy_cost, sell_cost, topk, capital]):
        raise ValueError("Costs, count and capital must be finite")
    if not (0 <= buy_cost < 0.1 and 0 <= sell_cost < 0.1) or topk < 1 or capital <= 0:
        raise ValueError("Invalid costs, position count, or capital")
    df = read_bars(source, profile)
    if cost_model not in ("india", "proportional"):
        raise ValueError("Unknown cost model")
    if cost_before_coverage not in ("error", "proportional"):
        raise ValueError("Unknown pre-coverage cost policy")
    wall_clock_budget = timeout_seconds(mode, timeout_hours)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "running", "mode": mode, "synthetic": synthetic, "source_sha256": digest(source)}
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    def progress(stage, **details):
        record = {"stage": stage, "elapsed_seconds": round(time.monotonic() - started, 2), **details}
        print("[indian-quant] " + json.dumps(record), file=sys.stderr, flush=True)
        temporary = output / "progress.json.tmp"
        temporary.write_text(json.dumps(record, indent=2))
        temporary.replace(output / "progress.json")

    progress("input_validated", rows=len(df), historical_instruments=df.symbol.nunique())
    if calendar_path:
        calendar = pd.DatetimeIndex(pd.to_datetime(Path(calendar_path).read_text().splitlines()))
    elif synthetic:
        calendar = pd.DatetimeIndex(sorted(df.date.unique()))
    else:
        raise ValueError("Real research requires --calendar with independently verified NSE sessions")
    if calendar.has_duplicates or not calendar.is_monotonic_increasing:
        raise ValueError("Calendar must be unique and sorted")
    if not df.date.isin(calendar).all():
        raise ValueError("Bars contain sessions outside the supplied calendar")
    if (
        not (0 < turnover_limit <= 2 and 0 < participation <= 1)
        or min_turnover < 0
        or not 0 <= impact_bps <= 1000
    ):
        raise ValueError("Invalid turnover, participation, liquidity or impact settings")
    if hold_buffer < 0 or horizon not in (1, 5, 20) or not 9 <= null_draws <= 999:
        raise ValueError("Invalid buffer, horizon or null simulation budget")
    if rebalance not in ("daily", "weekly", "monthly") or terminal_policy not in ("error", "writeoff"):
        raise ValueError("Invalid execution policy")
    eligible, intervals = None, []
    if membership:
        from .membership import eligibility

        eligible, intervals = eligibility(membership, index, calendar, expected_size, assume_membership_known)
    symbols = sorted(set(df.symbol) - {benchmark})
    if benchmark not in set(df.symbol) or len(symbols) < 3 or topk > len(symbols):
        raise ValueError("Provide benchmark plus at least 3 equities, with topk <= equity count")
    from indian_trader.core import suspect_jumps

    suspected_actions = suspect_jumps(
        {
            "symbol": row.symbol,
            "timestamp": row.date.strftime("%Y-%m-%dT09:15:00+05:30"),
            "open": row.open,
            "close": row.close,
        }
        for row in df.itertuples(index=False)
    )
    (output / "suspected_actions.json").write_text(json.dumps(suspected_actions, indent=2))
    manifest["suspected_action_count"] = len(suspected_actions)
    provider = write_qlib(df, output / "qlib", calendar)
    if intervals:
        (provider / "instruments" / "historical.txt").write_text(
            "".join(f"{symbol.lower()}\t{start.date()}\t{end.date()}\n" for symbol, start, end in intervals)
        )
    import qlib
    from qlib.data import D

    qlib.init(
        provider_uri=str(provider),
        region="us",
        kernels=workers,
        expression_cache=None,
        dataset_cache=None,
        redis_port=-1,
        logging_level=30,
    )
    # Region is a compatibility setting, not an assertion of US market rules.
    features = dict(FEATURES)
    if feature_set == "alpha158":
        from qlib.contrib.data.loader import Alpha158DL

        expressions, names = Alpha158DL.get_feature_config()
        features = dict(zip(names, expressions))
    label = f"Ref($open,-{horizon + 1})/Ref($open,-1)-1"
    progress("qlib_features", feature_set=feature_set, instruments=len(symbols))
    panel = D.features(
        symbols, list(features.values()) + [label], start_time=calendar[0], end_time=calendar[-1]
    )
    panel.columns = [*features, "label"]
    panel = panel.loc[
        panel.index.get_level_values("datetime") >= calendar[60 if feature_set == "alpha158" else 20]
    ]
    # Future outcome availability MUST NOT decide which stocks can be predicted.
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["ROC20"] if feature_set == "alpha158" else list(features)
    )
    if eligible:
        panel = panel.loc[[symbol.upper() in eligible(day) for symbol, day in panel.index]]
    splits, boundaries = split_panel(panel, calendar, horizon)
    if any(len(part.dropna(subset=["label"])) < 20 for part in splits.values()):
        raise ValueError("Too few complete observations in a chronological segment")
    from lightgbm import LGBMRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    candidates = {
        "momentum": None,
        "ridge": make_pipeline(
            SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), Ridge(alpha=10.0)
        ),
        "lightgbm": LGBMRegressor(
            n_estimators=60,
            max_depth=3,
            num_leaves=7,
            learning_rate=0.03,
            n_jobs=workers,
            random_state=17,
            verbosity=-1,
        ),
    }
    folds = [(splits, boundaries)]
    if evaluation == "walk-forward":
        if train_years < 1 or valid_years < 1:
            raise ValueError("Training and validation years must be positive")
        folds = []
        years = sorted(set(calendar.year))
        for year in years[train_years + valid_years :]:
            if year == years[-1] and not open_final:
                continue
            stamp = panel.index.get_level_values("datetime")
            train_start = pd.Timestamp(year=year - valid_years - train_years, month=1, day=1)
            val_start = pd.Timestamp(year=year - valid_years, month=1, day=1)
            test_start = pd.Timestamp(year=year, month=1, day=1)
            end_map = dict(zip(calendar[: -(horizon + 1)], calendar[horizon + 1 :]))
            label_end = pd.DatetimeIndex(stamp.map(end_map))
            split = {
                "train": panel.loc[(stamp >= train_start) & (label_end < val_start)],
                "valid": panel.loc[(stamp >= val_start) & (stamp < test_start) & (label_end < test_start)],
                "test": panel.loc[(stamp.year == year) & (label_end.year == year)],
            }
            if all(len(x.dropna(subset=["label"])) >= 20 for x in split.values()):
                folds.append(
                    (
                        split,
                        {
                            "test_signal_start": str(test_start.date()),
                            "validation_start": str(val_start.date()),
                        },
                    )
                )
        if not folds:
            raise ValueError(
                "No usable walk-forward folds; supply more history (last year stays closed by default)"
            )
    elif evaluation != "holdout":
        raise ValueError("Unknown evaluation")
    from .cost_policy import coverage

    first_signal = min(split["test"].index.get_level_values("datetime").min() for split, _ in folds)
    last_signal = max(split["test"].index.get_level_values("datetime").max() for split, _ in folds)
    cost_dates = calendar[calendar.get_loc(first_signal) + 1 : calendar.get_loc(last_signal) + 2]
    fee_coverage = coverage(cost_dates, cost_model, cost_before_coverage, buy_cost, sell_cost)
    boundaries = {**boundaries, **folds[0][1]}
    protocol = {
        "schema_version": 2,
        "timeout_seconds": wall_clock_budget,
        "cost_before_coverage": cost_before_coverage,
        "registered_at": datetime.now(UTC).isoformat(),
        "registration_scope": "Before fitting in this run; not proof of registration before data inspection",
        "hypothesis_id": output.name,
        "primary_metric": "validation mean daily rank IC",
        "candidate_models": list(candidates),
        "selection_rule": "maximum available validation rank IC; test results excluded",
        "external_trials_count": None,
        "feature_set_sha256": hashlib.sha256(json.dumps(features, sort_keys=True).encode()).hexdigest(),
        "evaluation": evaluation,
        "horizon": horizon,
        "features": feature_set,
        "rebalance": rebalance,
        "execution": {
            "capital": capital,
            "topk": topk,
            "hold_buffer": hold_buffer,
            "turnover_limit": turnover_limit,
            "min_turnover": min_turnover,
            "participation": participation,
            "impact_bps": impact_bps,
            "cost_model": cost_model,
            "broker": broker,
            "buy_cost": buy_cost,
            "sell_cost": sell_cost,
            "terminal_policy": terminal_policy,
        },
        "null_draws": null_draws,
        "seed": 17,
        "folds": [bound for _, bound in folds],
        "last_year_closed": evaluation == "walk-forward" and not open_final,
        "source_sha256": digest(source),
        "membership_sha256": digest(membership) if membership else None,
    }
    (output / "protocol.json").write_text(json.dumps(protocol, indent=2))
    predictions, validation, test_scores, selected_parts, fold_results = {}, {}, {}, [], []
    model_parts = {name: [] for name in candidates}
    for fold_number, (split, bound) in enumerate(folds, start=1):
        progress("fit_fold", fold=fold_number, folds=len(folds))
        train = split["train"].dropna(subset=["label"])
        validation, model_evidence = {}, {}
        target = pd.concat([split["valid"], split["test"]]).sort_index()
        for name, model in candidates.items():
            if model is None:
                # Alpha158 does not use the compact feature names.
                key = "momentum20" if "momentum20" in panel else "ROC20"
                prediction = target[key] * (1 if key == "momentum20" else -1)
                model_evidence[name] = {"fit_seconds": 0.0, "inference_seconds": 0.0, "fitted": False}
            else:
                prediction, _, model_evidence[name] = fit_candidate(model, train, target, list(features))
            predictions[name] = prediction
            validation[name] = rank_ic(split["valid"].assign(prediction=prediction).dropna(subset=["label"]))
            model_parts[name].append(split["test"].assign(prediction=prediction))
        selected = select_model(validation)
        selected_parts.append(split["test"].assign(prediction=predictions[selected]))
        fold_results.append(
            {
                **bound,
                "selected_model": selected,
                "validation_rank_ic": validation,
                "model_evidence": model_evidence,
            }
        )
    progress("models_complete", folds=len(folds))
    test = pd.concat(selected_parts).sort_index()
    model_frames = {name: pd.concat(parts).sort_index() for name, parts in model_parts.items()}
    test_scores = {name: rank_ic(frame.dropna(subset=["label"])) for name, frame in model_frames.items()}
    test.to_csv(output / "predictions.csv")
    test_dates = sorted(test.index.get_level_values("datetime").unique())
    start = calendar[calendar.get_loc(test_dates[0]) + 1]
    end = calendar[calendar.get_loc(test_dates[-1]) + 1]
    dates = calendar[(calendar >= start) & (calendar <= end)]
    from .execution import DEPLOYMENT_TARGET, prepare_market, simulate
    from .statistics import hac_t, ic_series, interval, multiple_model_check, paired_return_interval
    from .trade_audit import exposure_warning, round_trips, summarize

    # Qlib normalizes instrument identifiers to lowercase; source symbols are canonical uppercase.
    def canonical(signal):
        signal = signal.copy()
        signal.index = pd.MultiIndex.from_tuples(
            [(s.upper(), d) for s, d in signal.index], names=signal.index.names
        )
        return signal

    progress("prepare_market", valuation_sessions=len(dates))
    prepared = prepare_market(df, dates, benchmark, calendar)
    execution = {
        "bars": df,
        "prepared": prepared,
        "cost_before_coverage": cost_before_coverage,
        "full_calendar": calendar,
        "dates": dates,
        "benchmark": benchmark,
        "capital": capital,
        "topk": topk,
        "buy_cost": buy_cost,
        "sell_cost": sell_cost,
        "rebalance": rebalance,
        "hold_buffer": hold_buffer,
        "turnover_limit": turnover_limit,
        "min_turnover": min_turnover,
        "participation": participation,
        "impact_bps": impact_bps,
        "eligible": eligible,
        "terminal_policy": terminal_policy,
        "cost_model": cost_model,
        "broker": broker,
    }
    progress("selected_portfolio")
    portfolio, fills = simulate(signals=canonical(test.prediction), **execution)
    portfolio.to_csv(output / "portfolio.csv")
    fills.to_csv(output / "fills.csv", index=False)
    trades = round_trips(fills)
    trades.to_csv(output / "trades.csv", index=False)
    trade_summary = summarize(trades)
    if not np.isclose(trade_summary["net_pnl"], portfolio.equity.iloc[-1] - capital, rtol=1e-9, atol=1e-5):
        raise ValueError("Trade P&L does not reconcile with final portfolio equity")
    progress("equal_weight_baseline")
    baseline, _ = simulate(signals=canonical(test.prediction), equal_weight=True, **execution)
    baseline.to_csv(output / "equal_weight.csv")
    progress("momentum_baselines")
    momentum, _ = simulate(signals=canonical(model_frames["momentum"].prediction), **execution)
    momentum.to_csv(output / "momentum.csv")
    slow_momentum, _ = simulate(
        signals=canonical(model_frames["momentum"].prediction), **{**execution, "rebalance": "monthly"}
    )
    slow_momentum.to_csv(output / "momentum_monthly.csv")
    # Fold attribution uses one continuous account; no artificial annual liquidation.
    starts = [
        calendar[calendar.get_loc(part.index.get_level_values("datetime").min()) + 1]
        for part in selected_parts
    ]
    for i, (part, record) in enumerate(zip(selected_parts, fold_results)):
        stop = starts[i + 1] if i + 1 < len(starts) else dates[-1] + pd.Timedelta(days=1)
        segment = portfolio.loc[(portfolio.index >= starts[i]) & (portfolio.index < stop)]
        record.update(factor_evidence(part, horizon))
        record.update(performance(segment))
        record.update(
            valuation_start=str(segment.index.min().date()),
            valuation_end=str(segment.index.max().date()),
            attribution="Continuous account segment; holdings can cross fold boundaries; final exit only at study end",
        )
    (output / "folds.json").write_text(json.dumps(fold_results, indent=2, allow_nan=False))
    pd.DataFrame(
        [{k: v for k, v in record.items() if not isinstance(v, dict)} for record in fold_results]
    ).to_csv(output / "folds.csv", index=False)
    rng = np.random.default_rng(17)
    null_returns = []
    for draw in range(null_draws):
        progress("shuffled_signals", completed=draw, total=null_draws)
        shuffled = test.prediction.groupby(level="datetime", group_keys=False).transform(
            lambda x: rng.permutation(x.to_numpy())
        )
        null_portfolio, _ = simulate(signals=canonical(shuffled), **execution)
        null_returns.append(float(null_portfolio.equity.iloc[-1] / capital - 1))
    progress("shuffled_signals", completed=null_draws, total=null_draws)
    daily_ic = ic_series(test)
    daily_ic.rename("rank_ic").to_csv(output / "ic.csv")
    deciles = test.dropna(subset=["label"]).copy()
    deciles["decile"] = deciles.groupby(level="datetime").prediction.transform(
        lambda x: np.ceil(x.rank(method="average", pct=True) * 10).astype(int)
    )
    deciles.groupby("decile").label.agg(["mean", "count"]).to_csv(output / "deciles.csv")
    stress = {}
    for multiplier in (1, 2, 3, 5, 10):
        progress("cost_stress", multiplier=multiplier)
        stressed, _ = simulate(
            signals=canonical(test.prediction),
            **{
                **execution,
                "buy_cost": buy_cost * multiplier,
                "sell_cost": sell_cost * multiplier,
                "impact_bps": impact_bps * multiplier,
                "cost_multiplier": multiplier,
            },
        )
        stress[str(multiplier)] = float(stressed.equity.iloc[-1] / capital - 1)
    net = portfolio["return"] - portfolio["cost"]
    wealth = (1 + net).cumprod()
    peaks = wealth.cummax().clip(lower=1.0)
    total = float(wealth.iloc[-1] - 1)
    volatility = float(net.std(ddof=1))
    metrics = {
        "total_return_net": total,
        "annualized_return_net": float((1 + total) ** (252 / len(net)) - 1),
        "max_drawdown": float((wealth / peaks - 1).min()),
        "sharpe_zero_rf": float(net.mean() / volatility * np.sqrt(252)) if volatility else None,
        "benchmark_total_return": float((1 + portfolio.bench).prod() - 1),
        "mean_daily_turnover": float(portfolio.turnover.mean()),
        "sum_daily_cost_ratios": float(portfolio.cost.sum()),
        "test_sessions": len(net),
    }
    comparison = paired_return_interval(net, baseline["return"] - baseline.cost, block=max(5, horizon))
    deployment_warning = exposure_warning(portfolio, DEPLOYMENT_TARGET)
    statistics = {
        "selected_minus_equal_weight": comparison,
        "trade_summary": trade_summary,
        "deployment_target": DEPLOYMENT_TARGET,
        "signal_availability": {
            "yearly_eligible_without_signal": {
                str(year): int(part.eligible_without_signal.sum())
                for year, part in portfolio.groupby(portfolio.index.year)
            },
            "note": "Counted on rebalance sessions: execution-date members lacking a non-null score from the preceding session. Causes can include feature warmup/missing required inputs, membership becoming effective after the signal date, or no prediction on that date. This count alone does not identify the cause; it is not a count of unique stocks or missing future labels.",
        },
        "net_return_interval": interval(net, block=max(5, horizon)),
        "rank_ic_hac_t": hac_t(daily_ic, lag=max(5, horizon)),
        "label_coverage": float(test.label.notna().mean()),
        "shuffled_signal": {
            "draws": null_draws,
            "seed": 17,
            "median_net_return": float(np.median(null_returns)),
            "p_value": (1 + sum(x >= total for x in null_returns)) / (null_draws + 1),
        },
        "multiple_model_check": multiple_model_check(model_frames, block=max(5, horizon)),
        "execution_constraints": {
            "totals": {
                column: float(portfolio[column].sum())
                for column in portfolio.columns
                if column.startswith("buy_")
                or column in ("filtered_liquidity", "filtered_untradable", "eligible_without_signal")
            },
            "note": "Unfilled buy value attributed sequentially to turnover, participation, then cash/fees. Filter counts are candidate-session counts, not currency or proof of causality. Weekly/monthly partial buys are retried only on a later scheduled rebalance; positions are not automatically topped up each intervening day.",
        },
        "fold_dispersion": fold_dispersion(fold_results),
        "momentum_net_return": float(momentum.equity.iloc[-1] / capital - 1),
        "monthly_momentum_net_return": float(slow_momentum.equity.iloc[-1] / capital - 1),
        "selected_minus_momentum_return": total - float(momentum.equity.iloc[-1] / capital - 1),
        "performance_extended": performance(portfolio),
        "equal_weight_net_return": float(baseline.equity.iloc[-1] / capital - 1),
        "cost_stress_net_returns": stress,
        "first_tested_nonpositive_cost_multiplier": next((int(k) for k, v in stress.items() if v <= 0), None),
        "mean_exposure": float(portfolio.exposure.mean()),
        "stale_holding_sessions": int((portfolio.stale_holdings > 0).sum()),
        "terminal_writeoff": float(portfolio.writeoff.sum()),
        "fees_and_impact": float((portfolio.fees + portfolio.impact).sum()),
        "yearly_net_returns": {
            str(year): float((1 + part).prod() - 1) for year, part in net.groupby(net.index.year)
        },
        "interpretation": "Synthetic prices have no designed alpha; apparent success is not evidence of an edge."
        if synthetic
        else "Resampling diagnostics are conditional on supplied data and assumptions, not probability of future profit.",
    }
    gross_profit = capital * total + statistics["fees_and_impact"]
    statistics["cost_share_of_gross_profit"] = (
        statistics["fees_and_impact"] / gross_profit if gross_profit > 0 else None
    )
    statistics["consistent_with_chance"] = bool(
        synthetic
        or statistics["shuffled_signal"]["p_value"] > 0.05
        or statistics["net_return_interval"]["low"] <= 0
    )
    try:
        revision = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        )
        dirty = bool(
            subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL).strip()
        )
    except (OSError, subprocess.CalledProcessError):
        revision = "unknown"
        dirty = None
    manifest.update(
        {
            "status": "completed",
            "schema_version": 2,
            "statistics": statistics,
            "cost_coverage": fee_coverage,
            "resource_budget": {
                "timeout_seconds": wall_clock_budget,
                "max_historical_instruments": profile.max_instruments,
                "max_rows": profile.max_rows,
            },
            "data_quality": quality_panel(df, calendar),
            "research_validity": validity_panel(
                synthetic, membership, assume_membership_known, evaluation, statistics
            ),
            "folds": fold_results,
            "protocol": protocol,
            "selected_model": selected,
            "validation_rank_ic": validation,
            "test_rank_ic": test_scores,
            "metrics": metrics,
            "boundaries": boundaries,
            "rows": len(df),
            "equities": len(symbols),
            "workers": workers,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "ai_calls": 0,
            "code_revision": revision,
            "code_worktree_dirty": dirty,
            "python": platform.python_version(),
            "versions": {
                p: importlib.metadata.version(p)
                for p in ["pyqlib", "numpy", "pandas", "scikit-learn", "lightgbm", "indian-trader-skill"]
            },
            "assumptions": {
                "capital": capital,
                "topk": topk,
                "buy_cost": buy_cost,
                "sell_cost": sell_cost,
                "cost_model": cost_model,
                "broker": broker,
                "deployment": 0.95,
                "execution": "local fractional adjusted-unit ledger; next session open; daily close valuation; final close sale",
                "rebalance": rebalance,
                "participation": participation,
                "min_turnover": min_turnover,
                "impact_bps": impact_bps,
                "hold_buffer": hold_buffer,
                "turnover_limit": turnover_limit,
                "calendar_sha256": digest(calendar_path) if calendar_path else "synthetic weekday calendar",
            },
            "limitations": [
                "SYNTHETIC integration evidence only"
                if synthetic
                else "Historical membership supplied; missing delisted prices still compromise coverage"
                if membership
                else "Fixed supplied universe; NOT survivorship-bias-free",
                "Fees use the selected cost model; no price-band checks; square-root impact is an illustrative model",
                "Pre-coverage proportional bridge used; historical statutory fees are not reconstructed"
                if "proportional_bridge" in fee_coverage["valuation_sessions"]
                else "India delivery schedule estimates or explicit proportional fees; verify broker contract notes",
                "Final close liquidation includes fees and impact; unresolved positions require explicit writeoff or fail",
                "Benchmark is supplied price-return series unless user supplies a documented total-return series",
                f"Label uses {horizon} sessions after next-open entry; portfolio is marked daily to close and holds persistent positions",
                "Walk-forward folds retrain annually; final year stays closed unless explicitly opened"
                if evaluation == "walk-forward"
                else "One chronological holdout; not production validation",
                f"Suspected unadjusted split/bonus gaps: {len(suspected_actions)}; review suspected_actions.json; not proof or automatic adjustment",
                "No live orders, broker integration, automatic paper fills or AI API calls",
            ],
        }
    )
    if "proportional_bridge" in fee_coverage["valuation_sessions"]:
        manifest["research_validity"]["flags"].append(
            {
                "severity": "WARNING",
                "code": "COST_COVERAGE_BRIDGE",
                "message": "Pre-coverage executions use explicit proportional assumptions; see cost coverage dates/rates",
            }
        )
    if deployment_warning:
        manifest["research_validity"]["flags"].append(deployment_warning)
    progress("reports")
    render(manifest, portfolio, output / "report.html")
    brief = {
        k: manifest[k]
        for k in ["status", "synthetic", "selected_model", "metrics", "limitations", "ai_calls"]
    }
    brief["evidence"] = {
        "consistent_with_chance": statistics["consistent_with_chance"],
        "return_interval": statistics["net_return_interval"],
        "shuffle_p": statistics["shuffled_signal"]["p_value"],
    }
    brief["equal_weight_comparison"] = {k: comparison[k] for k in ("difference", "low", "high")}
    brief["warnings"] = [deployment_warning["message"]] if deployment_warning else []
    brief["research_status"] = manifest["research_validity"]["status"]
    text = json.dumps(brief, separators=(",", ":"), allow_nan=False)
    if len(text) > profile.brief_chars:
        raise ValueError("Brief budget exceeded")
    (output / "brief.json").write_text(text, encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    progress("completed")
    return manifest
