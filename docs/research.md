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

## What the executable recipe does

Five Qlib expressions describe 5/20-session momentum, 20-session volatility, daily range and volume ratio. After a 20-session warmup, the recipe predicts `open[t+2]/open[t+1]-1` using information available through close t.

The calendar splits at 60% and 80%. Training rows whose label endpoint touches validation are removed; validation rows whose label endpoint touches test are removed. Ridge scaling is fitted only on training data. LightGBM uses fixed modest settings. The momentum score is the rules-based baseline. No hyperparameter grid or AI factor search runs.

Choose the model with the greatest mean daily validation rank IC. Report all three test rank ICs for transparency, but do not reselect using them. The chosen model's test signals feed Qlib's top-k dropout strategy. Orders use the next session's open; the account is valued at daily close. Rank scores are not return promises. A one-day label guides selection, while portfolio holdings can persist across days.

The strategy uses a 0.95 deployment setting when constructing purchases, not a guaranteed continuous 95% exposure cap. Price movement and Qlib's rebalance mechanics can change actual exposure. Positions are not liquidated at the final close; the report states this explicitly.

## Costs and execution limits

`--buy-cost` and `--sell-cost` are decimal proportional all-in assumptions, e.g. 0.001 means 0.1%. They are not a verified Indian statutory schedule. Costs are charged through Qlib. The defaults are demonstration assumptions, not recommended live-trading estimates.

The simulator does not model instrument-specific historical price bands, order-book depth, market impact, borrow, futures margin, option assignment or liquidity participation. Positive bar volume does not prove fillability. Treat results as a preliminary hypothetical study. Test higher costs and smaller capacity before making any practical interpretation.

## Avoid learning the test set

Save every attempted hypothesis and parameter choice, including failures. Repeatedly looking at a test period and revising the strategy turns that period into training evidence. Reserve a new untouched period or use a formally designed walk-forward study. This release has one holdout, not a walk-forward engine or multiple-testing correction.

Useful next experiments, each separately justified:

1. Compare against a simple equal-weight or momentum benchmark.
2. Perturb one parameter at a time to inspect stability.
3. Stress costs and delayed execution.
4. Compare market regimes, sectors and liquidity groups.
5. Study whether performance depends on a handful of names/dates.
6. Use historical membership and delisted data before claiming broad Nifty 500 evidence.

A poor recent period is not automatic evidence that the strategy should be retrained or its rules changed. Investigate data issues, implementation differences, random variation, changing liquidity and regime dependence first.

## Evidence ladder

Synthetic integration → audited real-data exploration → untouched evaluation → robustness and capacity checks → paper observation → separately authorized execution pilot.

The current code supports the first two steps and a simple chronological holdout. It does not automatically promote a strategy or place orders.
