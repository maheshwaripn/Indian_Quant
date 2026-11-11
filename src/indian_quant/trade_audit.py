"""Holding-episode accounting from actual simulated fill cash flows."""

import pandas as pd

COLUMNS = [
    "trade_id",
    "symbol",
    "entry_date",
    "exit_date",
    "holding_days",
    "buy_quantity",
    "sell_quantity",
    "writeoff_quantity",
    "entry_value",
    "exit_value",
    "fees",
    "impact",
    "net_pnl",
    "return_on_buy_outlay",
    "exit_reason",
]


def round_trips(fills):
    rows = []
    for trade_id, group in fills.groupby("trade_id", sort=False):
        if group.iloc[-1].position_after != 0:
            raise ValueError("Round-trip report requires closed holdings")
        buys, sells = group[group.side == "buy"], group[group.side == "sell"]
        entry, exit_ = group.date.iloc[0], group.date.iloc[-1]
        paid, received, fees = buys.value.sum(), sells.value.sum(), group.fee.sum()
        outlay = paid + buys.fee.sum()
        pnl = received - paid - fees
        rows.append(
            {
                "trade_id": trade_id,
                "symbol": group.symbol.iloc[0],
                "entry_date": entry,
                "exit_date": exit_,
                "holding_days": (pd.Timestamp(exit_) - pd.Timestamp(entry)).days,
                "buy_quantity": buys.quantity.sum(),
                "sell_quantity": sells.quantity.sum(),
                "writeoff_quantity": group.loc[group.side == "writeoff", "quantity"].sum(),
                "entry_value": paid,
                "exit_value": received,
                "fees": fees,
                "impact": group.impact.sum(),
                "net_pnl": pnl,
                "return_on_buy_outlay": pnl / outlay if outlay else None,
                "exit_reason": group.reason.iloc[-1],
            }
        )
    return pd.DataFrame(rows, columns=COLUMNS)


def summarize(trades):
    count = len(trades)
    return {
        "closed_holdings": count,
        "win_rate": float((trades.net_pnl > 0).mean()) if count else None,
        "mean_holding_calendar_days": float(trades.holding_days.mean()) if count else None,
        "net_pnl": float(trades.net_pnl.sum()),
        "best_trade_pnl": float(trades.net_pnl.max()) if count else None,
        "worst_trade_pnl": float(trades.net_pnl.min()) if count else None,
        "writeoff_holdings": int((trades.writeoff_quantity > 0).sum()),
        "definition": "One flat-to-flat holding episode including all additions, partial exits and terminal writeoffs; impact is already embedded in fill values; fractional adjusted units, not broker lots.",
    }


def exposure_warning(portfolio, target):
    mean = float(portfolio.exposure.mean())
    if mean >= 0.8 * target:
        return None
    columns = [c for c in portfolio if c.startswith("buy_unfilled_")]
    totals = portfolio[columns].sum()
    if totals.sum() > 0:
        cause = totals.idxmax()
        explanation = f"Largest recorded unfilled-buy constraint: {cause} ({totals.max():.2f} currency units over all attempts)."
    else:
        counts = portfolio[["eligible_without_signal", "filtered_liquidity", "filtered_untradable"]].sum()
        explanation = (
            f"Largest recorded candidate exclusion: {counts.idxmax()} ({int(counts.max())} candidate-sessions)."
            if counts.sum() > 0
            else "No binding buy constraint recorded; inspect cadence, target availability and final liquidation."
        )
    return {
        "severity": "WARNING",
        "code": "LOW_DEPLOYMENT",
        "message": f"Mean end-of-session exposure {mean:.1%} is below 80% of the {target:.0%} target. {explanation} Attribution is descriptive, not causal; terminal liquidation is included.",
    }
