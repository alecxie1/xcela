#!/usr/bin/env python3
"""test_product_refs.py - falsifiable self-test for feature 013 (role-tagged references).

No paid calls: pure imports (scene_author, conductor, server parse helpers) + grep-gates on the
served form HTML (the WEAKEST gate, declared per the 010 precedent). Contract rows refer to
specs/013-role-tagged-references/contracts/product_refs_contract.md.

Run:  .venv/bin/python test_product_refs.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO / "frontend"))
import scene_author  # noqa: E402
import conductor  # noqa: E402

# Same fixture as test_lossless_brief (and its T001 baseline): minimal key, one message,
# marketing register, photo dialect, reference fed, nothing optional.
KEY = {"fields": {"brand_name_cn": {"value": "测试"}, "brand_name_en": {"value": "Test"},
                  "colors": {"items": [{"name_cn": "红", "name_en": "Red",
                                        "printed_html": "D81E05", "role": "primary"}]}}}
MARKETING = {"inferred_register": "marketing"}

# Pre-013 baseline (byte-identical to test_lossless_brief.EXPECTED_PREFEATURE_PROMPT: the 012
# fixture carries no asset_type/occasion and no products, so the prompt is unchanged since).
sys.path.insert(0, str(REPO))
from test_lossless_brief import EXPECTED_PREFEATURE_PROMPT  # noqa: E402


def _assemble(**kw):
    return scene_author.assemble_thin_prompt(KEY, ["新品上市"], register_profile=MARKETING,
                                             asset_profile="photo", has_reference=True, **kw)


def check1_fidelity_section():
    """T002 contract rows 1-2 + 12: section values verbatim with count; no-products prompt
    byte-identical to the pre-013 baseline; no em-dash in the new section."""
    prods = ["/tmp/p1.png", "/tmp/p2.png"]
    p = _assemble(product_images=prods)
    row1 = ("PRODUCT FIDELITY (the 2 additional supplied image(s) are the brand's REAL products)" in p
            and "same printed branding and label text" in p
            and "Do NOT redraw them as generic products" in p
            and "Only their backgrounds may be discarded" in p
            and "the ONLY words that may appear" in p)  # headline guard untouched
    row2 = (_assemble() == EXPECTED_PREFEATURE_PROMPT
            and _assemble(product_images=[]) == EXPECTED_PREFEATURE_PROMPT)
    section = p[p.index("PRODUCT FIDELITY"):p.index("Only their backgrounds") + 40]
    row12 = "—" not in section
    passed = row1 and row2 and row12
    return passed, f"section_values={row1}; no_products_byte_identical={row2}; no_emdash={row12}"


def check2_refs_list():
    """T002 contract rows 6-7: refs = [style, logo] + products (appended, prefix stable);
    zero products = exactly [style, logo]; the logo:omit fallback unchanged."""
    f = scene_author._thin_generation_refs
    style, logo, prods = "/r/ref.jpg", "/b/logo.png", ["/r/p1.png", "/r/p2.png"]
    with_p = f(style, logo, False, prods) == [style, logo] + prods
    without = f(style, logo, False, None) == [style, logo] and f(style, logo, False, []) == [style, logo]
    omit_fallback = f(None, logo, True, None) == [logo]           # historical fallback
    omit_with_p = f(None, logo, True, prods) == prods             # products satisfy the >=1 need
    passed = with_p and without and omit_fallback and omit_with_p
    return passed, (f"appended={with_p}; zero_products_prefeature={without}; "
                    f"omit_fallback={omit_fallback}; omit_with_products={omit_with_p}")


def check3_argparse_append():
    """T002 contract row 4: repeated --product-image collects into an ordered list."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--product-image", action="append", default=None)
    got = ap.parse_args(["--product-image", "a.png", "--product-image", "b.png"]).product_image
    none_case = ap.parse_args([]).product_image is None
    passed = got == ["a.png", "b.png"] and none_case
    return passed, f"ordered_append={got == ['a.png', 'b.png']}; default_none={none_case}"


def _inputs(product_images=None, ref="/tmp/ref.png"):
    d = {"asset_type": "poster", "format_size": "60x40cm", "reference_image": ref,
         "reference_relationship": "extend", "render_style": "photographic",
         "mandatory_elements": [], "forbidden_elements": [],
         "context": {"usage_context": "wall-posted", "occasion": "",
                     "vibe": {"formality": 2, "playfulness": 7},
                     "logo_treatment": "omit", "brand_strictness": "brand + accents"},
         "signs": [{"id": "s1", "messages": ["新品上市"], "hero_icon": None}]}
    if product_images is not None:
        d["product_images"] = product_images
    return d


def _plan_argvs(inputs, label):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        plan = conductor.build_plan(inputs, "aia", Path(d) / "o", no_approve=True, thin=True)
    return [s["argv"] for s in plan["steps"] if s["label"] == label]


def _exec_argvs(inputs, label):
    import contextlib
    import io
    import json as _json
    import tempfile
    captured = []

    def stub(step):
        captured.append(step)
        return {"label": step["label"], "phase": step["phase"], "ok": False, "returncode": 1}

    orig = conductor.run_step
    conductor.run_step = stub
    try:
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "run"
            out.mkdir()
            ip = Path(d) / "inputs.json"
            ip.write_text(_json.dumps(inputs), encoding="utf-8")
            plan = conductor.build_plan(inputs, "aia", out, no_approve=True, thin=True)
            with contextlib.redirect_stdout(io.StringIO()):
                conductor.execute(inputs, "aia", out, ip, True, plan, thin=True)
    finally:
        conductor.run_step = orig
    return [s["argv"] for s in captured if s["label"] == label]


def _prod_flags(argv):
    return [argv[i + 1] for i, a in enumerate(argv) if a == "--product-image"]


def check4_conductor_threading():
    """T003 contract rows 3 + 14: ordered --product-image at BOTH call sites when the brief
    carries them; absent entirely for a legacy brief without the key (byte-compat)."""
    prods = ["/tmp/pr_a.png", "/tmp/pr_b.png"]
    with_p, legacy = _inputs(prods), _inputs()
    parts = []
    for name, get in (("plan", _plan_argvs), ("execute", _exec_argvs)):
        wa, la = get(with_p, "scene_author"), get(legacy, "scene_author")
        carried = bool(wa) and all(_prod_flags(a) == prods for a in wa)
        absent = bool(la) and all("--product-image" not in a for a in la)
        parts.append((carried and absent, f"{name}: carried_ordered={carried} legacy_absent={absent}"))
    passed = all(ok for ok, _ in parts)
    return passed, "; ".join(msg for _, msg in parts)


def check5_cap_and_missing_fail_loud():
    """T003 contract row 5: validate_inputs fail-louds (named error) on >6 products and on a
    listed file missing from disk; <=6 existing files pass."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        real = []
        for i in range(7):
            p = Path(d) / f"p{i}.png"
            p.write_bytes(b"x")
            real.append(str(p))
        over = _inputs(real)  # 7 files > cap
        try:
            conductor.validate_inputs(over)
            over_ok = False
        except SystemExit as e:
            over_ok = "6" in str(e) and "product_images" in str(e)
        missing = _inputs([str(Path(d) / "nope.png")])
        try:
            conductor.validate_inputs(missing)
            missing_ok = False
        except SystemExit as e:
            missing_ok = "not found" in str(e)
        good = _inputs(real[:6])
        good_ok = conductor.validate_inputs(good) is good
    passed = over_ok and missing_ok and good_ok
    return passed, f"over_cap_named={over_ok}; missing_named={missing_ok}; six_pass={good_ok}"


def check6_calibration_isolation():
    """T003 contract row 8 (SC-003): the calibrate step argv is IDENTICAL for the same brief
    with and without product_images; product truth never reaches magnitude/register."""
    import tempfile
    prods = ["/tmp/pr_a.png"]
    with tempfile.TemporaryDirectory() as d:  # SAME out dir so only the brief differs
        out = Path(d) / "o"
        pw = conductor.build_plan(_inputs(prods), "aia", out, no_approve=True, thin=True)
        po = conductor.build_plan(_inputs(), "aia", out, no_approve=True, thin=True)

    def argvs(plan, label):
        return [s["argv"] for s in plan["steps"] if s["label"] == label]

    cal_with, cal_without = argvs(pw, "calibrate"), argvs(po, "calibrate")
    derive_with, derive_without = argvs(pw, "derive_register"), argvs(po, "derive_register")
    passed = (cal_with == cal_without and bool(cal_with)
              and derive_with == derive_without and bool(derive_with))
    return passed, (f"calibrate_identical={cal_with == cal_without}; "
                    f"derive_identical={derive_with == derive_without}")


def check7_style_only_end_to_end():
    """T004/US2 (contract rows 7, 13, 14 consolidation): a verbatim pre-013 brief (no
    product_images key) yields a plan whose scene_author argv has NO --product-image and whose
    calibrate argv is unchanged; validate_inputs passes it untouched; the zero-products refs
    equality is already pinned by check2. A build that invents a default product list fails."""
    legacy = _inputs()  # no product_images key at all (the pre-013 shape)
    validated = conductor.validate_inputs(dict(legacy, signs=[dict(s) for s in legacy["signs"]]))
    no_key = "product_images" not in validated
    sa = _plan_argvs(legacy, "scene_author")
    cal = _plan_argvs(legacy, "calibrate")
    clean = (bool(sa) and all("--product-image" not in a for a in sa)
             and bool(cal) and all("product" not in " ".join(a) for a in cal))
    passed = no_key and clean
    return passed, f"legacy_validates_without_key={no_key}; plan_clean={clean}"


def _multipart_body(files, form_json='{"brand":"aia"}'):
    """Build a multipart body: one `form` field + the given {part_name: (filename, bytes)}."""
    B = "testboundary42"
    parts = [f'--{B}\r\nContent-Disposition: form-data; name="form"\r\n\r\n{form_json}\r\n']
    for part_name, (fn, data) in files.items():
        parts.append(f'--{B}\r\nContent-Disposition: form-data; name="{part_name}"; '
                     f'filename="{fn}"\r\nContent-Type: image/png\r\n\r\n')
        parts.append(data)
        parts.append("\r\n")
    parts.append(f"--{B}--\r\n")
    body = b"".join(p if isinstance(p, bytes) else p.encode("utf-8") for p in parts)
    return body, f"multipart/form-data; boundary={B}"


def check8_server_multipart_products():
    """T005 contract rows 9-10: parse_run_form 0/2/7 product parts (7 rejects naming the cap);
    write_run_inputs saves product_<i>.<ext> via the shared home and injects the paths in
    order; the 0-product case stays a pre-013 inputs file (no key). Plus a cap drift guard
    (server constant == conductor constant)."""
    import json as _json
    import tempfile
    import server

    ref = {"reference": ("style.jpg", b"REF")}
    # 0 products: today's behavior, 3-tuple with an empty list
    b0, ct = _multipart_body(dict(ref))
    f0, r0, p0 = server.parse_run_form(b0, ct)
    zero_ok = p0 == [] and r0[0] == "style.jpg"
    # 2 products, distinct part names, order by numeric suffix
    b2, ct = _multipart_body(dict(ref, product_2=("cupB.png", b"B"), product_1=("cupA.png", b"A")))
    _, _, p2 = server.parse_run_form(b2, ct)
    two_ok = [t[0] for t in p2] == ["cupA.png", "cupB.png"]
    # 7 products: ValueError naming the cap, never truncation
    seven = {f"product_{i}": (f"c{i}.png", b"x") for i in range(1, 8)}
    b7, ct = _multipart_body(dict(ref, **seven))
    try:
        server.parse_run_form(b7, ct)
        seven_ok = False
    except ValueError as e:
        seven_ok = "6" in str(e)
    # write_run_inputs: saved names + injected ordered paths; 0-product file has no key
    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d) / "run"
        form = {"reference_image": "", "messages": ["m"], "product_images": None}
        ip = server.write_run_inputs({"messages": ["m"]}, ("style.jpg", b"REF"), run_dir,
                                     products=[("cupA.png", b"A"), ("cupB.png", b"B")])
        inputs = _json.loads(Path(ip).read_text("utf-8"))
        saved = inputs.get("product_images") or []
        write_ok = ([Path(p).name for p in saved] == ["product_1.png", "product_2.png"]
                    and all(Path(p).is_file() for p in saved)
                    and Path(p2 := saved[0]).read_bytes() == b"A")
        ip0 = server.write_run_inputs({"messages": ["m"]}, ("style.jpg", b"REF"),
                                      Path(d) / "run0", products=[])
        no_key = "product_images" not in _json.loads(Path(ip0).read_text("utf-8"))
    cap_guard = server.MAX_PRODUCT_IMAGES == conductor.MAX_PRODUCT_IMAGES
    passed = zero_ok and two_ok and seven_ok and write_ok and no_key and cap_guard
    return passed, (f"zero={zero_ok}; two_ordered={two_ok}; seven_named_cap={seven_ok}; "
                    f"saved+injected={write_ok}; zero_no_key={no_key}; cap_drift_guard={cap_guard}")


def check9_form_controls():
    """T006 contract rows 11-12 (greps, the weakest gate): style-reference label on the old
    upload; an optional multiple-file product control capped client-side; the JS appends
    DISTINCT part names product_1..N; no em-dash in the new labels."""
    html = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
    style_label = "Style reference (required" in html and "how the asset should feel" in html
    control = ('id="product_images" multiple' in html
               and "Product shots (optional, up to 6)" in html
               and "must appear in the design" in html)
    distinct = ('fd.append("product_" + (i + 1), f, f.name)' in html
                and "prodFiles.length > 6" in html)
    new_lines = [l for l in html.splitlines()
                 if "Style reference" in l or "Product shots" in l or "product shots are supported" in l]
    no_emdash = bool(new_lines) and not any("—" in l for l in new_lines)
    passed = style_label and control and distinct and no_emdash
    return passed, (f"style_label={style_label}; multi_control={control}; "
                    f"distinct_parts+client_cap={distinct}; no_emdash={no_emdash}")


CHECKS = [
    ("US1 product fidelity section (values, byte-identity, no em-dash)", check1_fidelity_section),
    ("US1 generation refs list ([style, logo] + products; prefix byte-stable)", check2_refs_list),
    ("US1 repeatable --product-image collects in order", check3_argparse_append),
    ("US1 conductor threads product_images at BOTH call sites; legacy absent", check4_conductor_threading),
    ("US1 cap + missing-file fail LOUD (never truncate)", check5_cap_and_missing_fail_loud),
    ("US1 calibration isolation (calibrate/derive argv identical with products)", check6_calibration_isolation),
    ("US2 style-only brief byte-identical end to end (legacy shape untouched)", check7_style_only_end_to_end),
    ("US3 multipart product uploads (0/2/7 parts, shared save home, cap guard)", check8_server_multipart_products),
    ("US3 form: style-reference label + multi-file product control + distinct parts", check9_form_controls),
]


def main():
    print("=" * 78)
    print("test_product_refs.py - falsifiable self-test (013, no paid calls)")
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
