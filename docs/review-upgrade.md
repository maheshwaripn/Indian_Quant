# Review implementation and operating guide

## 1. Install and prove the environment

Use README installation in a fresh virtual environment. Run `indian-quant doctor`, then `indian-quant demo`. The demo is fictional and intentionally carries a no-edge warning. Read `brief.json`, then `report.html`, then only the CSV needed for your question. Computation and charts run in Python with zero AI calls. Alpha158 and repeated null simulations cost CPU, not tokens.

## 2. Prepare and preserve data

Choose licensed broker history, your own archive or a permitted source. Convert NSE cash bhavcopies with:

```bash
indian-quant bhavcopy /path/day1.csv /path/day2.csv --output /path/raw-bars.csv
indian-quant calendar-build --start 2026-01-01 --end 2026-11-06 --output /path/sessions.txt
```

Conversion sets factor=1 and leaves raw OHLC unchanged. It does not solve splits, dividends, symbol identity or missing delisted companies. Research writes suspected_actions.json using Trader's split-like-gap heuristic; false positives and missed/reverse splits are possible. Audit and adjust these before research. The bundled calendar covers 2026 only, including special-session dates; extend with `--extra /path/calendar.json` for verified earlier years. Unknown years fail. The calendar is daily eligibility, not a complete intraday auction schedule.

Import adjusted bars into the immutable bank with provider, licence, adjustment convention and retrieval date. Retain rejected rows and correction evidence separately; never silently fill a delisted name with zero or repeat its last quote as an executable price.

## 3. Reconcile historical membership

```bash
indian-quant membership-audit /path/membership.csv --output /path/audit.json
```

Nifty 50/100/200/500 cardinalities are recognised. Research `--expected-size N` supports other specified universes. Fix transitions using source evidence; do not change 501 to 500 by arbitrary deletion. Missing `available_date` requires an explicit effective-date knowledge assumption. The supplied NiftyHistory raw dataset is not bundled and its known conflicts remain unresolved. A clean membership file still needs prices for removed names.

## 4. Predeclare and run

Example, after data and fee coverage checks:

```bash
indian-quant run --data /path/bars.parquet --calendar /path/sessions.txt \
  --benchmark NIFTY50 --membership /path/reconciled.csv --index Nifty500 \
  --assume-membership-known --evaluation walk-forward --train-years 3 --valid-years 1 \
  --horizon 5 --feature-set alpha158 --rebalance monthly --hold-buffer 5 \
  --topk 20 --min-turnover 10000000 --participation 0.01 --impact-bps 25 \
  --turnover-limit 0.5 --cost-model proportional --buy-cost 0.0015 --sell-cost 0.0015 \
  --null-draws 99 --mode lab --output workspace/runs/predeclared-study-001
```

These numbers illustrate syntax, not recommended investment settings. Older multi-year studies can explicitly select `--cost-before-coverage proportional` with documented buy/sell rates before coverage (see [issue #1 resolution](issue-1-resolution.md)). Without that bridge, `--cost-model india --broker discount` is limited to 2023-04-01 through 2026-11-08. Do not pass the knowledge-assumption flag if you have not accepted it. On a short dataset use `--evaluation holdout`; insufficient yearly folds fail. Omit `--open-final` until settings are frozen. Use a new output directory for every attempt. Review resources before raising null draws (9–999); the parent CLI kills jobs exceeding the selected profile timeout or explicit `--timeout-hours` budget.

## 5. Read the evidence

| Artifact | Question answered |
|---|---|
| protocol.json | What settings were fixed before fitting? Which final year is closed? |
| manifest.json | Which data/code versions, fold selections, limitations and uncertainty checks apply? |
| predictions.csv | What scores and available future labels were evaluated? |
| portfolio.csv / fills.csv | Where did capital, fees, impact, exposure and stale holdings go? Were final sales charged? |
| equal_weight.csv | Does a simpler portfolio explain the performance? |
| ic.csv | Is ordering skill persistent or concentrated in a few dates? |
| deciles.csv | Do higher predicted ranks correspond to higher gross forward returns? |
| report.html | How do the results and cautions fit together? |

Bootstrap intervals are conditional estimates, not worst-case loss bounds. The shuffle p-value is a resampling tail frequency, not the probability the strategy is false. The first nonpositive tested cost multiplier is a coarse cost-stress threshold; nonmonotonic sizing prevents treating it as exact breakeven. Report losing years and the full trial history. A blank statistic is unavailable, not zero.

## 6. Choose the next investigation

If results fail, first distinguish missing data, implementation error, costs, liquidity and chance. Ask the assistant to explain missing assumptions, offer alternatives and record skipped checks. Change one justified item in a new predeclared experiment; do not optimise until a desired Sharpe appears. A successful synthetic or historical run authorises no live deployment.

## Compatibility and upgrade path

Qlib is pinned to 0.9.7. It uses region US as the supported data initialization base; Indian assumptions live in the local ledger/shared core. Python 3.11/3.12 remain the tested installation target: Qlib 0.9.7 has no CPython 3.13 wheel on PyPI when checked. Do not add a nominal CI version that requires an untested source build. Upgrade Qlib only in an isolated environment, rerun expression semantics, sparse-history accounting, purge and end-to-end fixtures, compare saved outputs, then update the pin and validation record.
