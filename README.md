# Indian Quant

**CPU-first Indian equity research with Qlib, reproducible experiments, and optional AI coaching.**

[![Research checks](https://github.com/maheshwaripn/Indian_Quant/actions/workflows/ci.yml/badge.svg)](https://github.com/maheshwaripn/Indian_Quant/actions/workflows/ci.yml)

Run calculations locally. Ask Claude, Codex, Gemini or Copilot to help define hypotheses and interpret compact results. No AI subscription, API key, GPU or market-data credentials are needed for the synthetic demonstration.

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

## What v0.1 actually does

- Validates daily CSV/Parquet bars, stores source snapshots by SHA256, and creates canonical Parquet plus provenance manifests.
- Writes a derived Qlib binary cache and loads real Qlib factor expressions.
- Compares momentum, scaled Ridge and a small CPU LightGBM model using chronological train/validation/test segments with label-boundary purging.
- Selects a model on validation rank IC; runs Qlib's daily top-k long-only portfolio simulation using next-session open prices.
- Produces predictions, portfolio records, a reproducibility manifest, a standalone HTML report and a small AI-readable brief.
- Offers four resource profiles and a NiftyHistory membership audit command.
- Supplies portable AI instructions, research coaching and detailed operating guides.

## Deliberate first-release boundaries

This is a **research foundation**, not a production trading bot or a complete institutional platform. The pilot uses a complete fixed universe: it does **not** claim survivorship-free portfolios. The NiftyHistory audit is not yet connected to portfolio eligibility. Costs are configurable constant assumptions; there is no dated Indian fee/tax engine, circuit-band enforcement, order-book simulation or impact model. There is one chronological holdout, not walk-forward evaluation.

No live orders, broker SDK integrations, automatic paper fills, autonomous model tuning, options research, hosted dashboard or AI API calls are implemented. See [roadmap and acceptance gates](docs/roadmap.md).

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

Required columns: `date,symbol,open,high,low,close,volume,factor`. Do not rename a raw vendor export and assume it is compatible. Follow the [data contract](docs/data-contract.md), including adjustment factors, benchmark volume convention and verified calendar requirements. Outputs must go to a new directory.

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

Code: [MIT licence](LICENSE). Qlib is an upstream dependency with its own licence. No proprietary exchange data, broker credentials or NiftyHistory raw history is distributed. [Indian_Trader_skill](https://github.com/maheshwaripn/Indian_Trader_skill) is the companion workflow project; this package installs independently.
