---
name: quant-costs
description: Choose dated India delivery costs, liquidity assumptions and cost-stress interpretation.
---
Read ../../docs/review-upgrade.md and the shared Trader cost documentation. Ask for product, dates, broker, capital, liquidity and fee convention when missing. Quant supports cash delivery only. Use the shared cost engine within its stated coverage; otherwise require explicit proportional assumptions rather than extrapolating rates. Explain STT on both delivery legs, DP aggregation limitations, prior-turnover sizing, impact, partial fills and terminal liquidation. Run bounded cost stress and compare the baseline. A coarse losing multiplier is not exact breakeven. Never claim executable capacity from daily bars alone.
