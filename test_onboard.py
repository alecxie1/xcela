#!/usr/bin/env python3
"""test_onboard.py — falsifiable self-test for the web onboarding wizard (feature 006).

No paid calls; model-free (the wizard logic is asserted over the synthetic fixture; the OCR organ is
proven in 005). Covers the 3 wizard steps as PURE functions (no live HTTP):
  US1: start_draft -> draft_id + 1-indexed suggestions (hex page, not the mention page).
  US2: extract_draft -> color locks + name candidates; zero-color page set -> BLOCK.
  US3: save_draft -> a validated key (validate_lean_key pass + primary hex in the thin prompt) with no
       typography.styles; FAIL-LOUD on no primary / no logo / unacknowledged flag / existing id; the
       saved brand appears in frontend.server._brands(); keep-flagged persists needs_review.

Run:  .venv/bin/python test_onboard.py
"""

import hashlib
import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
for p in ("frontend", "brand_intake", "harness", "register", "tests_support", str(REPO)):
    sys.path.insert(0, str(REPO / p) if not p.startswith("/") else p)

import onboard                          # noqa: E402  (frontend/onboard.py)
import validate_key                     # noqa: E402
import persist                          # noqa: E402
from make_pdf import make_default       # noqa: E402
from scene_author import assemble_thin_prompt  # noqa: E402
from derive_register import derive_register    # noqa: E402

PDF_BYTES = Path(make_default(Path(tempfile.mkdtemp()) / "vi.pdf")).read_bytes()
SUBFIELDS = {"usage_context": "held for photos / posed with",
             "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
             "logo_treatment": "omit", "brand_strictness": "expressive departure"}
THROWAWAY = "_t_onboard006"


def _cleanup():
    (REPO / "answer_keys" / f"{THROWAWAY}.json").unlink(missing_ok=True)
    shutil.rmtree(REPO / "brands" / THROWAWAY, ignore_errors=True)


# ---- US1 ----

def check1_start_draft_suggests_hex_page():
    d = onboard.start_draft(PDF_BYTES)
    color = d["suggestions"]["color"]
    pdf_on_disk = Path(d["_pdf_path"]).is_file() if "_pdf_path" in d else True
    passed = bool(d.get("draft_id")) and 2 in color and 1 not in color and pdf_on_disk
    return passed, f"draft_id set={bool(d.get('draft_id'))}; color={color} (2 in / 1 out); pdf on disk={pdf_on_disk}"


# ---- US2 ----

def check2_extract_returns_locks():
    d = onboard.start_draft(PDF_BYTES)
    r = onboard.extract_draft(d["draft_id"], {"color": [2], "name": [1]})
    locks = r.get("locks", [])
    has_hex_flag = bool(locks) and all("hex" in c and "needs_review" in c for c in locks)
    return has_hex_flag, f"locks={[(c.get('hex'), c.get('needs_review')) for c in locks]}; names={r.get('names',{}).get('cn_candidates')}"


def check3_zero_color_blocks():
    d = onboard.start_draft(PDF_BYTES)
    r = onboard.extract_draft(d["draft_id"], {"color": [1], "name": [1]})  # page 1 has no hex
    passed = bool(r.get("block")) and not r.get("locks")
    return passed, f"block={r.get('block')!r}; locks={r.get('locks')}"


# ---- US3 ----

def _verified(role="primary", ack="confirm"):
    return {"brand": THROWAWAY, "brand_cn": THROWAWAY, "brand_en": "TBRAND",
            "colors": [{"hex": "#31B4E7", "rgb": [49, 180, 231], "role": role,
                        "name_cn": "", "name_en": "", "needs_review": True, "_ack": ack}]}


def _logo():
    p = Path(tempfile.mkdtemp()) / "logo.png"; p.write_bytes(b"\x89PNG\r\n"); return str(p)


def check4_save_writes_valid_key():
    _cleanup()
    d = onboard.start_draft(PDF_BYTES)
    onboard.extract_draft(d["draft_id"], {"color": [2], "name": [1]})
    onboard.save_draft(d["draft_id"], _verified(), _logo())
    key = json.loads((REPO / "answer_keys" / f"{THROWAWAY}.json").read_text(encoding="utf-8"))
    validate_key.validate_lean_key(key)
    rp = derive_register(SUBFIELDS, key)
    prompt = assemble_thin_prompt(key, ["守住钱袋子"], register_profile=rp)
    no_styles = "styles" not in key.get("fields", {}).get("typography", {})
    draft_gone = not Path(d.get("_draft_dir", "/nonexistent")).exists() if d.get("_draft_dir") else True
    passed = ("#31B4E7" in prompt or "31B4E7" in prompt) and no_styles and draft_gone
    _cleanup()
    return passed, f"key written + validates; primary hex in prompt={'31B4E7' in prompt.upper()}; no typography.styles={no_styles}; draft discarded={draft_gone}"


def _save_should_fail(verified, logo, why):
    _cleanup()
    d = onboard.start_draft(PDF_BYTES)
    onboard.extract_draft(d["draft_id"], {"color": [2], "name": [1]})
    raised = False
    try:
        onboard.save_draft(d["draft_id"], verified, logo)
    except Exception:  # noqa: BLE001
        raised = True
    wrote = (REPO / "answer_keys" / f"{THROWAWAY}.json").exists()
    _cleanup()
    return (raised and not wrote), f"{why}: raised={raised}, file written={wrote} (want raised + no file)"


def check5_fail_no_primary():
    return _save_should_fail(_verified(role="secondary"), _logo(), "no primary")


def check6_fail_no_logo():
    return _save_should_fail(_verified(), "", "missing logo")


def check7_fail_unacknowledged():
    return _save_should_fail(_verified(ack=None), _logo(), "unacknowledged flag")


def check8_fail_existing_id():
    # reuse an existing committed brand id (aia) -> collision -> fail loud, no overwrite
    v = _verified(); v["brand"] = "aia"
    _cleanup()
    d = onboard.start_draft(PDF_BYTES)
    onboard.extract_draft(d["draft_id"], {"color": [2], "name": [1]})
    before = hashlib.sha256((REPO / "answer_keys" / "aia.json").read_bytes()).hexdigest()
    raised = False
    try:
        onboard.save_draft(d["draft_id"], v, _logo())
    except Exception:  # noqa: BLE001
        raised = True
    after = hashlib.sha256((REPO / "answer_keys" / "aia.json").read_bytes()).hexdigest()
    return (raised and before == after), f"collision raised={raised}; aia.json unchanged={before == after}"


def check9_saved_brand_in_dropdown():
    _cleanup()
    d = onboard.start_draft(PDF_BYTES)
    onboard.extract_draft(d["draft_id"], {"color": [2], "name": [1]})
    onboard.save_draft(d["draft_id"], _verified(ack="keep-flagged"), _logo())
    server = importlib.import_module("server")
    in_dropdown = THROWAWAY in server._brands()
    key = json.loads((REPO / "answer_keys" / f"{THROWAWAY}.json").read_text(encoding="utf-8"))
    kept = any(c.get("needs_review") is True for c in key["fields"]["colors"]["items"])
    _cleanup()
    return (in_dropdown and kept), f"in _brands()={in_dropdown}; keep-flagged persisted needs_review={kept}"


CHECKS = [
    ("US1 start_draft suggests the hex page (1-indexed)", check1_start_draft_suggests_hex_page),
    ("US2 extract_draft returns color locks + names", check2_extract_returns_locks),
    ("US2 zero-color page set BLOCKS (no fabricated color)", check3_zero_color_blocks),
    ("US3 save writes a valid key (no typography.styles) + draft discarded", check4_save_writes_valid_key),
    ("US3 save FAILS LOUD: no primary", check5_fail_no_primary),
    ("US3 save FAILS LOUD: missing logo", check6_fail_no_logo),
    ("US3 save FAILS LOUD: unacknowledged flag", check7_fail_unacknowledged),
    ("US3 save FAILS LOUD: existing brand id (no overwrite)", check8_fail_existing_id),
    ("US3 saved brand in _brands() + keep-flag persists", check9_saved_brand_in_dropdown),
]


def main():
    print("=" * 78)
    print("test_onboard.py — falsifiable self-test (006 US1-US3, no paid calls)")
    print("=" * 78)
    passed = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        passed += int(ok)
        print(f"\nCHECK {i}/{len(CHECKS)} — {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed}/{len(CHECKS)} checks passed")
    print("=" * 78)
    sys.exit(0 if passed == len(CHECKS) else 1)


if __name__ == "__main__":
    main()
