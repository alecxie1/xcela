#!/usr/bin/env python3
"""test_per_sign_elements.py — falsifiable self-test for per-sign mandatory/forbidden elements (002 delta).

No paid calls. Asserts VALUES the campaign-only build cannot satisfy (constitution §III):
- TARGETING: campaign mandatory [] + only s5/s6 carrying 分别画叉 -> 分别画叉 on s5/s6 ONLY, not s1-s4.
  (The current build stamps the campaign list on EVERY sign, so it would put it on all or none.)
- UNION + DEDUP: campaign ["A"] ++ a sign ["A","B"] -> effective ["A","B"] (order kept, "A" not
  duplicated); a sign with no per-sign field -> ["A"].
- VERBATIM: 分别画叉 survives byte-for-byte (equality, not `in`).
- PER-SIGN CONFLICT: a sign whose effective mandatory ∩ forbidden is non-empty -> needs_review set
  with a reason naming the item; a clean sign is NOT flagged by this rule.
- BACK-COMPAT: inputs with NO per-sign fields produce the SAME result as today.
- VALIDATION: a per-sign field that is not a list of strings raises SystemExit.
- ON-DISK (DoD): a dry-run writes 分别画叉 into s5/s6 composition.json ONLY.

Run:  .venv/bin/python test_per_sign_elements.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import conductor  # noqa: E402


# Six signs with confident icon matches (so needs_review is driven by elements, not icon misses).
_MESSAGES = {
    "s1": ["守住钱袋子"], "s2": ["护好幸福家"], "s3": ["存款安全"],
    "s4": ["家庭平安"], "s5": ["警惕诈骗"], "s6": ["远离非法金融"],
}


def _inputs(campaign_mandatory=None, campaign_forbidden=None, per_sign=None):
    """per_sign: {sign_id: {"mandatory_elements": [...], "forbidden_elements": [...]}}."""
    per_sign = per_sign or {}
    signs = []
    for sid, msgs in _MESSAGES.items():
        sign = {"id": sid, "messages": list(msgs), "hero_icon": None}
        sign.update(per_sign.get(sid, {}))
        signs.append(sign)
    return {
        "asset_type": "手举牌 hand-held event sign",
        "mandatory_elements": campaign_mandatory or [],
        "forbidden_elements": campaign_forbidden or [],
        "context": {"usage_context": "held for photos / posed with",
                    "vibe": {"formality": 2, "playfulness": 8, "warmth": 7},
                    "logo_treatment": "omit", "brand_strictness": "expressive departure",
                    "occasion": "anti-fraud"},
        "signs": signs,
    }


def _compose(inputs_obj):
    """validate + build_compositions, mirroring the real conductor flow. Returns {sign_id: comp}."""
    conductor.validate_inputs(inputs_obj)
    comps = conductor.build_compositions(inputs_obj, "aia")
    return {c["sign_id"]: c for c in comps}


def check1_targeting():
    by_id = _compose(_inputs(per_sign={"s5": {"mandatory_elements": ["分别画叉"]},
                                       "s6": {"mandatory_elements": ["分别画叉"]}}))
    on56 = ("分别画叉" in by_id["s5"]["mandatory_elements"]
            and "分别画叉" in by_id["s6"]["mandatory_elements"])
    off1234 = all("分别画叉" not in by_id[s]["mandatory_elements"] for s in ("s1", "s2", "s3", "s4"))
    return (on56 and off1234), (f"s5={by_id['s5']['mandatory_elements']} s6={by_id['s6']['mandatory_elements']}; "
                                f"s1-s4 carry it={not off1234}")


def check2_union_dedup():
    by_id = _compose(_inputs(campaign_mandatory=["A"],
                             per_sign={"s1": {"mandatory_elements": ["A", "B"]}}))
    union_ok = by_id["s1"]["mandatory_elements"] == ["A", "B"]   # order kept, "A" not duplicated
    plain_ok = by_id["s2"]["mandatory_elements"] == ["A"]        # no per-sign field -> campaign only
    return (union_ok and plain_ok), (f"s1(eff)={by_id['s1']['mandatory_elements']} "
                                     f"s2(eff)={by_id['s2']['mandatory_elements']}")


def check3_verbatim():
    by_id = _compose(_inputs(per_sign={"s5": {"mandatory_elements": ["分别画叉"]}}))
    elems = by_id["s5"]["mandatory_elements"]
    exact = len(elems) == 1 and elems[0] == "分别画叉"   # equality, not substring
    return exact, f"s5 mandatory elements (exact)={elems!r}"


def check4_per_sign_conflict():
    by_id = _compose(_inputs(
        per_sign={"s5": {"mandatory_elements": ["分别画叉"], "forbidden_elements": ["分别画叉"]}}))
    s5, s1 = by_id["s5"], by_id["s1"]
    phrase = "both contain"
    flagged = bool(s5["needs_review"]) and bool(s5.get("needs_review_reason")) \
        and "分别画叉" in s5["needs_review_reason"] and phrase in s5["needs_review_reason"]
    clean = phrase not in (s1.get("needs_review_reason") or "")
    return (flagged and clean), (f"s5 needs_review={s5['needs_review']} reason={s5.get('needs_review_reason')!r}; "
                                 f"s1 conflict-flagged={not clean}")


def check5_back_compat():
    # No per-sign fields anywhere: every comp carries exactly the campaign list (today's behavior).
    by_id = _compose(_inputs(campaign_mandatory=["设计两种样式"]))
    same = all(by_id[s]["mandatory_elements"] == ["设计两种样式"] for s in _MESSAGES)
    no_forbidden = all(by_id[s]["forbidden_elements"] == [] for s in _MESSAGES)
    return (same and no_forbidden), f"every sign mandatory==['设计两种样式']={same}; forbidden all []={no_forbidden}"


def check6_validation_rejects_non_list():
    bad = _inputs()
    bad["signs"][0]["mandatory_elements"] = "分别画叉"   # bare string, not a list -> must raise
    try:
        conductor.validate_inputs(bad)
    except SystemExit as exc:
        return ("must be a list of strings" in str(exc)), f"raised SystemExit: {exc}"
    return False, "validate_inputs did NOT reject a per-sign mandatory_elements string"


def check7_on_disk_dry_run():
    """DoD: a dry-run writes 分别画叉 into s5/s6 composition.json ONLY (per-sign targeting on disk)."""
    inputs_obj = _inputs(per_sign={"s5": {"mandatory_elements": ["分别画叉"]},
                                   "s6": {"mandatory_elements": ["分别画叉"]}})
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "in.json").write_text(json.dumps(inputs_obj, ensure_ascii=False), encoding="utf-8")
        out = d / "out"
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "harness" / "conductor.py"), "--dry-run",
             "--inputs", str(d / "in.json"), "--brand", "aia", "--out", str(out), "--no-approve"],
            cwd=str(REPO_ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            return False, f"dry-run failed (rc={proc.returncode}): {proc.stderr[-300:]}"
        got = {}
        for sid in _MESSAGES:
            comp = json.loads((out / f"sign_{sid}" / "composition.json").read_text(encoding="utf-8"))
            got[sid] = "分别画叉" in comp.get("mandatory_elements", [])
    carriers = sorted(s for s, v in got.items() if v)
    return (carriers == ["s5", "s6"]), f"composition.json carries 分别画叉 on: {carriers}"


CHECKS = [
    ("Per-sign TARGETING: 分别画叉 on s5/s6 only, not s1-s4", check1_targeting),
    ("UNION + DEDUP: campaign ['A'] ++ ['A','B'] -> ['A','B']", check2_union_dedup),
    ("VERBATIM: 分别画叉 survives byte-for-byte (equality)", check3_verbatim),
    ("PER-SIGN CONFLICT -> needs_review naming the item (§V)", check4_per_sign_conflict),
    ("BACK-COMPAT: no per-sign fields == today's behavior", check5_back_compat),
    ("VALIDATION: non-list per-sign field raises SystemExit", check6_validation_rejects_non_list),
    ("ON-DISK (DoD): dry-run writes 分别画叉 to s5/s6 only", check7_on_disk_dry_run),
]


def main():
    print("=" * 78)
    print("test_per_sign_elements.py — falsifiable self-test (002 delta, no paid calls)")
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
