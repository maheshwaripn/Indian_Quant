# Daily data contract, version 1

## Canonical bars

One row represents one stable instrument on one exchange session. CSV and Parquet share the same columns:

| Field | Meaning |
|---|---|
| `date` | Session date, midnight without timezone, interpreted as the Asia/Kolkata exchange session |
| `symbol` | Stable uppercase research ID; letters, digits, underscore and hyphen; never reuse for another security |
| `open,high,low,close` | Positive, consistently adjusted prices; valid OHLC ordering |
| `volume` | Nonnegative volume in units consistent with the adjustment convention |
| `factor` | Positive adjusted-price / raw-price ratio; raw price = adjusted price / factor |

Example: if a historical raw close is 200 and the chosen split-adjusted close is 100, factor is 0.5. Do not independently normalize close without transforming open/high/low and documenting volume. Do not assume dividend, split and bonus adjustments are interchangeable. Provider adjustment methodologies differ; the importer validates numerical integrity, not financial correctness.

The first-release research recipe additionally requires a complete positive-volume panel. Zero-volume bars are rejected for this recipe. For a non-tradable index benchmark, document a positive placeholder volume (e.g. 1); the benchmark is excluded from eligible equities and its volume is not used as a tradable liquidity measure. This exception must never be used to disguise zero-volume equities.

## Calendar

For real-data runs, supply `--calendar sessions.txt`, one ISO date per line, sorted and unique. Cover exactly the study period and verify special sessions and holidays against the exchange. Weekdays are not a substitute for NSE sessions. Do not derive a supposedly authoritative calendar solely from observed stock bars, since an outage could remove an entire session.

The synthetic demo deliberately uses weekdays and is labelled fictional. The Qlib writer retains missing values rather than filling them; the pilot research recipe rejects incomplete panels before simulation.

## Identity and point-in-time roadmap

Price IDs, exchange ticker aliases, ISINs and historical membership are different concepts. Keep a source identity mapping beside the input dataset. The future instrument master will store alias validity intervals and immutable IDs; do not silently equate similarly named securities.

Historical membership needs multiple intervals per instrument, including removal and re-entry. Fundamental information needs `available_at` timestamps, not only fiscal period ends. A later revised value must not replace the value known during the original experiment.

Version 1 validates bars and audits source membership. It does not enforce point-in-time eligibility, automatic corporate actions, fundamental availability or delisted-security recovery. A clean numerical validation result is not evidence that these requirements are satisfied.

## Conversion and compatibility

`write_qlib` creates `calendars/day.txt`, `instruments/all.txt`, and per-instrument float32 feature files. The first float is the start calendar offset. Values are supplied adjusted values, not freshly adjusted values. Float32 introduces precision loss; tests use a tolerance.

The source CSV/Parquet and manifest remain authoritative. Delete and regenerate a derived cache rather than hand-editing binary files. Qlib uses `region='us'` only as a supported initialization base; portfolio settings explicitly choose one-share units and supplied costs. This is not India regulatory or exchange-rule support.
