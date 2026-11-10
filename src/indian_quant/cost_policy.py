"""Explicit policy around the pinned shared cost engine; never invent historical taxes."""

from datetime import date

# Coverage of the exact shared-core revision pinned in pyproject.toml.
INDIA_FIRST = "2023-04-01"
INDIA_LAST = "2026-11-08"


def cost_regime(day, model, before_coverage="error"):
    if model not in ("india", "proportional") or before_coverage not in ("error", "proportional"):
        raise ValueError("Unknown fee model or pre-coverage policy")
    day = date.fromisoformat(str(day)[:10]).isoformat()
    if model == "proportional":
        return "proportional"
    if day < INDIA_FIRST:
        if before_coverage == "proportional":
            return "proportional_bridge"
        raise ValueError(
            f"India fee coverage starts {INDIA_FIRST}; explicitly use --cost-before-coverage proportional with --buy-cost/--sell-cost assumptions"
        )
    if day > INDIA_LAST:
        raise ValueError(
            f"India fee coverage ends {INDIA_LAST}; pre-coverage bridge does not extrapolate future rates"
        )
    return "india"


def coverage(dates, model, before_coverage, buy_cost, sell_cost):
    regimes = {}
    for day in dates:
        key = cost_regime(day, model, before_coverage)
        regimes.setdefault(key, []).append(str(day)[:10])
    return {
        "before_coverage_policy": before_coverage,
        "india_verified_interval": [INDIA_FIRST, INDIA_LAST],
        "valuation_sessions": {
            key: {"first": values[0], "last": values[-1], "sessions": len(values)}
            for key, values in regimes.items()
        },
        "bridge_buy_rate": buy_cost,
        "bridge_sell_rate": sell_cost,
        "note": "Coverage applies to portfolio valuation/execution dates, not training history. Proportional bridge is an explicit aggregate assumption, not historical statutory tax reconstruction.",
    }
