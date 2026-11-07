# Roadmap and acceptance gates

## v0.1 — research foundation (implemented)

Daily CSV/Parquet validation; source snapshot bank; Qlib conversion/expressions; momentum/Ridge/LightGBM comparison; chronological label-boundary purging; selected-model Qlib portfolio simulation; standalone report and compact brief; four resource modes; membership audit; portable AI guidance and setup documentation.

Acceptance: real Qlib integration test completes without credentials; cost and turnover are nonzero; invalid bars, duplicates, unsafe IDs and misaligned calendars fail; label endpoints do not cross split boundaries; reports expose limitations.

## v0.2 — historically valid universe and stronger evaluation (planned)

Stable instrument master, source correction ledger, multiple historical membership intervals, publication-time handling, delisted price coverage, dated corporate actions, rolling/walk-forward evaluations and explicit experiment registry.

Acceptance: hand-calculated removal/re-entry and corporate-action fixtures; no future knowledge in eligibility/features; no disappearance of held delisted instruments; stable results when future-only data changes; verified train-only preprocessing in every fold.

## v0.3 — India execution realism and richer dashboards (planned)

Versioned fees/taxes, dated instrument bands, liquidity/capacity constraints, delayed-fill sensitivity, portfolio exposures, confidence intervals, factor quantiles, rolling performance and run comparison.

Acceptance: manually verified cost examples and denied/unfillable-order scenarios; documented benchmark comparability; every dashboard metric linked to source records and definitions.

## v0.4 — provider and paper integration (planned)

Dhan data adapter first, Zerodha later; incremental ingestion; scheduled monitoring; paper intents/fills/positions; token health and reconciliation. Keep public repo free of user data and secrets.

Acceptance: mocked broker failures plus read-only integration checks; retry/idempotency tests; restored-state reconciliation; observed paper performance separate from historical research.

## Later — execution and advanced research (not implemented)

Separately authorized live pilot after applicable broker/regulatory checks; intraday and derivatives data models; optional bounded RD-Agent experimentation; local AI or API integrations with usage accounting.

Options require expiry/strike/right, historical contract identities, quotes, rolls, exercise/settlement and fill assumptions. Theoretical prices cannot replace observed executable history. Autonomous factor search requires budgets and multiple-testing controls, not just an LLM loop.
