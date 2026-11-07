import json
import os
import subprocess
import sys

import pandas as pd

from indian_quant.research import split_panel


def test_label_end_purged():
    dates = pd.bdate_range("2020-01-01", periods=200)
    index = pd.MultiIndex.from_product([["A", "B"], dates], names=["instrument", "datetime"])
    panel = pd.DataFrame({"label": 1.0}, index=index)
    splits, _ = split_panel(panel, dates)
    assert splits["train"].index.get_level_values("datetime").max() == dates[117]
    assert splits["valid"].index.get_level_values("datetime").min() == dates[120]
    assert splits["valid"].index.get_level_values("datetime").max() == dates[157]
    assert splits["test"].index.get_level_values("datetime").max() == dates[197]


def test_real_qlib_end_to_end(tmp_path):
    subprocess.run(
        [sys.executable, "-m", "indian_quant", "demo", "--workspace", str(tmp_path)],
        check=True,
        timeout=180,
        env={**os.environ, "OMP_NUM_THREADS": "1"},
    )
    run = next((tmp_path / "runs").iterdir())
    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["status"] == "completed"
    assert manifest["versions"]["pyqlib"] == "0.9.7"
    assert manifest["ai_calls"] == 0
    assert manifest["metrics"]["test_sessions"] > 50
    predictions = pd.read_csv(run / "predictions.csv")
    assert predictions.datetime.min() >= manifest["boundaries"]["test_signal_start"]
    portfolio = pd.read_csv(run / "portfolio.csv")
    assert portfolio.cost.sum() > 0
    assert portfolio.turnover.sum() > 0
    assert (run / "report.html").stat().st_size > 3000
    assert len((run / "brief.json").read_text()) <= 4000


def test_prediction_labels_match_next_open(tmp_path):
    # Verify expression semantics against hand-indexed prices, independent of model score.
    import numpy as np
    import qlib
    from qlib.data import D

    from indian_quant.data import synthetic, write_qlib
    from indian_quant.research import LABEL

    bars = synthetic(tmp_path / "bars.csv", sessions=30, instruments=3)
    dates = pd.DatetimeIndex(sorted(bars.date.unique()))
    path = write_qlib(bars, tmp_path / "qlib", dates)
    qlib.init(provider_uri=str(path), region="us", kernels=1, expression_cache=None, dataset_cache=None)
    result = D.features(["DEMO00"], [LABEL], start_time=dates[0], end_time=dates[-1])
    opening = bars[bars.symbol == "DEMO00"].open.to_numpy()
    np.testing.assert_allclose(result.iloc[:-2, 0], opening[2:] / opening[1:-1] - 1, atol=2e-7)
    assert result.iloc[-2:, 0].isna().all()
