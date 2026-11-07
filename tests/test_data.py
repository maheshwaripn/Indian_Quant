import numpy as np
import pandas as pd
import pytest

from indian_quant.data import bank_import, synthetic, validate, write_qlib
from indian_quant.resources import PROFILES, Profile


@pytest.fixture
def bars(tmp_path):
    return synthetic(tmp_path / "bars.csv", sessions=10, instruments=3)


def test_duplicates_rejected(bars):
    with pytest.raises(ValueError, match="Duplicate"):
        validate(pd.concat([bars, bars.iloc[:1]]))


@pytest.mark.parametrize("field,value", [("close", 0), ("factor", -1), ("volume", -1), ("open", np.inf)])
def test_bad_numbers_rejected(bars, field, value):
    bars.loc[0, field] = value
    with pytest.raises(ValueError):
        validate(bars)


def test_bad_ohlc_rejected(bars):
    bars.loc[0, "high"] = 1
    with pytest.raises(ValueError, match="OHLC"):
        validate(bars)


def test_path_traversal_rejected(bars):
    bars.loc[0, "symbol"] = "../secret"
    with pytest.raises(ValueError, match="instrument IDs"):
        validate(bars)


def test_resource_limit(bars):
    with pytest.raises(ValueError, match="resource"):
        validate(bars, Profile(1, 4, 5, 60, 1000, 4))


def test_bank_idempotent_and_provenance_preserved(tmp_path):
    source = tmp_path / "source.csv"
    synthetic(source, sessions=10, instruments=3)
    first = bank_import(source, tmp_path / "bank", PROFILES["essential"], "synthetic")
    assert bank_import(source, tmp_path / "bank", PROFILES["essential"], "synthetic") == first
    assert (first / "bars.parquet").exists()
    with pytest.raises(ValueError, match="provenance"):
        bank_import(source, tmp_path / "bank", PROFILES["essential"], "unrelated")


def test_bin_roundtrip_and_gap_preserved(tmp_path, bars):
    calendar = pd.DatetimeIndex(sorted(bars.date.unique()))
    symbol = bars.symbol.iloc[0]
    part = bars[bars.symbol == symbol].drop(index=2)
    destination = write_qlib(part, tmp_path / "cache", calendar)
    values = np.fromfile(destination / "features" / symbol.lower() / "close.day.bin", dtype="<f4")
    assert values[0] == 0
    assert np.isnan(values[3])
    np.testing.assert_allclose(values[1:3], part.close.iloc[:2], rtol=1e-6)


def test_calendar_mismatch_rejected(tmp_path, bars):
    calendar = sorted(bars.date.unique())[1:]
    with pytest.raises(ValueError, match="outside"):
        write_qlib(bars, tmp_path / "cache", calendar)
