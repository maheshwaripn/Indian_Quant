# A first experiment, step by step

## 1. Prepare an isolated environment

Use Python 3.11 or 3.12 on Ubuntu/Linux. Avoid installing the project into system Python. On Ubuntu, install Python's venv support using your normal package manager if `python3 -m venv` is unavailable. On a shared VPS, work as a dedicated unprivileged user.

Clone the public repository, enter it, create `.venv`, activate it, then run `python -m pip install -e '.[dev]'` as shown in the README. The editable install means changes to `src/` are immediately used. The `dev` extra adds tests and linting; normal users can use `pip install -e .`.

Qlib 0.9.7 is pinned. Other dependencies have compatibility ranges; each experiment records important installed versions. A fresh installation can therefore differ in transitive dependencies. Save `python -m pip freeze > workspace/environment.txt` for a study you need to reproduce. Never load untrusted pickle models or execute unknown Qlib/YAML configs.

## 2. Inspect before computing

Run:

```bash
indian-quant doctor
indian-quant modes
```

`doctor` prints Python, platform, CPU count, and a conservative starting mode. It does not certify RAM availability or broker readiness. Start with `essential`, even on a powerful VPS. Reserve capacity for other services.

## 3. Run the synthetic demonstration

```bash
indian-quant demo --workspace workspace --mode essential
```

The program creates 12 fictional stocks plus a fictional benchmark across 420 weekday sessions. This calendar is not an NSE calendar. It writes Qlib's binary cache, computes five expressions, trains baseline models, selects using validation, and executes a Qlib portfolio simulation. No data download or model API call is performed.

Each invocation writes a new run directory. Open `report.html` from the printed path. If accessing a remote machine, use the private report instructions in [VPS operation](vps.md).

## 4. Inspect evidence, in order

1. Read `brief.json`: a small overview for a person or AI.
2. Read `manifest.json`: status, dataset hash, model choice, split boundaries, assumptions and limitations.
3. Open `report.html`: equity, metrics, model comparison and reading guidance.
4. Inspect `predictions.csv`: test-period features, labels and chosen-model scores.
5. Inspect `portfolio.csv`: Qlib's daily portfolio valuation, costs, benchmark and turnover.

A successful run has `status: completed`. A failed/timeout run is not a completed experiment even if some files exist. Do not compare demo returns as if they were evidence of an Indian market edge.

## 5. Verify your installation

```bash
python -m pip check
pytest -q
ruff check src tests
python scripts/check_docs.py
```

The integration test uses Qlib itself, not a mock backtester. If the demo fails, read the terminal error before reinstalling packages or changing financial logic.

## 6. Move to a small real-data pilot

Prepare a complete dataset for a few equities and a benchmark, following [the contract](data-contract.md). Supply an independently checked session calendar. Start with a deliberately limited period and inspect adjusted/raw prices around corporate actions. Import into the bank with provenance, then point `run` at its canonical `bars.parquet`.

Use the same pilot cohort over the chosen period only for software/research exploration. Choosing today's survivors retrospectively introduces bias. Keep the fixed-universe warning visible until the future historical-universe engine is implemented and verified.

## Troubleshooting

| Symptom | First action |
|---|---|
| `indian-quant` not found | Activate `.venv`; check `python -m indian_quant doctor` |
| Package build failure | Confirm Python version and available wheel/platform; retain the installer error |
| Duplicate/session/price error | Correct source data with an audit trail; do not suppress validation |
| Existing output directory | Use a new run ID; never overwrite an experiment |
| Calendar mismatch | Verify session dates, timezone conversion and provider coverage |
| Worker timeout or low memory | Use a smaller universe/date range and one worker; inspect partial manifest |
| Missing LightGBM shared library | Install platform OpenMP runtime through the supported package manager |
| Poor or unstable returns | First inspect data, costs, sample size and hypothesis; do not automatically optimize more |

Windows/macOS are not certified by the initial CI matrix. Windows users can begin with WSL2 Ubuntu. Native platform support is a later validation target, not an assumed promise.
