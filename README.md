# Indian Quant

**CPU-first Indian equity research with Qlib, reproducible experiments, and optional AI coaching.**

[![Research checks](https://github.com/maheshwaripn/Indian_Quant/actions/workflows/ci.yml/badge.svg)](https://github.com/maheshwaripn/Indian_Quant/actions/workflows/ci.yml)

Run calculations locally. Ask Claude, Codex, Gemini or Copilot to help define hypotheses and interpret compact results. No AI subscription, API key, GPU or market-data credentials are needed for the synthetic demonstration.

## About this project

Indian Quant is an open-source, CPU-first quantitative research foundation for Indian equities, built around Microsoft Qlib. It helps users turn a prepared daily-price dataset into reproducible factor experiments, baseline model comparisons, hypothetical portfolios and understandable research reports.

The project is intended for traders moving toward systematic research, students learning quantitative methods, and developers building transparent local or VPS research workflows. Version 0.2 supports daily cash-equity studies with sparse histories and optional dated membership. No GPU or AI API is required for the supplied research pipeline.

### What you can use it for

- **Create traceable research inputs:** validate CSV/Parquet bars, retain source snapshots and provenance, and produce canonical Parquet datasets with checksums.
- **Use a genuine Qlib workflow:** build a derived binary cache and evaluate Qlib expressions for momentum, volatility, range and volume-based features.
- **Compare simple models before adding complexity:** evaluate a momentum baseline, scaled Ridge regression and a small CPU LightGBM model using chronological training, validation and test segments.
- **Reduce common evaluation mistakes:** fit preprocessing on training data, remove labels that overlap the next evaluation segment, and select the model using validation rather than test results.
- **Simulate a portfolio:** feed the selected model's scores into a local long-only accounting ledger with next-session-open execution, final liquidation, and configurable India delivery or proportional costs. Qlib supplies the features; this ledger is not Qlib's simulator.
- **Review results and reproducibility:** inspect prediction and portfolio files, model comparisons, performance explanations, resource usage and manifests recording data hashes and software versions.
- **Investigate historical membership:** audit a user-supplied NiftyHistory file for count and transition discrepancies before attempting broader point-in-time research.

### Resource-aware research with optional AI coaching

The four profiles—`essential`, `guided`, `lab` and `vps`—offer explicit worker, input-size and research-runtime budgets. RAM recommendations remain advisory. Computation stays in Python, while optional Claude, ChatGPT/Codex, Gemini or Copilot guidance can help define hypotheses, explain assumptions and interpret results.

The generated `brief.json` gives an assistant a compact starting point without uploading the full market history. The package makes no AI API calls and does not meter an external assistant's token use. Local/VPS access depends on the authorized capabilities of the AI client.

### How it relates to Indian Trader Skill

Use **Indian Quant** when the main question concerns factors, predictive models, stock rankings or simulated portfolio behaviour. Use **[Indian Trader Skill](https://github.com/maheshwaripn/Indian_Trader_skill)** for guided strategy formulation, reference trading-rule studies, data workflows and manual paper accounting. The repositories are independently installable companions; research predictions are not automatically converted into broker orders.

### What the first release does not establish

Successful runs demonstrate that the research pipeline works, not that a strategy has a durable market edge. Synthetic examples are software demonstrations. Real-data studies still depend on source quality, corporate-action treatment, universe selection and execution assumptions.

The pipeline offers chronological holdout or yearly walk-forward evaluation, historical membership intervals, uncertainty diagnostics, liquidity constraints and shared Indian cost estimates. It does not make incomplete historical data survivorship-free. Missing settlements, corporate actions, price bands and broker fillability remain material research limitations. See [the review implementation guide](docs/review-upgrade.md).

## Start here

Ubuntu/Linux with Python 3.11 or 3.12 is the first supported target. Qlib has a substantial scientific-Python dependency tree; installation needs internet and disk space even though research can subsequently run offline.

```bash
git clone https://github.com/maheshwaripn/Indian_Quant.git
cd Indian_Quant
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
indian-quant doctor
indian-quant demo
```

Open the printed `workspace/runs/demo-.../report.html` path in your browser. Read the warnings before interpreting the chart. **All demo prices and dates are fictional; results prove software integration, not investment performance.**

Start with [the complete tutorial](docs/getting-started.md), then [choose data](docs/data-bank.md) and [read reports](docs/reporting.md).

## What v0.2 implements

- Immutable data snapshots, sparse per-stock Qlib caches, dated membership including removals and re-entry.
- Compact or Alpha158 CPU features; 1-, 5- or 20-session labels; train-only scaling and horizon-aware purging.
- Holdout or annual walk-forward model selection; final walk-forward year closed by default.
- A local fractional adjusted-unit ledger: daily/weekly/monthly rebalancing, hold buffer, turnover limits, trailing liquidity filters and illustrative square-root impact.
- Shared Indian delivery charges, UDiFF conversion and a bounded 2026 calendar from `indian_market_core`, distributed with Trader and pinned to a specific commit.
- Final sales including costs, explicit handling of stale holdings, equal-weight baseline, bootstrap return intervals, shuffled-score simulations, HAC IC t-statistics, three-model resampling check and cost stress.
- Light standalone reports, yearly returns, IC/decile CSVs, exposure, fills, reproducibility manifests and compact AI briefs.

No broker orders, automated paper fills, options engine, corporate-action repair or certified investability are provided. Resource modes cap workers and runtime, not every allocation of RAM. [Remaining work](docs/roadmap.md) is explicitly separated from tested functionality.

## Four resource modes

| Mode | Worker cap | Row cap | Instrument cap including benchmark | Research timeout | Suggested RAM |
|---|---:|---:|---:|---:|---:|
| essential | 1 | 100,000 | 50 | 10 minutes | 4 GB |
| guided | 2 | 500,000 | 200 | 30 minutes | 8 GB |
| lab | 4 | 3,000,000 | 1,000 | 2 hours | 16 GB |
| vps | 2 | 1,000,000 | 600 | 1 hour | 8 GB |

Use `indian-quant modes` or `indian-quant demo --mode guided`. Workers and numerical thread pools are capped; CSV/Parquet row counts and instrument counts are checked; CLI research runs have a timeout. RAM and disk recommendations are **advisory**, not hard isolation. Three fixed model candidates are used in every mode. There are zero built-in AI calls, so these profiles do not control an external coding assistant's spending. See [resources](docs/resources.md).

## Bring your own data

```bash
indian-quant bank-import /path/bars.csv --bank workspace/bank \
  --provenance 'Provider; licence; adjusted OHLC and volume convention; retrieval date'
indian-quant run --data /path/bars.csv --calendar /path/sessions.txt \
  --benchmark NIFTY50 --output workspace/runs/my-first-study --mode guided
```

Required columns: `date,symbol,open,high,low,close,volume,factor`. Do not rename a raw vendor export and assume it is compatible. Follow the [data contract](docs/data-contract.md), including adjustment factors, non-tradable benchmark handling and verified calendar requirements. Outputs must go to a new directory.

## Use with an AI assistant

With authorized terminal access to the local machine or VPS, ask:

> Read AGENTS.md and skills/quant-setup/SKILL.md. Inspect this environment, explain the available modes and data choices, then help me run the synthetic demo. Use Python for computation and read brief.json before opening larger artifacts.

Browser chat alone cannot access your machine merely from a repository URL. See [AI setup and token efficiency](docs/ai-guide.md).

## Documentation map

| Guide | What it helps you do |
|---|---|
| [Getting started](docs/getting-started.md) | Install, verify, run and troubleshoot a first experiment |
| [Data bank](docs/data-bank.md) | Choose a source, preserve raw files and audit history |
| [Data contract](docs/data-contract.md) | Prepare dates, identities, prices, factors and calendars |
| [Research design](docs/research.md) | Turn ideas into hypotheses and interpret validation |
| [Reports](docs/reporting.md) | Read portfolio, factor and resource evidence |
| [AI guide](docs/ai-guide.md) | Use different assistants with minimal context |
| [Resources](docs/resources.md) | Select and tune a resource mode |
| [VPS operation](docs/vps.md) | Access reports privately and schedule a bounded run |
| [Broker readiness](docs/brokers.md) | Plan data/paper/live integration and verify prerequisites |
| [Architecture](docs/architecture.md) | Understand extension boundaries and companion-repo interfaces |
| [Roadmap](docs/roadmap.md) | Distinguish implemented features from later stages |
| [Contributing](CONTRIBUTING.md) | Test and submit changes |

## Responsibility and licensing

Educational and research use only; not personalized investment advice. You own your decisions, capital, data permissions and deployment risk. Backtests are hypothetical and cannot guarantee returns. Users may configure research risk assumptions, but this repository does not override broker, exchange, legal or AI-provider requirements.

Code: [MIT licence](LICENSE). Qlib is an upstream dependency with its own licence. No proprietary exchange data, broker credentials or NiftyHistory raw history is distributed. [Indian_Trader_skill](https://github.com/maheshwaripn/Indian_Trader_skill) is the companion workflow project; installation fetches a pinned companion distribution for the shared dependency-free market utilities; it does not run Trader commands.
