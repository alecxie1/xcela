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


def _pid_alive(pid):
    """Read-only liveness probe (signal 0). Stdlib-local on purpose: run_view stays
    import-light and PURE (no harness import just to share three lines)."""
    import os
    try:
        os.kill(int(pid), 0)
    except (OSError, TypeError, ValueError):
        return False
    return True


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
    error = _load_text(run_dir / "run_error.txt")  # written by the server if the conductor fails loud

    # Feature 015: the pre-spend gate stage. present=false is the honest null for pre-015
    # run dirs (they render exactly as before) and for a derive phase still in flight.
    gate_state = _load_json(run_dir / "gate_state.json")
    assumptions = _load_json(run_dir / "assumptions.json")
    if gate_state is None:
        gate = {"present": False, "content": None,
                "note": "no pre-spend gate (a pre-015 run dir, or the derive phase has not "
                        "written its state yet)"}
    else:
        gate = {"present": True, "note": None, "content": {
            "state": gate_state.get("state"),
            "assumptions": assumptions if isinstance(assumptions, list) else [],
            "answers_applied": gate_state.get("answers_applied") or [],
            "state_note": gate_state.get("note"),
        }}

    # Feature 016: the layered-export stage. present=false is the honest null for every
    # unexported run (pre-016 dirs included): export is opt-in and paid, never assumed.
    export_state = _load_json(run_dir / "export_state.json")
    export_manifest = _load_json(run_dir / "export_manifest.json")
    export_error = _load_text(run_dir / "export_error.txt")  # the export worker's own marker,
    # deliberately distinct from run_error.txt (which means the RUN failed, not the export)
    if export_state is None:
        export = {"present": False, "content": None,
                  "note": "not exported; export is opt-in and paid"}
    else:
        state = export_state.get("state")
        # An "exporting" nobody owns (reservation never adopted, or the worker pid is dead
        # after a hard kill) is STALE: surface it so the UI can offer the retry the state
        # machine accepts, instead of rendering a forever-spinner (honest null, §V).
        stale = (state == "exporting"
                 and not (export_state.get("started_at")
                          and _pid_alive(export_state.get("pid"))))
        export = {"present": True, "note": None, "content": {
            "state": state,
            "stale": stale,
            "cost_stated": export_state.get("cost_stated"),
            "calls": (export_state.get("plan") or {}).get("calls"),
            "error": export_state.get("error") or (export_error.strip() if export_error else None),
            "layers": (export_manifest or {}).get("layers") or [],
            "zip_ready": (run_dir / "layers.zip").is_file(),
        }}

    return {
        "run_id": run_dir.name,
        "brief": stage(brief is not None, brief),
        "register": stage(register is not None, register),
        "prompt": stage(prompt is not None, prompt),
        "image": stage(image_present, f"sign_{sign_id}/generated.png" if image_present else None),
        "gate": gate,
        "export": export,
        "manifest_notes": notes,
        "error": error.strip() if error else None,
    }
