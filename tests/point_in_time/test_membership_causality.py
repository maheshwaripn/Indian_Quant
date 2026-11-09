import csv

import pandas as pd
import pytest

from indian_quant.membership import eligibility


def write(path, future="C", available="2024-01-01"):
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["effective_date", "available_date", "index_type", "inclusions", "exclusions", "symbols"])
        w.writerow(["2024-01-01", available, "custom", "A,B", "", "A,B"])
        w.writerow(["2024-02-01", "2024-01-25", "custom", future, "A", f"B,{future}"])


def test_future_reconstitution_cannot_change_prior_eligibility(tmp_path):
    path = tmp_path / "members.csv"
    dates = pd.bdate_range("2024-01-01", periods=40)
    write(path)
    before, _ = eligibility(path, "custom", dates, expected_size=2)
    write(path, future="D")
    after, _ = eligibility(path, "custom", dates, expected_size=2)
    for date in dates[dates < "2024-02-01"]:
        assert before(date) == after(date) == {"A", "B"}
    assert before(pd.Timestamp("2024-02-05")) != after(pd.Timestamp("2024-02-05"))


def test_late_publication_cannot_be_backdated(tmp_path):
    path = tmp_path / "members.csv"
    write(path, available="2024-01-02")
    with pytest.raises(ValueError, match="Late publication"):
        eligibility(path, "custom", pd.bdate_range("2024-01-01", periods=40), expected_size=2)
