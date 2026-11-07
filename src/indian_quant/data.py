"""Strict daily-bar contract, content-addressed bank, and derived Qlib cache."""

import hashlib
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

FIELDS = ["open", "high", "low", "close", "volume", "factor"]
COLUMNS = ["date", "symbol", *FIELDS]
SYMBOL = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,63}$")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate(frame, profile=None):
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    df = frame[COLUMNS].copy()
    if df.empty:
        raise ValueError("Empty data")
    if profile and (len(df) > profile.max_rows or df.symbol.nunique() > profile.max_instruments):
        raise ValueError("Input exceeds selected resource profile; partition it or select a larger mode")
    df["date"] = pd.to_datetime(df.date, errors="raise")
    if df.date.dt.tz is not None or not (df.date == df.date.dt.normalize()).all():
        raise ValueError(
            "Daily dates must be timezone-naive midnight session dates (Asia/Kolkata convention)"
        )
    if (
        df.date.isna().any()
        or not df.symbol.map(lambda x: isinstance(x, str) and bool(SYMBOL.fullmatch(x))).all()
    ):
        raise ValueError("Invalid dates or instrument IDs; use stable uppercase safe identifiers")
    if df.duplicated(["symbol", "date"]).any():
        raise ValueError("Duplicate instrument/session; resolve upstream, never silently drop")
    for field in FIELDS:
        df[field] = pd.to_numeric(df[field], errors="raise")
    if not np.isfinite(df[FIELDS].to_numpy()).all():
        raise ValueError("Non-finite numeric values")
    cast = df[FIELDS].to_numpy().astype("float32")
    if not np.isfinite(cast).all() or (cast[:, [0, 1, 2, 3, 5]] <= 0).any():
        raise ValueError("Values cannot be represented safely in Qlib float32 storage")
    if (df[["open", "high", "low", "close", "factor"]] <= 0).any().any() or (df.volume < 0).any():
        raise ValueError("Prices/factors must be positive; volume must be nonnegative")
    if (
        (df.high < df[["open", "close", "low"]].max(axis=1))
        | (df.low > df[["open", "close", "high"]].min(axis=1))
    ).any():
        raise ValueError("Invalid OHLC ordering")
    return df.sort_values(["symbol", "date"]).reset_index(drop=True)


def read_bars(path, profile):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, nrows=profile.max_rows + 1)
    elif path.suffix.lower() == ".parquet":
        import pyarrow.parquet as pq

        if pq.ParquetFile(path).metadata.num_rows > profile.max_rows:
            raise ValueError("Parquet input exceeds row budget")
        df = pd.read_parquet(path)
    else:
        raise ValueError("Use .csv or .parquet")
    return validate(df, profile)


def bank_import(source, root, profile, provenance):
    source, root = Path(source), Path(root)
    df = read_bars(source, profile)
    sha = digest(source)
    target = root / sha
    if target.exists():
        existing = json.loads((target / "manifest.json").read_text())
        if existing["provenance"] != provenance:
            raise ValueError("Snapshot already exists with different provenance; do not silently relabel it")
        return target
    staging = root / (sha + ".partial")
    staging.mkdir(parents=True, exist_ok=False)
    try:
        shutil.copyfile(source, staging / ("source" + source.suffix.lower()))
        if digest(staging / ("source" + source.suffix.lower())) != sha or digest(source) != sha:
            raise ValueError("Source changed during import; retry from a stable snapshot")
        df.to_parquet(staging / "bars.parquet", index=False)
        metadata = {
            "schema_version": 1,
            "sha256": sha,
            "rows": len(df),
            "instruments": df.symbol.nunique(),
            "first_session": str(df.date.min().date()),
            "last_session": str(df.date.max().date()),
            "created_at": datetime.now(UTC).isoformat(),
            "provenance": provenance,
            "canonical_sha256": digest(staging / "bars.parquet"),
            "warnings": [
                "OHLC validation does not establish corporate-action correctness or PIT eligibility"
            ],
        }
        (staging / "manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target


def write_qlib(df, target, calendar):
    """Write Qlib's documented float32 layout; never adjust or fill missing prices."""
    df = validate(df)
    target = Path(target)
    dates = pd.DatetimeIndex(calendar)
    if dates.empty or dates.has_duplicates or not dates.is_monotonic_increasing:
        raise ValueError("Calendar must be nonempty, unique and sorted")
    if not df.date.isin(dates).all():
        raise ValueError("Bars contain sessions outside supplied calendar")
    target.mkdir(parents=True, exist_ok=False)
    (target / "calendars").mkdir()
    (target / "instruments").mkdir()
    (target / "calendars/day.txt").write_text("\n".join(dates.strftime("%Y-%m-%d")) + "\n")
    instruments = []
    for symbol, part in df.groupby("symbol"):
        start, end = dates.get_indexer([part.date.min(), part.date.max()])
        aligned = part.set_index("date").reindex(dates[start : end + 1])
        destination = target / "features" / symbol.lower()
        destination.mkdir(parents=True)
        for field in FIELDS:
            values = np.r_[float(start), aligned[field].to_numpy()].astype("<f4")
            values.tofile(destination / f"{field}.day.bin")
        instruments.append(f"{symbol}\t{dates[start]:%Y-%m-%d}\t{dates[end]:%Y-%m-%d}")
    (target / "instruments/all.txt").write_text("\n".join(instruments) + "\n")
    return target


def synthetic(path, sessions=420, instruments=12, seed=17):
    """Fictional prices/calendar for integration tests, never investment evidence."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-03", periods=sessions)
    rows = []
    for i in range(instruments + 1):
        symbol = "BENCH" if i == instruments else f"DEMO{i:02d}"
        close = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.012, sessions)))
        opening = close * np.exp(rng.normal(0, 0.003, sessions))
        for j, date in enumerate(dates):
            rows.append(
                [
                    date,
                    symbol,
                    opening[j],
                    max(opening[j], close[j]) * 1.01,
                    min(opening[j], close[j]) * 0.99,
                    close[j],
                    1_000_000.0,
                    1.0,
                ]
            )
    frame = pd.DataFrame(rows, columns=COLUMNS)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return frame
