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
    "lab": Profile(4, 3_000_000, 1000, 7200, 8000, 16),
    "vps": Profile(2, 1_000_000, 600, 3600, 6000, 8),
}


def configure(mode):
    profile = PROFILES[mode]
    workers = min(profile.workers, os.cpu_count() or 1)
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = str(workers)
    return profile, workers


def describe():
    return {name: asdict(profile) for name, profile in PROFILES.items()}
