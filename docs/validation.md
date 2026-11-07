# Release validation record

Initial local validation on Linux / Python 3.12:

- 17 tests passed, including a real Qlib end-to-end run and an independent next-open label calculation.
- Essential and guided mode synthetic demonstrations completed (one and two workers).
- Ruff, dependency consistency and relative documentation links passed.
- The supplied NiftyHistory file produced 137 audited rows, 49 count warnings and 114 transition mismatches; raw data remains private and is not committed.
- A read-only research-coaching exercise correctly identified adjusted-close-only inputs, current-constituent bias, repeated Sharpe optimization and absent live Dhan execution as limitations.

These are software checks, not market-performance validation. Synthetic returns are not an investment result. There has been no real-data strategy evaluation, broker integration, live-order test, historical-universe portfolio test, regulatory certification or capacity study.

Qlib emits upstream deprecation warnings and empty-slice warnings in optional execution indicators during the demonstration. The portfolio return, cost, turnover and prediction artifacts are checked; unavailable indicator statistics are not promoted into the report.

Automated browser preview was unavailable in the build environment because Chromium could not open its required local socket. HTML generation and artifact content were checked, but this is not a claim of visual browser certification. Users should open the offline report and report layout problems with their browser/viewport.

CI runs the same tests on Ubuntu Python 3.11 and 3.12. Check the linked GitHub Actions run rather than assuming a badge or this document proves the latest commit passed. Native Windows/macOS are not certified.
