import csv

import numpy as np
import pandas as pd
import pytest

from indian_quant.execution import simulate
from indian_quant.membership import audit, eligibility
from indian_quant.research import split_panel
from indian_quant.statistics import hac_t, interval


def fixture():
    dates = pd.bdate_range("2024-01-01", periods=30)
    bars = pd.DataFrame(
        [
            {
                "date": d,
                "symbol": s,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 10000.0,
                "factor": 1.0,
            }
            for s in ("A", "B", "BENCH")
            for d in dates
        ]
    )
    index = pd.MultiIndex.from_product([["A", "B"], dates[20:]], names=["instrument", "datetime"])
    signals = pd.Series([2.0] * 10 + [1.0] * 10, index=index)
    return dates, bars, signals


def test_sparse_unheld_and_zero_volume_benchmark():
    dates, bars, signals = fixture()
    bars = bars[~((bars.symbol == "B") & (bars.date >= dates[23]))].copy()
    bars.loc[bars.symbol == "BENCH", "volume"] = 0
    result, fills = simulate(bars, signals, dates[21:], "BENCH", topk=1)
    assert len(result) == 9
    assert result.stale_holdings.sum() == 0
    assert (fills.reason == "terminal_close").any()
    assert result.equity.iloc[-1] < 1e6  # flat prices lose costs, including final exit


def test_missing_held_price_never_disappears_or_sells_in_hindsight():
    dates, bars, signals = fixture()
    bars = bars[~((bars.symbol == "A") & (bars.date >= dates[25]))]
    with pytest.raises(ValueError, match="Unresolved terminal"):
        simulate(bars, signals, dates[21:], "BENCH", topk=1)
    result, fills = simulate(bars, signals, dates[21:], "BENCH", topk=1, terminal_policy="writeoff")
    assert result.loc[dates[25], "exposure"] > 0.9
    assert result.writeoff.iloc[-1] > 900000
    assert not ((fills.symbol == "A") & (fills.side == "sell") & (fills.date >= str(dates[25].date()))).any()


def test_weekly_rebalance_and_turnover_cap():
    dates, bars, signals = fixture()
    result, fills = simulate(
        bars, signals, dates[21:], "BENCH", topk=1, rebalance="weekly", turnover_limit=0.1
    )
    ordinary = result.iloc[:-1]
    assert ordinary.turnover.max() <= 0.10000001
    assert (fills.reason == "terminal_close").any()
    assert (ordinary.turnover == 0).any()


def test_nifty50_and_reentry_intervals(tmp_path):
    p = tmp_path / "members.csv"
    names = [f"S{i}" for i in range(50)]
    with p.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["effective_date", "index_type", "inclusions", "exclusions", "symbols"])
        writer.writerow(["2024-01-01", "Nifty 50", ",".join(names), "", ",".join(names)])
        writer.writerow(["2024-01-03", "Nifty 50", "NEW", "S0", ",".join(names[1:] + ["NEW"])])
        writer.writerow(["2024-01-05", "Nifty 50", "S0", "NEW", ",".join(names)])
    assert audit(p)["structural_checks_passed"]
    dates = pd.bdate_range("2024-01-01", periods=7)
    with pytest.raises(ValueError, match="available_date"):
        eligibility(p, "Nifty 50", dates)
    members, spans = eligibility(p, "Nifty 50", dates, assume_known=True)
    assert "S0" not in members(pd.Timestamp("2024-01-04"))
    assert len([span for span in spans if span[0] == "S0"]) == 2


def test_long_horizon_purge_and_missing_outcomes_preserved():
    dates = pd.bdate_range("2020-01-01", periods=200)
    ix = pd.MultiIndex.from_product([["A"], dates], names=["instrument", "datetime"])
    panel = pd.DataFrame({"label": np.nan}, index=ix)
    splits, _ = split_panel(panel, dates, horizon=20)
    assert splits["train"].index.get_level_values("datetime").max() == dates[98]
    assert len(splits["test"]) > 0  # missing future returns don't determine candidate availability


def test_statistics_do_not_certify_random_prices():
    draws = np.random.default_rng(17).normal(0, 0.01, 82)
    result = interval(draws)
    assert result == interval(draws)
    assert result["low"] < 0 < result["high"]
    assert hac_t([1.0, 2.0]) is None


def test_india_fees_do_not_allow_negative_cash():
    dates, bars, signals = fixture()
    result, fills = simulate(
        bars, signals, dates[21:], "BENCH", capital=1000, topk=1, cost_model="india", broker="flat20"
    )
    assert result.equity.min() > 0
    assert fills.fee.min() > 20


@pytest.mark.parametrize(
    "feature_set,evaluation,sessions,horizon",
    [("alpha158", "holdout", 250, 5), ("compact", "walk-forward", 1600, 1)],
)
def test_extended_qlib_paths(tmp_path, feature_set, evaluation, sessions, horizon):
    import json
    import subprocess
    import sys

    from indian_quant.data import synthetic

    synthetic(tmp_path / "bars.csv", sessions=sessions, instruments=4)
    output = tmp_path / "run"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "indian_quant",
            "run",
            "--data",
            str(tmp_path / "bars.csv"),
            "--output",
            str(output),
            "--benchmark",
            "BENCH",
            "--synthetic",
            "--topk",
            "2",
            "--feature-set",
            feature_set,
            "--evaluation",
            evaluation,
            "--horizon",
            str(horizon),
            "--train-years",
            "2",
            "--valid-years",
            "1",
            "--null-draws",
            "9",
            "--rebalance",
            "monthly",
        ],
        check=True,
        timeout=180,
    )
    result = json.loads((output / "manifest.json").read_text())
    assert result["status"] == "completed"
    assert result["statistics"]["consistent_with_chance"]
    if evaluation == "walk-forward":
        assert len(result["folds"]) == 3
        assert "2028" not in result["statistics"]["yearly_net_returns"]
        assert pd.read_csv(output / "predictions.csv").datetime.max() < "2028-01-01"


def test_real_run_accepts_delisted_like_sparse_history(tmp_path):
    import json
    import subprocess
    import sys

    from indian_quant.data import synthetic

    source = tmp_path / "sparse.csv"
    bars = synthetic(source, sessions=250, instruments=4)
    cutoff = sorted(bars.date.unique())[210]
    bars = bars[~((bars.symbol == "DEMO00") & (bars.date >= cutoff))]
    bars.loc[bars.symbol == "BENCH", "volume"] = 0
    bars.to_csv(source, index=False)
    output = tmp_path / "run"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "indian_quant",
            "run",
            "--data",
            str(source),
            "--output",
            str(output),
            "--benchmark",
            "BENCH",
            "--synthetic",
            "--topk",
            "2",
            "--terminal-policy",
            "writeoff",
            "--null-draws",
            "9",
        ],
        check=True,
        timeout=180,
    )
    result = json.loads((output / "manifest.json").read_text())
    assert result["status"] == "completed"
    assert result["statistics"]["label_coverage"] < 1
