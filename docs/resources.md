# Resource profiles and token discipline

Use `indian-quant modes` to see authoritative profile settings. Start with `essential`; expand only after measuring a representative run. `vps` means conservative unattended settings, not unlimited autonomy or automatically installed services.

## Enforced in the CLI

- Input row and instrument budgets are checked. CSV reading stops at row cap + 1; Parquet metadata is checked before loading.
- Qlib worker count and LightGBM threads use the profile cap, limited by detected CPUs.
- OpenMP/BLAS thread environment variables are set before scientific imports in CLI research workers.
- The parent CLI runs research with a wall-clock timeout.
- Reports use three fixed model candidates and a bounded brief size.
- Output directories cannot be reused by the research runner.

## Not enforced as hard isolation

RAM and disk usage are not sandboxed. A very wide/malformed input can still consume memory before validation; only process trusted research files. Import/audit commands do not have research timeouts. Direct Python calls to `research.run` bypass the parent CLI timeout. A killed process may leave partial artifacts; only completed manifests should be analysed.

On a shared VPS, add OS service limits for memory, CPU and process counts. Threads and subprocess termination behaviour depend on platform; use a service/container process boundary for strict enforcement. The initial supported platform is Linux.

## AI costs

The package makes zero AI calls. The resource modes do not meter your external assistant or subscription. Ask the assistant to read only one relevant skill plus the compact brief. Require a proposed call/trial budget before adding future external API automation.

Keep computation in Python, cache unchanged datasets, and preserve manifests so new sessions can resume without rereading large histories. Do not upload millions of price rows into chat. Do not describe a short character count as an exact token count: tokenization depends on the model.

## Long historical studies

Lab accepts up to 2,000 distinct historical instruments (including the benchmark) and 3,000,000 rows. This is a total-history cap, not an active daily membership limit. The 24 GB memory recommendation is advisory; Qlib feature matrices can require substantial memory. Measure a representative input before scaling.

The default lab timeout remains two hours. `--timeout-hours 8` explicitly permits eight hours; the supported override is greater than zero and at most 168 hours. It changes wall-clock time only, not thread or input budgets. Keep the parent CLI running: do not bypass its process-group cleanup with `--worker`.

Price and lagged-liquidity arrays are prepared once and reused across sequential portfolio/null trials. Null draws retain their seeded ordering; no parallel trial workers are introduced. Python callers reusing a prepared market must keep its source frame unchanged and use the same calendar, dates and benchmark.

The CLI sets `MLFLOW_DISABLE_AGENT_HINT=1` before Qlib imports to silence MLflow's unsolicited agent hint. An explicit user environment setting is preserved; this does not suppress research progress or errors.
