# Contributing

Use a supported Python environment and `pip install -e '.[dev]'`. Run `pytest -q`, `ruff check src tests`, `python scripts/check_docs.py`, and `python -m pip check` before proposing a change. The integration test exercises real Qlib on synthetic data.

Describe the concrete problem, final behaviour, validation and limitations. For financial logic changes add hand-verifiable fixtures: timing, costs, missing data, corporate actions, holdings and leakage should be understandable without trusting a chart.

Keep raw user data, credentials, generated research and environment files out of commits. Retain upstream copyright and licence notices. Do not introduce network calls into offline tests. Separate provider adapters from research and execution.

Report sensitive security issues privately through the repository owner's available private contact route; do not post credentials in public issues. If a credential was exposed, revoke it rather than relying on deletion alone.
