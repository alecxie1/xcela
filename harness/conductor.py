#!/usr/bin/env python3
"""harness/conductor.py — the brand-general human-gate conductor.

Wraps the PROVEN single-sign engine (scene_author.py) with the prep chain and the
human gates that a non-designer needs. It does NOT generate images itself: every
heavy step is delegated to an existing, individually-proven script run as ONE
synchronous foreground subprocess. That keeps this module stdlib-only and trivially
testable (no numpy / anthropic / openai import, no API keys needed to import it).

Flow (see CONDUCTOR_SPEC.md + CONDUCTOR_INPUTS_RECONCILIATION.md):
  1. INPUT GATE     ask the guided subfields (brief_schema_v3 buckets B/D) or load --inputs
  2. LOAD BRAND     verify answer_keys/<brand>.json exists (fail loudly otherwise)
  3. SUBFIELDS      write subfields.json = { asset_type, **context }  (identity pass-through)
  4. REGISTER PREP  [calibrate_from_reference if a reference] -> derive_register (--calibration
                    wired in so the reference still sets MAGNITUDE) -> register_profile.json
  5. PER-SIGN LOOP  [analyzer -> aligned_prompt.txt, recorded NOT injected] -> scene_author
                    (--asset-profile flat_graphic --chroma-contain --register-profile ...)
  6. APPROVE GATE   stop, show the drafts, take a plain-language nudge, re-run the touched sign
  7. MANIFEST       conductor_manifest.json: the provenance record

The human stays in the loop at gates 1 and 6 BY DESIGN. This tool is agent-free, not
human-free. It never reads a messy brief with an LLM and never decides taste.

v1 scope: output is ALWAYS flat_graphic (die-cut signs). asset_type is intent-framing
only; it does not unlock other rendering modes yet (recorded in the manifest).

Usage:
  .venv/bin/python harness/conductor.py --brand <brand_id>
  .venv/bin/python harness/conductor.py --brand <brand_id> --inputs inputs.json
  .venv/bin/python harness/conductor.py --brand <brand_id> --inputs inputs.json --dry-run
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable  # the (venv) python running this conductor; used for every subprocess

# Proven scripts the conductor sequences (repo-relative; run with cwd=REPO_ROOT).
SCENE_AUTHOR = "harness/scene_author.py"
DERIVE_REGISTER = "register/derive_register.py"
CALIBRATE = "register/calibrate_from_reference.py"
ANALYZER = "register/reference_style_to_prompt.py"

# v1: the only rendering dialect the conductor drives.
ASSET_PROFILE = "flat_graphic"
ASSET_TYPE_DEFAULT = "手举牌 hand-held event sign"

# Per-phase subprocess timeouts (seconds). Each step sets its OWN internal API timeout
# too; these are the outer ceilings so one wedged step cannot hang the run forever.
TIMEOUTS = {"calibrate": 240, "derive_register": 60, "analyzer": 240, "scene_author": 900}
MAX_NUDGES = 5
APPROVALS = {"y", "yes", "yep", "ok", "okay", "approve", "approved", "good", "looks good", "lgtm"}

# Smart defaults for the adaptive question form (brief_schema_v3). Brand-SAFE: logo
# required and brand+accents, so a fast user accepts all; the human flips logo->omit
# and strictness->expressive for a playful event prop (that flip is a taste call).
WARMTH_DEFAULT = 5
DEFAULT_AUDIENCE = "general public"
DEFAULT_SETTING = "event / festival"

# Reference-relationship DIAL (Axis B). The human's reference_relationship (free text,
# or one of the long brief_schema_v3 labels) maps to the clean enum the analyzer takes.
# A no-reference job has no dial (None).
DIAL_VALUES = ("extend", "match_style", "mood")
DEFAULT_DIAL = "extend"


def normalize_dial(value):
    """Map a free-text reference_relationship to {extend, match_style, mood}, or None
    when none is given (no-ref jobs have no dial). 'template...'->extend,
    'style...'->match_style, 'inspiration...'->mood; already-clean values pass through;
    anything unrecognized defaults to extend (max similarity, the proven gold)."""
    if not value:
        return None
    v = str(value).strip().lower()
    if v in DIAL_VALUES:
        return v
    if v.startswith("template") or "extend" in v or "series" in v:
        return "extend"
    if v.startswith("style") or "match" in v:
        return "match_style"
    if v.startswith("inspiration") or "mood" in v or "loose" in v:
        return "mood"
    return DEFAULT_DIAL


# --------------------------------------------------------------------------- #
# Pure builders (no I/O, no network): the testable core. dry-run and real mode
# both construct commands from these, so the plan and the execution never drift.
# --------------------------------------------------------------------------- #

def _usage_from_asset(asset_type: str) -> str:
    """brief_schema_v3: asset_type carries a default use-context. A hand-held sign
    is held for photos (=> event_prop downstream). Anything else falls back to the
    wall-posted reading default; the human can override the usage_context directly."""
    a = (asset_type or "").lower()
    if "手举牌" in (asset_type or "") or "hand-held" in a or "sign" in a:
        return "held for photos / posed with"
    return "wall-posted (read at distance)"


def feeling_phrase(context: dict) -> str:
    """A coarse FRAMING phrase for the per-sign intent's 'feeling' field. This is
    framing only: the authoritative register reaches scene_author via the
    register_profile (--register-profile), NOT via this string. Kept independent of
    derive_register's output so it is identical in dry-run and real mode."""
    uc = str(context.get("usage_context") or "").lower()
    formality = (context.get("vibe") or {}).get("formality")
    if any(k in uc for k in ("held for photos", "posed", "worn")):
        return "playful, energetic, grabbable photo-prop, approachable, NOT corporate"
    if isinstance(formality, int) and formality >= 7:
        return "polished, official, restrained, on-brand"
    return "polished, approachable, on-brand"


def build_subfields(inputs: dict) -> dict:
    """The reconciliation crux: inputs.context uses brief_schema_v3 field names
    verbatim, so the subfields derive_register consumes are an identity pass-through
    of context (plus asset_type). No inference, no judgment glue."""
    context = dict(inputs.get("context") or {})
    return {"asset_type": inputs.get("asset_type", ASSET_TYPE_DEFAULT), **context}


def build_intent(inputs: dict, sign: dict, brand: str) -> dict:
    """Deterministic per-sign Tier-2 intent dict for scene_author --intent-file.
    Templated from context + the sign; nothing is inferred by a model here."""
    context = inputs.get("context") or {}
    occasion = (context.get("occasion") or "").strip()
    messages = sign.get("messages", [])
    ref = inputs.get("reference_image")
    headline = "，".join(messages)
    return {
        "subject": f"{occasion} {inputs.get('asset_type', ASSET_TYPE_DEFAULT)} for brand '{brand}'".strip(),
        "asset_type": inputs.get("asset_type", ASSET_TYPE_DEFAULT),
        "occasion": occasion,
        "headline_message": f"{headline} (exact headline)" if headline else "",
        "feeling": feeling_phrase(context),
        "reference_image": Path(ref).name if ref else "logo only",
    }


def _calibrate_argv(ref: str, brand: str, out: str) -> list:
    return [CALIBRATE, "--image", ref, "--brand", brand, "--out", out]


def _derive_argv(brand: str, out: str, subfields_path: str, calibration_path) -> list:
    argv = [DERIVE_REGISTER, "--subfields", subfields_path, "--brand", brand, "--out", out]
    if calibration_path:
        argv += ["--calibration", calibration_path]
    return argv


def _analyzer_argv(ref: str, messages: list, hero_icon, sign_dir: str,
                   relationship: str = DEFAULT_DIAL) -> list:
    argv = [ANALYZER, "--image", ref]
    for m in messages:
        argv += ["--message", m]
    if hero_icon:
        argv += ["--hero-icon", hero_icon]
    argv += ["--relationship", relationship, "--out", sign_dir]
    return argv


def _scene_author_argv(brand: str, out: str, sign_id: str, messages: list,
                       ref, register_profile, aligned_prompt=None) -> list:
    """Reference job (aligned_prompt set): pass --aligned-prompt, DROP --chroma-contain
    (chroma is disabled for ref jobs) and --intent-file (tier-3 is skipped). No-ref job:
    keep --chroma-contain + --intent-file. --register-profile is kept on BOTH (place_measured
    reads the licensed font weight_hint from it)."""
    is_ref = bool(aligned_prompt)
    argv = [SCENE_AUTHOR, "--brand", brand, "--asset-profile", ASSET_PROFILE]
    if not is_ref:
        argv += ["--chroma-contain"]
    if register_profile:
        argv += ["--register-profile", register_profile]
    argv += ["--must-include", ";".join(messages), "--out", f"{out}/sign_{sign_id}"]
    if is_ref:
        argv += ["--aligned-prompt", aligned_prompt]
    else:
        argv += ["--intent-file", f"{out}/intent_{sign_id}.json"]
    if ref:
        argv += ["--ref-image", ref]
    return argv


def _cmd(phase: str, label: str, script_argv: list, sign_id=None, optional=False) -> dict:
    return {"phase": phase, "kind": "command", "label": label, "sign_id": sign_id,
            "optional": optional, "argv": [PY] + script_argv}


def build_plan(inputs: dict, brand: str, out_dir, no_approve: bool = False) -> dict:
    """Pure: inputs + brand -> the fully-parameterized HAPPY-PATH plan. dry-run
    writes this to plan.json (the falsifiable test surface); real mode executes it
    with documented honest-null fallbacks when a step fails."""
    out = str(out_dir)
    ref = inputs.get("reference_image")
    has_ref = bool(ref)
    dial = normalize_dial(inputs.get("reference_relationship")) if has_ref else None
    subfields_path = f"{out}/subfields.json"
    profile_path = f"{out}/register_profile.json"
    calibration_path = f"{out}/calibration.json"

    steps = []
    # 4. register prep (campaign-level: one profile shared by all signs)
    if has_ref:
        steps.append(_cmd("register", "calibrate", _calibrate_argv(ref, brand, out)))
        steps.append(_cmd("register", "derive_register",
                          _derive_argv(brand, out, subfields_path, calibration_path)))
    else:
        steps.append(_cmd("register", "derive_register",
                          _derive_argv(brand, out, subfields_path, None)))

    # 5. per-sign loop. Reference job: analyzer (dial-selected wording) -> aligned_prompt.txt,
    # which is INJECTED as scene_author's --aligned-prompt (no longer discarded).
    for sign in inputs["signs"]:
        sid = sign["id"]
        sign_dir = f"{out}/sign_{sid}"
        messages = sign.get("messages", [])
        aligned_prompt = None
        if has_ref:
            steps.append(_cmd(f"sign:{sid}", "analyzer",
                              _analyzer_argv(ref, messages, sign.get("hero_icon"), sign_dir,
                                             relationship=dial or DEFAULT_DIAL),
                              sign_id=sid, optional=True))
            aligned_prompt = f"{sign_dir}/aligned_prompt.txt"
        steps.append(_cmd(f"sign:{sid}", "scene_author",
                          _scene_author_argv(brand, out, sid, messages, ref if has_ref else None,
                                             profile_path, aligned_prompt=aligned_prompt),
                          sign_id=sid))

    # 6. approve gate (a gate step, not a command — present unless --no-approve)
    if not no_approve:
        steps.append({"phase": "approve", "kind": "gate", "label": "approve", "enabled": True})

    return {
        "brand": brand,
        "brand_paths": {"answer_key": f"answer_keys/{brand}.json",
                        "config": f"config/{brand}.yaml"},
        "out": out,
        "asset_type": inputs.get("asset_type", ASSET_TYPE_DEFAULT),
        "asset_profile_v1": ASSET_PROFILE,
        "asset_type_note": "v1: asset_type is intent-framing only; output is ALWAYS flat_graphic",
        "has_reference": has_ref,
        "reference_relationship_raw": inputs.get("reference_relationship"),
        "dial": dial,
        "subfields": subfields_path,
        "register_profile": profile_path,
        "sign_count": len(inputs["signs"]),
        "steps": steps,
    }


# --------------------------------------------------------------------------- #
# Input gate
# --------------------------------------------------------------------------- #

def _to_int(value, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def ask_questions(ask=input) -> dict:
    """The human input gate: a short, adaptive, accept-all guided-subfields form
    (brief_schema_v3 buckets B/D). `ask` is injectable so the form is testable
    without stdin. Returns the full inputs dict (brand comes from the CLI arg)."""
    def q(prompt, default):
        resp = (ask(f"{prompt} [{default}]: ") or "").strip()
        return resp or default

    print("=== Guided questions (press Enter to accept the default) ===")
    asset_type = q("Asset type", ASSET_TYPE_DEFAULT)
    reference = (ask("Reference image path (Enter to skip): ") or "").strip()
    # The reference-relationship dial is asked ONLY when a reference is supplied (a no-ref
    # job has no dial). 3 choices; defaults to extend (max similarity, the proven gold).
    reference_relationship = None
    if reference:
        reference_relationship = normalize_dial(
            q("Reference relationship? extend (clone look, change message) | match_style "
              "(same style, fresh layout) | mood (tone cue only)", DEFAULT_DIAL))
    formality = _to_int(q("How formal? 0 casual to 10 official", 5), 5)
    playfulness = _to_int(q("How playful? 0 serious to 10 fun", 5), 5)
    logo_treatment = q("Logo? required/prominent | subtle | omit", "required/prominent")
    brand_strictness = q("On-brand tightness? strict VI | brand + accents | expressive departure",
                         "brand + accents")
    occasion = (ask("Occasion / campaign (short, optional): ") or "").strip()

    context = {
        # bucket B (usage_context drives the register; audience/setting are inert provenance)
        "usage_context": _usage_from_asset(asset_type),
        "audience": DEFAULT_AUDIENCE,
        "setting": DEFAULT_SETTING,
        # bucket D (formality/playfulness/logo_treatment/brand_strictness drive the register;
        # warmth is inert provenance — derive_register does not read it today)
        "vibe": {"formality": formality, "playfulness": playfulness, "warmth": WARMTH_DEFAULT},
        "logo_treatment": logo_treatment,
        "brand_strictness": brand_strictness,
        "occasion": occasion,
    }
    signs = _ask_signs(ask)
    return {
        "asset_type": asset_type,
        "reference_image": reference or None,
        "reference_relationship": reference_relationship,  # dial (Axis B); None for no-ref jobs
        "context": context,
        "signs": signs,
    }


def _ask_signs(ask) -> list:
    """Collect the per-sign content (the messages the human actually wants printed)."""
    print("--- Per-sign content (the text on each sign) ---")
    signs = []
    i = 1
    while True:
        raw = (ask(f"Sign {i} message line(s), separate lines with '；' (Enter to finish): ") or "").strip()
        if not raw:
            break
        lines = [s.strip() for s in re.split(r"[；;]", raw) if s.strip()]
        hero = (ask(f"Sign {i} hero icon (optional): ") or "").strip() or None
        signs.append({"id": f"s{i}", "messages": lines, "hero_icon": hero})
        i += 1
    return signs


def validate_inputs(inputs: dict) -> dict:
    if not isinstance(inputs, dict):
        raise SystemExit("ERROR: inputs must be a JSON object.")
    if not isinstance(inputs.get("context"), dict):
        raise SystemExit("ERROR: inputs.context is required (brief_schema_v3 bucket B/D fields).")
    signs = inputs.get("signs")
    if not isinstance(signs, list) or not signs:
        raise SystemExit("ERROR: inputs.signs must be a non-empty list.")
    seen = set()
    for idx, sign in enumerate(signs):
        if not isinstance(sign, dict):
            raise SystemExit(f"ERROR: signs[{idx}] must be an object.")
        sign.setdefault("id", f"s{idx + 1}")
        if sign["id"] in seen:
            raise SystemExit(f"ERROR: duplicate sign id {sign['id']!r}.")
        seen.add(sign["id"])
        if not sign.get("messages"):
            raise SystemExit(f"ERROR: sign {sign['id']!r} has no messages.")
    inputs.setdefault("asset_type", ASSET_TYPE_DEFAULT)
    return inputs


# --------------------------------------------------------------------------- #
# Execution helpers (real mode only)
# --------------------------------------------------------------------------- #

def _shellish(arg) -> str:
    s = str(arg)
    return f'"{s}"' if (" " in s or ";" in s) else s


def run_step(step: dict) -> dict:
    """Run ONE command step as a synchronous foreground subprocess. No background
    process, no polling (CONDUCTOR_SPEC rule 7.1). Output streams to the human."""
    argv = step["argv"]
    label = step["label"]
    timeout = TIMEOUTS.get(label, 300)
    print(f"\n=== RUN [{step['phase']}] {label} (timeout {timeout}s) ===")
    print("  " + " ".join(_shellish(a) for a in argv[1:]))  # omit the python path for readability
    try:
        proc = subprocess.run(argv, cwd=str(REPO_ROOT), timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after {timeout}s", file=sys.stderr)
        return {"label": label, "phase": step["phase"], "ok": False, "error": f"timeout after {timeout}s"}
    except Exception as exc:  # noqa: BLE001
        print(f"  ERROR launching {label}: {exc}", file=sys.stderr)
        return {"label": label, "phase": step["phase"], "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    ok = proc.returncode == 0
    if not ok:
        print(f"  {label} exited non-zero ({proc.returncode})", file=sys.stderr)
    return {"label": label, "phase": step["phase"], "ok": ok, "returncode": proc.returncode}


def print_register_profile_plain(profile_path) -> None:
    """The calibration gate: show the derived register in plain language for an
    eyeball BEFORE generation (brief_schema_v3 calibration_gate). No model call."""
    try:
        profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] could not read register profile: {exc}", file=sys.stderr)
        return
    print("\n=== REGISTER PROFILE (eyeball this before generation) ===")
    print(f"  register   : {profile.get('inferred_register')}")
    print(f"  formality  : {profile.get('formality')}    playfulness: {profile.get('playfulness')}"
          f"    (magnitude source: {profile.get('_slider_source')})")
    print(f"  anchors held: {profile.get('brand_anchors_held')}")
    print(f"  locks flexed: {profile.get('brand_locks_flexed')}")
    font_resolved = profile.get("font_resolved") or {}
    if font_resolved:
        print(f"  font        : {font_resolved.get('preferred_member') or font_resolved.get('family')}")


def _collect_sign_outputs(sign_dir) -> dict:
    sign_dir = Path(sign_dir)
    names = {
        "generated": "generated.png", "final": "final.png", "cutout": "cutout.png",
        "preview_white": "preview_white.png", "tier3": "tier3_scene.json",
        "compliance": "final.png.compliance.json", "placement": "placement_report.json",
    }
    out = {}
    for key, filename in names.items():
        path = sign_dir / filename
        if path.exists():
            out[key] = {"path": str(path), "bytes": path.stat().st_size}
    return out


def _compliance_summary(sign_dir) -> dict | None:
    path = Path(sign_dir) / "final.png.compliance.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"error": f"unreadable compliance manifest: {exc}"}
    non_licensed = [m for m in data if not str(m.get("resolution", "")).startswith("licensed")]
    return {
        "layers": len(data),
        "licensed": len(data) - len(non_licensed),
        "non_compliant": len(non_licensed),
        "non_compliant_items": [{"content": m.get("content"), "resolution": m.get("resolution")}
                                for m in non_licensed],
    }


def _sha16(path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except Exception:  # noqa: BLE001
        return None


def run_approve_gate(state: list, inputs: dict, brand: str, out_dir, register_profile, ask=input) -> str:
    """The taste gate: show drafts, take a plain-language nudge, re-run the touched
    sign by RE-INVOKING scene_author with the nudge added as a binding style note.
    (approve.py is not chained here: its main() authors a fresh tier-3 from brand
    defaults and cannot nudge an already-generated specific sign — re-invoking
    scene_author with adjusted flags is the sanctioned path, CONDUCTOR_SPEC 5.6.)"""
    out = str(out_dir)
    for _ in range(MAX_NUDGES):
        print("\n=== DRAFTS READY — your taste call (the tool stops here by design) ===")
        for s in state:
            shown = s.get("preview_png") or s.get("final_png") or "(no draft produced)"
            print(f"  {s['sign_id']}: {shown}")
        resp = (ask("Approve all, or 'nudge <sign_id>: <change>', or 'abort': ") or "").strip()
        low = resp.lower()
        if low in APPROVALS or low.startswith("approve"):
            return "approved"
        if low.startswith("abort"):
            return "aborted"
        if low.startswith("nudge"):
            body = resp[len("nudge"):].lstrip(": ").strip()
            sid, _, change = body.partition(":")
            sid, change = sid.strip(), change.strip()
            target = next((s for s in state if s["sign_id"] == sid), None)
            if not target or not change:
                print("  Could not parse that. Use: nudge <sign_id>: <what to change>")
                continue
            argv = [PY] + _scene_author_argv(brand, out, sid, target["messages"],
                                             inputs.get("reference_image"), register_profile)
            argv += ["--style-notes", change]
            print(f"  Re-running sign {sid} with your nudge: {change!r}")
            run_step({"phase": f"sign:{sid}", "label": "scene_author", "argv": argv})
            refreshed = _collect_sign_outputs(Path(out) / f"sign_{sid}")
            target["final_png"] = (refreshed.get("final") or {}).get("path")
            target["preview_png"] = (refreshed.get("preview_white") or {}).get("path")
        else:
            print("  Please type: approve, 'nudge <sign_id>: <change>', or abort.")
    return "max_nudges_reached"


# --------------------------------------------------------------------------- #
# Real-mode execution
# --------------------------------------------------------------------------- #

def execute(inputs: dict, brand: str, out_dir, inputs_path, no_approve: bool, plan: dict) -> dict:
    out = str(out_dir)
    ref = inputs.get("reference_image")
    has_ref = bool(ref)
    notes = []
    subfields_path = f"{out}/subfields.json"
    calibration_path = Path(out) / "calibration.json"
    profile_path = Path(out) / "register_profile.json"

    # --- 4. register prep, with honest-null fallbacks ---
    used_calibration = False
    calibration_outcome = "skipped (no reference supplied)"
    if has_ref:
        if not Path(ref).exists():
            calibration_outcome = f"reference not found on disk: {ref}"
            notes.append(f"reference_image set but missing ({ref}); calibration skipped, "
                         "magnitude falls back to moderated defaults")
        else:
            result = run_step(_cmd("register", "calibrate", _calibrate_argv(ref, brand, out)))
            if result["ok"] and calibration_path.exists():
                used_calibration = True
                calibration_outcome = "calibrated from reference (magnitude = blind score)"
            else:
                calibration_outcome = "calibration failed; magnitude from moderated defaults"
                notes.append("calibrate_from_reference failed or wrote no calibration.json; "
                             "derive_register run WITHOUT --calibration")

    derive = run_step(_cmd("register", "derive_register",
                           _derive_argv(brand, out, subfields_path,
                                        str(calibration_path) if used_calibration else None)))
    have_profile = derive["ok"] and profile_path.exists()
    if have_profile:
        print_register_profile_plain(profile_path)
    else:
        notes.append("derive_register failed or wrote no register_profile.json; "
                     "scene_author will run WITHOUT --register-profile (a supported path)")

    register_profile_arg = str(profile_path) if have_profile else None
    dial = normalize_dial(inputs.get("reference_relationship")) if has_ref else None

    # --- 5. per-sign loop ---
    sign_results, state = [], []
    for sign in inputs["signs"]:
        sid = sign["id"]
        sign_dir = Path(out) / f"sign_{sid}"
        messages = sign.get("messages", [])

        analyzer_record = {"ran": False, "injected_into_generation": False,
                           "aligned_prompt": None, "dial": dial, "error": None}
        aligned_prompt_arg = None
        if has_ref and Path(ref).exists():
            ar = run_step(_cmd(f"sign:{sid}", "analyzer",
                               _analyzer_argv(ref, messages, sign.get("hero_icon"), str(sign_dir),
                                              relationship=dial or DEFAULT_DIAL),
                               sign_id=sid, optional=True))
            aligned_path = sign_dir / "aligned_prompt.txt"
            if ar["ok"] and aligned_path.exists():
                aligned_prompt_arg = str(aligned_path)
                analyzer_record.update(ran=True, injected_into_generation=True,
                                       aligned_prompt=str(aligned_path))
                print(f"  analyzer wrote {aligned_path} (dial={dial}) — INJECTED as --aligned-prompt")
            else:
                analyzer_record["error"] = ar.get("error", "analyzer failed")
                notes.append(f"sign {sid}: analyzer failed; aligned prompt NOT injected — "
                             "scene_author falls back to the register prompt + the fed ref image")

        sa_argv = _scene_author_argv(brand, out, sid, messages, ref if has_ref else None,
                                     register_profile_arg, aligned_prompt=aligned_prompt_arg)
        sr = run_step(_cmd(f"sign:{sid}", "scene_author", sa_argv, sign_id=sid))
        outputs = _collect_sign_outputs(sign_dir)
        # scene_author records needs_review (ref capture-failure: gpt text left in place).
        sign_needs_review = None
        srm_path = sign_dir / "run_manifest.json"
        if srm_path.exists():
            try:
                sign_needs_review = json.loads(srm_path.read_text(encoding="utf-8")).get("needs_review")
            except Exception:  # noqa: BLE001
                pass
        if sign_needs_review:
            notes.append(f"sign {sid}: needs_review=true (render-and-scrub capture failed; "
                         "gpt's rendered text left in place)")
        sign_results.append({
            "sign_id": sid,
            "ok": sr["ok"],
            "messages": messages,
            "scene_author_cmd": [PY] + sa_argv,
            "outputs": outputs,
            "analyzer": analyzer_record,
            "needs_review": sign_needs_review,
            "compliance": _compliance_summary(sign_dir),
        })
        state.append({"sign_id": sid, "messages": messages,
                      "final_png": (outputs.get("final") or {}).get("path"),
                      "preview_png": (outputs.get("preview_white") or {}).get("path")})

    # --- 6. approve gate ---
    approve_status = "skipped (--no-approve)"
    if not no_approve:
        approve_status = run_approve_gate(state, inputs, brand, out_dir, register_profile_arg)

    # --- 7. manifest (the provenance record) ---
    context = inputs.get("context") or {}
    manifest = {
        "conductor_version": "v1",
        "brand": brand,
        "brand_paths": plan["brand_paths"],
        "out": out,
        "inputs_file": str(inputs_path),
        "inputs_sha256_16": _sha16(inputs_path),
        "asset_type": inputs.get("asset_type"),
        "asset_profile": ASSET_PROFILE,
        "asset_type_note": "asset_type is intent-framing only in v1; output is ALWAYS flat_graphic",
        "reference_image": ref,
        "reference_relationship": inputs.get("reference_relationship"),
        "dial": dial,
        "reference_relationship_status": (
            "WIRED: the dial selects the analyzer aligned-prompt rung, injected as "
            "scene_author --aligned-prompt" if has_ref else "no reference supplied (no dial)"),
        "cutout_status": (
            "deferred for reference jobs (chroma disabled, no green backdrop) — final.png is "
            "the deliverable" if has_ref
            else "chroma cutout produced for no-reference die-cut jobs"),
        "inert_provenance_recorded_not_wired": {
            "audience": context.get("audience"),
            "setting": context.get("setting"),
            "warmth": (context.get("vibe") or {}).get("warmth"),
        },
        "register": {
            "profile_path": str(profile_path) if have_profile else None,
            "calibration_outcome": calibration_outcome,
            "used_calibration": used_calibration,
        },
        "signs": sign_results,
        "approve_status": approve_status,
        "notes": notes,
    }
    manifest_path = Path(out) / "conductor_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_signs = sum(1 for s in sign_results if s["ok"])
    print(f"\n=== DONE: {ok_signs}/{len(sign_results)} sign(s) generated, approve={approve_status} ===")
    print(f"manifest: {manifest_path}")
    if notes:
        print("notes (honest-null / fallbacks):")
        for n in notes:
            print(f"  - {n}")
    return manifest


def print_plan(plan: dict) -> None:
    print(f"\n=== PLAN (brand={plan['brand']}, signs={plan['sign_count']}, "
          f"reference={plan['has_reference']}) ===")
    print(f"  answer_key: {plan['brand_paths']['answer_key']}   "
          f"config: {plan['brand_paths']['config']} (optional in v1)")
    print(f"  asset_type: {plan['asset_type']}  ->  output profile: {plan['asset_profile_v1']}")
    print(f"  ({plan['asset_type_note']})")
    for i, step in enumerate(plan["steps"], 1):
        if step["kind"] == "command":
            print(f"  {i:>2}. [{step['phase']}] {step['label']}")
            print(f"      {' '.join(_shellish(a) for a in step['argv'][1:])}")
        else:
            print(f"  {i:>2}. [{step['phase']}] {step['label']} gate (enabled={step.get('enabled')})")


# --------------------------------------------------------------------------- #
# Local glue artifacts (pure functions of inputs; cheap; written in BOTH modes)
# --------------------------------------------------------------------------- #

def write_glue_artifacts(inputs: dict, brand: str, out_dir) -> None:
    out_dir = Path(out_dir)
    (out_dir / "subfields.json").write_text(
        json.dumps(build_subfields(inputs), ensure_ascii=False, indent=2), encoding="utf-8")
    for sign in inputs["signs"]:
        intent = build_intent(inputs, sign, brand)
        (out_dir / f"intent_{sign['id']}.json").write_text(
            json.dumps(intent, ensure_ascii=False, indent=2), encoding="utf-8")


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Brand-general human-gate conductor around scene_author. "
                    "Agent-free, not human-free: it asks guided questions and stops for approval.")
    parser.add_argument("--brand", required=True, help="brand id; loads answer_keys/<id>.json")
    parser.add_argument("--inputs", default="",
                        help="pre-filled inputs.json (skips the interactive questions). "
                             "Required for --dry-run.")
    parser.add_argument("--out", default="",
                        help="run folder (default: output/run_<brand>_<timestamp>/)")
    parser.add_argument("--dry-run", action="store_true",
                        help="plan only: write plan.json + local glue, run NO external or model "
                             "calls (no vision, no Anthropic, no image generation). Requires --inputs.")
    parser.add_argument("--no-approve", action="store_true",
                        help="skip the interactive approve gate (batch/test use)")
    args = parser.parse_args()

    if args.dry_run and not args.inputs:
        parser.error("--dry-run requires --inputs (there is no interactive gate in a dry run).")

    # 2. LOAD BRAND — fail loudly if the brand has no answer key.
    answer_key = REPO_ROOT / "answer_keys" / f"{args.brand}.json"
    if not answer_key.exists():
        available = sorted(p.stem for p in (REPO_ROOT / "answer_keys").glob("*.json"))
        sys.exit(f"ERROR: no answer key for brand {args.brand!r} (expected {answer_key}). "
                 f"Brands with an answer key: {available}")

    out_dir = Path(args.out) if args.out else REPO_ROOT / "output" / f"run_{args.brand}_{_timestamp()}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. INPUT GATE
    if args.inputs:
        inputs_path = Path(args.inputs)
        inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    else:
        inputs = ask_questions()
        inputs_path = out_dir / "inputs.json"
        inputs_path.write_text(json.dumps(inputs, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  wrote {inputs_path}")
    validate_inputs(inputs)

    # 3. SUBFIELDS + per-sign intents (pure; written in both modes)
    write_glue_artifacts(inputs, args.brand, out_dir)

    plan = build_plan(inputs, args.brand, out_dir, no_approve=args.no_approve)

    if args.dry_run:
        plan_path = out_dir / "plan.json"
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print_plan(plan)
        print(f"\n[DRY RUN] wrote {plan_path} + local glue (subfields.json, intent_*.json). "
              "No external calls made.")
        return

    execute(inputs, args.brand, out_dir, inputs_path, args.no_approve, plan)


if __name__ == "__main__":
    main()
