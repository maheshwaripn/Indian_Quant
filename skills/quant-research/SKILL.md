---
name: quant-research
description: Turn a trading or factor idea into an explicit Indian Quant research specification, evaluate missing assumptions, and run bounded experiments.
---
Read ../../docs/research.md and ../../docs/roadmap.md. Distinguish implemented research from implemented membership/walk-forward features and remaining execution limitations.

Create a research card covering hypothesis, universe, source/availability, signal time, later execution time, horizon/exits, portfolio sizing, costs/liquidity, baseline, validation, trial budget and failure criteria. Explain each missing choice and offer defaults, customization or a recorded skip. Never invent a user's risk preference or claim a skipped check passed.

Use Python and existing commands for calculations. Inspect data provenance and calendar first. Preserve every experiment and failed hypothesis. Fit preprocessing only on training data; purge overlapping labels. Never select or retune using the test results and still call them untouched evidence.

Read brief.json before larger outputs. Explain whether evidence supports, contradicts or fails to resolve the hypothesis. Recommend one justified next experiment, not an unbounded parameter search. Label fixed-universe, missing delisting, cost and execution limitations. Do not promote to live trading or alter risk controls automatically.
