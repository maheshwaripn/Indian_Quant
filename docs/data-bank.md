# Choose and maintain a data bank

## Choose a source before an experiment

| Source | Useful for | Questions to resolve |
|---|---|---|
| Existing CSV/Parquet | Fastest route for users with a research archive | Adjustments, timestamps, missing/delisted securities, redistribution rights |
| Yahoo Finance | Small educational daily-price exploration | Provider changes, adjusted/raw conventions, coverage and rate limits |
| NSE bhavcopy files | Exchange daily observations | Historical formats, corporate actions, identifiers and permission to store/use |
| Dhan or Zerodha data | Broker-supported observations | Subscription, endpoint coverage, retention, entitlement and API limits |
| Licensed historical vendor | Delisted/PIT and specialist research | Survivorship coverage, revisions, licence, timestamps and quality evidence |

The first release imports user-supplied CSV/Parquet. It does not include an authenticated broker adapter or a one-click provider downloader. Do not imply that Qlib supplies Indian history. Downloading data and having permission to redistribute it are separate questions.

For Yahoo, use the provider's maintained client/documentation to export a small known symbol first. Inspect both raw and adjusted columns and corporate actions. Explicitly choose adjustment behaviour; default values can change. Convert into the repository contract only after checking a known split/dividend. The optional `yahoo` dependency is convenience for your own acquisition script, not an implemented command.

For bhavcopies, keep the original downloaded archive and its acquisition date. Normalize only the intended equity series; do not mix spot equities, ETFs, debt, derivatives and repeated series into one symbol. Join a reviewed instrument identity mapping. Preserve source fields alongside normalized output.

For broker data, follow [broker readiness](brokers.md). Never paste access tokens into chat or commit them. Fetch outside the training process so a model experiment cannot unexpectedly consume API limits or produce orders.

## Import and inspect

```bash
indian-quant bank-import /path/normalized.csv --bank workspace/bank \
  --provenance 'Provider and retrieval date; permitted research use; adjustment method and known gaps'
```

The resulting directory is named with the SHA256 of the supplied file. It contains the unchanged supplied source, canonical `bars.parquet`, and `manifest.json`. Preserve original vendor downloads separately if the supplied CSV was already transformed. This command cannot reconstruct provenance that was discarded before import.

The manifest includes row count, instrument count, date range, canonical checksum and provenance text. Re-importing the same source with identical provenance reuses the snapshot. Conflicting provenance is rejected. Never edit a completed snapshot; create a new version from a corrected input and record why it changed.

No retention deletion is automatic. Back up the source snapshots and manifests; derived Qlib caches can be rebuilt. Keep backups outside the VPS and test restoration. List bank manifest files to catalogue snapshots; a searchable database catalogue and incremental provider jobs are future work.

## NiftyHistory membership audit

Obtain history from [NiftyHistory](https://niftyhistory.in/) under its applicable terms, then run:

```bash
indian-quant membership-audit /path/nifty500-history.csv \
  --output workspace/membership-audit.json
```

Expected columns: `effective_date,index_type,inclusions,exclusions,symbols`. Symbol lists can be comma-separated or literal lists of strings. The command checks chronological order, 500-member counts, and each transition against `(previous - exclusions) | inclusions`.

The user-supplied history previously reviewed spans 1998-01-08 to 2026-09-30 despite its wider filename range. It contained membership-count and transition discrepancies. Audit your copy rather than treating the filename or a previous audit as authoritative. No raw history is redistributed here because redistribution permission has not been established.

Do not silently repair BBOX/BLACKBOX or similar aliases. Resolve identities using authoritative evidence and preserve a correction ledger. A no-issue audit means only that these structural checks passed; it does not prove complete PIT accuracy, publication timing, or delisted price coverage. Research can consume clean snapshots with explicit knowledge assumptions; see review-upgrade.md.

## Maintenance checklist

1. Acquire new data into a separate staging location.
2. Validate source identity, licence and schema.
3. Compare overlap with the previous snapshot; investigate revisions.
4. Review corporate actions and unexpected price/volume jumps.
5. Store a new content-addressed version and its provenance.
6. Rebuild affected derived caches; retain old experiment inputs.
7. Run a small integration study before scheduling a larger job.

Missing data should lead to investigation or an explicit restricted study, not silent forward-filling. Record excluded instruments and periods; exclusions themselves can introduce selection bias.
