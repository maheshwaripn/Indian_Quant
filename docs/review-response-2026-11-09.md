# Review response — 9 November 2026

The supplied review evaluated public structure/documentation, not a reproduced code audit. Several findings describe v0.1. Main already contained the v0.2 implementation before this review arrived. The review's maturity score and 4–6 week estimates are opinions, not validated project measurements.

| Recommendation | Current disposition |
|---|---|
| Walk-forward before more models | Annual rolling train/validation/test already implemented. This update adds fold evidence, model timing and dispersion. Quarterly/monthly retraining, expanding windows and configurable embargo remain future work. |
| Historical membership in eligibility | Already implemented for training/prediction and execution, including re-entry. Clean snapshots and availability assumptions are required. Stable IDs, event history and authoritative missing/delisted coverage remain open. |
| Indian component costs | Already shared with Trader and pinned by commit. Covered dates are explicit. Statutory tables are not strategy constants. External versioned rate configuration and per-fill exported component breakdown remain open. |
| Liquidity and partial fills | Prior average turnover, per-order participation, turnover budget, partial fills, missing quotes and square-root impact already implemented. Circuit rules, calibrated volatility/spread impact and ideal-versus-executable comparisons remain open. |
| Corporate actions | Snapshot preservation and split-like anomaly warnings exist. No event-driven corporate-action engine or automatic rights/merger/delisting reconstruction is claimed. |
| Leakage regression tests | Dedicated leakage and point-in-time tests added: training isolation, future training rejection, purge horizons, model selection and historical membership causality. They cannot detect arbitrary semantic leakage in vendor data. |
| Benchmark suite | Index series, equal-weight and repeated random rankings already present. Same-cadence and monthly momentum portfolios added. Sector-neutral and dated risk-free comparisons need licensed historical inputs. |
| Statistical confidence | Block return/Sharpe/drawdown intervals, HAC IC t and a three-model max-t check already present. Fold dispersion added. DSR, PBO and broad hypothesis correction require a sufficiently complete trial ledger and valid assumptions; they are not interchangeable badges. |
| Declarative configuration | CLI resolves parameters into protocol.json. Registration time, feature hash and candidate/selection metadata added. This is not a YAML experiment loader, proof of advance registration, or complete cross-run trial count. |
| Decision-use reporting | Quality and validity panels, fold metrics and momentum comparisons added. Sector/market-cap/factor exposures are explicitly unavailable without dated classifications. |
| Engineering/release | Existing clean Ubuntu 3.11/3.12 integration checks retained; build-artifact smoke checks added, changelog repaired. Full dependency locking, SBOM, vulnerability/type checks, dependency update automation and signed releases remain planned. No signing key or signed-tag claim is fabricated. |

## Evidence rather than automatic approval

The suggested threshold of positive IC in at least 60% of folds is reported only when there is more than one fold and all folds have usable IC. It is a descriptive screen, not a statistically established acceptance standard. Unknown regime coverage cannot be assumed to pass. No run is automatically labelled a trading candidate. Thresholds must be chosen before inspection and considered with cost, liquidity, missing history and all attempted trials.

A shifted feature is not guaranteed to improve results; likewise a single shuffled-label run is not guaranteed to produce IC exactly zero. Tests should verify causal isolation and use distributions under stated nulls, not encode a desired performance outcome. Future-adjusted vendor fields cannot be identified merely from numerical values; provenance and event/availability evidence are still needed.

## Delivered artifacts

`folds.json` includes validation choice, training fingerprint, per-model fit/inference duration, IC/ICIR, gross top-minus-bottom quintile label spread, net portfolio metrics and valuation boundaries. `folds.csv` is the flat analysis view. Performance is attributed from the continuous account, so holdings can cross fold boundaries and final exit costs occur once at study end. Daily hit fraction is explicitly a session statistic, not trade win rate.

`momentum.csv` uses the same constraints and rebalance cadence as the selected model. `momentum_monthly.csv` changes only cadence; it is a monthly comparator, not a promise of lower realised turnover. Do not choose a model after seeing these test comparisons and call that selection untouched.

`research_validity` exposes fixed-universe, assumed availability, single-holdout and unresolved-writeoff flags. Prior test access and external trial count remain unknown, not invented as zero. Invalid numerical inputs fail before accepted-input quality metrics are computed. No live-order path was added.

Read the [validity checklist](research-validity-checklist.md), [data mapping guide](data-provider-adapters.md), and [operations runbook](runbook.md).
