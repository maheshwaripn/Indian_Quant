import pandas as pd
import pytest

from indian_quant.evidence import fold_dispersion, performance, quality_panel, validity_panel


def test_performance_definitions_and_unavailable_ratios():
    portfolio = pd.DataFrame(
        {"return": [0.1, -0.1], "cost": [0.0, 0.0], "bench": [0.0, 0.0], "turnover": [0.2, 0.4]}
    )
    stats = performance(portfolio)
    assert stats["total_return_net"] == pytest.approx(-0.01)
    assert stats["max_drawdown"] == pytest.approx(-0.1)
    assert stats["positive_session_fraction"] == 0.5
    flat = portfolio.assign(**{"return": 0.0, "cost": 0.0})
    stats = performance(flat)
    assert stats["sharpe_zero_rf"] is None
    assert stats["sortino_zero_target"] is None
    assert stats["calmar"] is None


def test_ic_screen_never_approves_without_regime_evidence():
    folds = [{"rank_ic": x, "total_return_net": 0.1} for x in [0.1, 0.2, 0.1, -0.1, -0.1]]
    result = fold_dispersion(folds)
    assert result["positive_ic_60pct_screen"]
    assert result["candidate_status"].startswith("NOT_ASSESSED")
    folds[0]["rank_ic"] = None
    assert not fold_dispersion(folds)["positive_ic_60pct_screen"]


def test_quality_counts_internal_gaps_without_claiming_delisting_coverage():
    dates = pd.bdate_range("2024-01-01", periods=4)
    bars = pd.DataFrame({"date": dates[[0, 1, 3]], "symbol": "A", "close": 100.0, "volume": [1.0, 0.0, 1.0]})
    result = quality_panel(bars, dates)
    assert result["internal_missing_instrument_sessions"] == 1
    assert result["zero_volume_rows_including_benchmark"] == 1
    assert not result["listing_or_delisting_coverage_verified"]


def test_fixed_universe_is_prominently_exploratory():
    result = validity_panel(False, None, False, "holdout", {"terminal_writeoff": 0})
    assert result["status"] == "EXPLORATORY_ONLY"
    assert any(f["code"] == "FIXED_UNIVERSE" for f in result["flags"])
    assert result["prior_test_access"] == "UNKNOWN"
