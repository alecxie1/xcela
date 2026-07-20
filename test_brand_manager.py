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
        # 2026-07-20 (023 US3): color rows now CARRY the names so page edits can
        # round-trip them (the wipe fix); the seeded key has none -> empty strings
        a = (tb["name_cn"] == "测试牌" and tb["logo_resolved"] is True
             and tb["colors"][0] == {"hex": "#D81E05", "role": "primary",
                                     "name_cn": "", "name_en": ""})
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


def check6_ui():
    """UI wiring (greps, value-bearing): manage.html carries the four verbs (list fetch,
    update/logo/delete posts) with the retype-confirm prompt and the PNG/JPG/WebP accept;
    ALL FOUR pages carry the 品牌管理 nav link; the run form renders the per-brand asset
    status from /brands/detail (best-effort, never blocking); the playbook documents the
    manager incl. the loud-refusal contract."""
    mg = (REPO / "frontend" / "manage.html").read_text(encoding="utf-8")
    # 2026-07-14 (021): the page's API calls go through the jf() 401 wrapper now; the
    # pinned value moved WITH the call, never weakened
    a = all(s in mg for s in ('jf("/brands/detail")', "/update", "/logo", "/delete",
                              "原样输入品牌 ID", 'accept=".png,.jpg,.jpeg,.webp"',
                              "缺少 logo 素材"))
    pages = ["index.html", "onboard.html", "manage.html", "playbook.html"]
    b = all('href="/manage"' in (REPO / "frontend" / p).read_text(encoding="utf-8")
            for p in pages)
    ix = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
    c = ('id="brandstatus"' in ix and 'jf("/brands/detail")' in ix  # 021: via jf()
         and "renderBrandStatus" in ix and "✓ 素材齐全" in ix)
    pb = (REPO / "frontend" / "playbook.html").read_text(encoding="utf-8")
    e = "品牌管理" in pb and "明确拒绝" in pb
    # 019 T004: the wizard shares the ONE guard (server-side call + narrowed accept)
    ob = (REPO / "frontend" / "onboard.html").read_text(encoding="utf-8")
    srv = (REPO / "frontend" / "server.py").read_text(encoding="utf-8")
    f = ('accept=".png,.jpg,.jpeg,.webp"' in ob
         and "brand_manager.validate_logo_format(logo[0], logo[1])" in srv)
    ok = a and b and c and e and f
    return ok, f"manage-page={a}; nav-x4={b}; form-status={c}; playbook={e}; wizard-guard={f}"


def check7_palette_management():
    """023 (US3): the wipe wart is dead by value - an update carrying names writes them
    (round-trip through disk), rgb is COMPUTED from hex (never None for a valid hex), a
    grown palette (add) and a shrunk one (remove) both land through the same validate
    gate, and the page renders add/remove controls + per-color name inputs."""
    keys, _ = _workspace()
    try:
        code, _b = bm.update_brand("TB", {"colors": [
            {"hex": "#31B4E7", "role": "primary", "name_cn": "天空蓝", "name_en": "Sky Blue"},
            {"hex": "73C900", "role": "secondary", "name_cn": "鲜草绿", "name_en": "Fresh Green"},
            {"hex": "096208", "role": "accent", "name_cn": "深绿", "name_en": "Deep Green"}]})
        after = json.loads((keys / "TB.json").read_text(encoding="utf-8"))
        items = after["fields"]["colors"]["items"]
        a = (code == 200 and len(items) == 3    # grown from the seeded 2: add works
             and items[0]["name_cn"] == "天空蓝" and items[0]["name_en"] == "Sky Blue"
             and items[2]["name_cn"] == "深绿")
        b = items[0]["rgb"] == [49, 180, 231] and items[1]["rgb"] == [115, 201, 0]
        # names survive a role-only edit (the CJXQ scenario: the page always sends what
        # it renders, and it now renders the names)
        detail = {r["brand"]: r for r in bm.list_brands_detail()}["TB"]
        c = detail["colors"][0]["name_cn"] == "天空蓝"
        code2, _b2 = bm.update_brand("TB", {"colors": [
            {"hex": "#31B4E7", "role": "primary", "name_cn": "天空蓝", "name_en": "Sky Blue"}]})
        after2 = json.loads((keys / "TB.json").read_text(encoding="utf-8"))
        d = (code2 == 200 and len(after2["fields"]["colors"]["items"]) == 1  # remove works
             and after2["fields"]["colors"]["items"][0]["name_cn"] == "天空蓝")
    finally:
        _cleanup()
    mg = (REPO / "frontend" / "manage.html").read_text(encoding="utf-8")
    e = ("addColor(" in mg and "添加颜色" in mg and 'data-ncn' in mg and 'data-nen' in mg
         and "颜色名（中文）" in mg and 'name_cn: row.querySelector("input[data-ncn]").value.trim()' in mg)
    ok = a and b and c and d and e
    return ok, (f"names-written+grown={a}; rgb-computed={b}; detail-carries-names={c}; "
                f"shrink-lands={d}; page-controls={e}")


CHECKS = [
    ("019 list detail: honest logo_resolved, corrupt tolerance", check1_list_detail),
    ("019 update: validate-gated, refusal leaves bytes identical", check2_update),
    ("019 logo: ext + header guard by value, relative placement", check3_logo_guard_and_replace),
    ("019 delete: server-side confirm, key-only, honest note", check4_delete),
    ("019 routes: lock, traversal guard, views, wizard guard intact", check5_route_wiring),
    ("019 UI: manage page, nav on all pages, form status line, playbook section", check6_ui),
    ("023 US3: palette add/remove/names round-trip + rgb computed", check7_palette_management),
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
