# Issue #2 resolution: trade-level audit and meaningful comparisons

[Issue #2](https://github.com/maheshwaripn/Indian_Quant/issues/2) confirms the previous operational fixes on the author's private panel. This release addresses its four requests:

| Request | Resolution |
| --- | --- |
| Warn when deployment is low | Report and compact brief warn below 80% of the ledger's 95% target; identify the largest recorded purchase constraint or candidate exclusion. |
| Audit fills and round trips | Price, quantity, impact, position balance and persistent holding ID in fills; closed episodes and reconciled P&L in trades.csv; explicit writeoff records. |
| Explain missing signals | Document several possible causes and aggregate rebalance-date candidate counts per test year. |
| Headline equal-weight comparison | Show strategy and equal-weight net returns, their difference and a paired 95% block interval next to performance metrics; include compact bounds in brief.json. |

No new flags are required. Run the existing command into a **new** output directory after updating the package, then read report.html, brief.json, fills.csv and trades.csv. Preserve previous completed runs unchanged: old fills do not contain enough information for exact impact-aware reconstruction. See [report definitions](reporting.md) before using the new fields.

Ten regression cases cover zero/nonzero impact, additions/partial exits/re-entry, stale and capacity writeoffs, empty histories, warning thresholds, paired intervals, known cash-flow arithmetic, missing-score counting and end-to-end artifact/brief generation. Tests reconcile trade profits with the portfolio; original execution assumptions remain unchanged. The private NSE panel and external reported returns were not independently rerun here.
