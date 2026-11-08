"""Standalone, escaped HTML with local SVG chart and metric reading guidance."""

import html
import json

import pandas as pd

GUIDE = {
    "total_return_net": "Compounded return after configured costs. This is simulated, not an achievable-return claim.",
    "annualized_return_net": "Geometric extrapolation using 252 sessions. Short samples can exaggerate this number.",
    "max_drawdown": "Worst decline from the initial capital or a subsequent peak. Future losses can exceed this.",
    "sharpe_zero_rf": "Annualized mean / standard deviation, assuming zero risk-free return; ignores tail shape.",
    "benchmark_total_return": "Compounded supplied benchmark returns. Check price versus total-return comparability.",
    "mean_daily_turnover": "Average gross traded value / prior closing equity in the local ledger. High turnover increases cost sensitivity.",
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
    stats = manifest.get("statistics", {})
    intervals = stats.get("net_return_interval", {}).get("metric_intervals", {})
    rows = ""
    for key, value in manifest["metrics"].items():
        bounds = intervals.get(key)
        uncertainty = f"{bounds[0]:.5f} to {bounds[1]:.5f}" if bounds else "Descriptive / not estimated"
        rendered = f"{value:.5f}" if isinstance(value, (int, float)) else "Unavailable"
        rows += f"<tr><td>{escape(key)}</td><td>{rendered}</td><td>{uncertainty}</td><td>{escape(GUIDE.get(key, 'See manifest'))}</td></tr>"

    def spark(values, label):
        values = pd.Series(values).dropna().tolist()
        if len(values) < 2:
            return "<p>Insufficient observations</p>"
        low, high = min(values), max(values)
        points = " ".join(
            f"{20 + i * 760 / (len(values) - 1):.2f},{210 - (v - low) * 180 / max(high - low, 0.001):.2f}"
            for i, v in enumerate(values)
        )
        return f'<p>{escape(label)}: vertical range {low:.4f} to {high:.4f}; chronological sessions.</p><svg viewBox="0 0 800 240" role="img" aria-label="{escape(label)}"><polyline points="{points}" fill="none" stroke="#0369a1" stroke-width="2"/></svg>'

    ic = pd.read_csv(path.parent / "ic.csv")
    deciles = pd.read_csv(path.parent / "deciles.csv")
    charts = spark(ic.iloc[:, -1], "Daily rank IC") + spark(portfolio.exposure, "Invested fraction")
    yearly = "".join(
        f"<tr><td>{escape(year)}</td><td>{value:.2%}</td></tr>"
        for year, value in stats.get("yearly_net_returns", {}).items()
    )
    decile_table = deciles.to_html(index=False, escape=True, float_format=lambda value: f"{value:.5f}")
    limitations = "".join(f"<li>{escape(v)}</li>" for v in manifest["limitations"])
    status = (
        "SYNTHETIC DEMONSTRATION"
        if manifest["synthetic"]
        else "RESEARCH SIMULATION — CHECK UNIVERSE COVERAGE"
    )
    diagnostics = escape(json.dumps(manifest.get("statistics", {}), indent=2))
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Indian Quant research report</title><style>
body{{font:16px system-ui;background:#f8fafc;color:#1e293b;max-width:1100px;margin:auto;padding:30px}}
h1,h2{{color:#0f172a}}.banner{{background:#fef3c7;padding:15px;border-radius:8px}}table{{border-collapse:collapse;width:100%}}
td,th{{text-align:left;border-bottom:1px solid #475569;padding:12px;overflow-wrap:anywhere}}svg{{width:100%;background:#fff}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere}}.card{{background:#fff;padding:20px;margin:20px 0;border-radius:12px}}
</style><h1>Indian Quant</h1><p class="banner">{status} · Educational use · No live orders</p>
<div class="card"><h2>Out-of-sample equity</h2><p>Blue: strategy after configured costs. Gold: supplied benchmark.
Both start at 1. Vertical range: {low:.3f}–{high:.3f}. Horizontal axis: test sessions in chronological order.</p>
<svg viewBox="0 0 800 260" role="img" aria-label="Strategy and benchmark compounded equity">{"".join(lines)}</svg></div>
<h2>Performance and interpretation</h2><table><tr><th>Metric</th><th>Value (ratios)</th><th>95% block interval</th><th>How to read it</th></tr>{rows}</table>
<div class="card"><h2>Model comparison</h2><p>Last fold model, selected on validation rank IC: {escape(manifest["selected_model"])}.
Rank IC measures ordering skill, not net profitability. Test results must not be used for repeated tuning.</p>
<pre>{escape(json.dumps({"validation": manifest["validation_rank_ic"], "test": manifest["test_rank_ic"]}, indent=2))}</pre></div>
<h2>Uncertainty, baselines and cost stress</h2>
<p>Read these alongside every headline metric. A confidence interval crossing zero or a large shuffle p-value
means results remain consistent with chance under these checks. A small p-value does not prove an edge.
Intervals cover return, annualised return, Sharpe and drawdown under the same block bootstrap. They are conditional estimates, not future-loss bounds. Other metrics are descriptive.
Cost stress reruns sizing and execution; the first losing tested multiplier is a coarse threshold, not an exact breakeven.</p>
<h2>Year-by-year net performance</h2><table><tr><th>Year</th><th>Net return</th></tr>{yearly}</table>
<h2>Ordering skill and exposure over time</h2>{charts}
<h2>Gross forward returns by predicted decile</h2>{decile_table}
<details><summary>Full uncertainty, baseline, capacity and cost diagnostics</summary><pre>{diagnostics}</pre></details>
<p>ic.csv shows daily rank IC; deciles.csv shows gross forward label returns by predicted rank (10 highest),
not investable portfolios. portfolio.csv includes exposure, stale holdings and final writeoffs. equal_weight.csv
uses all eligible tradable stocks with the same execution assumptions. Read folds in manifest.json for yearly selections.</p>
<h2>Limitations and next checks</h2><ul>{limitations}</ul><h2>Resources and reproducibility</h2>
<p>{manifest["rows"]} rows · {manifest["workers"]} workers · {manifest["elapsed_seconds"]} seconds · 0 AI calls.</p>
<p>Keep manifest.json, predictions.csv and portfolio.csv together. Before extending research, audit historical
membership, corporate actions, price bands, liquidity and costs; compare a fresh untouched period.</p></html>"""
    path.write_text(page, encoding="utf-8")
