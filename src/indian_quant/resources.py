"""Explicit CPU and input budgets; no implicit external AI calls."""

import os
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Profile:
    workers: int
    max_rows: int
    max_instruments: int
    timeout_seconds: int
    brief_chars: int
    suggested_ram_gb: int


PROFILES = {
    "essential": Profile(1, 100_000, 50, 600, 4000, 4),
    "guided": Profile(2, 500_000, 200, 1800, 6000, 8),
    "lab": Profile(4, 3_000_000, 2000, 7200, 8000, 24),
    "vps": Profile(2, 1_000_000, 600, 3600, 6000, 8),
}


def configure(mode):
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    profile = PROFILES[mode]
    workers = min(profile.workers, os.cpu_count() or 1)
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = str(workers)
    return profile, workers


def describe():
    return {name: asdict(profile) for name, profile in PROFILES.items()}


def timeout_seconds(mode, hours=None):
    import math

    if hours is None:
        return PROFILES[mode].timeout_seconds
    if not math.isfinite(hours) or not 0 < hours <= 168:
        raise ValueError("--timeout-hours must be finite, positive and at most 168")
    return hours * 3600
