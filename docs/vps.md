# Run on a VPS

## Prepare

Use an unprivileged account with a private home/project directory. Install a supported Python and Git through your OS package manager. Clone and install as described in [getting started](getting-started.md). Keep broker secrets out of the repository and restrict any credential file to its owner. No credentials are needed for the demo.

Run `indian-quant doctor`, then `indian-quant demo --mode essential`. Verify the report before using larger datasets. Shared VPS capacity should be reserved for existing services; do not automatically use every CPU.

## View a report privately

On the VPS, serve the completed run directory on loopback only:

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory workspace/runs/YOUR-RUN
```

From your local computer, open an SSH tunnel:

```bash
ssh -L 8000:127.0.0.1:8000 your-user@your-vps
```

Open `http://127.0.0.1:8000/report.html` locally. Keep the terminal sessions open while viewing. Do not expose Python's development HTTP server publicly. A future public dashboard requires authentication, TLS and a separate deployment review.

## Schedule a verified research job

First prove the exact command works manually with an absolute data path, a verified calendar and a new output directory. `examples/run-research.sh` demonstrates this with an exclusive `flock` and timestamped run ID. Review and set `IQ_REPO`, `IQ_DATA`, `IQ_CALENDAR`, and `IQ_BENCHMARK` in your own environment. This script performs no data downloads or trades.

Use your preferred scheduler to call it, capturing stdout/stderr to a protected log. The repository does not install cron/systemd automatically. Ensure the scheduler has the same environment and permissions as the manual run. Avoid running it during data-update writes; use complete immutable snapshots.

For strict resource isolation, configure your service manager's CPU, memory, task and runtime limits. On systemd, evaluate `CPUQuota`, `MemoryMax`, `TasksMax`, `RuntimeMaxSec` and `KillMode=control-group` for your host. Settings depend on other workloads; no universally safe memory limit is assumed here.

## Recover

Treat only manifests with `status: completed` as valid results. If a job fails or times out, preserve its directory for diagnosis, correct the cause, and rerun into a new directory. A power failure can leave `running` status; that is not success. Check disk space and backup snapshots before removing derived caches.

Test backup restoration and scheduled execution with synthetic data before depending on it. VPS scheduling is not live-trading authorization or production readiness.
