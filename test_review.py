#!/usr/bin/env python3
"""test_review.py — falsifiable self-test for the review digest (feature 002, US3).

No paid calls. Builds a SYNTHETIC run dir (manifest + per-sign composition.json + a fixture final.png
+ compliance) and asserts the digest surfaces, per sign, the image + icon + archetype + text_zone +
needs_review, plus the campaign fields the pipeline received; and that a sign with a MISSING image or
a run with NO kit composition is reported as honest-null (no crash, profile-agnostic, D8).

Run:  .venv/bin/python test_review.py
"""

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import review  # noqa: E402


def _make_run(d: Path, with_final=True, with_composition=True):
    man = {
        "brand": "aia",
        "format_size": "60x40cm",
        "size_resolution": {"width": 1536, "height": 1024, "orientation": "landscape",
                            "aspect_resolved": 1.5, "needs_review": False},
        "mandatory_elements": ["分别画叉", "设计两种样式"],
        "forbidden_elements": [],
        "needs_review_campaign": None,
        "brief_fields_received": {"asset_type": "手举牌 hand-held event sign",
                                  "signs": [{"id": "s1"}, {"id": "s2"}]},
        "signs": [{"sign_id": "s1"}, {"sign_id": "s2"}],
    }
    (d / "conductor_manifest.json").write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    # s1: full kit sign (icon + archetype + final + compliance)
    s1 = d / "sign_s1"
    s1.mkdir(parents=True, exist_ok=True)
    if with_composition:
        (s1 / "composition.json").write_text(json.dumps({
            "sign_id": "s1", "chosen_icon": "money_bag", "chosen_archetype": "protect_solid",
            "text_zone": {"x_frac": 0.12, "y_frac": 0.52, "w_frac": 0.76, "h_frac": 0.34},
            "needs_review": False, "needs_review_reason": None}, ensure_ascii=False), encoding="utf-8")
    if with_final:
        (s1 / "final.png").write_bytes(b"\x89PNG\r\n")  # fixture bytes; review only checks existence
        (s1 / "final.png.compliance.json").write_text(json.dumps(
            [{"content": "守住钱袋子", "resolution": "licensed_exact"}], ensure_ascii=False), encoding="utf-8")
    # s2: needs_review sign, no final.png yet (honest null on the image)
    s2 = d / "sign_s2"
    s2.mkdir(parents=True, exist_ok=True)
    (s2 / "composition.json").write_text(json.dumps({
        "sign_id": "s2", "chosen_icon": None, "chosen_archetype": None, "text_zone": None,
        "needs_review": True, "needs_review_reason": "no icon match: ambiguous tie"},
        ensure_ascii=False), encoding="utf-8")
    return man


def check1_per_sign_digest():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _make_run(d)
        text = review.build_review(d)
    needed = ["sign_s1/final.png", "money_bag", "protect_solid", "text_zone",
              "needs_review: True", "no icon match: ambiguous tie", "licensed"]
    missing = [s for s in needed if s not in text]
    return (not missing), (f"all per-sign fields present={not missing}"
                           if not missing else f"MISSING from digest: {missing}")


def check2_campaign_fields_shown():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _make_run(d)
        text = review.build_review(d)
    ok = ("60x40cm" in text and "1536x1024" in text and "分别画叉" in text
          and "2 sign(s)" in text)
    return ok, f"format_size+resolved+mandatory+inputs-count shown={ok}"


def check3_missing_image_honest_null():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _make_run(d, with_final=False)
        text = review.build_review(d)  # must NOT raise
    ok = "(no image yet)" in text
    return ok, f"missing final.png -> '(no image yet)' honest null={ok}"


def check4_non_kit_run_graceful():
    # A run with NO kit composition (e.g. a future photo/poster run) must not crash and must say so.
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        man = {"brand": "taichi", "signs": [{"sign_id": "s1"}]}
        (d / "conductor_manifest.json").write_text(json.dumps(man), encoding="utf-8")
        (d / "sign_s1").mkdir()
        text = review.build_review(d)  # must NOT raise
    ok = "no kit composition" in text
    return ok, f"non-kit sign reported as honest null={ok}"


CHECKS = [
    ("Per-sign digest: image+icon+archetype+text_zone+needs_review", check1_per_sign_digest),
    ("Campaign fields shown (size, mandatory, inputs received)", check2_campaign_fields_shown),
    ("Missing image -> honest null (no crash)", check3_missing_image_honest_null),
    ("Non-kit run -> graceful honest null (profile-agnostic)", check4_non_kit_run_graceful),
]


def main():
    print("=" * 78)
    print("test_review.py — falsifiable self-test (US3, no paid calls)")
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
