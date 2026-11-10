# Local/VPS research operations runbook

## Before a run

Activate the project's virtual environment. Run `indian-quant doctor` and `python -m pip check`. Record the Git commit and dependency versions. Verify free disk space, immutable source snapshot, independent session calendar and expected membership/cost coverage. Start in essential mode for a small fixture; choose a larger mode deliberately. Keep credentials outside Git and reports.

Use a unique output path per attempt. Record the exact command and hypothesis before running. CLI research runs have a parent timeout; direct Python calls do not. Do not schedule two runs writing the same directory or mutate source data during a run.

## Completion and interpretation

Require `manifest.json` with `status: completed`, then inspect `brief.json` and research validity flags. Retain protocol, manifest, predictions, fills, portfolio, folds, baseline files and report together. A chart or partial CSV alone is not a completed result. Zero AI calls means Python computation did not call a model; it says nothing about your external assistant's token usage.

## Backup and restore

Copy immutable raw/canonical snapshots, provenance manifests, membership/calendar sources, all run directories (including failed runs), hypothesis notes, exact dependency records and the repository revision to a separate backup location. Verify checksums after copying. Test restoration into a separate directory before deleting anything. Restore secrets through a separate protected channel, not a public archive.

The Qlib cache is derived and may be regenerated from a verified snapshot, calendar and compatible code. Do not treat it as the sole data backup. Relative local paths may change during restore: resolve them explicitly rather than modifying a prior manifest to conceal the move.

## Failure recovery

- **Input/calendar/membership error:** preserve the error and source; correct with documented evidence in a new snapshot. Do not drop inconvenient securities or dates merely to pass.
- **Timeout or interrupted process:** preserve partial output. Inspect logs and resource limits, then rerun into a new path. A power failure may leave `running`; it is not success.
- **Unresolved terminal holdings:** provide verified settlement history or run an explicitly labelled writeoff scenario. Never use the hindsight last quote as a guaranteed sale.
- **Fee dates outside coverage:** supply a documented alternative assumption or extend the shared engine with reviewed sources/tests; never extrapolate silently.
- **Missing Python dependency:** repair the environment and run `pip check`; do not mix system Python and virtual-environment installations.
- **Scheduler failures:** check its working directory, interpreter path, permissions, environment and log destination against a successful manual run. Avoid concurrent ingestion writes.

## Disk cleanup and reproducibility

Review disk usage first. Remove only identified, regenerable caches after backups and checksums are verified. Never automatically delete source snapshots, completed experiments or failed trials to improve the apparent result history. Exact bitwise model output across numerical-library versions/platforms is not guaranteed; compare accounting/timing invariants and documented numerical tolerances. Timings and registration timestamps are expected to differ between reruns.

## Upgrades

Use an isolated environment and a clean Git revision. Run tests, lint, docs and package build checks before adopting a new Qlib/shared-core version. Preserve old environments or dependency inventories for previous studies. No systemd/cron job, public report server or broker connection is installed by this runbook.

## Progress and explicit historical fee assumptions

Run with `--timeout-hours 8` when a measured study needs more than the mode default. Redirect stderr to a retained log if desired. `progress.json` is atomically replaced with the stage, elapsed seconds and, during shuffles, completed/total draws. It is a stage checkpoint, not a continuously refreshed heartbeat or a restart/resume file. Long individual model fits can leave the stage unchanged. Only a completed manifest establishes success.

For India fees before 2023-04-01, explicitly select `--cost-before-coverage proportional` and set `--buy-cost` and `--sell-cost` to documented aggregate assumptions. Within verified coverage the shared India engine still applies. Dates after 2026-11-08 still fail. Training dates alone do not require fee coverage. The manifest, fills and report disclose the bridge; it is not a reconstruction of historical taxes. See [the complete example](issue-1-resolution.md).
