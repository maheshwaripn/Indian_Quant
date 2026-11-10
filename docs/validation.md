# Review validation record — 0.2

Local Linux/Python 3.12 checks on 2026-11-08:

- Original 17 tests passed before the extension.
- The expanded suite covers actual Qlib demo execution; missing/delisted-like history; zero-volume non-tradable benchmarks; stale holdings and explicit writeoffs; final-sale charges; weekly turnover limits; Nifty 50 cardinality and removal/re-entry intervals; missing-label eligibility; long-horizon purging; reproducible uncertainty diagnostics; and India fee accounting.
- Separate subprocess integration cases exercise Alpha158 with undefined constant-volume correlations and a multi-year walk-forward run. The latter verifies that no returns or predictions enter the closed final year.
- The first extended walk-forward check exposed a year-boundary label crossing; it was corrected before publication and is covered by the regression test. Alpha158 missing-feature handling is fitted on training data.
- CLI docs, Ruff, package dependency consistency and the synthetic demo are checked. The shared Trader wheel was inspected for its calendar resource.

These are software/accounting checks, not market-performance validation. There has been no real-data alpha evaluation, calibrated impact study, authoritative historical-universe reconciliation, authenticated broker test or live execution. The original user-supplied NiftyHistory file's 137 rows included 49 count warnings and 114 transition conflicts; it remains private and unresolved, not silently repaired.

Qlib 0.9.7 emits upstream pandas/NumPy deprecation warnings. CI targets Ubuntu Python 3.11/3.12; no CPython 3.13 wheel was available for the pinned Qlib release when checked. Native Quant Windows/macOS installation is not certified. Reports are generated as escaped standalone HTML with local SVGs; no claim of browser/viewport visual certification is made.

Check [GitHub Actions](https://github.com/maheshwaripn/Indian_Quant/actions) for the exact commit's result. A historical validation note is not evidence that a later revision passes. Only `status: completed` manifests represent completed runs; preserve failed/partial runs for the trial record.

## Follow-up documentation review — 2026-11-09

New tests verify train-only fitted preprocessing despite perturbed future targets, rejection of future training rows, no arbitrary selection without validation IC, purging for 1/5/20-session labels, and historical membership invariance under future reconstitution changes. A separate-process Qlib test perturbs future prices and verifies earlier feature values remain unchanged. Hand-checked evidence tests cover compounding, drawdown, unavailable ratios, fold screens and incomplete quality coverage. Existing Qlib demo, Alpha158, sparse-history and annual walk-forward integration cases remain mandatory. Package smoke checks verify CLI entry point and distribution metadata from built artifacts. These checks do not certify semantic correctness of vendor adjustments or market execution.

## Issue #1 regression coverage (0.2.2)

Nine additional tests exercise explicit historical fee bridges, resource overrides, custom membership sizes, prepared simulation equivalence and purchase-constraint accounting. The complete suite contains 49 tests. Performance evidence and its synthetic-data limits are recorded in [issue #1 resolution](issue-1-resolution.md).
