#!/usr/bin/env python3
"""frontend/auth.py - login whitelist + disk-backed sessions (feature 021). Stdlib only.

The HTTP-free core the server gate (T002) calls, plus the whole user-management surface
Kevin gets in v1: a CLI (add/remove/list). Auth activates ONLY when the users file exists
(asset_paths.users_file, env XCELA_USERS_FILE); no file = enabled() False and the server
behaves byte-identically to pre-021 (THE pin). Passwords are real (hashlib.scrypt,
per-user salt, constant-time compare), never a spoofable bare-username whitelist.

  users.json      {username: {salt, hash, role}}   role in {"user", "super"}
  sessions.json   {token: {user, expires}}         beside the users file; 30-day expiry;
                                                   a server restart logs nobody out

Both files are runtime state (gitignored). Sessions are written only by mint/drop (the
lookup path is read-only), so unauthenticated GET traffic never writes disk.
"""

import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from http import cookies as _cookies
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "harness"))
from asset_paths import users_file  # noqa: E402

COOKIE_NAME = "xcela_session"
SESSION_TTL_S = 30 * 24 * 3600           # 30 days (binding decision 4)
# scrypt parameters (binding decision 2); RFC 7914 interactive-login strength
_SCRYPT = {"n": 2 ** 14, "r": 8, "p": 1}


def sessions_file() -> Path:
    return users_file().parent / "sessions.json"


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001  (missing or corrupt = no entries, never a crash)
        return {}


def _write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)             # hashes and live tokens: owner-only
    except OSError:
        pass


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, **_SCRYPT)


def enabled() -> bool:
    """True iff the users file exists: the ONE activation switch. Kevin opts in by
    creating users; deleting the file returns the deployment to open access."""
    return users_file().is_file()


def verify(username: str, password: str) -> bool:
    """True iff `username` is whitelisted AND the password matches its scrypt hash.
    A missing user still burns one scrypt (no timing oracle for user enumeration)."""
    rec = _read_json(users_file()).get(username)
    if rec is None:
        _hash(password or "", b"\x00" * 16)
        return False
    try:
        expected = bytes.fromhex(rec["hash"])
        got = _hash(password or "", bytes.fromhex(rec["salt"]))
    except (KeyError, ValueError, TypeError):
        return False                       # malformed record = refuse, never crash
    return hmac.compare_digest(got, expected)


def role(username: str):
    """"user" | "super" for a whitelisted username, None otherwise."""
    rec = _read_json(users_file()).get(username)
    if rec is None:
        return None
    return "super" if rec.get("role") == "super" else "user"


def mint_session(username: str) -> str:
    """New 30-day session token for an ALREADY-VERIFIED username (the caller runs
    verify() first). Prunes expired tokens while it holds the write anyway."""
    sessions = _read_json(sessions_file())
    now = time.time()
    sessions = {t: s for t, s in sessions.items()
                if isinstance(s, dict) and s.get("expires", 0) > now}
    token = secrets.token_urlsafe(32)
    sessions[token] = {"user": username, "expires": now + SESSION_TTL_S}
    _write_json(sessions_file(), sessions)
    return token


def _cookie_token(cookie_header: str):
    try:
        jar = _cookies.SimpleCookie(cookie_header or "")
    except _cookies.CookieError:
        return None
    morsel = jar.get(COOKIE_NAME)
    return morsel.value if morsel else None


def session_user(cookie_header: str):
    """{user, role} for a live session on the request's Cookie header, else None.
    Read-only: expiry is checked, not pruned here (mint/drop own the writes). A user
    removed from the whitelist loses every session immediately (role() returns None)."""
    token = _cookie_token(cookie_header)
    if not token:
        return None
    rec = _read_json(sessions_file()).get(token)
    if not isinstance(rec, dict) or rec.get("expires", 0) <= time.time():
        return None
    user_role = role(rec.get("user"))
    if user_role is None:
        return None
    return {"user": rec["user"], "role": user_role}


def drop_session(token: str):
    """Logout: delete the token (idempotent; unknown tokens are a silent no-op)."""
    sessions = _read_json(sessions_file())
    if token in sessions:
        del sessions[token]
        _write_json(sessions_file(), sessions)


# ---- user management (the CLI's pure half; tests call these by value) ----

def add_user(username: str, password: str, is_super: bool = False):
    """Create or replace (re-adding IS the password reset, per the spec's out-of-scope
    list). Refuses empty names/passwords loudly."""
    username = (username or "").strip()
    if not username:
        raise SystemExit("auth: username must be non-empty")
    if not password:
        raise SystemExit("auth: password must be non-empty")
    users = _read_json(users_file())
    salt = secrets.token_bytes(16)
    users[username] = {"salt": salt.hex(), "hash": _hash(password, salt).hex(),
                       "role": "super" if is_super else "user"}
    _write_json(users_file(), users)


def remove_user(username: str) -> bool:
    """Drop a user from the whitelist (their sessions die via the role() check).
    Returns False if the user was not present. Removing the LAST user deletes the
    users file entirely, so auth deactivates instead of locking everyone out."""
    users = _read_json(users_file())
    if username not in users:
        return False
    del users[username]
    if users:
        _write_json(users_file(), users)
    else:
        users_file().unlink(missing_ok=True)
    return True


def list_users() -> list:
    """[{user, role}] sorted by name."""
    users = _read_json(users_file())
    return [{"user": u, "role": ("super" if (r or {}).get("role") == "super" else "user")}
            for u, r in sorted(users.items())]


def main(argv=None, password_reader=None):
    """CLI: add <user> [--super] | remove <user> | list. `password_reader` is injectable
    for the self-test; the default prompts twice via getpass (typos lock a teammate out
    until a re-add, so confirm)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    usage = ("usage: python frontend/auth.py add <user> [--super] | remove <user> | list\n"
             f"users file: {users_file()} (env override: XCELA_USERS_FILE)")
    if not argv:
        raise SystemExit(usage)
    cmd, rest = argv[0], argv[1:]
    if cmd == "add":
        names = [a for a in rest if not a.startswith("--")]
        if len(names) != 1:
            raise SystemExit(usage)
        if password_reader is None:
            import getpass
            pw = getpass.getpass(f"password for {names[0]}: ")
            if pw != getpass.getpass("repeat password: "):
                raise SystemExit("auth: passwords do not match; nothing written")
        else:
            pw = password_reader()
        add_user(names[0], pw, is_super="--super" in rest)
        print(f"added {names[0]} ({'super' if '--super' in rest else 'user'}) "
              f"-> {users_file()}")
    elif cmd == "remove":
        if len(rest) != 1:
            raise SystemExit(usage)
        if remove_user(rest[0]):
            print(f"removed {rest[0]}")
            if not enabled():
                print("users file is now empty and was deleted: auth is OFF (open access)")
        else:
            raise SystemExit(f"auth: no user {rest[0]!r} in {users_file()}")
    elif cmd == "list":
        rows = list_users()
        if not rows:
            print(f"no users ({users_file()} absent): auth is OFF (open access)")
        for r in rows:
            print(f"{r['user']}\t{r['role']}")
    else:
        raise SystemExit(usage)


if __name__ == "__main__":
    main()
