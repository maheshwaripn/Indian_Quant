import json

import numpy as np
import pandas as pd
import pytest

from indian_quant.data import synthetic
from indian_quant.execution import simulate
from indian_quant.statistics import paired_return_interval
from indian_quant.trade_audit import exposure_warning, round_trips, summarize


def market():
    dates = pd.bdate_range("2024-01-01", periods=45)
    bars = pd.DataFrame(
        [
            {"date": d, "symbol": s, "open": 100.0, "close": 100.0, "volume": 100000.0}
            for s in ["A", "B", "BENCH"]
            for d in dates
        ]
    )
    ix = pd.MultiIndex.from_product([["A", "B"], dates], names=["instrument", "datetime"])
    scores = pd.Series([2.0 if i % 10 < 5 else 0.0 for i in range(45)] + [1.0] * 45, index=ix)
    return dates, bars, scores


@pytest.mark.parametrize("impact", [0, 100])
def test_round_trips_reconcile_partial_fills_and_reentry(impact):
    dates, bars, scores = market()
    portfolio, fills = simulate(
        bars, scores, dates[21:], "BENCH", topk=1, capital=100000.0, turnover_limit=0.3, impact_bps=impact
    )
    assert np.allclose(fills.price * fills.quantity, fills.value)
    assert np.allclose(
        fills.groupby("date").impact.sum().reindex(portfolio.index.strftime("%Y-%m-%d"), fill_value=0),
        portfolio.impact,
    )
    trades = round_trips(fills)
    assert len(trades[trades.symbol == "A"]) >= 2
    assert fills.groupby("trade_id").size().max() > 2  # additions/partial exits retain ID
    assert np.allclose(trades.buy_quantity, trades.sell_quantity)
    assert trades.net_pnl.sum() == pytest.approx(portfolio.equity.iloc[-1] - 100000.0)
    for _, group in fills.groupby("trade_id"):
        position = (group.quantity * group.side.map({"buy": 1, "sell": -1})).cumsum()
        assert np.allclose(position, group.position_after, atol=1e-8)
    assert summarize(trades)["net_pnl"] == pytest.approx(trades.net_pnl.sum())


@pytest.mark.parametrize("stale", [True, False])
def test_writeoff_is_not_a_sale_and_reconciles(stale):
    dates, bars, scores = market()
    scores[:] = 1.0
    if stale:
        bars.loc[(bars.symbol == "A") & (bars.date == dates[-1]), "volume"] = 0
    else:
        # Collapse trailing liquidity only after entry, so final liquidation exceeds capacity.
        bars.loc[(bars.symbol == "A") & (bars.date >= dates[22]), "volume"] = 1
    portfolio, fills = simulate(
        bars,
        scores,
        dates[21:],
        "BENCH",
        topk=1,
        capital=100000.0,
        rebalance="monthly",
        participation=0.1,
        terminal_policy="writeoff",
    )
    losses = fills[fills.side == "writeoff"]
    assert len(losses) == 1
    assert losses.value.iloc[0] == 0
    assert losses.position_after.iloc[0] == 0
    assert losses.writeoff_value.sum() == pytest.approx(portfolio.writeoff.sum())
    trades = round_trips(fills)
    assert trades.net_pnl.sum() == pytest.approx(portfolio.equity.iloc[-1] - 100000.0)
    assert summarize(trades)["writeoff_holdings"] == 1


def test_empty_fills_have_auditable_schema():
    dates, bars, scores = market()
    portfolio, fills = simulate(bars, scores, dates[21:], "BENCH", min_turnover=1e20)
    trades = round_trips(fills)
    assert trades.empty
    assert summarize(trades)["win_rate"] is None
    assert "price" in fills and "net_pnl" in trades
    warning = exposure_warning(portfolio, 0.95)
    assert "filtered_liquidity" in warning["message"]


def test_low_exposure_warning_and_boundary():
    frame = pd.DataFrame(
        {"exposure": [0.39, 0.39], "buy_unfilled_turnover": [100.0, 200.0], "buy_unfilled_cash": [0.0, 1.0]}
    )
    assert "buy_unfilled_turnover" in exposure_warning(frame, 0.95)["message"]
    frame.exposure = 0.76
    assert exposure_warning(frame, 0.95) is None


def test_paired_interval_preserves_joint_dates_and_compounding():
    a = pd.Series([0.1, -0.05, 0.03, -0.02] * 10)
    equal = paired_return_interval(a, a)
    assert equal["difference"] == equal["low"] == equal["high"] == 0
    b = a - 0.01
    result = paired_return_interval(a, b)
    assert result == paired_return_interval(a, b)
    assert result["difference"] == pytest.approx((1 + a).prod() - (1 + b).prod())
    assert result["low"] > 0
    with pytest.raises(ValueError, match="dates"):
        paired_return_interval(a, b.set_axis(range(1, len(b) + 1)))


def test_end_to_end_brief_report_and_trade_files(tmp_path):
    from indian_quant.research import run

    data = tmp_path / "bars.csv"
    synthetic(data, instruments=3, sessions=250)
    out = tmp_path / "run"
    run(data, out, "essential", "BENCH", synthetic=True, topk=2, null_draws=9, turnover_limit=0.01)
    manifest = json.loads((out / "manifest.json").read_text())
    brief = json.loads((out / "brief.json").read_text())
    assert brief["warnings"] and "turnover" in brief["warnings"][0]
    assert len((out / "brief.json").read_text()) <= 4000
    assert "equal_weight_comparison" in brief
    trades = pd.read_csv(out / "trades.csv")
    assert trades.net_pnl.sum() == pytest.approx(manifest["statistics"]["trade_summary"]["net_pnl"])
    counts = manifest["statistics"]["signal_availability"]["yearly_eligible_without_signal"]
    assert (
        sum(counts.values())
        == manifest["statistics"]["execution_constraints"]["totals"]["eligible_without_signal"]
    )
    html = (out / "report.html").read_text()
    assert "LOW_DEPLOYMENT" in html and "Net return versus equal weight" in html


def test_known_cashflows_and_impact_not_deducted_twice():
    fills = pd.DataFrame(
        [
            {
                "trade_id": "T1",
                "symbol": "A",
                "date": "2024-01-01",
                "side": "buy",
                "quantity": 10.0,
                "value": 1010.0,
                "fee": 2.0,
                "impact": 10.0,
                "position_after": 10.0,
                "reason": "rebalance",
            },
            {
                "trade_id": "T1",
                "symbol": "A",
                "date": "2024-01-03",
                "side": "sell",
                "quantity": 4.0,
                "value": 440.0,
                "fee": 1.0,
                "impact": 4.0,
                "position_after": 6.0,
                "reason": "rebalance",
            },
            {
                "trade_id": "T1",
                "symbol": "A",
                "date": "2024-01-05",
                "side": "sell",
                "quantity": 6.0,
                "value": 660.0,
                "fee": 1.0,
                "impact": 6.0,
                "position_after": 0.0,
                "reason": "terminal_close",
            },
        ]
    )
    trade = round_trips(fills).iloc[0]
    assert trade.net_pnl == 86.0  # 1100 - 1010 - 4; impact already in cash flows
    assert trade.holding_days == 4
    assert trade.return_on_buy_outlay == pytest.approx(86 / 1012)
    assert summarize(round_trips(fills))["win_rate"] == 1.0


def test_missing_signal_counts_rebalance_only_and_new_members():
    dates, bars, scores = market()
    # B is eligible at execution but has no score; count each rebalance, not every date.
    scores = scores.loc[["A"]]
    portfolio, _ = simulate(
        bars, scores, dates[21:], "BENCH", topk=1, rebalance="weekly", eligible=lambda day: {"A", "B"}
    )
    assert (portfolio.loc[portfolio.rebalance_session, "eligible_without_signal"] == 1).all()
    assert (portfolio.loc[~portfolio.rebalance_session, "eligible_without_signal"] == 0).all()
