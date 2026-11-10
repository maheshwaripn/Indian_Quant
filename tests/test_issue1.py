import csv
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from indian_quant.cli import launch, parser
from indian_quant.cost_policy import cost_regime, coverage
from indian_quant.data import synthetic, validate
from indian_quant.execution import prepare_market, simulate
from indian_quant.resources import PROFILES, configure, timeout_seconds


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
    ix = pd.MultiIndex.from_product([["A", "B"], dates[20:]], names=["instrument", "datetime"])
    return dates, bars, pd.Series([2.0] * 10 + [1.0] * 10, index=ix)


def test_fee_bridge_only_before_coverage():
    with pytest.raises(ValueError, match="coverage starts"):
        cost_regime("2020-01-02", "india")
    assert cost_regime("2020-01-02", "india", "proportional") == "proportional_bridge"
    assert cost_regime("2023-04-01", "india", "proportional") == "india"
    with pytest.raises(ValueError, match="does not extrapolate"):
        cost_regime("2027-01-01", "india", "proportional")
    result = coverage(pd.bdate_range("2023-03-30", periods=4), "india", "proportional", 0.001, 0.002)
    assert result["valuation_sessions"]["proportional_bridge"]["sessions"] == 2
    assert result["valuation_sessions"]["india"]["sessions"] == 2


def test_precoverage_fill_rates_and_audit_labels():
    dates, bars, signals = fixture()
    old_dates = dates - pd.DateOffset(years=4)
    bars.date = bars.date - pd.DateOffset(years=4)
    signals.index = pd.MultiIndex.from_tuples(
        [(s, d - pd.DateOffset(years=4)) for s, d in signals.index], names=signals.index.names
    )
    args = {
        "bars": bars,
        "signals": signals,
        "dates": old_dates[21:],
        "benchmark": "BENCH",
        "topk": 1,
        "buy_cost": 0.001,
        "sell_cost": 0.002,
    }
    base, base_fills = simulate(**args)
    bridge, fills = simulate(**args, cost_model="india", cost_before_coverage="proportional")
    pd.testing.assert_frame_equal(base, bridge)
    pd.testing.assert_frame_equal(base_fills.drop(columns="cost_regime"), fills.drop(columns="cost_regime"))
    assert set(fills.cost_regime) == {"proportional_bridge"}
    assert fills.iloc[0].fee == pytest.approx(fills.iloc[0].value * 0.001)
    assert fills.iloc[-1].fee == pytest.approx(fills.iloc[-1].value * 0.002)


def test_rotating_history_fits_lab_and_remains_bounded():
    frame = pd.DataFrame(
        {
            "date": ["2020-01-01"] * 1361,
            "symbol": [f"S{i}" for i in range(1361)],
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 100.0,
            "factor": 1.0,
        }
    )
    assert len(validate(frame, PROFILES["lab"])) == 1361
    too_wide = pd.concat([frame, frame.assign(symbol=lambda x: x.symbol + "X")])
    with pytest.raises(ValueError, match="resource"):
        validate(too_wide, PROFILES["lab"])


def test_custom_size_audit_cli(tmp_path):
    source = tmp_path / "custom.csv"
    with source.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["effective_date", "index_type", "inclusions", "exclusions", "symbols"])
        writer.writerow(["2024-01-01", "LIQUID2", "A,B", "", "A,B"])
    destination = tmp_path / "audit.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "indian_quant",
            "membership-audit",
            str(source),
            "--expected-size",
            "2",
            "--output",
            str(destination),
        ],
        check=True,
    )
    assert json.loads(destination.read_text())["structural_checks_passed"]


def test_timeout_override_reaches_parent_and_worker(monkeypatch, tmp_path):
    seen = {}

    class FakeProcess:
        def __init__(self, command, **kwargs):
            seen["command"] = command

        def wait(self, timeout=None):
            seen["timeout"] = timeout
            return 0

    monkeypatch.setattr(subprocess, "Popen", FakeProcess)
    args = parser().parse_args(
        [
            "run",
            "--data",
            "input.csv",
            "--output",
            str(tmp_path / "out"),
            "--benchmark",
            "BENCH",
            "--timeout-hours",
            "8",
            "--cost-before-coverage",
            "proportional",
        ]
    )
    launch(args)
    assert seen["timeout"] == 28800
    assert "--timeout-hours" in seen["command"]
    assert "--cost-before-coverage" in seen["command"]
    for invalid in (0, -1, float("nan"), float("inf"), 169):
        with pytest.raises(ValueError):
            timeout_seconds("lab", invalid)


def test_mlflow_hint_default_and_user_override(monkeypatch):
    monkeypatch.delenv("MLFLOW_DISABLE_AGENT_HINT", raising=False)
    configure("essential")
    assert os.environ["MLFLOW_DISABLE_AGENT_HINT"] == "1"
    monkeypatch.setenv("MLFLOW_DISABLE_AGENT_HINT", "0")
    configure("essential")
    assert os.environ["MLFLOW_DISABLE_AGENT_HINT"] == "0"


def test_cached_market_and_constraint_accounting():
    dates, bars, signals = fixture()
    args = {
        "bars": bars,
        "signals": signals,
        "dates": dates[21:],
        "benchmark": "BENCH",
        "topk": 1,
        "turnover_limit": 0.5,
        "participation": 0.01,
        "terminal_policy": "writeoff",
    }
    plain, plain_fills = simulate(**args)
    market = prepare_market(bars, dates[21:], "BENCH")
    fast, fast_fills = simulate(**args, prepared=market)
    pd.testing.assert_frame_equal(plain, fast)
    pd.testing.assert_frame_equal(plain_fills, fast_fills)
    first = fast.iloc[0]
    assert first.buy_unfilled_turnover == pytest.approx(450000)
    assert first.buy_unfilled_participation == pytest.approx(490000)
    assert first.buy_filled_value == pytest.approx(10000)
    sum_columns = [
        "buy_filled_value",
        "buy_unfilled_turnover",
        "buy_unfilled_participation",
        "buy_unfilled_cash",
        "buy_unfilled_no_liquidity",
    ]
    np.testing.assert_allclose(fast.buy_requested_value, fast[sum_columns].sum(axis=1), atol=1e-6)
    assert not market.quotes.flags.writeable
    with pytest.raises(ValueError, match="snapshot"):
        simulate(**{**args, "bars": bars.copy()}, prepared=market)


def test_liquidity_filter_and_missing_signals_are_separate():
    dates, bars, signals = fixture()
    result, _ = simulate(bars, signals, dates[21:], "BENCH", min_turnover=1e9)
    assert result.filtered_liquidity.iloc[0] == 2
    assert result.eligible_without_signal.iloc[0] == 0
    assert result.exposure.max() == 0


def test_bridge_progress_and_timeout_metadata_end_to_end(tmp_path):
    source = tmp_path / "bars.csv"
    bars = synthetic(source, sessions=250, instruments=4)
    bars.date = bars.date - pd.DateOffset(years=2)
    bars.to_csv(source, index=False)
    output = tmp_path / "run"
    result = subprocess.run(
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
            "--null-draws",
            "9",
            "--cost-model",
            "india",
            "--cost-before-coverage",
            "proportional",
            "--timeout-hours",
            "1",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    )
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "completed"
    assert manifest["resource_budget"]["timeout_seconds"] == 3600
    assert "proportional_bridge" in manifest["cost_coverage"]["valuation_sessions"]
    assert any(f["code"] == "COST_COVERAGE_BRIDGE" for f in manifest["research_validity"]["flags"])
    assert json.loads((output / "progress.json").read_text())["stage"] == "completed"
    assert "shuffled_signals" in result.stderr
