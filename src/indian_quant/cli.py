"""Small CLI: isolated, time-bounded research; no arbitrary config execution."""

import argparse
import json
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path

from .resources import PROFILES, configure, describe


def parser():
    p = argparse.ArgumentParser(description="Indian Quant: educational CPU-first research")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Inspect Python/CPU; no external requests")
    sub.add_parser("modes", help="Show resource profiles")
    demo = sub.add_parser("demo", help="Generate fictional bars and run genuine Qlib integration")
    demo.add_argument("--workspace", type=Path, default=Path("workspace"))
    demo.add_argument("--mode", choices=PROFILES, default="essential")
    run = sub.add_parser("run", help="Run fixed-universe chronological research")
    run.add_argument("--data", required=True, type=Path)
    run.add_argument("--output", required=True, type=Path)
    run.add_argument("--calendar", type=Path)
    run.add_argument("--benchmark", required=True)
    run.add_argument("--mode", choices=PROFILES, default="essential")
    run.add_argument("--synthetic", action="store_true", help="Only for fictional demonstration data")
    run.add_argument("--buy-cost", type=float, default=0.001)
    run.add_argument("--sell-cost", type=float, default=0.0015)
    run.add_argument("--topk", type=int, default=5)
    run.add_argument("--capital", type=float, default=1_000_000)
    run.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    bank = sub.add_parser("bank-import", help="Validate and snapshot a supplied CSV/Parquet")
    bank.add_argument("source", type=Path)
    bank.add_argument("--bank", type=Path, default=Path("workspace/bank"))
    bank.add_argument("--provenance", required=True, help="Source, licence and adjustment convention")
    bank.add_argument("--mode", choices=PROFILES, default="essential")
    member = sub.add_parser("membership-audit", help="Audit a user-supplied NiftyHistory CSV")
    member.add_argument("source", type=Path)
    member.add_argument("--output", type=Path, required=True)
    return p


def launch(args):
    profile, _ = configure(args.mode)
    command = [
        sys.executable,
        "-m",
        "indian_quant",
        "run",
        "--worker",
        "--data",
        str(args.data),
        "--output",
        str(args.output),
        "--benchmark",
        args.benchmark,
        "--mode",
        args.mode,
        "--buy-cost",
        str(args.buy_cost),
        "--sell-cost",
        str(args.sell_cost),
        "--topk",
        str(args.topk),
        "--capital",
        str(args.capital),
    ]
    if args.synthetic:
        command.append("--synthetic")
    if args.calendar:
        command.extend(["--calendar", str(args.calendar)])
    process = subprocess.Popen(command, start_new_session=(os.name == "posix"))
    try:
        code = process.wait(timeout=profile.timeout_seconds)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.wait()
        mark_failed(args.output, "timeout" if isinstance(error, subprocess.TimeoutExpired) else "interrupted")
        raise ValueError("Research interrupted or exceeded time budget; inspect partial artifacts") from None
    if code:
        mark_failed(args.output, "failed")
        raise ValueError("Research failed; inspect the error above and partial manifest")


def mark_failed(output, status):
    path = Path(output) / "manifest.json"
    if path.exists():
        manifest = json.loads(path.read_text())
        if manifest.get("status") == "running":
            manifest["status"] = status
            path.write_text(json.dumps(manifest, indent=2))


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "doctor":
            print(
                json.dumps(
                    {
                        "python": platform.python_version(),
                        "platform": platform.system(),
                        "cpus": os.cpu_count(),
                        "recommended_mode": "essential",
                        "ai_required": False,
                        "live_execution": False,
                    },
                    indent=2,
                )
            )
        elif args.command == "modes":
            print(json.dumps(describe(), indent=2))
        elif args.command == "demo":
            configure(args.mode)
            from .data import synthetic

            args.workspace.mkdir(parents=True, exist_ok=True)
            args.data = args.workspace / "synthetic.csv"
            if not args.data.exists():
                synthetic(args.data)
            args.output = args.workspace / "runs" / ("demo-" + str(time.time_ns()))
            args.benchmark, args.synthetic, args.calendar = "BENCH", True, None
            args.buy_cost, args.sell_cost, args.topk, args.capital = 0.001, 0.0015, 5, 1_000_000
            launch(args)
            print(f"Report: {args.output / 'report.html'}")
        elif args.command == "run":
            if args.worker:
                configure(args.mode)
                from .research import run

                run(
                    args.data,
                    args.output,
                    args.mode,
                    args.benchmark,
                    args.synthetic,
                    args.calendar,
                    args.buy_cost,
                    args.sell_cost,
                    args.topk,
                    args.capital,
                )
            else:
                launch(args)
        elif args.command == "bank-import":
            configure(args.mode)
            from .data import bank_import

            print(bank_import(args.source, args.bank, PROFILES[args.mode], args.provenance))
        elif args.command == "membership-audit":
            from .membership import write_audit

            print(json.dumps(write_audit(args.source, args.output), indent=2))
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0
