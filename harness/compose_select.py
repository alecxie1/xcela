#!/usr/bin/env python3
"""harness/compose_select.py — deterministic per-message composition selection.

Feature 001-kit-of-parts-composition, the heart of US1. Stdlib-only (so the stdlib-only
conductor imports it directly): given a message and a validated kit, DETERMINISTICALLY

  1. match the message MEANING to one icon-vocabulary entry (cue substring count), and
  2. select a layout archetype for the icon's mode, avoiding collisions across the campaign.

No LLM, no generative guess (D2). Honest-null + needs_review when no confident match exists
(constitution §V). The match rule is pinned so a wrong build fails the test (A1):

  icon_match_score(entry) = number of distinct meaning_cues that are substrings of the
  joined message text. Eligible iff score >= 1. The winner is the SINGLE highest-scoring
  eligible entry. Honest-null when the top score is 0 (no cue) OR two+ entries tie for top.

Output is a composition dict per contracts/composition-schema.md.

CLI:
  .venv/bin/python harness/compose_select.py --brand aia \
      --message "守住钱袋子;护好幸福家" --campaign-used resist_panel --out <dir>/composition.json
  add --explain to print the composition JSON and exit.
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
import kit as kitlib  # noqa: E402  (stdlib-only)


def _joined(message_lines) -> str:
    return "".join(message_lines or [])


def select_icon(kit: dict, message_lines) -> dict:
    """Deterministic meaning->icon match. Returns {chosen_icon, detected_mode,
    icon_match_score, needs_review, needs_review_reason}."""
    text = _joined(message_lines)
    scored = []
    for e in kit.get("icon_vocabulary", []):
        score = sum(1 for cue in set(e.get("meaning_cues", [])) if cue and cue in text)
        if score >= 1:
            scored.append((score, e))
    if not scored:
        return {"chosen_icon": None, "detected_mode": None, "icon_match_score": 0,
                "needs_review": True,
                "needs_review_reason": "no icon match: message meaning matched no kit icon (top score 0)"}
    top = max(s for s, _ in scored)
    winners = [e for s, e in scored if s == top]
    if len(winners) > 1:
        ids = ", ".join(e["id"] for e in winners)
        return {"chosen_icon": None, "detected_mode": None, "icon_match_score": top,
                "needs_review": True,
                "needs_review_reason": f"no icon match: ambiguous tie at score {top} between {ids}"}
    win = winners[0]
    return {"chosen_icon": win["id"], "detected_mode": win.get("mode"), "icon_match_score": top,
            "needs_review": False, "needs_review_reason": None}


def select_archetype(kit: dict, mode, campaign_used) -> dict:
    """Collision-avoiding layout selection. Picks the first archetype (vocabulary order)
    serving `mode` that is NOT in campaign_used; reuses the first serving one only when the
    vocabulary is exhausted (archetype_reused=True). Returns {chosen_archetype, text_zone,
    archetype_reused}. mode=None -> no archetype."""
    used = set(campaign_used or [])
    if not mode:
        return {"chosen_archetype": None, "text_zone": None, "archetype_reused": False}
    candidates = [a for a in kit.get("layout_vocabulary", []) if mode in (a.get("modes") or [])]
    if not candidates:
        return {"chosen_archetype": None, "text_zone": None, "archetype_reused": False}
    unused = [a for a in candidates if a["id"] not in used]
    if unused:
        a = unused[0]
        return {"chosen_archetype": a["id"], "text_zone": a.get("text_zone"), "archetype_reused": False}
    a = candidates[0]  # exhausted -> reuse, and flag it
    return {"chosen_archetype": a["id"], "text_zone": a.get("text_zone"), "archetype_reused": True}


def compose_message(kit: dict, sign_id: str, message_lines, campaign_used) -> dict:
    """Full per-sign composition: icon + archetype + reserved text_zone + needs_review.
    fitted_type is filled later by the fit-to-zone clamp (US2/US3); null here."""
    icon = select_icon(kit, message_lines)
    arch = select_archetype(kit, icon["detected_mode"], campaign_used)

    reasons = []
    if icon["needs_review"] and icon["needs_review_reason"]:
        reasons.append(icon["needs_review_reason"])
    if arch["archetype_reused"]:
        reasons.append(f"layout archetype reused (vocabulary exhausted): {arch['chosen_archetype']}")
    needs_review = bool(reasons)

    return {
        "sign_id": sign_id,
        "message": list(message_lines or []),
        "detected_mode": icon["detected_mode"],
        "chosen_icon": icon["chosen_icon"],
        "icon_match_score": icon["icon_match_score"],
        "chosen_archetype": arch["chosen_archetype"],
        "archetype_reused": arch["archetype_reused"],
        "text_zone": arch["text_zone"],
        "fitted_type": None,
        "needs_review": needs_review,
        "needs_review_reason": ("; ".join(reasons) if reasons else None),
    }


def compose_campaign(kit: dict, signs: list) -> list:
    """Compose a whole campaign, threading campaign_used so distinct-mode signs get distinct
    archetypes (collision avoidance). signs: [{id, messages}, ...]."""
    used = []
    out = []
    for sign in signs:
        comp = compose_message(kit, sign.get("id"), sign.get("messages", []), used)
        if comp["chosen_archetype"]:
            used.append(comp["chosen_archetype"])
        out.append(comp)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic per-message composition selection.")
    ap.add_argument("--brand", required=True)
    ap.add_argument("--kit", default="", help="kit path (default kits/<brand>.json)")
    ap.add_argument("--sign-id", default="s1")
    ap.add_argument("--message", required=True, help="semicolon-separated message lines")
    ap.add_argument("--campaign-used", default="", help="comma-separated archetype ids already used")
    ap.add_argument("--out", default="")
    ap.add_argument("--explain", action="store_true", help="print the composition JSON and exit")
    args = ap.parse_args()

    kit = kitlib.load_kit(args.brand) if not args.kit else kitlib.validate_kit(
        json.loads(Path(args.kit).read_text(encoding="utf-8")), args.brand)
    lines = [s.strip() for s in args.message.replace("；", ";").split(";") if s.strip()]
    used = [s.strip() for s in args.campaign_used.split(",") if s.strip()]

    comp = compose_message(kit, args.sign_id, lines, used)
    print(json.dumps(comp, ensure_ascii=False, indent=2))
    if args.explain:
        return
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(comp, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
