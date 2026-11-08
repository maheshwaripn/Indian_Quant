"""Audit source membership snapshots without silently inventing corrections."""

import ast
import csv
import json
from datetime import date


def symbols(value):
    value = value.strip()
    if not value:
        return set()
    if value.startswith("["):
        parsed = ast.literal_eval(value)
        if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
            raise ValueError("Expected list of symbol strings")
        return {s.strip() for s in parsed if s.strip()}
    return {s.strip() for s in value.split(",") if s.strip()}


def audit(path, expected_size=None):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Empty membership file")
    required = {"effective_date", "index_type", "inclusions", "exclusions", "symbols"}
    if not required <= rows[0].keys():
        raise ValueError(f"Expected columns: {sorted(required)}")
    previous = {}
    issues, snapshots = [], []
    for row in rows:
        effective = date.fromisoformat(row["effective_date"])
        index = row["index_type"]
        members = symbols(row["symbols"])
        added, removed = symbols(row["inclusions"]), symbols(row["exclusions"])
        normalized = index.lower().replace(" ", "").replace("_", "")
        size = expected_size or {"nifty50": 50, "nifty100": 100, "nifty200": 200, "nifty500": 500}.get(
            normalized
        )
        if size is None:
            issues.append({"date": str(effective), "index": index, "issue": "unknown_index_size"})
        if size is not None and len(members) != size:
            issues.append(
                {
                    "date": str(effective),
                    "index": index,
                    "issue": "member_count",
                    "count": len(members),
                    "expected": size,
                }
            )
        if index in previous:
            previous_date, previous_members = previous[index]
            if effective <= previous_date:
                raise ValueError("Membership dates must be strictly increasing within each index")
            expected = (previous_members - removed) | added
            if expected != members:
                issues.append(
                    {
                        "date": str(effective),
                        "index": index,
                        "issue": "transition_mismatch",
                        "unexpected": sorted(members - expected),
                        "missing": sorted(expected - members),
                    }
                )
        previous[index] = effective, members
        snapshots.append(
            {
                "effective_date": str(effective),
                "index_type": index,
                "members": sorted(members),
                "available_date": row.get("available_date", ""),
            }
        )
    return {
        "source": "https://niftyhistory.in/",
        "rows": len(rows),
        "issues": issues,
        "snapshots": snapshots,
        "structural_checks_passed": not issues,
        "research_eligible": False,
        "limitations": [
            "Availability/publication timestamps not supplied; effective dates alone do not prove PIT knowledge",
            "No alias corrections inferred; no market-price or delisting coverage established",
            "Research requires a clean selected index and explicit availability assumptions",
        ],
    }


def write_audit(source, destination):
    result = audit(source)
    with open(destination, "x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    return {
        "rows": result["rows"],
        "issues": len(result["issues"]),
        "research_eligible": result["research_eligible"],
    }


def eligibility(path, index, calendar, expected_size=None, assume_known=False):
    """Return date-aware membership and Qlib inclusive instrument intervals.

    available_date means known before that session's open; effective-only histories
    require an explicit assumption. No membership is inferred before the first row.
    """
    import pandas as pd

    result = audit(path, expected_size)
    if any(issue["index"] == index for issue in result["issues"]):
        raise ValueError("Membership audit failed for selected index; reconcile source explicitly")
    rows = [row for row in result["snapshots"] if row["index_type"] == index]
    if not rows:
        raise ValueError("Selected index is absent from membership file")
    snapshots = []
    for row in rows:
        available = row["available_date"]
        if not available and not assume_known:
            raise ValueError("Membership requires available_date or --assume-membership-known")
        effective = pd.Timestamp(row["effective_date"])
        known = pd.Timestamp(available) if available else effective
        if known > effective:
            raise ValueError(
                "Late publication requires reconciled dated membership; refusing retroactive eligibility"
            )
        snapshots.append((effective, set(row["members"])))

    def members(day):
        prior = [values for effective, values in snapshots if effective <= day]
        return prior[-1] if prior else set()

    intervals, starts = [], {}
    previous = None
    for day in calendar:
        today = members(day)
        for symbol in set(starts) - today:
            intervals.append((symbol, starts.pop(symbol), previous))
        for symbol in today - set(starts):
            starts[symbol] = day
        previous = day
    intervals.extend((symbol, start, previous) for symbol, start in starts.items())
    return members, intervals
