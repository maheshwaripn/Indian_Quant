"""Fixed chronological evaluation using Qlib expressions and portfolio execution."""

import importlib.metadata
import json
import math
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .data import digest, read_bars, write_qlib
from .report import render
from .resources import configure

FEATURES = {
    "momentum5": "$close/Ref($close,5)-1",
    "momentum20": "$close/Ref($close,20)-1",
    "volatility20": "Std($close/Ref($close,1)-1,20)",
    "range": "($high-$low)/$close",
    "volume_ratio": "$volume/Mean($volume,20)",
}
LABEL = "Ref($open,-2)/Ref($open,-1)-1"


def split_panel(panel, calendar):
    """Purge labels touching the next segment; no fitted preprocessing crosses boundaries."""
    dates = pd.DatetimeIndex(calendar)
    if len(dates) < 150:
        raise ValueError("At least 150 sessions required for this research recipe")
    validation_start, test_start = dates[int(len(dates) * 0.6)], dates[int(len(dates) * 0.8)]
    end_map = dict(zip(dates[:-2], dates[2:]))
    timestamp = panel.index.get_level_values("datetime")
    label_end = pd.DatetimeIndex(timestamp.map(end_map))
    train = (timestamp < validation_start) & (label_end < validation_start)
    valid = (timestamp >= validation_start) & (timestamp < test_start) & (label_end < test_start)
    test = (timestamp >= test_start) & label_end.notna()
    return {"train": panel.loc[train], "valid": panel.loc[valid], "test": panel.loc[test]}, {
        "validation_start": str(validation_start.date()),
        "test_signal_start": str(test_start.date()),
        "label": "open[t+2] / open[t+1] - 1",
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
):
    started = time.monotonic()
    profile, workers = configure(mode)
    if not all(math.isfinite(v) for v in [buy_cost, sell_cost, topk, capital]):
        raise ValueError("Costs, count and capital must be finite")
    if not (0 <= buy_cost < 0.1 and 0 <= sell_cost < 0.1) or topk < 1 or capital <= 0:
        raise ValueError("Invalid costs, position count, or capital")
    df = read_bars(source, profile)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "running", "mode": mode, "synthetic": synthetic, "source_sha256": digest(source)}
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    if calendar_path:
        calendar = pd.DatetimeIndex(pd.to_datetime(Path(calendar_path).read_text().splitlines()))
    elif synthetic:
        calendar = pd.DatetimeIndex(sorted(df.date.unique()))
    else:
        raise ValueError("Real research requires --calendar with independently verified NSE sessions")
    if calendar.has_duplicates or not calendar.is_monotonic_increasing:
        raise ValueError("Calendar must be unique and sorted")
    # Pilot recipe requires a complete fixed panel: missing returns must not disappear from P&L.
    if not df.date.isin(calendar).all() or any(
        len(part) != len(calendar) or (part.volume <= 0).any() for _, part in df.groupby("symbol")
    ):
        raise ValueError(
            "Pilot requires complete positive-volume bars for every calendar session; no forward fills"
        )
    symbols = sorted(set(df.symbol) - {benchmark})
    if benchmark not in set(df.symbol) or len(symbols) < 3 or topk > len(symbols):
        raise ValueError("Provide benchmark plus at least 3 equities, with topk <= equity count")
    provider = write_qlib(df, output / "qlib", calendar)
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
    expressions = list(FEATURES.values()) + [LABEL]
    panel = D.features(symbols, expressions, start_time=calendar[0], end_time=calendar[-1])
    panel.columns = [*FEATURES, "label"]
    # A full 20-session warmup is required even if an expression offers partial windows.
    panel = panel.loc[panel.index.get_level_values("datetime") >= calendar[20]]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna()
    splits, boundaries = split_panel(panel, calendar)
    if any(len(part) < 20 for part in splits.values()):
        raise ValueError("Too few complete observations in a chronological segment")
    from lightgbm import LGBMRegressor
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    candidates = {
        "momentum": None,
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
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
    predictions, validation, test_scores = {}, {}, {}
    for name, model in candidates.items():
        if model is None:
            prediction = panel.momentum20
        else:
            model.fit(splits["train"][list(FEATURES)], splits["train"].label)
            prediction = pd.Series(model.predict(panel[list(FEATURES)]), index=panel.index)
        predictions[name] = prediction
        validation[name] = rank_ic(splits["valid"].assign(prediction=prediction))
        test_scores[name] = rank_ic(splits["test"].assign(prediction=prediction))
    # Select solely on validation; report test once, never use it for automatic tuning.
    selected = max(validation, key=lambda name: validation[name] if validation[name] is not None else -np.inf)
    test = splits["test"].copy()
    test["prediction"] = predictions[selected].reindex(test.index)
    test.to_csv(output / "predictions.csv")
    test_dates = sorted(test.index.get_level_values("datetime").unique())
    start = calendar[calendar.get_loc(test_dates[0]) + 1]
    end = calendar[calendar.get_loc(test_dates[-1]) + 1]
    from qlib.backtest import backtest
    from qlib.backtest.executor import SimulatorExecutor
    from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy

    strategy = TopkDropoutStrategy(
        signal=test.prediction, topk=topk, n_drop=topk, only_tradable=True, risk_degree=0.95
    )
    executor = SimulatorExecutor(time_per_step="day", generate_portfolio_metrics=True)
    portfolios, _ = backtest(
        start_time=start,
        end_time=end,
        strategy=strategy,
        executor=executor,
        account=capital,
        benchmark=benchmark,
        exchange_kwargs={
            "freq": "day",
            "deal_price": "$open",
            "limit_threshold": None,
            "open_cost": buy_cost,
            "close_cost": sell_cost,
            "min_cost": 0,
            "trade_unit": 1,
        },
    )
    portfolio, _ = portfolios["1day"]
    portfolio.to_csv(output / "portfolio.csv")
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
            "schema_version": 1,
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
                for p in ["pyqlib", "numpy", "pandas", "scikit-learn", "lightgbm"]
            },
            "assumptions": {
                "capital": capital,
                "topk": topk,
                "buy_cost": buy_cost,
                "sell_cost": sell_cost,
                "deployment": 0.95,
                "execution": "next session open; daily close valuation",
                "calendar_sha256": digest(calendar_path) if calendar_path else "synthetic weekday calendar",
            },
            "limitations": [
                "SYNTHETIC integration evidence only"
                if synthetic
                else "Fixed supplied universe; NOT survivorship-bias-free",
                "No dated India tax engine, price-band validation, impact, bid-ask or volume participation limit",
                "Constant cost rates are illustrative all-in assumptions, not statutory fee calculations",
                "No final liquidation: terminal holdings marked to close; exit costs remain unrealized",
                "Benchmark is supplied price-return series unless user supplies a documented total-return series",
                "Label is next-open to following-open; portfolio is marked daily to close and holds persistent positions",
                "One chronological holdout, not walk-forward or production validation",
                "No live orders, broker integration, automatic paper fills or AI API calls",
            ],
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    render(manifest, portfolio, output / "report.html")
    brief = {
        k: manifest[k]
        for k in ["status", "synthetic", "selected_model", "metrics", "limitations", "ai_calls"]
    }
    text = json.dumps(brief, indent=2, allow_nan=False)
    if len(text) > profile.brief_chars:
        raise ValueError("Brief budget exceeded")
    (output / "brief.json").write_text(text, encoding="utf-8")
    return manifest
