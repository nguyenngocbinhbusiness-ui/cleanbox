"""Reusable release verification entrypoint for local and CI use."""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class CheckCommand:
    name: str
    command: Sequence[str]


def run_command(check: CheckCommand) -> int:
    """Run a verification command and return its exit code."""
    print(f"[verify-release] Running {check.name}: {' '.join(check.command)}")
    result = subprocess.run(check.command, cwd=PROJECT_ROOT, check=False)
    return result.returncode


def build_checks(include_flake8: bool = False) -> list[CheckCommand]:
    """Build the ordered list of release verification checks."""
    checks = [
        CheckCommand("pytest", [sys.executable, "-m", "pytest", "-q"]),
        CheckCommand("bandit", [sys.executable, "-m", "bandit", "-r", "src", "-f", "txt", "-ll"]),
        CheckCommand("compileall", [sys.executable, "-m", "compileall", "-q", "src"]),
        CheckCommand("pyinstaller-version", [sys.executable, "-m", "PyInstaller", "--version"]),
    ]
    if include_flake8:
        checks.insert(
            1,
            CheckCommand("flake8", [sys.executable, "-m", "flake8", "src", "tests", "--count", "--statistics"]),
        )
    return checks


def run_checks(include_flake8: bool = False) -> int:
    """Run release-blocking checks and return process exit code."""
    for check in build_checks(include_flake8=include_flake8):
        returncode = run_command(check)
        if returncode != 0:
            print(f"[verify-release] FAILED: {check.name} exited with {returncode}")
            return returncode
    print("[verify-release] All checks passed")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-flake8",
        action="store_true",
        help="Skip flake8 when lint is already enforced in a separate step.",
    )
    parser.add_argument(
        "--include-flake8",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry for CI and local release verification."""
    args = parse_args(argv)
    include_flake8 = args.include_flake8 or not args.skip_flake8
    return run_checks(include_flake8=include_flake8)


if __name__ == "__main__":
    raise SystemExit(main())
