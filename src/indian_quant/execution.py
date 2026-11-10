"""Transparent long-only ledger; Qlib supplies features, not this execution engine.

Missing quotes retain marked holdings. An unresolved final holding is either rejected
or explicitly written off, never sold at its hindsight last available price.
"""

from collections import namedtuple
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .cost_policy import cost_regime

Quote = namedtuple("Quote", "open close volume")


@dataclass(frozen=True)
class PreparedMarket:
    source: pd.DataFrame
    dates: pd.DatetimeIndex
    calendar: pd.DatetimeIndex
    symbols: tuple
    quotes: np.ndarray
    adv: np.ndarray
    benchmark: str
    benchmark_returns: pd.Series


def prepare_market(bars, dates, benchmark, full_calendar=None):
    """Align prices and lagged liquidity once, reused read-only across portfolio trials."""
    dates = pd.DatetimeIndex(dates)
    calendar = pd.DatetimeIndex(sorted(bars.date.unique()) if full_calendar is None else full_calendar)
    symbols, quotes, turnover = [], [], []
    benchmark_returns = None
    for symbol, group in bars.groupby("symbol"):
        indexed = group.set_index("date")
        aligned = indexed.reindex(dates)
        history = indexed.reindex(calendar)
        symbols.append(symbol)
        quotes.append(aligned[["open", "close", "volume"]].to_numpy(dtype=float))
        turnover.append(
            (history.close * history.volume)
            .rolling(20, min_periods=20)
            .mean()
            .shift(1)
            .reindex(dates)
            .to_numpy()
        )
        if symbol == benchmark:
            if aligned.close.isna().any():
                raise ValueError("Benchmark must cover every valuation session (zero volume is permitted)")
            benchmark_returns = aligned.close.pct_change(fill_method=None).fillna(
                aligned.close.iloc[0] / aligned.open.iloc[0] - 1
            )
    if benchmark_returns is None:
        raise ValueError("Benchmark absent")
    quotes, turnover = np.stack(quotes, axis=1), np.stack(turnover, axis=1)
    quotes.setflags(write=False)
    turnover.setflags(write=False)
    return PreparedMarket(
        bars, dates, calendar, tuple(symbols), quotes, turnover, benchmark, benchmark_returns
    )


def simulate(
    bars,
    signals,
    dates,
    benchmark,
    capital=1e6,
    topk=5,
    buy_cost=0.001,
    sell_cost=0.0015,
    rebalance="daily",
    hold_buffer=0,
    turnover_limit=1.0,
    min_turnover=0.0,
    participation=1.0,
    impact_bps=0.0,
    eligible=None,
    terminal_policy="error",
    equal_weight=False,
    cost_model="proportional",
    broker="zero",
    cost_multiplier=1.0,
    full_calendar=None,
    prepared=None,
    cost_before_coverage="error",
):
    def charges(day, side, value):
        if cost_regime(day, cost_model, cost_before_coverage) == "india":
            from indian_market_core.costs import leg

            return leg("delivery", day.date().isoformat(), side, value, broker)["total"] * cost_multiplier
        return value * (buy_cost if side == "buy" else sell_cost)

    market = prepared if prepared is not None else prepare_market(bars, dates, benchmark, full_calendar)
    if (
        market.source is not bars
        or not market.dates.equals(pd.DatetimeIndex(dates))
        or market.benchmark != benchmark
        or (full_calendar is not None and not market.calendar.equals(pd.DatetimeIndex(full_calendar)))
    ):
        raise ValueError("Prepared market must match the input snapshot, calendar, dates and benchmark")
    all_dates = market.calendar
    by_day = {d: g.droplevel("datetime") for d, g in signals.groupby(level="datetime")}
    cash, positions, marks = float(capital), {}, {}
    previous, last_period, rows, fills = float(capital), None, [], []
    for i, day in enumerate(dates):
        quote = {s: Quote(*values) for s, values in zip(market.symbols, market.quotes[i])}
        adv = dict(zip(market.symbols, market.adv[i]))
        diagnostics = {
            "buy_requested_value": 0.0,
            "buy_filled_value": 0.0,
            "buy_unfilled_turnover": 0.0,
            "buy_unfilled_participation": 0.0,
            "buy_unfilled_cash": 0.0,
            "buy_unfilled_no_liquidity": 0.0,
        }
        tradable = {s for s, q in quote.items() if pd.notna(q.open) and q.volume > 0 and s != benchmark}
        # Signals carry their original dates and execute only on a later session.
        loc = all_dates.get_loc(day)
        signal_day = all_dates[loc - 1] if loc else None
        scores = by_day.get(signal_day, pd.Series(dtype=float)).dropna()
        members = set(market.symbols) - {benchmark} if eligible is None else eligible(day)
        missing_signals = len(members - set(scores.index)) if not equal_weight else 0
        scored = set(scores.index) & members
        filtered_untradable = len(scored - tradable)
        filtered_liquidity = len(
            {s for s in scored & tradable if not np.isfinite(adv[s]) or adv[s] < min_turnover}
        )
        allowed = members & tradable
        allowed = {s for s in allowed if pd.notna(adv[s]) and adv[s] >= min_turnover}
        if equal_weight:
            scores = pd.Series(1.0, index=sorted(allowed))
        scores = scores[scores.index.isin(allowed)].sort_values(ascending=False, kind="stable")
        period = (
            str(day.date())
            if rebalance == "daily"
            else str(day.to_period("W" if rebalance == "weekly" else "M"))
        )
        scheduled = period != last_period
        fee_total, traded, impact_total = 0.0, 0.0, 0.0
        open_equity = cash + sum(
            q * (quote[s].open if s in tradable else marks[s]) for s, q in positions.items()
        )
        budget = open_equity * turnover_limit
        if scheduled:
            ranked = list(scores.index)
            count = len(ranked) if equal_weight else topk
            keep = [s for s in positions if s in ranked[: count + hold_buffer]]
            chosen = (keep + [s for s in ranked if s not in keep])[:count]
            targets = {s: 0.95 * open_equity / len(chosen) for s in chosen} if chosen else {}
            last_period = period
        else:
            targets = {s: q * (quote[s].open if s in tradable else marks[s]) for s, q in positions.items()}
        for s in set(targets) - members:
            targets.pop(s)
        for s in list(positions):
            if s not in members:
                targets.pop(s, None)
        # Sells before buys; partial fills respect trailing liquidity and gross turnover budget.
        for side in ("sell", "buy"):
            for s in sorted(set(positions) | set(targets)):
                if s not in tradable:
                    continue
                px = float(quote[s].open)
                current = positions.get(s, 0.0) * px
                delta = targets.get(s, 0.0) - current
                if (side == "sell" and delta >= -1e-8) or (side == "buy" and delta <= 1e-8):
                    continue
                if side == "buy":
                    diagnostics["buy_requested_value"] += delta
                liquidity = adv[s]
                if not np.isfinite(liquidity) or liquidity <= 0:
                    if side == "buy":
                        diagnostics["buy_unfilled_no_liquidity"] += delta
                    continue
                after_turnover = min(abs(delta), max(budget, 0.0))
                value = min(after_turnover, participation * liquidity)
                if side == "buy":
                    diagnostics["buy_unfilled_turnover"] += delta - after_turnover
                    diagnostics["buy_unfilled_participation"] += after_turnover - value
                before_cash = value
                rate = buy_cost if side == "buy" else sell_cost
                slip = impact_bps / 10000 * np.sqrt(value / liquidity)
                if side == "buy":
                    value = min(value, cash / ((1 + slip) * (1 + rate)))
                if value <= 1e-8:
                    if side == "buy":
                        diagnostics["buy_unfilled_cash"] += before_cash
                    continue
                units = value / px
                execution = value * (1 + slip if side == "buy" else 1 - slip)
                if side == "buy" and execution + charges(day, side, execution) > cash:
                    low, high = 0.0, value
                    for _ in range(40):
                        middle = (low + high) / 2
                        proposed = middle * (1 + slip)
                        if proposed + charges(day, side, proposed) <= cash:
                            low = middle
                        else:
                            high = middle
                    value = low
                    units = value / px
                    execution = value * (1 + slip)
                if side == "buy":
                    diagnostics["buy_unfilled_cash"] += before_cash - value
                    diagnostics["buy_filled_value"] += value
                if value < 1e-8:
                    continue
                fee = charges(day, side, execution)
                positions[s] = positions.get(s, 0.0) + (units if side == "buy" else -units)
                cash += -execution - fee if side == "buy" else execution - fee
                marks[s] = px
                if positions[s] < 1e-9:
                    del positions[s]
                budget -= value
                traded += value
                fee_total += fee
                impact_total += value * slip
                fills.append(
                    {
                        "date": str(day.date()),
                        "symbol": s,
                        "side": side,
                        "value": execution,
                        "fee": fee,
                        "reason": "rebalance",
                        "cost_regime": cost_regime(day, cost_model, cost_before_coverage),
                    }
                )
        stale = []
        for s in positions:
            if pd.notna(quote[s].close) and quote[s].volume > 0:
                marks[s] = float(quote[s].close)
            else:
                stale.append(s)
        writeoff = 0.0
        if i == len(dates) - 1:
            for s, units in list(positions.items()):
                if s in stale:
                    if terminal_policy == "error":
                        raise ValueError(
                            f"Unresolved terminal holding {s}; supply settlement data or explicitly choose writeoff"
                        )
                    writeoff += units * marks[s]
                else:
                    value = units * marks[s]
                    liquidity = adv[s]
                    if not np.isfinite(liquidity) or value > participation * liquidity:
                        if terminal_policy == "error":
                            raise ValueError(f"Terminal liquidation exceeds capacity for {s}")
                        writeoff += value
                        del positions[s]
                        continue
                    slip = impact_bps / 10000 * np.sqrt(value / liquidity)
                    execution = value * (1 - slip)
                    fee = charges(day, "sell", execution)
                    cash += execution - fee
                    fee_total += fee
                    impact_total += value * slip
                    traded += value
                    fills.append(
                        {
                            "date": str(day.date()),
                            "symbol": s,
                            "side": "sell",
                            "value": execution,
                            "fee": fee,
                            "reason": "terminal_close",
                            "cost_regime": cost_regime(day, cost_model, cost_before_coverage),
                        }
                    )
                del positions[s]
        exposure = sum(units * marks[s] for s, units in positions.items())
        equity = cash + exposure
        net = equity / previous - 1
        cost = (fee_total + impact_total) / previous
        rows.append(
            dict(
                date=day,
                **{"return": net + cost},
                cost=cost,
                turnover=traded / previous,
                equity=equity,
                exposure=exposure / equity if equity else 0.0,
                stale_holdings=len(stale),
                writeoff=writeoff,
                fees=fee_total,
                impact=impact_total,
                rebalance_session=scheduled,
                filtered_untradable=filtered_untradable if scheduled else 0,
                filtered_liquidity=filtered_liquidity if scheduled else 0,
                eligible_without_signal=missing_signals if scheduled else 0,
                cash=cash,
                **diagnostics,
            )
        )
        if cash < -1e-6 or equity <= 0:
            raise ValueError("Costs exhaust account cash/equity; no borrowing is implemented")
        previous = equity
    frame = pd.DataFrame(rows).set_index("date")
    frame["bench"] = market.benchmark_returns
    return frame, pd.DataFrame(fills)
