#!/usr/bin/env python3
"""test_register_render_aware.py - falsifiable self-test for feature 011 (render-aware register).

No paid calls: pure-function imports only (derive_register + conductor builders), no subprocess.
Asserts VALUES a wrong build cannot satisfy (constitution III). SC-007 (does the paid output READ
as a playful marketing poster) is the deferred human eye-gate, NOT here. Contract rows refer to
specs/011-register-render-aware/contracts/derive_register_contract.md.

Run:  .venv/bin/python test_register_render_aware.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO / "register"))
import conductor  # noqa: E402
import derive_register as dr  # noqa: E402


def _inputs(render_style=None):
    """Thin-route brief inputs (shape mirrors test_render_modes._inputs)."""
    d = {"asset_type": "poster", "format_size": "60x40cm",
         "mandatory_elements": [], "forbidden_elements": [],
         "context": {"usage_context": "wall-posted (read at distance)",
                     "vibe": {"formality": 2, "playfulness": 8},
                     "logo_treatment": "omit", "brand_strictness": "brand + accents",
                     "occasion": "x"},
         "signs": [{"id": "s1", "messages": ["新品上市"], "hero_icon": None}]}
    if render_style is not None:
        d["render_style"] = render_style
    return d


def check1_thin_subfields_plumbing():
    """T002/FR-001: thin subfields carry render_style VERBATIM; kit/legacy byte-identical."""
    inputs = _inputs("photographic")
    thin_sf = conductor.build_subfields(inputs, thin=True)
    raw_ok = thin_sf.get("render_style") == "photographic"  # raw term, NOT "photo"
    # thin route without the key in the brief: no invented key (honest pass-through)
    thin_absent = conductor.build_subfields(_inputs(), thin=True)
    absent_ok = "render_style" not in thin_absent
    # kit/legacy (thin=False, and the no-arg default) never see the key even when the
    # brief carries it, and the dict equals the pre-feature shape exactly
    legacy_default = conductor.build_subfields(inputs)
    legacy_explicit = conductor.build_subfields(inputs, thin=False)
    prefeature_shape = {"asset_type": inputs["asset_type"], **inputs["context"]}
    legacy_ok = legacy_default == prefeature_shape == legacy_explicit
    passed = raw_ok and absent_ok and legacy_ok
    return passed, (f"thin_raw_verbatim={raw_ok}; thin_no_key_when_absent={absent_ok}; "
                    f"kit_legacy_byte_identical={legacy_ok}")


def check2_normalizer_drift_guard():
    """T003 contract drift guard: the engine's local predicate and the conductor's
    normalize_render_style must agree on the shared input table (research D2)."""
    table = ["photographic", "photo", " PHOTOGRAPHIC ", "flat vector", "", None, "watercolor"]
    disagreements = [v for v in table
                     if dr._render_is_photo(v) != (conductor.normalize_render_style(v) == "photo")]
    # value-level spot checks so a both-wrong drift cannot pass silently
    values_ok = (dr._render_is_photo(" PHOTOGRAPHIC ") is True
                 and dr._render_is_photo("watercolor") is False
                 and dr._render_is_photo(None) is False)
    passed = not disagreements and values_ok
    return passed, f"disagreements={disagreements}; value_spot_checks={values_ok}"


CHECKS = [
    ("US-all plumbing: thin subfields carry raw render_style, kit/legacy untouched",
     check1_thin_subfields_plumbing),
    ("US-all drift guard: engine predicate agrees with conductor normalize_render_style",
     check2_normalizer_drift_guard),
]


def main():
    print("=" * 78)
    print("test_register_render_aware.py - falsifiable self-test (011, no paid calls)")
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
