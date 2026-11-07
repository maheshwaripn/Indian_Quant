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


def audit(path):
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
        if len(members) != 500:
            issues.append(
                {"date": str(effective), "index": index, "issue": "member_count", "count": len(members)}
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
        snapshots.append({"effective_date": str(effective), "index_type": index, "members": sorted(members)})
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
            "Audit output is not wired into the v0.1 fixed-universe portfolio",
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
