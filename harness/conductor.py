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

# The kit-of-parts engine modules are stdlib-only too, so importing them keeps this
# conductor import-light (no numpy/anthropic/openai). They power the bespoke-composition
# route used whenever a brand has an authored kit (feature 001-kit-of-parts-composition).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit as kitlib  # noqa: E402
import compose_select  # noqa: E402
import format_size as fmtsize  # noqa: E402  (stdlib size resolver, feature 002)
import prompt_elements  # noqa: E402  (stdlib mandatory/forbidden clause, feature 002)

# Proven scripts the conductor sequences (repo-relative; run with cwd=REPO_ROOT).
SCENE_AUTHOR = "harness/scene_author.py"
DERIVE_REGISTER = "register/derive_register.py"
CALIBRATE = "register/calibrate_from_reference.py"
ANALYZER = "register/reference_style_to_prompt.py"
KIT = "harness/kit.py"

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


def normalize_render_style(value) -> str:
    """Feature 009: map the user's render_style (free text) to the engine asset_profile.
    'photographic' -> 'photo'; everything else (including 'flat vector', blank, omitted, unrecognized)
    -> 'flat_graphic' (the safe default, honest-null). Case / whitespace-insensitive. Mirrors
    normalize_dial. The thin route is the only path that consumes this; kit/legacy stay flat_graphic."""
    v = str(value or "").strip().lower()
    if v in ("photographic", "photo"):
        return "photo"
    return "flat_graphic"


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


def build_subfields(inputs: dict, thin: bool = False) -> dict:
    """The reconciliation crux: inputs.context uses brief_schema_v3 field names
    verbatim, so the subfields derive_register consumes are an identity pass-through
    of context (plus asset_type). No inference, no judgment glue.

    thin (feature 011): the thin route also passes the brief's render_style through
    VERBATIM (the raw human term, not the normalized asset_profile) so derive_register
    can gate the playful-vibe event_prop promotion for photographic renders. Kit and
    legacy routes never receive the key: their subfields.json stays byte-identical
    (those paths always render flat, the register gate must not see a render choice)."""
    context = dict(inputs.get("context") or {})
    subfields = {"asset_type": inputs.get("asset_type", ASSET_TYPE_DEFAULT), **context}
    if thin and "render_style" in inputs:
        subfields["render_style"] = inputs.get("render_style")
    return subfields


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


def _kit_argv(brand: str, out: str, has_ref: bool) -> list:
    """Build kit_profile.json once per campaign (DERIVED kit layer: palette/font/frame from the
    answer key + register_profile; answer key wins). Runs AFTER derive_register."""
    argv = [KIT, "--brand", brand, "--answer-key", f"answer_keys/{brand}.json",
            "--register-profile", f"{out}/register_profile.json",
            "--out", f"{out}/kit_profile.json"]
    if has_ref:
        argv += ["--calibration", f"{out}/calibration.json"]
    return argv


def _scene_author_kit_argv(brand: str, out: str, sign_id: str, size=None) -> list:
    """Kit reserve-box composition: scene_author paints panel + chosen icon in the icon zone and
    keeps the reserved text zone clear, then composites the fitted headline into it. No clone
    dial, no render-and-scrub. Inputs are the campaign kit_profile + this sign's composition.
    `size` (WxH, feature 002) is the format_size-resolved output dimensions."""
    argv = [SCENE_AUTHOR, "--brand", brand, "--asset-profile", ASSET_PROFILE,
            "--kit-profile", f"{out}/kit_profile.json",
            "--composition", f"{out}/sign_{sign_id}/composition.json",
            "--out", f"{out}/sign_{sign_id}"]
    if size:
        argv += ["--size", size]
    return argv


def _scene_author_thin_argv(brand: str, out: str, sign_id: str, messages: list, ref,
                            register_profile, dial, mandatory, forbidden, size=None,
                            style_notes=None, asset_profile=ASSET_PROFILE,
                            asset_type=None, occasion=None) -> list:
    """THIN ROUTE (feature 003): scene_author --thin assembles ONE prompt from the brief and lets
    gpt-image-2 compose the whole sign (STOP at generated.png). No kit, no compose_select, no
    analyzer/aligned-prompt, no measure, no composite. The reference (if any) is fed as a visual
    exemplar via --ref-image and still sets register MAGNITUDE upstream (calibrate); it is NOT
    cloned through the analyzer. mandatory/forbidden are this sign's EFFECTIVE union, verbatim."""
    argv = [SCENE_AUTHOR, "--brand", brand, "--asset-profile", asset_profile, "--thin"]
    if register_profile:
        argv += ["--register-profile", register_profile]
    argv += ["--must-include", ";".join(messages), "--out", f"{out}/sign_{sign_id}"]
    if mandatory:
        argv += ["--mandatory-elements", "；".join(mandatory)]
    if forbidden:
        argv += ["--forbidden-elements", "；".join(forbidden)]
    if dial:
        argv += ["--dial", dial]
    if size:
        argv += ["--size", size]
    if style_notes:
        argv += ["--style-notes", style_notes]
    # Feature 012: the brief's asset_type + occasion ride to the SCENE/SUBJECT section VERBATIM.
    if asset_type and str(asset_type).strip():
        argv += ["--asset-type", str(asset_type)]
    if occasion and str(occasion).strip():
        argv += ["--occasion", str(occasion)]
    if ref:
        argv += ["--ref-image", ref]
    return argv


def _union_elements(campaign, per_sign) -> list:
    """Order-preserving union: campaign elements first, then this sign's, with exact-duplicate
    strings dropped while first-seen order is preserved (002 delta). Verbatim passthrough
    (FR-003): each string is copied byte-for-byte, never rephrased, reordered (beyond the defined
    campaign-then-per-sign concatenation), interpreted, or expanded. No agent/LLM in this path."""
    out, seen = [], set()
    for item in list(campaign or []) + list(per_sign or []):
        s = str(item)
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def build_compositions(inputs: dict, brand: str):
    """Deterministic per-sign compositions for the kit route (icon + collision-avoided
    archetype + reserved text zone + needs_review). Returns None when the brand has no kit
    (legacy route). A pre-filled hero_icon is recorded as a human OVERRIDE of the proposal."""
    if not kitlib.kit_exists(brand):
        return None
    kit = kitlib.load_kit(brand)
    signs = [{"id": s["id"], "messages": s.get("messages", [])} for s in inputs["signs"]]
    comps = compose_select.compose_campaign(kit, signs)
    # Feature 002 (+ per-sign delta): each composition carries the EFFECTIVE elements = the
    # order-preserving union of the campaign-level mandatory/forbidden (apply to all signs) and that
    # sign's OWN mandatory/forbidden (this sign only), de-duplicated. So a campaign with
    # mandatory_elements [] and only s5/s6 carrying 分别画叉 puts 分别画叉 on s5/s6 ONLY. Verbatim
    # passthrough: copied as-is, never rephrased or interpreted into variant counts (FR-003/FR-004).
    mandatory_campaign = list(inputs.get("mandatory_elements") or [])
    forbidden_campaign = list(inputs.get("forbidden_elements") or [])
    for sign, comp in zip(inputs["signs"], comps):
        if sign.get("hero_icon"):
            comp["human_hero_icon"] = sign["hero_icon"]
        eff_mandatory = _union_elements(mandatory_campaign, sign.get("mandatory_elements"))
        eff_forbidden = _union_elements(forbidden_campaign, sign.get("forbidden_elements"))
        comp["mandatory_elements"] = eff_mandatory
        comp["forbidden_elements"] = eff_forbidden
        # Per-sign conflict (constitution §V): if this sign's effective mandatory ∩ forbidden is
        # non-empty, flag needs_review naming the item(s); never silently resolve. Augments (does
        # not clobber) any icon/archetype needs_review compose_select already set.
        conflict = sorted(prompt_elements.has_conflict(eff_mandatory, eff_forbidden))
        if conflict:
            reason = ("mandatory_elements and forbidden_elements both contain: "
                      + ", ".join(conflict) + " (human must resolve)")
            comp["needs_review"] = True
            comp["needs_review_reason"] = "; ".join(
                r for r in (comp.get("needs_review_reason"), reason) if r)
    return comps


def _cmd(phase: str, label: str, script_argv: list, sign_id=None, optional=False) -> dict:
    return {"phase": phase, "kind": "command", "label": label, "sign_id": sign_id,
            "optional": optional, "argv": [PY] + script_argv}


def build_plan(inputs: dict, brand: str, out_dir, no_approve: bool = False,
               thin: bool = False, style_notes=None) -> dict:
    """Pure: inputs + brand -> the fully-parameterized HAPPY-PATH plan. dry-run
    writes this to plan.json (the falsifiable test surface); real mode executes it
    with documented honest-null fallbacks when a step fails.

    thin (feature 003): take the prompt-compose THIN route — one assemble_thin_prompt +
    generate per sign, NO kit / compose_select / measure / composite. Wins over kit even for
    a brand that has an authored kit (the kit code stays, it is just not SELECTED by default)."""
    out = str(out_dir)
    ref = inputs.get("reference_image")
    has_ref = bool(ref)
    dial = normalize_dial(inputs.get("reference_relationship")) if has_ref else None
    # Feature 009: the human-picked render_style drives the thin render dialect (photo vs flat_graphic);
    # the conductor maps the user term to the engine asset_profile here and stops hard-wiring flat.
    thin_asset_profile = normalize_render_style(inputs.get("render_style"))
    subfields_path = f"{out}/subfields.json"
    profile_path = f"{out}/register_profile.json"
    calibration_path = f"{out}/calibration.json"
    kit_mode = kitlib.kit_exists(brand) and not thin
    compositions = build_compositions(inputs, brand) if kit_mode else None
    mand_campaign = list(inputs.get("mandatory_elements") or [])
    forb_campaign = list(inputs.get("forbidden_elements") or [])
    # Feature 002: resolve the output pixel size from the brief's format_size ONCE (aspect-preserving,
    # nearest the default target; honest null on unparseable). Threaded to the kit scene_author call.
    size_resolution = fmtsize.resolve_size(inputs.get("format_size"))
    size_wh = fmtsize.size_str(size_resolution)
    _conflict = sorted(prompt_elements.has_conflict(
        inputs.get("mandatory_elements"), inputs.get("forbidden_elements")))
    needs_review_campaign = (("mandatory_elements and forbidden_elements both contain: "
                              + ", ".join(_conflict) + " (human must resolve)") if _conflict else None)

    steps = []
    # 4. register prep (campaign-level: one profile shared by all signs)
    if has_ref:
        steps.append(_cmd("register", "calibrate", _calibrate_argv(ref, brand, out)))
        steps.append(_cmd("register", "derive_register",
                          _derive_argv(brand, out, subfields_path, calibration_path)))
    else:
        steps.append(_cmd("register", "derive_register",
                          _derive_argv(brand, out, subfields_path, None)))

    if thin:
        # 4b. THIN ROUTE (feature 003): NO kit step, NO analyzer/aligned-prompt, NO compose_select.
        # Register/dial prep already ran above; each sign goes straight to scene_author --thin
        # (assemble_thin_prompt -> generate -> STOP). The reference (if any) is fed as a visual
        # exemplar via --ref-image; it set MAGNITUDE upstream (calibrate) but is NOT cloned.
        for sign in inputs["signs"]:
            sid = sign["id"]
            eff_mandatory = _union_elements(mand_campaign, sign.get("mandatory_elements"))
            eff_forbidden = _union_elements(forb_campaign, sign.get("forbidden_elements"))
            steps.append(_cmd(f"sign:{sid}", "scene_author",
                              _scene_author_thin_argv(brand, out, sid, sign.get("messages", []),
                                                      ref if has_ref else None, profile_path, dial,
                                                      eff_mandatory, eff_forbidden, size=size_wh,
                                                      style_notes=style_notes,
                                                      asset_profile=thin_asset_profile,
                                                      asset_type=inputs.get("asset_type"),
                                                      occasion=(inputs.get("context") or {}).get("occasion")),
                              sign_id=sid))
    elif kit_mode:
        # 4b. KIT ROUTE: derive the campaign kit_profile once, then compose each sign bespoke.
        # The reference (if any) feeds the kit via calibration; it does NOT clone a prompt (D6),
        # so there is no analyzer/aligned-prompt step here.
        steps.append(_cmd("kit", "kit", _kit_argv(brand, out, has_ref)))
        for sign in inputs["signs"]:
            sid = sign["id"]
            steps.append(_cmd(f"sign:{sid}", "scene_author",
                              _scene_author_kit_argv(brand, out, sid, size=size_wh), sign_id=sid))
    else:
        # 5. legacy per-sign loop. Reference job: analyzer (dial-selected wording) ->
        # aligned_prompt.txt, INJECTED as scene_author's --aligned-prompt.
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

    plan = {
        "brand": brand,
        "brand_paths": {"answer_key": f"answer_keys/{brand}.json",
                        "config": f"config/{brand}.yaml"},
        "out": out,
        "asset_type": inputs.get("asset_type", ASSET_TYPE_DEFAULT),
        "render_style": inputs.get("render_style"),
        "asset_profile_v1": (thin_asset_profile if thin else ASSET_PROFILE),
        "asset_type_note": ("feature 009: on the thin route the human-picked render_style drives the "
                            "asset_profile (photo|flat_graphic); kit/legacy paths stay flat_graphic"),
        "format_size": inputs.get("format_size"),
        "size_resolution": size_resolution,
        "mandatory_elements": inputs.get("mandatory_elements") or [],
        "forbidden_elements": inputs.get("forbidden_elements") or [],
        "needs_review_campaign": needs_review_campaign,
        "thin": thin,
        "route": "thin" if thin else ("kit" if kit_mode else "legacy"),
        "kit_mode": kit_mode,
        "kit_profile": f"{out}/kit_profile.json" if kit_mode else None,
        "has_reference": has_ref,
        "reference_relationship_raw": inputs.get("reference_relationship"),
        "dial": dial,
        "subfields": subfields_path,
        "register_profile": profile_path,
        "sign_count": len(inputs["signs"]),
        "steps": steps,
    }
    if kit_mode:
        # Surface the bespoke per-sign choices in the plan (the falsifiable dry-run surface):
        # chosen icon + distinct archetype + reserved text zone + needs_review, no model calls.
        plan["compositions"] = [{
            "sign_id": c["sign_id"], "detected_mode": c["detected_mode"],
            "chosen_icon": c["chosen_icon"], "chosen_archetype": c["chosen_archetype"],
            "archetype_reused": c["archetype_reused"], "text_zone": c["text_zone"],
            "needs_review": c["needs_review"], "needs_review_reason": c["needs_review_reason"],
            "human_hero_icon": c.get("human_hero_icon"),
        } for c in compositions]
    return plan


# --------------------------------------------------------------------------- #
# Input gate
# --------------------------------------------------------------------------- #

def _to_int(value, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _split_list(raw) -> list:
    """Split a human-typed list on the CN/EN semicolon, VERBATIM (each item stripped only of
    surrounding whitespace; never rephrased). Blank -> [] (honest null)."""
    return [s.strip() for s in re.split(r"[；;]", str(raw or "")) if s.strip()]


def ask_questions(ask=input) -> dict:
    """The human input gate: a short, adaptive, accept-all guided-subfields form
    (brief_schema_v3 buckets B/D). `ask` is injectable so the form is testable
    without stdin. Returns the full inputs dict (brand comes from the CLI arg)."""
    def q(prompt, default):
        resp = (ask(f"{prompt} [{default}]: ") or "").strip()
        return resp or default

    print("=== Guided questions (press Enter to accept the default) ===")
    asset_type = q("Asset type", ASSET_TYPE_DEFAULT)
    # Feature 002: bucket-A physical size (was dropped). Free text, e.g. 60x40cm; Enter to skip.
    format_size = (ask("Physical format / size (e.g. 60x40cm, Enter to skip): ") or "").strip() or None
    reference = (ask("Reference image path (Enter to skip): ") or "").strip()
    # The reference-relationship dial is asked ONLY when a reference is supplied (a no-ref
    # job has no dial). 3 choices; defaults to extend (max similarity, the proven gold).
    reference_relationship = None
    if reference:
        reference_relationship = normalize_dial(
            q("Reference relationship? extend (clone look, change message) | match_style "
              "(same style, fresh layout) | mood (tone cue only)", DEFAULT_DIAL))
    # bucket B is now human-settable (was derived/defaulted), defaulting to today's values.
    audience = q("Audience", DEFAULT_AUDIENCE)
    usage_context = q("Usage context", _usage_from_asset(asset_type))
    formality = _to_int(q("How formal? 0 casual to 10 official", 5), 5)
    playfulness = _to_int(q("How playful? 0 serious to 10 fun", 5), 5)
    logo_treatment = q("Logo? required/prominent | subtle | omit", "required/prominent")
    brand_strictness = q("On-brand tightness? strict VI | brand + accents | expressive departure",
                         "brand + accents")
    occasion = (ask("Occasion / campaign (short, optional): ") or "").strip()
    # Feature 002: bucket-C mandatory/forbidden elements (were dropped). VERBATIM passthrough —
    # split on the CN/EN semicolon only; each item kept exactly as typed (no rephrase, FR-003).
    mandatory_elements = _split_list(ask(
        "Mandatory elements (must appear; e.g. 分别画叉；设计两种样式; separate with '；', Enter for none): "))
    forbidden_elements = _split_list(ask(
        "Forbidden elements (must NOT appear; separate with '；', Enter for none): "))

    context = {
        # bucket B (usage_context drives the register; audience/setting are provenance)
        "usage_context": usage_context,
        "audience": audience,
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
        "format_size": format_size,
        "reference_image": reference or None,
        "reference_relationship": reference_relationship,  # dial (Axis B); None for no-ref jobs
        "mandatory_elements": mandatory_elements,
        "forbidden_elements": forbidden_elements,
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
        # 002 delta: a sign MAY carry its own mandatory_elements / forbidden_elements (this sign
        # only). OPTIONAL — absent stays absent (honest null; back-compat unchanged). When present
        # they MUST be lists of strings; verbatim, no agent inference (FR-003).
        for key in ("mandatory_elements", "forbidden_elements"):
            if key not in sign or sign[key] is None:
                continue
            val = sign[key]
            if not isinstance(val, list) or not all(isinstance(v, str) for v in val):
                raise SystemExit(
                    f"ERROR: sign {sign['id']!r} {key} must be a list of strings.")
    inputs.setdefault("asset_type", ASSET_TYPE_DEFAULT)
    # Feature 002: the previously-dropped bucket-A/C fields. OPTIONAL (back-compat): absent ->
    # empty/None, never invented. Lists pass through verbatim; a bare string is kept as one item
    # (faithful, not rephrased). No agent inference.
    inputs.setdefault("format_size", None)
    for key in ("mandatory_elements", "forbidden_elements"):
        val = inputs.get(key)
        if val is None or val == "":
            inputs[key] = []
        elif isinstance(val, list):
            inputs[key] = [str(v) for v in val]
        else:
            inputs[key] = [str(val)]
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


def _apply_kit_override(out: str, sid: str, change: str, brand: str) -> str | None:
    """Kit-route taste override: 'icon=<id>' or 'arch=<id>' edits the sign's composition.json
    (the human overriding the tool's PROPOSAL, constitution §I). Returns a note or None if the
    change was not an icon/arch override (caller falls back to a free-text style nudge)."""
    low = change.lower()
    field = "chosen_icon" if low.startswith("icon=") else ("chosen_archetype" if low.startswith("arch=") else None)
    if not field:
        return None
    value = change.split("=", 1)[1].strip()
    comp_path = Path(out) / f"sign_{sid}" / "composition.json"
    if not comp_path.exists():
        return f"no composition.json for {sid}"
    comp = json.loads(comp_path.read_text(encoding="utf-8"))
    comp[field] = value
    comp["human_override"] = {**(comp.get("human_override") or {}), field: value}
    # A human-picked icon clears an icon-miss review; archetype override clears reuse review.
    if field == "chosen_icon":
        comp["needs_review"] = bool(comp.get("archetype_reused"))
    comp_path.write_text(json.dumps(comp, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"{field}={value} (human override recorded)"


def run_approve_gate(state: list, inputs: dict, brand: str, out_dir, register_profile,
                     ask=input, kit_mode: bool = False, thin: bool = False) -> str:
    """The taste gate: show drafts (and, on the kit route, the proposed icon + layout per sign),
    take a plain-language nudge, re-run the touched sign. On the kit route a nudge may be
    'icon=<id>' or 'arch=<id>' to OVERRIDE the tool's proposal; otherwise it is a binding style
    note. The human stays in the loop here BY DESIGN (constitution §I)."""
    out = str(out_dir)
    for _ in range(MAX_NUDGES):
        print("\n=== DRAFTS READY — your taste call (the tool stops here by design) ===")
        for s in state:
            shown = s.get("preview_png") or s.get("final_png") or "(no draft produced)"
            if kit_mode:
                flag = "  [needs_review]" if s.get("needs_review") else ""
                print(f"  {s['sign_id']}: icon={s.get('icon')} layout={s.get('archetype')}{flag}  {shown}")
            else:
                print(f"  {s['sign_id']}: {shown}")
        hint = ("Approve all, 'nudge <sign_id>: icon=<id> | arch=<id> | <free change>', or 'abort': "
                if kit_mode else "Approve all, or 'nudge <sign_id>: <change>', or 'abort': ")
        resp = (ask(hint) or "").strip()
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
            if thin:
                # THIN ROUTE nudge: re-run scene_author --thin with the human's note as a binding
                # style rule (the taste call). Elements/dial recomputed from the brief (verbatim).
                sign = next((s for s in inputs["signs"] if s.get("id") == sid), {})
                eff_mandatory = _union_elements(inputs.get("mandatory_elements"),
                                                sign.get("mandatory_elements"))
                eff_forbidden = _union_elements(inputs.get("forbidden_elements"),
                                                sign.get("forbidden_elements"))
                dial = (normalize_dial(inputs.get("reference_relationship"))
                        if inputs.get("reference_image") else None)
                argv = [PY] + _scene_author_thin_argv(
                    brand, out, sid, target["messages"], inputs.get("reference_image"),
                    register_profile, dial, eff_mandatory, eff_forbidden)
                argv += ["--style-notes", change]
                print(f"  Re-running sign {sid} (thin) with your nudge: {change!r}")
                run_step({"phase": f"sign:{sid}", "label": "scene_author", "argv": argv})
            elif kit_mode:
                override = _apply_kit_override(out, sid, change, brand)
                if override is not None:
                    print(f"  Sign {sid}: {override}; re-composing.")
                    refreshed_comp = json.loads((Path(out) / f"sign_{sid}" / "composition.json").read_text(encoding="utf-8"))
                    target["icon"] = refreshed_comp.get("chosen_icon")
                    target["archetype"] = refreshed_comp.get("chosen_archetype")
                    target["needs_review"] = refreshed_comp.get("needs_review")
                argv = [PY] + _scene_author_kit_argv(brand, out, sid)
                if override is None:
                    argv += ["--style-notes", change]
                print(f"  Re-running sign {sid}.")
                run_step({"phase": f"sign:{sid}", "label": "scene_author", "argv": argv})
            else:
                argv = [PY] + _scene_author_argv(brand, out, sid, target["messages"],
                                                 inputs.get("reference_image"), register_profile)
                argv += ["--style-notes", change]
                print(f"  Re-running sign {sid} with your nudge: {change!r}")
                run_step({"phase": f"sign:{sid}", "label": "scene_author", "argv": argv})
            refreshed = _collect_sign_outputs(Path(out) / f"sign_{sid}")
            target["final_png"] = ((refreshed.get("final") or refreshed.get("generated") or {})
                                   .get("path"))
            target["preview_png"] = (refreshed.get("preview_white") or {}).get("path")
        else:
            print("  Please type: approve, 'nudge <sign_id>: <change>', or abort.")
    return "max_nudges_reached"


# --------------------------------------------------------------------------- #
# Real-mode execution
# --------------------------------------------------------------------------- #

def execute(inputs: dict, brand: str, out_dir, inputs_path, no_approve: bool, plan: dict,
            thin: bool = False, style_notes=None) -> dict:
    out = str(out_dir)
    ref = inputs.get("reference_image")
    has_ref = bool(ref)
    notes = []
    mand_campaign = list(inputs.get("mandatory_elements") or [])
    forb_campaign = list(inputs.get("forbidden_elements") or [])
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
    # Feature 009 fix: the EXECUTE path must resolve the brief's render_style exactly like
    # build_plan does (line ~336). It previously omitted asset_profile at the thin call site,
    # so every REAL run silently fell back to the flat_graphic default while dry-run plans
    # (and the plan-only tests) showed photo — the plan/execution drift this module promises
    # not to have. Caught by the human eye on run_CJXQ_20260701_152554.
    thin_asset_profile = normalize_render_style(inputs.get("render_style"))
    kit_mode = kitlib.kit_exists(brand) and not thin
    # Feature 002: resolve output size once; flag a mandatory/forbidden contradiction (honest null).
    size_resolution = fmtsize.resolve_size(inputs.get("format_size"))
    size_wh = fmtsize.size_str(size_resolution)
    if size_resolution.get("needs_review"):
        notes.append(f"format_size: {size_resolution.get('note')}")
    element_conflict = sorted(prompt_elements.has_conflict(
        inputs.get("mandatory_elements"), inputs.get("forbidden_elements")))
    needs_review_campaign = None
    if element_conflict:
        needs_review_campaign = ("mandatory_elements and forbidden_elements both contain: "
                                 + ", ".join(element_conflict) + " (human must resolve)")
        notes.append(f"needs_review: {needs_review_campaign}")

    # --- 4b. KIT ROUTE: build the campaign kit_profile once (DERIVED layer) ---
    kit_profile_ok = False
    if kit_mode:
        if have_profile:
            kr = run_step(_cmd("kit", "kit", _kit_argv(brand, out, has_ref and Path(ref).exists())))
            kit_profile_ok = kr["ok"] and (Path(out) / "kit_profile.json").exists()
            if not kit_profile_ok:
                notes.append("kit.py failed or wrote no kit_profile.json; scene_author kit mode "
                             "will fall back to brand defaults (honest null)")
        else:
            notes.append("no register_profile; kit_profile not derived (kit needs the register lane)")

    # --- 5. per-sign loop ---
    sign_results, state = [], []
    for sign in inputs["signs"]:
        sid = sign["id"]
        sign_dir = Path(out) / f"sign_{sid}"
        messages = sign.get("messages", [])

        if thin:
            # THIN ROUTE (feature 003): one scene_author --thin per sign. No analyzer, no kit, no
            # composite. The reference is fed as a visual exemplar; mandatory/forbidden are this
            # sign's EFFECTIVE union (campaign + per-sign), verbatim.
            eff_mandatory = _union_elements(mand_campaign, sign.get("mandatory_elements"))
            eff_forbidden = _union_elements(forb_campaign, sign.get("forbidden_elements"))
            element_sign_conflict = sorted(prompt_elements.has_conflict(eff_mandatory, eff_forbidden))
            if element_sign_conflict:
                notes.append(f"sign {sid}: mandatory ∩ forbidden = {element_sign_conflict} "
                             "(human must resolve)")
            sa_argv = _scene_author_thin_argv(brand, out, sid, messages, ref if has_ref else None,
                                              register_profile_arg, dial, eff_mandatory,
                                              eff_forbidden, size=size_wh, style_notes=style_notes,
                                              asset_profile=thin_asset_profile,
                                              asset_type=inputs.get("asset_type"),
                                              occasion=(inputs.get("context") or {}).get("occasion"))
            sr = run_step(_cmd(f"sign:{sid}", "scene_author", sa_argv, sign_id=sid))
            outputs = _collect_sign_outputs(sign_dir)
            srm = {}
            srm_path = sign_dir / "run_manifest.json"
            if srm_path.exists():
                try:
                    srm = json.loads(srm_path.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    pass
            sign_results.append({
                "sign_id": sid, "ok": sr["ok"], "messages": messages,
                "scene_author_cmd": [PY] + sa_argv, "outputs": outputs,
                "route": "thin", "licensed_type": srm.get("licensed_type", "deferred (raw gpt text)"),
                "mandatory_elements": eff_mandatory, "forbidden_elements": eff_forbidden,
                "needs_review": bool(element_sign_conflict),
                "needs_review_reason": ("; ".join(element_sign_conflict) if element_sign_conflict else None),
            })
            state.append({"sign_id": sid, "messages": messages,
                          "final_png": (outputs.get("generated") or {}).get("path"),
                          "preview_png": None})
            continue

        if kit_mode:
            # composition.json was written by write_glue_artifacts (pure fn of inputs + kit).
            comp = {}
            comp_path = sign_dir / "composition.json"
            if comp_path.exists():
                try:
                    comp = json.loads(comp_path.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    pass
            if comp.get("needs_review"):
                notes.append(f"sign {sid}: needs_review=true ({comp.get('needs_review_reason')})")
            sa_argv = _scene_author_kit_argv(brand, out, sid, size=size_wh)
            sr = run_step(_cmd(f"sign:{sid}", "scene_author", sa_argv, sign_id=sid))
            outputs = _collect_sign_outputs(sign_dir)
            sign_results.append({
                "sign_id": sid, "ok": sr["ok"], "messages": messages,
                "scene_author_cmd": [PY] + sa_argv, "outputs": outputs,
                "composition": {"chosen_icon": comp.get("chosen_icon"),
                                "chosen_archetype": comp.get("chosen_archetype"),
                                "archetype_reused": comp.get("archetype_reused"),
                                "human_hero_icon": comp.get("human_hero_icon")},
                "needs_review": comp.get("needs_review"),
                "needs_review_reason": comp.get("needs_review_reason"),
                "compliance": _compliance_summary(sign_dir),
            })
            state.append({"sign_id": sid, "messages": messages,
                          "final_png": (outputs.get("final") or {}).get("path"),
                          "preview_png": (outputs.get("preview_white") or {}).get("path"),
                          "icon": comp.get("chosen_icon"), "archetype": comp.get("chosen_archetype"),
                          "needs_review": comp.get("needs_review")})
            continue

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
        approve_status = run_approve_gate(state, inputs, brand, out_dir, register_profile_arg,
                                          kit_mode=kit_mode, thin=thin)

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
        "render_style": inputs.get("render_style"),
        "asset_profile": plan.get("asset_profile_v1", ASSET_PROFILE),
        "asset_type_note": ("feature 009: render_style drives the thin asset_profile (photo|flat_graphic); "
                            "kit/legacy stay flat_graphic"),
        "reference_image": ref,
        "reference_relationship": inputs.get("reference_relationship"),
        "dial": dial,
        # Feature 002: the previously-dropped fields, recorded VERBATIM, plus a lossless echo of the
        # inputs the pipeline actually consumed (FR-002 / SC-001). size_resolution is added by the
        # size-wiring step (US2).
        "format_size": inputs.get("format_size"),
        "size_resolution": size_resolution,
        "mandatory_elements": inputs.get("mandatory_elements") or [],
        "forbidden_elements": inputs.get("forbidden_elements") or [],
        "needs_review_campaign": needs_review_campaign,
        "brief_fields_received": inputs,
        "reference_relationship_status": (
            "WIRED: the dial selects the analyzer aligned-prompt rung, injected as "
            "scene_author --aligned-prompt" if has_ref else "no reference supplied (no dial)"),
        "cutout_status": (
            "thin route: no cutout/composite — the raw generated.png IS the deliverable "
            "(moat deferred)" if thin
            else "deferred for reference jobs (chroma disabled, no green backdrop) — final.png is "
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
        "route": "thin" if thin else ("kit" if kit_mode else "legacy"),
        # Feature 003: the licensed-font MOAT is DEFERRED on the thin route — the deliverable is
        # the raw gpt-painted generated.png. Tracked here, not silent (constitution §V honest null).
        "licensed_type": "deferred (raw gpt text)" if thin else "licensed composite (kit/legacy)",
        "kit": {
            "kit_mode": kit_mode,
            "kit_path": f"kits/{brand}.json" if kit_mode else None,
            "kit_profile_path": (str(Path(out) / "kit_profile.json")
                                 if kit_mode and kit_profile_ok else None),
            "route": ("thin (prompt-compose; kit not selected)" if thin else
                      "kit of parts + bespoke per-message composition" if kit_mode else
                      "legacy (render-and-scrub / aligned-prompt)"),
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

def write_glue_artifacts(inputs: dict, brand: str, out_dir, thin: bool = False) -> None:
    out_dir = Path(out_dir)
    (out_dir / "subfields.json").write_text(
        json.dumps(build_subfields(inputs, thin=thin), ensure_ascii=False, indent=2), encoding="utf-8")
    for sign in inputs["signs"]:
        intent = build_intent(inputs, sign, brand)
        (out_dir / f"intent_{sign['id']}.json").write_text(
            json.dumps(intent, ensure_ascii=False, indent=2), encoding="utf-8")
    # Thin route (feature 003) writes NO composition.json — the kit/composition layer is not
    # selected. Kit route: write each sign's bespoke composition (pure function of inputs + kit),
    # so it is visible in BOTH dry-run and real mode and consumed by scene_author kit-mode.
    compositions = None if thin else build_compositions(inputs, brand)
    if compositions is not None:
        for comp in compositions:
            sign_dir = out_dir / f"sign_{comp['sign_id']}"
            sign_dir.mkdir(parents=True, exist_ok=True)
            (sign_dir / "composition.json").write_text(
                json.dumps(comp, ensure_ascii=False, indent=2), encoding="utf-8")


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
    parser.add_argument("--style-notes", default="",
                        help="Binding style note (feature 004): a campaign-level nudge threaded "
                             "VERBATIM to the thin scene_author as --style-notes (a binding clause). "
                             "Lets the browser taste gate's nudge-rerun reach generation "
                             "non-interactively. Empty = none.")
    parser.add_argument("--thin", action="store_true",
                        help="THIN ROUTE (feature 003): route flat_graphic jobs through the "
                             "prompt-compose spine — one assembled prompt per sign, gpt-image-2 "
                             "composes the whole sign, STOP at generated.png. No kit, no "
                             "compose_select, no measure, no composite. The kit code stays in the "
                             "repo but is NOT selected. Moat (licensed font) deferred.")
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
    write_glue_artifacts(inputs, args.brand, out_dir, thin=args.thin)

    style_notes = args.style_notes.strip() or None
    plan = build_plan(inputs, args.brand, out_dir, no_approve=args.no_approve, thin=args.thin,
                      style_notes=style_notes)

    if args.dry_run:
        plan_path = out_dir / "plan.json"
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print_plan(plan)
        print(f"\n[DRY RUN] wrote {plan_path} + local glue (subfields.json, intent_*.json). "
              "No external calls made.")
        return

    execute(inputs, args.brand, out_dir, inputs_path, args.no_approve, plan, thin=args.thin,
            style_notes=style_notes)


if __name__ == "__main__":
    main()
