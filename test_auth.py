#!/usr/bin/env python3
"""test_auth.py - falsifiable self-test for feature 021 (auth + multi-tenancy).

T001 scope: the HTTP-free auth core (scrypt store, disk sessions, CLI). The T002 gate
checks (open-access byte-identity pin, 302/401, login round-trip) and the T003 ownership
matrix append here as the feature builds.

Fully hermetic: every check points XCELA_USERS_FILE at a fresh tmp dir; the repo's real
users.json (if any) is never read or written. NO paid calls anywhere.

Run:  .venv/bin/python test_auth.py
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "frontend"))
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO))

import auth  # noqa: E402


def _workspace() -> Path:
    """A tmp users file location (file NOT created: auth starts disabled)."""
    d = Path(tempfile.mkdtemp(prefix="auth_ws_"))
    os.environ["XCELA_USERS_FILE"] = str(d / "users.json")
    return d


def _cleanup():
    os.environ.pop("XCELA_USERS_FILE", None)


def check1_enabled_switch():
    """The activation pin at core level: no users file = enabled() False AND every lookup
    is a clean negative (verify/role/session_user all null, never a crash); creating the
    first user flips enabled() True; removing the LAST user deletes the file so auth
    deactivates instead of locking everyone out."""
    ws = _workspace()
    try:
        a = (auth.enabled() is False and auth.verify("kevin", "pw") is False
             and auth.role("kevin") is None
             and auth.session_user("xcela_session=deadbeef") is None)
        auth.add_user("kevin", "pw1")
        b = auth.enabled() is True and (ws / "users.json").is_file()
        removed = auth.remove_user("kevin")
        c = removed is True and auth.enabled() is False and not (ws / "users.json").exists()
    finally:
        _cleanup()
    ok = a and b and c
    return ok, f"off-is-null={a}; first-user-enables={b}; last-removal-disables={c}"


def check2_scrypt_verify():
    """Password truth BY VALUE: the right password verifies, a wrong one and a
    non-whitelisted user do not; hashes are real scrypt (per-user salt: two users with
    the SAME password store different hashes; the plaintext appears nowhere on disk)."""
    ws = _workspace()
    try:
        auth.add_user("alice", "s3cret-密码")
        auth.add_user("bob", "s3cret-密码")
        a = auth.verify("alice", "s3cret-密码") is True
        b = (auth.verify("alice", "wrong") is False
             and auth.verify("alice", "") is False
             and auth.verify("mallory", "s3cret-密码") is False)
        store = json.loads((ws / "users.json").read_text(encoding="utf-8"))
        c = (store["alice"]["hash"] != store["bob"]["hash"]
             and store["alice"]["salt"] != store["bob"]["salt"]
             and "s3cret-密码" not in (ws / "users.json").read_text(encoding="utf-8"))
        # re-add IS the password reset (the spec's out-of-scope list)
        auth.add_user("alice", "newpw")
        d = auth.verify("alice", "newpw") is True and auth.verify("alice", "s3cret-密码") is False
    finally:
        _cleanup()
    ok = a and b and c and d
    return ok, f"right-pw={a}; wrong+missing-refused={b}; salted-no-plaintext={c}; readd-resets={d}"


def check3_roles():
    """role() by value: --super marks super, default is user, unknown is None; list_users
    reports both."""
    _workspace()
    try:
        auth.add_user("kevin", "pw", is_super=True)
        auth.add_user("designer", "pw")
        a = auth.role("kevin") == "super" and auth.role("designer") == "user"
        b = auth.role("ghost") is None
        c = auth.list_users() == [{"user": "designer", "role": "user"},
                                  {"user": "kevin", "role": "super"}]
    finally:
        _cleanup()
    ok = a and b and c
    return ok, f"super+user={a}; unknown-None={b}; list={c}"


def check4_sessions():
    """Session lifecycle: mint -> the cookie header round-trips {user, role}; a bogus
    token and a MISSING cookie are None; expiry is enforced (a token forced past its
    expires is dead); logout (drop_session) kills exactly that token; sessions.json sits
    BESIDE the users file and holds no plaintext password."""
    ws = _workspace()
    try:
        auth.add_user("alice", "pw", is_super=True)
        token = auth.mint_session("alice")
        hdr = f"other=1; {auth.COOKIE_NAME}={token}"
        a = auth.session_user(hdr) == {"user": "alice", "role": "super"}
        b = (auth.session_user(f"{auth.COOKIE_NAME}=forged") is None
             and auth.session_user("") is None and auth.session_user(None) is None)
        sfile = ws / "sessions.json"
        c = sfile.is_file() and "pw" not in sfile.read_text(encoding="utf-8")
        # force expiry on disk (30 days is not simulated with sleep)
        sessions = json.loads(sfile.read_text(encoding="utf-8"))
        sessions[token]["expires"] = time.time() - 1
        sfile.write_text(json.dumps(sessions), encoding="utf-8")
        d = auth.session_user(hdr) is None
        token2 = auth.mint_session("alice")
        # the expired token was pruned by the next mint (write path owns cleanup)
        e = token not in json.loads(sfile.read_text(encoding="utf-8"))
        auth.drop_session(token2)
        f = auth.session_user(f"{auth.COOKIE_NAME}={token2}") is None
    finally:
        _cleanup()
    ok = a and b and c and d and e and f
    return ok, (f"roundtrip={a}; forged/absent-None={b}; beside+no-plaintext={c}; "
                f"expiry-dead={d}; mint-prunes={e}; logout-kills={f}")


def check5_removed_user_sessions_die():
    """A user removed from the whitelist loses LIVE sessions immediately (the session
    record alone is not an identity: role() must still resolve)."""
    _workspace()
    try:
        auth.add_user("alice", "pw")
        auth.add_user("bob", "pw")
        t_alice = auth.mint_session("alice")
        t_bob = auth.mint_session("bob")
        auth.remove_user("alice")
        a = auth.session_user(f"{auth.COOKIE_NAME}={t_alice}") is None
        b = auth.session_user(f"{auth.COOKIE_NAME}={t_bob}") == {"user": "bob", "role": "user"}
    finally:
        _cleanup()
    ok = a and b
    return ok, f"removed-user-dead={a}; others-unaffected={b}"


def check6_cli():
    """The CLI IS Kevin's user management v1: add (injectable password reader, --super),
    list, remove all work through main() by value; remove of an unknown user refuses
    loudly (SystemExit); malformed argv refuses with usage."""
    _workspace()
    try:
        auth.main(["add", "kevin", "--super"], password_reader=lambda: "kpw")
        auth.main(["add", "designer"], password_reader=lambda: "dpw")
        a = (auth.verify("kevin", "kpw") and auth.role("kevin") == "super"
             and auth.verify("designer", "dpw") and auth.role("designer") == "user")
        auth.main(["remove", "designer"])
        b = auth.role("designer") is None and auth.enabled() is True
        try:
            auth.main(["remove", "ghost"])
            c = False
        except SystemExit as exc:
            c = "ghost" in str(exc)
        try:
            auth.main(["frobnicate"])
            d = False
        except SystemExit as exc:
            d = "usage" in str(exc)
        try:
            auth.main(["add"])       # missing username
            e = False
        except SystemExit as exc:
            e = "usage" in str(exc)
    finally:
        _cleanup()
    ok = a and b and c and d and e
    return ok, f"add+super={a}; remove={b}; unknown-loud={c}; bad-cmd={d}; bad-add={e}"


CHECKS = [
    ("021 enabled(): the no-users-file activation switch", check1_enabled_switch),
    ("021 scrypt verify: right/wrong/missing by value, salted, re-add resets", check2_scrypt_verify),
    ("021 roles: super/user/None + list", check3_roles),
    ("021 sessions: mint/lookup/expiry/logout on disk", check4_sessions),
    ("021 whitelist removal kills live sessions", check5_removed_user_sessions_die),
    ("021 CLI: add/remove/list via main()", check6_cli),
]


def main():
    print("=" * 78)
    print("test_auth.py - falsifiable self-test (021, no paid calls)")
    print("=" * 78)
    passed = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        passed += int(ok)
        print(f"\nCHECK {i}/{len(CHECKS)} - {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed}/{len(CHECKS)} checks passed")
    print("=" * 78)
    sys.exit(0 if passed == len(CHECKS) else 1)


if __name__ == "__main__":
    main()
