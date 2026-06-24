#!/usr/bin/env python3
"""harness/review.py — self-service review digest over a run's artifacts (feature 002, US3).

Stdlib-only, READ-ONLY, ASSET-PROFILE-agnostic. Gives the human ONE place to render the eye verdict
(constitution II): the output images, the inputs the pipeline ACTUALLY received, the per-sign
composition picks (icon, layout archetype, reserved text zone), the compliance summary, and every
needs_review flag. It recomputes NOTHING (thin over the core, FR-009) and degrades gracefully
(honest null) on missing artifacts or runs without a kit composition (e.g. a future photo/poster run).

  .venv/bin/python harness/review.py --run output/run_aia_<ts>
"""

import argparse
import json
import sys
from pathlib import Path


def _load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _compliance_summary(sign_dir: Path):
    data = _load(sign_dir / "final.png.compliance.json")
    if not isinstance(data, list):
        return None
    non_lic = [m for m in data if not str(m.get("resolution", "")).startswith("licensed")]
    return {"layers": len(data), "licensed": len(data) - len(non_lic), "non_compliant": len(non_lic)}


def _sign_ids(run_dir: Path, manifest: dict):
    signs = manifest.get("signs")
    if signs:
        return [s.get("sign_id") for s in signs]
    return sorted(p.name[len("sign_"):] for p in run_dir.glob("sign_*") if p.is_dir())


def build_review(run_dir) -> str:
    """Assemble the digest text from the existing run_*/ artifacts. Never raises on a partial run."""
    run_dir = Path(run_dir)
    man = _load(run_dir / "conductor_manifest.json") or {}
    out = [f"RUN: {run_dir}    brand: {man.get('brand', '?')}"]

    sr = man.get("size_resolution") or {}
    if sr:
        out.append(f"format_size: {man.get('format_size')}  ->  resolved: "
                   f"{sr.get('width')}x{sr.get('height')} ({sr.get('orientation')}, "
                   f"aspect {sr.get('aspect_resolved')})"
                   + ("  [needs_review]" if sr.get("needs_review") else ""))
    mand = man.get("mandatory_elements") or []
    forb = man.get("forbidden_elements") or []
    out.append(f"mandatory_elements: {'; '.join(mand) if mand else '(none)'}    "
               f"forbidden_elements: {'; '.join(forb) if forb else '(none)'}")
    if man.get("needs_review_campaign"):
        out.append(f"CAMPAIGN needs_review: {man['needs_review_campaign']}")
    bf = man.get("brief_fields_received")
    if isinstance(bf, dict):
        out.append(f"inputs received: {len(bf.get('signs', []))} sign(s); "
                   f"asset_type={bf.get('asset_type')}")

    out.append("")
    out.append("PER SIGN:")
    for sid in _sign_ids(run_dir, man):
        sd = run_dir / f"sign_{sid}"
        comp = _load(sd / "composition.json")
        final, gen = sd / "final.png", sd / "generated.png"
        img = (f"sign_{sid}/final.png" if final.exists()
               else f"sign_{sid}/generated.png" if gen.exists() else "(no image yet)")
        out.append(f"  {sid}  image: {img}")
        if comp:
            out.append(f"      icon: {comp.get('chosen_icon')}   layout: {comp.get('chosen_archetype')}"
                       f"   text_zone: {comp.get('text_zone')}")
            nr = comp.get("needs_review")
            out.append(f"      needs_review: {nr}"
                       + (f"  -> {comp.get('needs_review_reason')}" if nr else ""))
        else:
            out.append("      (no kit composition for this sign; nothing to recompute - honest null)")
        cs = _compliance_summary(sd)
        if cs:
            out.append(f"      compliance: {cs['layers']} layer(s), {cs['licensed']} licensed, "
                       f"{cs['non_compliant']} non-compliant")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Self-service review digest over a run's artifacts.")
    ap.add_argument("--run", required=True, help="path to an output/run_*/ directory")
    args = ap.parse_args()
    run_dir = Path(args.run)
    if not run_dir.exists():
        sys.exit(f"ERROR: run directory not found: {run_dir}")
    text = build_review(run_dir)
    print(text)
    (run_dir / "review.md").write_text(text + "\n", encoding="utf-8")
    print(f"\n(review digest written to {run_dir / 'review.md'})", file=sys.stderr)


if __name__ == "__main__":
    main()
