---
name: quant-setup
description: Set up Indian Quant on a local machine or VPS, choose resource and data options, and verify a first Qlib research run.
---
Read ../../docs/getting-started.md and ../../docs/resources.md. Inspect the current directory and environment before changing anything. Explain that browser chat needs an authorized terminal connector or user-run commands.

Run `python -m indian_quant doctor` if installed. Otherwise use a dedicated virtual environment and the documented install. Present essential, guided, lab and vps modes; begin conservatively. Offer existing CSV/Parquet, Yahoo, NSE files or broker-sourced data, explaining that only file import is implemented.

Run the synthetic demo before a large real dataset. Inspect completion, report artifacts and limitations. For real inputs read ../../docs/data-contract.md and ../../docs/data-bank.md. Never invent adjustment factors, dates, missing prices or permissions. Offer concrete corrections and explain why each matters.

For VPS access read ../../docs/vps.md. Do not expose reports publicly or configure broker accounts as part of a demo. Finish with the verified command, report location, resource use and one next learning step.
