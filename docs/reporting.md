# Read reports without over-interpreting them

The standalone HTML report works offline and makes no external requests. It is an initial research report, not a hosted live dashboard. Open it directly or serve it privately as described in [VPS operation](vps.md).

## Portfolio metrics

All returns are ratios: 0.05 means 5%. `total_return_net` compounds Qlib daily return minus daily cost. `annualized_return_net` extrapolates using 252 sessions and is unstable for short samples. `max_drawdown` compares wealth against initial capital and all subsequent peaks; it does not predict the largest future loss.

Sharpe uses zero risk-free return and daily standard deviation. It does not capture liquidity, skewness, gap risk, estimation uncertainty or all serial dependence. A large short-sample Sharpe is not a reason to deploy.

The benchmark is whatever series you supplied. A price index excludes reinvested dividends; comparing it to a dividend-adjusted strategy can be unfair. The benchmark is close-to-close while the strategy begins at its first trading open. Explain this first-day difference when comparing short studies.

Mean turnover describes trading intensity. Summed daily cost ratios are a descriptive total, not an exact rupee cost; `portfolio.csv` includes Qlib's cumulative `total_cost` column for that purpose. The equity curve retains final positions at marked value, so hypothetical liquidation costs are not included.

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
