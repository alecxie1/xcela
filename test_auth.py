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


# ---- T002: the server gate (ephemeral instances, the deploy-readiness check9 pattern) ----

def _server_instance():
    """(srv, port): an ephemeral live server on 127.0.0.1:0. keys_dir is ALSO pinned to a
    tmp dir so /brands never reads the machine's real runtime keys."""
    import threading
    from http.server import ThreadingHTTPServer
    os.environ["XCELA_ANSWER_KEYS_DIR"] = tempfile.mkdtemp(prefix="auth_keys_")
    import server
    srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def _req(port, method, path, body=None, cookie=None, ctype="application/json"):
    """(status, headers, json_or_bytes) via a real HTTP round trip."""
    import http.client
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {}
    if cookie:
        headers["Cookie"] = cookie
    if body is not None:
        headers["Content-Type"] = ctype
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    hdrs = dict(resp.getheaders())
    if (hdrs.get("Content-Type") or "").startswith("application/json"):
        return resp.status, hdrs, json.loads(data or b"{}")
    return resp.status, hdrs, data


def check7_open_access_pin():
    """THE PIN: no users file = the server is byte-for-byte today's open server. The four
    pages and the API answer 200 WITHOUT any cookie, whoami says {auth: false}, and
    POST /login refuses (there is nothing to log into)."""
    _workspace()   # users file location set but NOT created: auth off
    srv = None
    try:
        srv, port = _server_instance()
        s1, h1, b1 = _req(port, "GET", "/")
        a = s1 == 200 and b"topnav" in b1 and "Set-Cookie" not in h1
        s2, _h2, b2 = _req(port, "GET", "/brands")
        b = s2 == 200 and "brands" in b2
        s3, _h3, b3 = _req(port, "GET", "/whoami")
        c = s3 == 200 and b3 == {"auth": False}
        s4, _h4, b4 = _req(port, "POST", "/login",
                           body=json.dumps({"username": "x", "password": "y"}))
        d = s4 == 409 and "auth is off" in b4["error"]
        s5, _h5, _b5 = _req(port, "GET", "/login")
        e = s5 == 200   # the page itself serves; its JS bounces home when auth is off
    finally:
        if srv:
            srv.shutdown()
        os.environ.pop("XCELA_ANSWER_KEYS_DIR", None)
        _cleanup()
    ok = a and b and c and d and e
    return ok, f"pages-open={a}; api-open={b}; whoami-off={c}; login-409={d}; login-page={e}"


def check8_gate_roundtrip():
    """With a users file: pages 302 to /login, APIs 401, a wrong password stays out, the
    right one sets the HttpOnly SameSite=Lax session cookie, the cookie opens every
    route, whoami round-trips {user, role}, and logout kills the session server-side."""
    _workspace()
    srv = None
    try:
        auth.add_user("kevin", "kpw", is_super=True)
        srv, port = _server_instance()
        s1, h1, _b1 = _req(port, "GET", "/")
        a = s1 == 302 and h1.get("Location") == "/login"
        s2, _h2, b2 = _req(port, "GET", "/brands")
        b = s2 == 401 and b2["error"] == "login required"
        s3, _h3, _b3 = _req(port, "POST", "/run/xxx/confirm", body="{}")
        c = s3 == 401   # spending routes are gated like every API
        s4, h4, _b4 = _req(port, "POST", "/login",
                           body=json.dumps({"username": "kevin", "password": "wrong"}))
        d = s4 == 401 and "Set-Cookie" not in h4
        s5, h5, b5 = _req(port, "POST", "/login",
                          body=json.dumps({"username": "kevin", "password": "kpw"}))
        sc = h5.get("Set-Cookie", "")
        e = (s5 == 200 and b5["role"] == "super" and sc.startswith(f"{auth.COOKIE_NAME}=")
             and "HttpOnly" in sc and "SameSite=Lax" in sc)
        cookie = sc.split(";", 1)[0]
        s6, _h6, b6 = _req(port, "GET", "/brands", cookie=cookie)
        s7, _h7, _b7 = _req(port, "GET", "/", cookie=cookie)
        f = s6 == 200 and "brands" in b6 and s7 == 200
        s8, _h8, b8 = _req(port, "GET", "/whoami", cookie=cookie)
        g = s8 == 200 and b8 == {"auth": True, "user": "kevin", "role": "super"}
        s9, h9, _b9 = _req(port, "POST", "/logout", body="{}", cookie=cookie)
        s10, _h10, _b10 = _req(port, "GET", "/brands", cookie=cookie)
        h = s9 == 200 and "Max-Age=0" in h9.get("Set-Cookie", "") and s10 == 401
    finally:
        if srv:
            srv.shutdown()
        os.environ.pop("XCELA_ANSWER_KEYS_DIR", None)
        _cleanup()
    ok = a and b and c and d and e and f and g and h
    return ok, (f"page-302={a}; api-401={b}; spend-401={c}; wrong-pw={d}; cookie-set={e}; "
                f"cookie-opens={f}; whoami={g}; logout-kills={h}")


def check9_ui_wiring():
    """UI wiring (greps, value-bearing): login.html carries the Chinese form posting to
    /login; index.html + manage.html route API calls through the jf() 401 wrapper (no
    stray `await fetch(` outside the whoami chip); onboard.html's jpost gained the same
    check; ALL FOUR pages carry the /whoami user chip with the 退出 button."""
    fe = REPO / "frontend"
    lg = (fe / "login.html").read_text(encoding="utf-8")
    a = all(s in lg for s in ('id="username"', 'id="password"', 'fetch("/login"', "登录"))
    pages = ["index.html", "manage.html"]
    b = all("async function jf(" in (fe / p).read_text(encoding="utf-8") for p in pages)
    # every non-chip fetch goes through jf: raw `await fetch(` survives ONLY for
    # /whoami and /logout (the chip, deliberately outside the 401-redirect loop)
    import re
    c = True
    for p in pages + ["onboard.html", "playbook.html"]:
        for m in re.findall(r"await (?:\(await )?fetch\(([^,)]*)", (fe / p).read_text(encoding="utf-8")):
            if '"/whoami"' not in m and '"/logout"' not in m and '"/login"' not in m and "url" not in m:
                c = False
    ob = (fe / "onboard.html").read_text(encoding="utf-8")
    d = "r.status === 401" in ob and 'location.href = "/login"' in ob
    e = all('fetch("/whoami")' in (fe / p).read_text(encoding="utf-8")
            and "退出" in (fe / p).read_text(encoding="utf-8")
            and 'id="userchip"' in (fe / p).read_text(encoding="utf-8")
            for p in ["index.html", "manage.html", "onboard.html", "playbook.html"])
    srv = (fe / "server.py").read_text(encoding="utf-8")
    f = ('HTML_PAGES = ("/", "/onboard", "/playbook", "/manage")' in srv
         and '"/whoami"' in srv and "def _authed" in srv)
    ok = a and b and c and d and e and f
    return ok, (f"login-page={a}; jf-defined={b}; no-stray-fetch={c}; jpost-401={d}; "
                f"chip-x4={e}; server-gate={f}")


CHECKS = [
    ("021 enabled(): the no-users-file activation switch", check1_enabled_switch),
    ("021 scrypt verify: right/wrong/missing by value, salted, re-add resets", check2_scrypt_verify),
    ("021 roles: super/user/None + list", check3_roles),
    ("021 sessions: mint/lookup/expiry/logout on disk", check4_sessions),
    ("021 whitelist removal kills live sessions", check5_removed_user_sessions_die),
    ("021 CLI: add/remove/list via main()", check6_cli),
    ("021 THE PIN: no users file = open access, live server", check7_open_access_pin),
    ("021 gate: 302/401, login cookie, whoami, logout, live server", check8_gate_roundtrip),
    ("021 UI: login page, jf wrapper, jpost check, chip on all four pages", check9_ui_wiring),
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
