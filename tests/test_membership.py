import csv

import pytest

from indian_quant.membership import audit, symbols


def test_symbols():
    assert symbols("A,B") == {"A", "B"}
    assert symbols("['A', 'B']") == {"A", "B"}


def test_transition_flagged(tmp_path):
    path = tmp_path / "history.csv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["effective_date", "index_type", "inclusions", "exclusions", "symbols"])
        writer.writerow(["2020-01-01", "Nifty500", "A,B", "", "A,B"])
        writer.writerow(["2020-02-01", "Nifty500", "C", "A", "A,B,C"])
    result = audit(path)
    assert not result["research_eligible"]
    assert any(i["issue"] == "transition_mismatch" for i in result["issues"])


def test_no_code_execution():
    with pytest.raises((ValueError, SyntaxError)):
        symbols('[__import__("os").getcwd()]')
