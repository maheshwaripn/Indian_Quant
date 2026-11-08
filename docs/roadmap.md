# Implemented scope and remaining acceptance gates

Version 0.2 implements sparse histories, dated membership intervals, annual walk-forward selection, CPU Alpha158, 1/5/20-session labels, a local portfolio ledger, shared India delivery fees, prior-turnover liquidity limits, terminal liquidation, uncertainty diagnostics, baselines and light reports. See [the operating guide](review-upgrade.md) for commands and limitations.

Still open:

- Authoritative stable-ID/alias master, correction ledger, corporate-action adjustment and delisting settlement imports. Gate: independently reconciled real historical universe with event fixtures.
- A tamper-evident cross-run trial registry and enforced access separation for a final holdout. Current protocol files and preserved directories support manual audit; they do not prevent selective reporting.
- Calibrated market impact, historical price bands, raw-share lot rounding, auction fillability, settlement cash constraints and broker-specific DP aggregation. Gate: independent contract-note and unfillable-order reconciliation.
- Rich interactive report comparison, sector/factor exposure and additional dependence-aware diagnostics for every derived metric. Current offline report plus CSVs is an exploratory dashboard, not a complete institutional risk system.
- More verified calendar years and broader dated fee history. Unknown coverage must fail rather than invent dates or rates.
- Broker data adapters, automatic paper fills and separately authorised live execution. None are implemented in Quant.
- Intraday/options research, autonomous factor search, local-model/API orchestration and explicit token metering. These need separate data models and bounded trial controls.

Do not describe membership eligibility as fully survivorship-free without delisted prices and settlement evidence. Do not describe local execution as Qlib's simulator. Each future extension requires meaningful accounting/timing tests and updated documentation.
