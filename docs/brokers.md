# Broker data, paper workflows and eventual live execution

**Status: readiness guidance only.** v0.1 has no broker adapter, authenticated request command, paper-fill engine or live order path. Its Qlib simulation is not broker paper trading. Dhan is the planned first adapter; Zerodha follows after a shared interface is validated.

## Data-only setup

1. Choose your broker and confirm account/API and historical-data entitlements.
2. Use the official developer portal to create the required API application or credentials.
3. Complete the documented authentication flow. Store secrets outside Git and chat.
4. Use an official SDK example to retrieve a small read-only sample: instrument identity and historical bars.
5. Check exchange, segment, timezone, adjustment method, interval and endpoint history limits.
6. Respect documented rate limits; cache results locally and record acquisition time.
7. Normalize into the [data contract](data-contract.md), validate, and snapshot before training.

Dhan's documentation describes its Python client, token-based requests and separate data/order API limits. Zerodha's documentation describes developer-app setup, redirect URLs and the login flow. Use current official pages rather than copying credentials or stale snippets from social media:

- [DhanHQ v2 documentation](https://dhanhq.co/docs/v2/)
- [Kite Connect v3 documentation](https://kite.trade/docs/connect/v3/)

Documentation entry pages checked 2026-11-07. Exact endpoint availability, account eligibility and current broker operating requirements must be rechecked before implementation. This page does not certify compliance.

## Static outbound IP / allowlisting preparation

1. Determine whether your broker requires a registered static IP for your proposed API activity and obtain its current instructions.
2. Identify the actual public **outbound** IP of the execution host. A website DNS record or the server's private address is not sufficient evidence, especially behind NAT/proxies.
3. Arrange a stable egress IP with your VPS/network provider if required.
4. Register the address through the broker's supported portal/API and follow its verification/cooldown requirements.
5. Confirm that the process performing requests uses that same egress route; document failover and any secondary-IP policy.
6. Test allowed read-only access. Before an eventual order pilot, verify the broker's intended validation procedure and expected rejection behaviour for unauthorized origins.
7. Revalidate after host migration, VPN changes or networking changes. Do not bypass the allowlist with an unapproved relay.

Exact portal button names, IP-change limits and applicable dates are not hardcoded because they can change. No broker account is configured by this repository.

## Paper workflow before live

Export research scores with timestamps and model/data versions. A future paper service must consume only scores available at that time, use an explicit fill model, log intended orders and simulated fills, and reconcile positions and cash. A backtest run on newly downloaded history is not forward paper evidence.

Maintain a separate paper ledger and compare expected versus observed prices, missing signals, retries, costs and exposure. Do not promote a strategy solely because its research report looks good.

## Regulatory readiness record

Before adding live execution, consult current official SEBI circulars, exchange implementation standards and broker requirements for the exact activity: self-developed retail algorithm, third-party provider, or another arrangement. Start at [SEBI legal circulars](https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0), [NSE](https://www.nseindia.com/) and your broker's official updates.

Record applicable document identifiers and effective dates; broker approval/registration requirements where applicable; authentication/IP requirements; order tagging and rate controls; audit retention; permitted instruments and account scope. Obtain clarification from the broker or a qualified adviser if applicability is unclear. This release does not claim that a generic checklist establishes compliance.

A future live adapter must implement idempotent order intents, reconciliation, rejection handling, stale-data checks, exposure controls, a kill switch and restart recovery. Real orders require separate explicit user authorization and validated execution code. Educational disclaimers do not remove operational responsibilities.
