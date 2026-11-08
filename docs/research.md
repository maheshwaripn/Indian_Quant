# Research design and strategy coaching

## Turn an idea into a research card

Example idea: “Buy strong Nifty 500 momentum stocks.” Before computation, record:

- Mechanism: why should momentum persist, and when might it fail?
- Universe: historical constituents or an explicitly biased fixed cohort?
- Data: adjusted daily prices, benchmark, source dates, available history?
- Signal: exact momentum horizon, ranking, filters and timestamp?
- Execution: when can the signal be known, and at which later price can it trade?
- Portfolio: number of positions, concentration, rebalance, cash allocation?
- Costs: fees, taxes, spread, slippage and liquidity assumptions?
- Evaluation: baseline, untouched period, success/failure criteria and trial budget?
- Failure conditions: data error, regime change, turnover explosion, drawdown or lack of evidence?

Offer the user defaults, alternatives and explanations. A skipped recommendation remains a visible limitation. Do not invent capital, risk tolerance, data coverage or missing strategy rules. Read `skills/quant-research/SKILL.md` when using an assistant.

## Executable protocol

Choose `--horizon 1|5|20`: label is `open[t+horizon+1]/open[t+1]-1`. Features use information through close t. Undefined Alpha158 correlations are retained as missing: Ridge uses a training-fitted median imputer (zero for wholly missing training columns); LightGBM handles missing values natively. Compact features need 20-session warmup; `--feature-set alpha158` uses Qlib's CPU expressions and 60-session warmup. Future label availability never determines which feature-complete stocks can receive predictions. Missing labels reduce IC coverage and are reported.

Holdout splits at 60% and 80%; label endpoints must be strictly before the next segment. Walk-forward uses rolling training years, separate validation years, then one test calendar year. Retraining and validation-only selection repeat annually. The label horizon supplies the purge gap. Last available year remains closed unless `--open-final`; this is a workflow guard, not access control over the source file. Partial first/last calendar years are possible: inspect fold coverage. Require enough history for every fold.

Ridge scaling is fitted on each training fold. Fixed LightGBM settings and momentum are compared on validation rank IC. Test scores are disclosed for every candidate but never used to choose a model. `protocol.json` records settings before fitting. Preserve every run directory, including failures; failed runs are trials too. Record ideas and all external experiments in your research log. A file cannot prevent a human from repeatedly tuning on disclosed results.

## Portfolio accounting

Qlib computes features; `execution.py` is a separate transparent ledger, not Qlib's exchange simulator. Signals from the immediately preceding session execute at the next open. Fractional adjusted units avoid pretending to model historical raw-share rounding. Set `--rebalance daily|weekly|monthly`; weekly means first available simulation session in each Monday–Sunday week, monthly the first in each month. A mid-period test starts with an initial allocation. A hold buffer retains existing names within top-k plus the buffer. Target deployment is 95%; prices, stale holdings and partial fills change actual exposure.

`--turnover-limit` caps ordinary daily gross traded value / opening equity. `--min-turnover` filters prior 20-session average turnover; `--participation` caps each fill against that lagged average, not future same-day volume. `--impact-bps` multiplies the square root of order value / lagged average turnover. These are research assumptions, not calibrated execution forecasts. Zero-volume or missing quotes cannot fill. Removal from membership schedules liquidation at an available quote subject to the same limits. Missing prices retain stale marks; last-known prices are never treated as hindsight delisting settlements.

Final close sells include fees and impact and may exceed the ordinary turnover cap; they must satisfy the liquidity cap. Missing/unfillable final holdings either fail (default) or are explicitly written off with `--terminal-policy writeoff`. The latter is a conservative scenario, not a recovered delisting payoff. Final close auction fillability is not verified.

## Evidence and costs

Use [the step-by-step upgrade guide](review-upgrade.md). India fees come from the same implementation as Trader. The supported date interval is deliberately bounded; choose explicit proportional assumptions for older history and disclose them. Hypothetical stress scales fees and impact, including statutory amounts, to measure sensitivity; this differs from Trader's brokerage-plus-slippage stress convention.

Read net return beside its moving-block interval and the shuffled-score comparison. Cross-sectional shuffling preserves each day's score distribution, features and market returns; it tests ranking association conditional on this dataset, not all possible luck. The three-model check is a block sign-flip max HAC-t of IC, conditional on sign symmetry. It does not correct undisclosed trials, horizons or feature experiments. Few null draws are coarse: 19 cannot report p below 0.05. Increase the predeclared budget, not only after a promising result.

Synthetic prices contain no designed alpha: a high Sharpe does not become success because the code ran. Equal-weight uses all eligible tradable names meeting the liquidity filter with identical execution/cost assumptions. Decile returns are gross label diagnostics, not tradeable portfolio returns. Short samples, concentration, missing delisted history and unstable regimes can invalidate apparent results. Never automatically promote to paper/live trading.
