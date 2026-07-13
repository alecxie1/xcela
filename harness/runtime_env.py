#!/usr/bin/env python3
"""runtime_env.py — feature 018: the ONE way keys and config enter the process.

Precedence (the deployment contract, README + .env.example):
  1. real environment variables (systemd unit, Docker, shell)  — ALWAYS win
  2. <repo>/.env                                               — the deployer's file
  3. ~/.hermes/.env                                            — legacy fallback (our machines)

Neither file load overrides anything already set (override=False). The pre-018 per-module
loads set the override flag, making the FILE beat the real environment, the opposite of
every standard convention; that behavior is gone (and grep-guarded by the self-test).
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_runtime_env(_repo: Path | None = None, _home: Path | None = None) -> None:
    """Idempotent; cheap to call from every entry module. The underscore params exist for
    the self-test only (hermetic precedence proof); production callers pass nothing."""
    from dotenv import load_dotenv
    load_dotenv((_repo or REPO_ROOT) / ".env", override=False)
    load_dotenv((_home or Path.home()) / ".hermes" / ".env", override=False)


def require(*names: str) -> None:
    """Fail LOUD with a named message when required variables are missing (never a deep
    stack trace from an SDK): call at the top of a paid path."""
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise SystemExit(f"missing required environment variables: {', '.join(missing)} "
                         "(set them in the environment or in <repo>/.env; see .env.example)")
