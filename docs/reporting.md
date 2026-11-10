# Read reports without over-interpreting them

The standalone HTML report works offline and makes no external requests. It is an initial research report, not a hosted live dashboard. Open it directly or serve it privately as described in [VPS operation](vps.md).

## Portfolio metrics

All returns are ratios: 0.05 means 5%. `total_return_net` compounds Qlib daily return minus daily cost. `annualized_return_net` extrapolates using 252 sessions and is unstable for short samples. `max_drawdown` compares wealth against initial capital and all subsequent peaks; it does not predict the largest future loss.

Sharpe uses zero risk-free return and daily standard deviation. It does not capture liquidity, skewness, gap risk, estimation uncertainty or all serial dependence. A large short-sample Sharpe is not a reason to deploy.

The benchmark is whatever series you supplied. A price index excludes reinvested dividends; comparing it to a dividend-adjusted strategy can be unfair. The benchmark is close-to-close while the strategy begins at its first trading open. Explain this first-day difference when comparing short studies.

Mean turnover describes gross trading intensity. Daily fees and impact are currency values in portfolio.csv; final close sales include their costs. Read uncertainty, yearly returns and baseline results alongside headline performance. See [the operating guide](review-upgrade.md).

## Factor and model evidence

Rank IC is the daily Spearman correlation between predicted scores and the future return label, averaged over eligible days. Positive IC means useful ordering in that sample. It does not prove profitability after costs or an investable edge. Missing/constant cross-sections cannot produce meaningful correlations.

Model selection uses validation only. Inspect test results once against the predeclared hypothesis. Showing every model's test IC is transparent but also creates an opportunity for hindsight selection; record what you decided before reading them.

## Data and operations

The manifest records input hash, versions, revision, resources, assumptions and limitations. A `completed` status proves that this pipeline completed; it does not certify source licensing, adjusted-price correctness or PIT membership.

Data quality is currently represented through validation failures, manifests and membership-audit JSON. Rich gap heatmaps, sector exposures, drift monitoring, confidence intervals, trade attribution and searchable run comparisons are later dashboard work. Do not label absent metrics as passed checks.

The compact `brief.json` is designed for an assistant to read first. It retains major limitations so token savings do not hide important caveats. Read full artifacts only to answer a specific follow-up question.

## Practical review sequence

1. Confirm synthetic versus real-data status and completion.
2. Inspect universe, dates, source and benchmark methodology.
3. Check costs, turnover and execution assumptions.
4. Examine drawdown before annualized return.
5. Compare validation and test ordering skill.
6. Identify the weakest missing evidence and propose one next experiment.

Always separate research simulations, paper observations and actual broker fills. This release produces only research simulations.

## Fold and baseline evidence

`folds.json` preserves validation selection, training fingerprint, fit/inference durations, IC/ICIR and net risk/return statistics; `folds.csv` is the flat view. Fold returns are continuous-account segments, not independently reset portfolios. Cross-fold holdings remain attributed to the current valuation segment and final liquidation occurs once. IC uses available labels; missing labels are counted. ICIR is unannualized mean daily IC / sample standard deviation. Gross quintile label spread is not a costed long-short portfolio. Sortino uses zero-target root-mean-square downside over all sessions; daily positive-session fraction is not trade win rate. Calmar is annualized return / absolute drawdown, unavailable when drawdown is zero.

`momentum.csv` uses the same rebalance, costs and execution controls; `momentum_monthly.csv` changes cadence only. Monthly does not guarantee lower realised turnover. Compare these before claiming machine learning adds value; do not reselect on displayed test results. The report's input-quality panel covers accepted data between each instrument's observed endpoints and cannot prove complete listing/delisting coverage.

Research status remains synthetic-only or exploratory-only. Prior test access and external trial counts are UNKNOWN. See [the validity checklist](research-validity-checklist.md).

## Explaining low exposure

`portfolio.csv` records cash and requested/filled buy notionals. Unfilled requested buys are attributed sequentially to turnover, participation, then available cash/fees; unavailable liquidity is recorded separately. These currency totals explain the algorithm's constraints, not a unique counterfactual estimate of the return lost to cash. Repeated attempts can count the same desired investment on multiple rebalance dates.

`filtered_untradable`, `filtered_liquidity` and `eligible_without_signal` are candidate-session counts on rebalance dates, not currency values. They describe candidates excluded before target purchases and must not be added to unfilled notionals. The report includes aggregate purchase constraints alongside exposure. Weekly/monthly partial fills are reconsidered at the next scheduled rebalance, not automatically topped up every day. Compare cadence deliberately without weakening liquidity limits merely to increase exposure.

The fee-coverage panel and `fills.csv` cost regime identify proportional bridge assumptions separately from verified India fee calculations. A bridge warning remains visible in research validity.
