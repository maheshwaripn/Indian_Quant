"""Standalone, escaped HTML with local SVG chart and metric reading guidance."""

import html
import json

GUIDE = {
    "total_return_net": "Compounded return after configured costs. This is simulated, not an achievable-return claim.",
    "annualized_return_net": "Geometric extrapolation using 252 sessions. Short samples can exaggerate this number.",
    "max_drawdown": "Worst decline from the initial capital or a subsequent peak. Future losses can exceed this.",
    "sharpe_zero_rf": "Annualized mean / standard deviation, assuming zero risk-free return; ignores tail shape.",
    "benchmark_total_return": "Compounded supplied benchmark returns. Check price versus total-return comparability.",
    "mean_daily_turnover": "Average traded-value ratio reported by Qlib. High turnover increases cost sensitivity.",
    "sum_daily_cost_ratios": "Sum of daily cost ratios, not an exact currency total or compounded return difference.",
    "test_sessions": "Number of simulated out-of-sample valuation sessions; short samples provide weak evidence.",
}


def render(manifest, portfolio, path):
    escape = html.escape
    wealth = (1 + portfolio["return"] - portfolio.cost).cumprod()
    benchmark = (1 + portfolio.bench).cumprod()
    series = [wealth.tolist(), benchmark.tolist()]
    low = min(1.0, *(min(s) for s in series))
    high = max(1.0, *(max(s) for s in series))
    span = max(high - low, 0.001)
    lines = []
    for values, color in zip(series, ["#38bdf8", "#fbbf24"]):
        values = [1.0, *values]
        points = " ".join(
            f"{20 + i * 760 / (len(values) - 1):.2f},{230 - (v - low) * 200 / span:.2f}"
            for i, v in enumerate(values)
        )
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"/>')
    rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{v:.5f}</td><td>{escape(GUIDE[k])}</td></tr>"
        if isinstance(v, (float, int))
        else f"<tr><td>{escape(k)}</td><td>Unavailable</td><td>{escape(GUIDE[k])}</td></tr>"
        for k, v in manifest["metrics"].items()
    )
    limitations = "".join(f"<li>{escape(v)}</li>" for v in manifest["limitations"])
    status = "SYNTHETIC DEMONSTRATION" if manifest["synthetic"] else "RESEARCH SIMULATION — FIXED UNIVERSE"
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Indian Quant research report</title><style>
body{{font:16px system-ui;background:#0f172a;color:#e2e8f0;max-width:1100px;margin:auto;padding:30px}}
h1,h2{{color:#fff}}.banner{{background:#78350f;padding:15px;border-radius:8px}}table{{border-collapse:collapse;width:100%}}
td,th{{text-align:left;border-bottom:1px solid #475569;padding:12px;overflow-wrap:anywhere}}svg{{width:100%;background:#172033}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere}}.card{{background:#1e293b;padding:20px;margin:20px 0;border-radius:12px}}
</style><h1>Indian Quant</h1><p class="banner">{status} · Educational use · No live orders</p>
<div class="card"><h2>Out-of-sample equity</h2><p>Blue: strategy after configured costs. Gold: supplied benchmark.
Both start at 1. Vertical range: {low:.3f}–{high:.3f}. Horizontal axis: test sessions in chronological order.</p>
<svg viewBox="0 0 800 260" role="img" aria-label="Strategy and benchmark compounded equity">{"".join(lines)}</svg></div>
<h2>Performance and interpretation</h2><table><tr><th>Metric</th><th>Value (ratios)</th><th>How to read it</th></tr>{rows}</table>
<div class="card"><h2>Model comparison</h2><p>Selected on validation rank IC: {escape(manifest["selected_model"])}.
Rank IC measures ordering skill, not net profitability. Test results must not be used for repeated tuning.</p>
<pre>{escape(json.dumps({"validation": manifest["validation_rank_ic"], "test": manifest["test_rank_ic"]}, indent=2))}</pre></div>
<h2>Limitations and next checks</h2><ul>{limitations}</ul><h2>Resources and reproducibility</h2>
<p>{manifest["rows"]} rows · {manifest["workers"]} workers · {manifest["elapsed_seconds"]} seconds · 0 AI calls.</p>
<p>Keep manifest.json, predictions.csv and portfolio.csv together. Before extending research, audit historical
membership, corporate actions, price bands, liquidity and costs; compare a fresh untouched period.</p></html>"""
    path.write_text(page, encoding="utf-8")
