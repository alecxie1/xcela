#!/usr/bin/env python3
"""brand_intake/intake.py — standalone CLI: PDF -> human-verified lean answer_key (feature 005).

The front-half flow (each stage fails loud or honest-null + a note, never green-on-empty):
  suggest_pages -> human CONFIRM pages -> reuse extractors -> human VERIFY gate (assign color roles,
  ACKNOWLEDGE every needs_review) -> build_lean_key -> validate_lean_key (FAIL LOUD) ->
  write answer_keys/<brand>.json + place the logo under brands/<brand>/.

The verify-gate DECISION logic is pure + testable (unacknowledged_flags / finalize_items); the
interactive prompting lives in main(). `--no-gate` runs the deterministic path non-interactively for
tests / batch WITHOUT weakening the fail-loud validation.

  .venv/bin/python brand_intake/intake.py --pdf <VI.pdf> --brand <id> --verified-by "<you>" \
      [--pages-color 24,25] [--pages-name 1] [--logo <path>] [--no-gate]
"""

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO))
import page_finder
import extract as extract_mod
import assemble_key
import validate_key

_ACKS = {"confirm", "edit", "keep-flagged"}


# ---- pure verify-gate decision logic (testable without stdin) ----

def unacknowledged_flags(items):
    """Items carrying needs_review that have NOT been acknowledged (no valid `_ack`). Save is blocked
    while this is non-empty (acknowledgment gate, not clear gate)."""
    return [c for c in items if c.get("needs_review") and c.get("_ack") not in _ACKS]


def finalize_items(items):
    """Strip the scratch `_ack` field for saving. confirm/edit clear the flag; keep-flagged persists
    needs_review:true in the saved item (an honest record)."""
    out = []
    for c in items:
        c2 = {k: v for k, v in c.items() if k != "_ack"}
        ack = c.get("_ack")
        if ack in ("confirm", "edit"):
            c2.pop("needs_review", None)
        elif ack == "keep-flagged":
            c2["needs_review"] = True
        out.append(c2)
    return out


# ---- CLI ----

def _parse_pages(s):
    return [int(x) for x in str(s).replace(" ", "").split(",") if x] if s else []


def main():
    ap = argparse.ArgumentParser(description="Brand-intake front-half: PDF -> verified lean answer_key.")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--brand", required=True, help="brand id; writes answer_keys/<id>.json")
    ap.add_argument("--verified-by", default="")
    ap.add_argument("--pages-color", default="", help="comma-separated 1-indexed color pages (else use suggestion)")
    ap.add_argument("--pages-name", default="", help="comma-separated 1-indexed brand-name pages")
    ap.add_argument("--logo", default="", help="path to the brand logo file (REQUIRED to save)")
    ap.add_argument("--no-gate", action="store_true", help="non-interactive (tests/batch); still validates loud")
    args = ap.parse_args()

    pdf = args.pdf
    sugg = page_finder.suggest_pages(pdf)
    print("=== suggested pages (1-indexed; confirm or override) ===")
    print(json.dumps(sugg, ensure_ascii=False, indent=2))

    def confirm_pages(kind, suggested):
        override = _parse_pages(getattr(args, f"pages_{kind}"))
        if override:
            return override
        if args.no_gate or not suggested:
            return suggested
        resp = input(f"{kind} pages {suggested} -- Enter to accept, or type comma-separated: ").strip()
        return _parse_pages(resp) or suggested

    color_pages = confirm_pages("color", sugg["color"])
    name_pages = confirm_pages("name", sugg["brand_name"])

    col = extract_mod.extract_brand_colors(pdf, color_pages)
    if col["note"]:
        print(f"  [note] {col['note']}", file=sys.stderr)
    names = extract_mod.read_brand_names(pdf, name_pages)

    # build verify-gate items from the color records (role unset; needs_review carried)
    items = [{"hex": r["value"]["hex"], "rgb": r["value"].get("rgb"),
              "needs_review": r.get("needs_review", False), "role": None,
              "name_cn": "", "name_en": ""} for r in col["records"]]

    if args.no_gate:
        # batch: first (highest-OCR-confidence) color is primary, auto-acknowledged; the rest secondary.
        for i, it in enumerate(items):
            it["role"] = "primary" if i == 0 else "secondary"
            if it.get("needs_review"):
                it["_ack"] = "confirm"
        brand_cn = args.brand
        brand_en = (names["en_candidates"] or [args.brand])[0]
    else:
        print("\n=== VERIFY gate: assign roles + acknowledge flags (confirm/edit/keep-flagged) ===")
        print(f"  brand-name candidates: cn={names['cn_candidates']}  en={names['en_candidates']}")
        brand_cn = input(f"  brand (CN) [{args.brand}]: ").strip() or args.brand
        brand_en = input("  brand_en: ").strip()
        for it in items:
            print(f"  color {it['hex']} (needs_review={it['needs_review']})")
            it["role"] = input("    role [primary/secondary/background]: ").strip() or "secondary"
            if it["needs_review"]:
                it["_ack"] = (input("    acknowledge [confirm/edit/keep-flagged]: ").strip() or "keep-flagged")

    blocked = unacknowledged_flags(items)
    if blocked:
        sys.exit(f"ERROR: {len(blocked)} color flag(s) not acknowledged; cannot save. "
                 "Acknowledge each needs_review (confirm/edit/keep-flagged).")

    logo = args.logo or (input("  logo file path: ").strip() if not args.no_gate else "")
    # place the logo under brands/<brand>/ (the JSON references it there)
    logo_dest = ""
    if logo and Path(logo).is_file():
        brand_dir = _REPO / "brands" / args.brand
        brand_dir.mkdir(parents=True, exist_ok=True)
        logo_dest = str(brand_dir / Path(logo).name)
        if Path(logo).resolve() != Path(logo_dest).resolve():
            shutil.copyfile(logo, logo_dest)

    key = assemble_key.build_lean_key(
        brand_cn, brand_en, finalize_items(items), logo_dest,
        Path(pdf).name, args.verified_by, date.today().isoformat())

    validate_key.validate_lean_key(key)  # FAILS LOUD on missing primary / logo_path

    out = _REPO / "answer_keys" / f"{args.brand}.json"
    out.write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    print(f"Logo placed: {logo_dest or '(none)'}")
    print("Run the back-half:  .venv/bin/python harness/conductor.py --brand "
          f"{args.brand} --thin --no-approve --inputs <single_sign>.json")


if __name__ == "__main__":
    main()
