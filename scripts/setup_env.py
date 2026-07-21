"""
scripts/setup_env.py - Local setup routine for water-puppetry-staging-design.

Creates a virtualenv (optional), installs runtime + dev dependencies, copies
.env.example to .env if absent, and verifies the project validates. Safe to
re-run; idempotent.

Usage:
    python -m scripts.setup_env [--venv .venv] [--skip-venv] [--dev]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], cwd: Path = ROOT) -> int:
    print(f"$ {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(cwd))


def main() -> int:
    parser = argparse.ArgumentParser(description="Local setup for water-puppetry-staging-design")
    parser.add_argument("--venv", default=".venv", help="Virtualenv directory name")
    parser.add_argument("--skip-venv", action="store_true", help="Skip venv creation")
    parser.add_argument("--dev", action="store_true", help="Also install dev dependencies")
    args = parser.parse_args()

    env_example = ROOT / ".env.example"
    env = ROOT / ".env"
    if env_example.exists() and not env.exists():
        shutil.copyfile(env_example, env)
        print("created .env from .env.example")

    py = sys.executable
    if not args.skip_venv:
        venv_path = ROOT / args.venv
        if not venv_path.exists():
            rc = run([py, "-m", "venv", str(venv_path)])
            if rc != 0:
                print("venv creation failed", file=sys.stderr)
                return rc
        if venv_path.exists():
            py = (
                str(venv_path / "Scripts" / "python.exe")
                if sys.platform == "win32"
                else str(venv_path / "bin" / "python")
            )

    rc = run([py, "-m", "pip", "install", "--upgrade", "pip"])
    if rc != 0:
        return rc
    rc = run([py, "-m", "pip", "install", "-r", "requirements.txt"])
    if rc != 0:
        return rc
    if args.dev:
        rc = run([py, "-m", "pip", "install", "-e", ".[dev]"])
        if rc != 0:
            return rc

    rc = run([py, "-m", "tools.validate_project"])
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
