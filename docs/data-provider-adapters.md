# Data sources and field mappings

These are mappings for user-supplied data. The executable adapter is `indian-quant bhavcopy`; there is no authenticated Dhan/Zerodha downloader in Quant. Provider permissions, history coverage and adjustment conventions remain the user's responsibility.

| Canonical field | NSE legacy cash CSV | NSE UDiFF cash CSV | User-supplied broker daily export |
|---|---|---|---|
| date | TIMESTAMP, parsed day-month-name-year | TradDt, ISO session date | Convert timestamp to Asia/Kolkata **before** taking the session date |
| symbol | SYMBOL, SERIES=EQ | TckrSymb, SctySrs=EQ, stock rows | Map provider security ID to a stable historical identity; retain alias evidence |
| open | OPEN | OpnPric | Provider open, consistently adjusted |
| high | HIGH | HghPric | Provider high, same convention |
| low | LOW | LwPric | Provider low, same convention |
| close | CLOSE | ClsPric | Provider close, same convention |
| volume | TOTTRDQTY | TtlTradgVol | Share units consistent with price adjustment |
| factor | Converter writes 1 | Converter writes 1 | Adjusted/raw price ratio; do not infer from adjusted close alone |

```bash
indian-quant bhavcopy /path/day1.csv /path/day2.csv --output /path/raw-bars.csv
indian-quant bank-import /path/adjusted-bars.csv --bank workspace/bank \
  --provenance 'Source; retrieval date; licence; adjustment method; event-reference path'
```

Bhavcopy conversion is raw normalization, not corporate-action adjustment. Keep the raw file and independently validated adjusted snapshot. Never rename provider columns and assume financial equivalence. A symbol rename is not a new stock; a reused ticker is not the same security.

For Yahoo-origin data, document auto-adjust choices and whether volume is transformed consistently. Adjusted close plus raw OHLC is not a coherent bar. A broker export may contain unfinished daily bars, contract IDs or intraday timestamps; exclude incomplete observations and do not mix futures/options with this cash-equity contract.

Benchmark volume may be zero because the benchmark is not traded. Benchmark closes must cover every valuation session. Label it price-return or total-return; do not imply a costed ETF investment. Weekday lists are synthetic-only: use independent sessions and verified calendar years. Missing stock quotes remain absent, not forward-filled executable bars.

No universal downloader, automatic rights/merger adjustment or delisting recovery is implemented. See [the data contract](data-contract.md) and [review disposition](review-response-2026-11-09.md).
