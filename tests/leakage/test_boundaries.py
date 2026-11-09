import numpy as np
import pandas as pd
import pytest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from indian_quant.evidence import fit_candidate, select_model
from indian_quant.research import split_panel


def panel(dates):
    ix = pd.MultiIndex.from_product([["A", "B", "C"], dates], names=["instrument", "datetime"])
    values = np.arange(len(ix), dtype=float)
    return pd.DataFrame({"signal": values, "label": values / 10}, index=ix)


def test_future_target_cannot_change_training_scaler_or_imputer():
    dates = pd.bdate_range("2024-01-01", periods=40)
    train, target = panel(dates[:20]), panel(dates[25:])
    train.iloc[0, 0] = np.nan
    model = make_pipeline(SimpleImputer(), StandardScaler(), Ridge())
    _, first, audit1 = fit_candidate(model, train, target, ["signal"])
    changed = target.copy()
    changed["signal"] += 1e9
    changed["label"] = -1e12
    _, second, audit2 = fit_candidate(model, train, changed, ["signal"])
    np.testing.assert_array_equal(first[0].statistics_, second[0].statistics_)
    np.testing.assert_array_equal(first[1].mean_, second[1].mean_)
    np.testing.assert_array_equal(first[2].coef_, second[2].coef_)
    assert audit1["training_frame_sha256"] == audit2["training_frame_sha256"]
    assert not hasattr(model[1], "mean_")  # cloning prevents cross-fold retained fitting state


def test_future_training_row_is_rejected():
    dates = pd.bdate_range("2024-01-01", periods=40)
    with pytest.raises(ValueError, match="strictly precede"):
        fit_candidate(Ridge(), panel(dates), panel(dates[20:]), ["signal"])


def test_missing_validation_scores_do_not_pick_arbitrary_model():
    with pytest.raises(ValueError, match="usable validation IC"):
        select_model({"momentum": None, "ridge": float("nan")})
    assert select_model({"momentum": 0.1, "ridge": -0.5}) == "momentum"


@pytest.mark.parametrize("horizon", [1, 5, 20])
def test_label_end_stays_before_next_segment(horizon):
    dates = pd.bdate_range("2020-01-01", periods=200)
    pieces, _ = split_panel(panel(dates), dates, horizon=horizon)
    for name, boundary in [("train", dates[120]), ("valid", dates[160])]:
        latest = pieces[name].index.get_level_values("datetime").max()
        assert dates[dates.get_loc(latest) + horizon + 1] < boundary


def test_qlib_features_ignore_changed_future_prices(tmp_path):
    # Separate Qlib processes prevent cache reuse from concealing a causal failure.
    import subprocess
    import sys

    from indian_quant.data import synthetic

    original = synthetic(tmp_path / "before.csv", sessions=80, instruments=3)
    changed = original.copy()
    changed.loc[changed.date > sorted(original.date.unique())[49], ["open", "high", "low", "close"]] *= 7
    changed.to_csv(tmp_path / "after.csv", index=False)
    script = """
import sys
from pathlib import Path
import pandas as pd
import qlib
from qlib.data import D
from indian_quant.data import validate, write_qlib
from indian_quant.research import FEATURES
source, destination = map(Path, sys.argv[1:])
bars = validate(pd.read_csv(source))
dates = pd.DatetimeIndex(sorted(bars.date.unique()))
provider = write_qlib(bars, destination / 'qlib', dates)
qlib.init(provider_uri=str(provider), region='us', kernels=1, expression_cache=None, dataset_cache=None)
features = D.features(['DEMO00'], list(FEATURES.values()), start_time=dates[30], end_time=dates[49])
features.to_csv(destination / 'features.csv')
"""
    for name in ("before", "after"):
        subprocess.run(
            [sys.executable, "-c", script, str(tmp_path / f"{name}.csv"), str(tmp_path / name)],
            check=True,
            timeout=60,
        )
    before = pd.read_csv(tmp_path / "before/features.csv")
    after = pd.read_csv(tmp_path / "after/features.csv")
    pd.testing.assert_frame_equal(before, after)
