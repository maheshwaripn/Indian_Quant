# Research validity checklist

Complete this checklist before interpreting performance. It is a review record, not an executable approval service. Record evidence paths and mark missing items UNKNOWN or NOT APPLICABLE with reasons. Do not treat an unchecked item as passed.

1. **Purpose and trials:** write the hypothesis, mechanism, primary metric, rejection criteria and trial budget before outcomes. Preserve failures and prior experiments. A per-run timestamp does not establish how many external attempts preceded it.
2. **Data:** verify snapshot hashes, licence, retrieval date, adjustment convention, raw-to-adjusted reconciliation and calendar. Duplicate/invalid OHLC values must fail. Investigate internal missing sessions, zero volumes, unchanged-close streaks and suspected corporate actions.
3. **Universe:** explain fixed versus dated membership, availability dates and stable instrument identity. Supply removed and delisted instruments. Membership eligibility alone cannot establish survivorship-free evidence.
4. **Timing:** signal at close t; later execution; horizon-aware purging; train-only imputation/scaling. Check label coverage. Vendor adjustments and fundamental publication times require independent evidence. Built-in causal expressions cannot certify externally revised data.
5. **Evaluation:** record fold boundaries, training fingerprint, selected model and test metrics. Keep the final year closed until settings are frozen. Disclose prior access as UNKNOWN when it cannot be established. Read IC dispersion and losing folds, not just an average.
6. **Baselines:** compare supplied index series, equal-weight, same-cadence momentum, monthly momentum and random rankings. Index series omit fund implementation costs. Do not silently reselect using these test outcomes.
7. **Costs/execution:** check fee coverage and broker assumptions, participation, gross turnover cap, impact, missing quotes, final liquidation and writeoffs. Daily bars do not establish circuit/auction fillability or executable capacity.
8. **Uncertainty:** read block intervals and null checks with their assumptions. Report all tested models and configurations. Three-model correction does not correct unrecorded research. A 60% positive-IC fold screen does not verify regime robustness.
9. **Exposures:** inspect positions and liquidity concentrations. Sector, market-cap and factor classifications must be dated and supplied; absent exposure statistics are unavailable, not diversified by default.
10. **Decision:** record supported findings, contrary evidence, missing evidence and one justified next experiment. Synthetic results are software evidence only. No checklist or report grants live-execution approval.

Severity meanings: INFO is context; WARNING is a material limitation requiring interpretation; INVALID_RESEARCH is reserved for demonstrated validity failures (invalid input may terminate before a report); EXECUTION_BLOCKED states that the repository has no live execution route. The report labels research EXPLORATORY_ONLY rather than certifying investment quality.
