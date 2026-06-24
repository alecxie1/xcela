#!/usr/bin/env python3
"""frontend/run_view.py - read a run dir into a progressive stage dict (feature 004, US2/US3).

Stdlib-only, READ-ONLY, PURE. The browser polls this while a run is in flight; each stage is
present-with-content OR absent-with-note (honest null, §V) as its artifact lands, so the dial + the
assembled prompt surface BEFORE the paid image returns. Recomputes nothing - it consumes the
agent-free artifact PATHS the thin route writes (SC-003).
"""

import json
from pathlib import Path


def _load_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _load_text(p):
    try:
        return Path(p).read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return None


def run_view(run_dir, sign_id: str = "s1") -> dict:
    """A run dir -> {run_id, brief, register, prompt, image, manifest_notes}. Each stage is
    {present, content, note}; an absent stage carries the manifest notes as its note (honest null).
    Never raises on a partial / nonexistent run dir."""
    run_dir = Path(run_dir)
    manifest = _load_json(run_dir / "conductor_manifest.json") or {}
    notes = manifest.get("notes") or []
    note_str = "; ".join(str(n) for n in notes) if notes else None
    sign_dir = run_dir / f"sign_{sign_id}"

    def stage(present, content):
        return {"present": bool(present), "content": content if present else None,
                "note": None if present else note_str}

    brief = _load_json(run_dir / "inputs.json")
    register = _load_json(run_dir / "register_profile.json")
    prompt = _load_text(sign_dir / "final_prompt.txt")
    image_present = (sign_dir / "generated.png").exists()

    return {
        "run_id": run_dir.name,
        "brief": stage(brief is not None, brief),
        "register": stage(register is not None, register),
        "prompt": stage(prompt is not None, prompt),
        "image": stage(image_present, f"sign_{sign_id}/generated.png" if image_present else None),
        "manifest_notes": notes,
    }
