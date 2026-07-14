#!/usr/bin/env python3
"""test_brand_manager.py - falsifiable self-test for feature 019 (the brand database).

Fully hermetic: every check runs against a TMP keys workspace (XCELA_ANSWER_KEYS_DIR) and a
TMP brands base (XCELA_BRANDS_DIR); the committed fixtures and the real runtime dirs are
never written. NO paid calls anywhere.

Run:  .venv/bin/python test_brand_manager.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "frontend"))
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO))

from PIL import Image  # noqa: E402

import brand_manager as bm  # noqa: E402


def _workspace():
    """(keys_tmp, brands_tmp) seeded: TB (valid, relative logo that resolves), TB2 (valid
    fields, DANGLING logo), corrupt.json (unreadable)."""
    keys = Path(tempfile.mkdtemp(prefix="bm_keys_"))
    brands = Path(tempfile.mkdtemp(prefix="bm_brands_"))
    (brands / "TB").mkdir()
    Image.new("RGB", (32, 32), (250, 250, 250)).save(brands / "TB" / "logo.png")

    def key(name_cn, logo_rel):
        return {"brand": "x", "logo_path": logo_rel, "verified_by": "test",
                "verified_date": "2026-07-14",
                "fields": {"brand_name_cn": {"value": name_cn},
                           "brand_name_en": {"value": "TB"},
                           "colors": {"items": [
                               {"printed_html": "D81E05", "role": "primary"},
                               {"printed_html": "888888", "role": "secondary"}]}}}
    (keys / "TB.json").write_text(json.dumps(key("测试牌", "TB/logo.png"),
                                             ensure_ascii=False), encoding="utf-8")
    (keys / "TB2.json").write_text(json.dumps(key("悬空牌", "TB2/gone.png"),
                                              ensure_ascii=False), encoding="utf-8")
    (keys / "corrupt.json").write_text("{not json", encoding="utf-8")
    os.environ["XCELA_ANSWER_KEYS_DIR"] = str(keys)
    os.environ["XCELA_BRANDS_DIR"] = str(brands)
    return keys, brands


def _cleanup():
    os.environ.pop("XCELA_ANSWER_KEYS_DIR", None)
    os.environ.pop("XCELA_BRANDS_DIR", None)


def _png_bytes():
    import io
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), (10, 200, 10)).save(buf, format="PNG")
    return buf.getvalue()


def check1_list_detail():
    """GET /brands/detail truth: shapes per the spec, logo_resolved is HONEST (True only
    when the file resolves; the dangling key reports False), a corrupt key lists with an
    error entry instead of crashing the page."""
    keys, brands = _workspace()
    try:
        rows = {r["brand"]: r for r in bm.list_brands_detail()}
        tb, tb2, cor = rows["TB"], rows["TB2"], rows["corrupt"]
        a = (tb["name_cn"] == "测试牌" and tb["logo_resolved"] is True
             and tb["colors"][0] == {"hex": "#D81E05", "role": "primary"})
        b = tb2["logo_resolved"] is False and tb2["logo_path"] == "TB2/gone.png"
        c = "unreadable" in (cor.get("error") or "")
    finally:
        _cleanup()
    ok = a and b and c
    return ok, f"shape+resolved={a}; dangling-honest={b}; corrupt-tolerant={c}"


def check2_update():
    """Edits land only through the validate gate: a valid rename persists; an edit that
    strips the primary color is refused with the named error and the file stays
    BYTE-IDENTICAL; updating a nonexistent brand 404s."""
    keys, _ = _workspace()
    try:
        code, body = bm.update_brand("TB", {"name_cn": "新名字"})
        after = json.loads((keys / "TB.json").read_text(encoding="utf-8"))
        a = code == 200 and after["fields"]["brand_name_cn"]["value"] == "新名字"

        before = (keys / "TB.json").read_bytes()
        code2, body2 = bm.update_brand("TB", {"colors": [
            {"hex": "112233", "role": "secondary"}]})   # no primary -> must refuse
        b = (code2 == 400 and "primary" in body2["error"]
             and (keys / "TB.json").read_bytes() == before)   # byte-identical after refusal

        code3, _b3 = bm.update_brand("NOPE", {"name_cn": "x"})
        c = code3 == 404
    finally:
        _cleanup()
    ok = a and b and c
    return ok, f"rename-lands={a}; invalid-refused+file-untouched={b}; missing-404={c}"


def check3_logo_guard_and_replace():
    """The ONE format guard by value: .svg refused by extension with the named reason;
    right extension + WRONG bytes refused by the header sniff; a real PNG lands, the key's
    logo_path updates to the brands-relative form, and the new file resolves."""
    keys, brands = _workspace()
    try:
        code, body = bm.replace_logo("TB", "logo.svg", b"<svg></svg>")
        a = code == 400 and "unsupported logo format .svg" in body["error"]

        code2, body2 = bm.replace_logo("TB", "fake.png", b"not an image at all")
        b = code2 == 400 and "does not look like PNG/JPG/WebP" in body2["error"]

        code3, body3 = bm.replace_logo("TB", "new logo.png", _png_bytes())
        after = json.loads((keys / "TB.json").read_text(encoding="utf-8"))
        c = (code3 == 200 and after["logo_path"] == "TB/new logo.png"
             and (Path(os.environ["XCELA_BRANDS_DIR"]) / "TB" / "new logo.png").is_file())
    finally:
        _cleanup()
    ok = a and b and c
    return ok, f"ext-refused={a}; header-refused={b}; png-lands-relative={c}"


def check4_delete():
    """Delete requires retyping the id (server-side, never trust the UI), removes ONLY the
    key (the response says assets remain), and 404s for unknown brands."""
    keys, _ = _workspace()
    try:
        code, body = bm.delete_brand("TB", confirm="wrong")
        a = code == 400 and "confirmation mismatch" in body["error"] and (keys / "TB.json").is_file()

        code2, body2 = bm.delete_brand("TB", confirm="TB")
        b = (code2 == 200 and not (keys / "TB.json").is_file()
             and "remain on disk" in body2["note"])

        code3, _b3 = bm.delete_brand("TB", confirm="TB")
        c = code3 == 404
    finally:
        _cleanup()
    ok = a and b and c
    return ok, f"confirm-required={a}; key-only-delete+honest-note={b}; gone-404={c}"


def check5_route_wiring():
    """The server side (greps, value-bearing): the three write routes exist and run through
    _brand_write, which takes the single-flight lock, rejects path-traversal ids, and
    releases in finally; /brands/detail and /manage are served; the wizard collision guard
    (key_exists) is untouched by this feature."""
    srv = (REPO / "frontend" / "server.py").read_text(encoding="utf-8")
    a = all(s in srv for s in ('path.endswith("/update")', 'path.endswith("/logo")',
                               'path.endswith("/delete")', 'def _brand_write'))
    guard = srv.split("def _brand_write")[1].split("def _run_export")[0]
    b = ("_inflight.acquire(blocking=False)" in guard
         and '".." in brand' in guard and "_inflight.release()" in guard)
    c = '"/brands/detail"' in srv and '"/manage"' in srv
    e = "key_exists" in (REPO / "brand_intake" / "persist.py").read_text(encoding="utf-8")
    ok = a and b and c and e
    return ok, f"routes={a}; lock+traversal-guard={b}; views={c}; wizard-guard-intact={e}"


CHECKS = [
    ("019 list detail: honest logo_resolved, corrupt tolerance", check1_list_detail),
    ("019 update: validate-gated, refusal leaves bytes identical", check2_update),
    ("019 logo: ext + header guard by value, relative placement", check3_logo_guard_and_replace),
    ("019 delete: server-side confirm, key-only, honest note", check4_delete),
    ("019 routes: lock, traversal guard, views, wizard guard intact", check5_route_wiring),
]


def main():
    print("=" * 78)
    print("test_brand_manager.py - falsifiable self-test (019, no paid calls)")
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
