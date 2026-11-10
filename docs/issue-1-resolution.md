# Issue #1: real-data workflow fixes

This release addresses [issue #1 and its follow-up](https://github.com/maheshwaripn/Indian_Quant/issues/1). The reported private NSE dataset and investment results have not been independently reproduced.

| Feedback | Implemented behavior |
| --- | --- |
| India cost coverage blocks older tests | Explicit proportional bridge before 2023-04-01; verified engine within coverage, future unsupported dates still rejected. Training history is not charged. |
| Historical universe exceeds 1,000 symbols | Lab accepts 2,000 historical instruments within its existing 3 million row budget; advisory RAM becomes 24 GB. |
| Custom index audit requires a size | `membership-audit --expected-size 300`; invalid sizes fail and genuine count mismatches remain findings. |
| MLflow agent hint | Suppressed by default before import; explicit environment preference preserved. |
| Two-hour timeout insufficient | `--timeout-hours 8`, bounded to at most 168 hours, with existing parent process cleanup. |
| Slow sequential null trials and no progress | Reuse aligned prices and lagged liquidity arrays across simulations; write `progress.json` and flushed stderr stages including null draw counts. |
| Low exposure is unexplained | Daily and aggregate requested/filled buys, sequential unfilled notionals and candidate filter counts, explained in the report. |

## Example workflow

Activate the installed virtual environment. Validate your adjusted price panel, independent session calendar and PIT membership source first. Adapt paths and predeclare the study and cost assumptions before running:

```bash
indian-quant membership-audit history.csv --expected-size 300 --output audit.json
indian-quant run --data panel.parquet --benchmark NIFTY500 --output runs/study-01 \
  --mode lab --membership history.csv --index LIQUID300 --expected-size 300 \
  --evaluation walk-forward --train-years 4 --valid-years 1 --horizon 5 \
  --rebalance weekly --topk 20 --null-draws 99 \
  --cost-model india --cost-before-coverage proportional \
  --buy-cost 0.0015 --sell-cost 0.0015 --timeout-hours 8
```

These rates and settings illustrate syntax, not recommended trading assumptions. Add your session calendar and any required membership knowledge acknowledgement using the [operating guide](review-upgrade.md). Keep the final period closed until the protocol is frozen. Each output directory must be new. Read `progress.json` during the run, then require `manifest.json` status `completed` and inspect the report's validity, fee and constraint panels. The pre-coverage bridge is an approximate aggregate cost, not historical statutory tax reconstruction; it does not extend coverage beyond 2026-11-08.

## Validation and performance evidence

Nine new regression tests cover the bridge and its dates, historical symbol budget, custom-size CLI audit, timeout propagation, MLflow environment behavior, prepared-market equivalence, reconciled purchase constraints, liquidity filters and an end-to-end older-date run.

A local synthetic benchmark used 201 instruments including the benchmark, 300 source sessions, 250 valuation sessions, weekly top-20 rebalancing, 2% participation and a 50% turnover cap. The previous implementation at commit `08106aa` took 2.413 seconds per simulation; the prepared implementation took 0.268 seconds, plus 0.142 seconds one-time preparation. Original portfolio columns and fills matched exactly. This is approximately 9x faster for that prepared simulation, not a claim of 9x faster model fitting or the user's complete 853-instrument run. Actual speed and memory depend on input and hardware. Trials remain serial and reproducibly seeded.

No verified historical tax schedule was invented, no liquidity/trading rules were relaxed, and no live trading capability was added. See [resource limits](resources.md), [operations](runbook.md) and [report interpretation](reporting.md).
