#!/usr/bin/env python3
"""test_form_size_progress.py - falsifiable self-test for feature 022 (form size units +
wait expectations). NO paid calls.

The compose and the wait rendering live in browser JS (vanilla-HTML surface), so the
automated half is VALUE-BEARING grep pins (the repo convention for this surface, declared
in the plan): the exact compose expression with the exact default values, the exact
refusal, the WAIT_EXPECT constants. The real composed inputs.json on disk is observed at
the T005 human gate (SC-002's stated proof split).

Run:  .venv/bin/python test_form_size_progress.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent

def _index() -> str:
    return (REPO / "frontend" / "index.html").read_text(encoding="utf-8")


def check1_size_controls():
    """022 US1/FR-001: the three controls exist with TODAY'S defaults (60 / 40 / cm as
    the selected-by-position first option) and offer exactly the cm + px units; the old
    single free-text field is GONE (a build that keeps both would double-report)."""
    ix = _index()
    a = ('id="size_w" type="number" min="0" step="any" value="60"' in ix
         and 'id="size_h" type="number" min="0" step="any" value="40"' in ix)
    b = ('<select id="size_unit"><option value="cm">' in ix
         and '<option value="px">' in ix and ix.count('id="size_unit"') == 1)
    c = 'id="format_size"' not in ix
    ok = a and b and c
    return ok, f"w/h-defaults={a}; unit-select-cm-first+px={b}; old-field-gone={c}"


def check2_compose_pin():
    """022 FR-002 (SC-002's automated half): formState composes format_size from EXACTLY
    the three controls with the exact expression - untouched defaults (60, 40, cm) can
    only compose the pre-022 literal "60x40cm". A build that reorders, pads, or renames
    the parts fails this by value."""
    ix = _index()
    a = ('format_size: $("size_w").value + "x" + $("size_h").value + $("size_unit").value'
         in ix)
    b = 'value="60"' in ix and 'value="40"' in ix and '<option value="cm">' in ix
    ok = a and b
    return ok, f"compose-expression-exact={a}; default-parts-60/40/cm={b}"


def check3_loud_refusal_and_draft_note():
    """022 FR-004 + FR-005: blank/zero/NaN W or H refuses loudly BEFORE any POST (the
    guard sits in startRun ahead of the form build), and the aspect-only draft
    expectation is stated next to the fields (Chinese, the exact wording pinned)."""
    ix = _index()
    guard = 'if (!(sizeW > 0) || !(sizeH > 0)) { $("formNote").textContent = "请填写有效的宽和高（都要大于 0）。"; return; }'
    a = guard in ix and ix.index(guard) < ix.index('fd.append("form"')
    b = "按此比例生成草稿图（约 150 万像素），不是精确像素稿或印刷分辨率文件" in ix
    ok = a and b
    return ok, f"refusal-before-launch={a}; draft-note={b}"


def check4_wait_constants_auditable():
    """022 US2/FR-007: WAIT_EXPECT is ONE constants map covering all three wait kinds,
    and the comment above it NAMES the measured runs + the per-kind method (the A1
    remediation: numbers are auditable, never invented). A build that invents numbers
    without the provenance comment fails."""
    ix = _index()
    a = (ix.count("const WAIT_EXPECT") == 1
         and all(f"{k}:" in ix.split("const WAIT_EXPECT")[1].split("};")[0]
                 for k in ("derive", "generate", "export")))
    prov = ix.split("const WAIT_EXPECT")[0]
    b = ("run_CJXQ_20260708" in prov and "MEASURED" in prov
         and "generated.png mtime" in prov and "layers.zip mtime" in prov)
    ok = a and b
    return ok, f"one-map-three-kinds={a}; provenance-names-runs+method={b}"


def check5_wait_wiring():
    """022 US2/FR-006/FR-008: the waitline element exists; poll() derives the wait kind
    from THIS run's states (export live -> generate confirmed/generating -> derive
    inflight-no-gate) and anything else CLEARS (the null path resets state and empties
    the line); switching runs resets observation (setCurrentRun, the one assignment
    home); resume semantics documented at the state (starts at observation)."""
    ix = _index()
    a = 'id="waitline"' in ix and "function noteWait(kind)" in ix
    b = ('if (exportingLive) waitKind = "export";' in ix
         and 'else if ((gateSt === "confirmed" || gateSt === "generating") && !v.image.present) waitKind = "generate";' in ix
         and 'else if (v.inflight && !v.image.present && !gateSt) waitKind = "derive";' in ix
         and "noteWait(waitKind);" in ix)
    body = ix.split("function noteWait(kind)")[1].split("\n}")[0]
    c = ('waitState = { kind: null, since: null };' in body
         and '$("waitline").textContent = "";' in body)
    d = 'waitState = { kind: null, since: null };   // 022: a switched run restarts observation' in ix
    e = "when THIS client began observing" in ix
    ok = a and b and c and d and e
    return ok, f"element+fn={a}; kind-ladder={b}; clear-path={c}; switch-reset={d}; resume-doc={e}"


def check6_no_progress_bar():
    """022 FR-007 (honest nulls): no progress element and no percentage anywhere in the
    wait rendering; the elapsed counter is seconds-only. A build that adds a bar or a
    fabricated percent fails."""
    ix = _index()
    a = "<progress" not in ix
    body = ix.split("function noteWait(kind)")[1].split("\n}")[0]
    b = "%" not in body and "percent" not in body.lower()
    c = "已等待" in body and "秒" in body
    ok = a and b and c
    return ok, f"no-progress-element={a}; no-percent-in-renderer={b}; seconds-counter={c}"


CHECKS = [
    ("022 US1: W/H/unit controls, defaults, old field gone", check1_size_controls),
    ("022 US1: the compose expression pin (byte-identity by construction)", check2_compose_pin),
    ("022 US1: loud size refusal + the aspect-only draft note", check3_loud_refusal_and_draft_note),
    ("022 US2: WAIT_EXPECT one map, provenance names runs + method", check4_wait_constants_auditable),
    ("022 US2: waitline wiring, kind ladder, clear + switch-reset", check5_wait_wiring),
    ("022 US2: no progress bar or percent, seconds-only counter", check6_no_progress_bar),
]


def main():
    print("=" * 78)
    print("test_form_size_progress.py - falsifiable self-test (022, no paid calls)")
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
