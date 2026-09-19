"""Run the TrafficAI data and prediction jobs on independent intervals."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class ScheduledJob:
    name: str
    script: Path
    interval_seconds: int
    next_run: float
    process: subprocess.Popen | None = None


jobs = [
    ScheduledJob(
        name="API update",
        script=PROJECT_ROOT / "scripts" / "run_update.py",
        interval_seconds=30 * 60,
        next_run=0,
    ),
    ScheduledJob(
        name="ML prediction",
        script=PROJECT_ROOT / "scripts" / "predict_traffic.py",
        interval_seconds=2 * 60,
        next_run=0,
    ),
]

stopping = False


def stop_scheduler(signum: int, _frame: object) -> None:
    """Stop the scheduler and terminate any job currently in progress."""
    global stopping
    print(f"Received signal {signum}; stopping scheduled jobs...", flush=True)
    stopping = True
    for job in jobs:
        if job.process and job.process.poll() is None:
            job.process.terminate()


def start_job(job: ScheduledJob) -> None:
    print(f"Starting {job.name}: {job.script.relative_to(PROJECT_ROOT)}", flush=True)
    job.process = subprocess.Popen(
        [sys.executable, str(job.script)],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
    )


def main() -> None:
    signal.signal(signal.SIGTERM, stop_scheduler)
    signal.signal(signal.SIGINT, stop_scheduler)

    print("TrafficAI scheduler started.", flush=True)
    print("API update interval: 30 minutes", flush=True)
    print("ML prediction interval: 2 minutes", flush=True)

    while not stopping:
        now = time.monotonic()

        for job in jobs:
            if job.process is not None:
                return_code = job.process.poll()
                if return_code is not None:
                    print(
                        f"{job.name} finished with exit code {return_code}.",
                        flush=True,
                    )
                    job.process = None

            if now >= job.next_run:
                if job.process is None:
                    start_job(job)
                else:
                    print(
                        f"Skipping {job.name}; the previous run is still active.",
                        flush=True,
                    )

                # Keep the schedule tied to the requested interval without
                # launching several catch-up runs after a long job.
                job.next_run = now + job.interval_seconds

        time.sleep(1)

    for job in jobs:
        if job.process:
            job.process.wait()
    print("TrafficAI scheduler stopped.", flush=True)


if __name__ == "__main__":
    main()