#!/usr/bin/env python3
"""harness/approve.py — Tier-3 approval loop (Gate 2 of brief_schema_v2 step_3_approve).

Usage:
  .venv/bin/python harness/approve.py --brand taichi --out output/approve_run1 \
      [--must-include "..."] [--no-generate] [--script responses.txt]
"""

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_env import load_runtime_env  # noqa: E402  (018: env > .env > legacy ~/.hermes)
load_runtime_env()

sys.path.insert(0, str(Path(__file__).parent))
from scene_author import load_brand, author_tier3, assemble_final_prompt, LOGO_PATH

APPROVALS = {"yes", "y", "yep", "ok", "okay", "looks good", "good", "approve", "approved", "lgtm", "perfect"}
MAX_NUDGES = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _anthropic_text(model: str, prompt: str, max_tokens: int = 4096) -> str:
    import anthropic
    msg = anthropic.Anthropic().messages.create(
        model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):  # strip markdown fences if the model adds them anyway
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()
    return raw


def summarize_scene(tier3: dict) -> str:
    prompt = (
        "Below is a tier-3 scene-construction JSON for a marketing poster. Turn it into ONE short,\n"
        "friendly paragraph that a non-designer marketing manager instantly understands.\n"
        "Rules: no hex codes, no pixel coordinates, no photography jargon (say 'soft warm light',\n"
        "not 'f/2.8 key light at 10 o'clock'). Name colors plainly, describe where things sit in\n"
        "everyday terms (top-left, center-right). Keep exact text strings (including Chinese) as-is.\n"
        "Start with \"Here's the plan:\" and end with: anything you'd like to change?\n\n"
        f"{json.dumps(tier3, ensure_ascii=False, indent=2)}"
    )
    return _anthropic_text("claude-sonnet-4-6", prompt, max_tokens=1024)


def summarize_diff(changed_fields: list[str], old: dict, new: dict) -> str:
    snippets = {f: {"before": old.get(f), "after": new.get(f)} for f in changed_fields}
    prompt = (
        "A marketing poster scene was just edited per a human's request. Write ONE short plain-language\n"
        "line describing only what changed, then say everything else is unchanged. No hex codes, no\n"
        "pixels, no jargon. Format: \"Updated: ... Everything else unchanged.\"\n\n"
        f"Changed fields (before/after):\n{json.dumps(snippets, ensure_ascii=False, indent=2)}"
    )
    return _anthropic_text("claude-sonnet-4-6", prompt, max_tokens=512)


def apply_nudge(tier3: dict, nudge: str) -> tuple[dict, list[str], list[str]]:
    """Edit ONLY the fields the nudge touches. Returns (new_scene, changed_fields, restored_fields)."""
    prompt = (
        "You are editing the tier-3 scene-construction JSON for a marketing poster.\n"
        "A human reviewer gave this plain-language nudge:\n"
        f"  \"{nudge}\"\n\n"
        "Edit ONLY the fields the nudge touches. Every other field must stay byte-identical —\n"
        "do not rephrase, reorder, reformat or 'improve' anything the nudge does not mention.\n"
        "Keep edits internally consistent (e.g. if a background color changes, its palette_resolved\n"
        "entry changes too — and that counts as a touched field).\n\n"
        "Return STRICT JSON only (no fences, no prose):\n"
        "{\"changed_fields\": [top-level keys you changed], \"scene\": {the FULL updated tier-3 JSON}}\n\n"
        f"Current tier-3 scene:\n{json.dumps(tier3, ensure_ascii=False, indent=2)}"
    )
    result = json.loads(_anthropic_text("claude-opus-4-5", prompt, max_tokens=8192))
    changed = [str(f).split(".")[0].split("[")[0] for f in result["changed_fields"]]
    new_scene = result["scene"]

    # Validate: untouched fields must be deep-identical. Restore any the model drifted.
    restored = []
    for key in tier3:
        if key not in changed and new_scene.get(key) != tier3[key]:
            new_scene[key] = copy.deepcopy(tier3[key])
            restored.append(key)
    for key in list(new_scene):  # model must not invent or drop top-level keys
        if key not in tier3 and key not in changed:
            del new_scene[key]
            restored.append(key)
    for key in tier3:
        if key not in new_scene:
            new_scene[key] = copy.deepcopy(tier3[key])
            if key not in restored:
                restored.append(key)
    # Drop claimed-changed fields that are actually identical (over-reporting).
    changed = [f for f in changed if new_scene.get(f) != tier3.get(f)]
    return new_scene, changed, restored


def main():
    parser = argparse.ArgumentParser(description="Tier-3 approval loop: author → summarize → nudge → generate.")
    parser.add_argument("--brand", default="taichi")
    parser.add_argument("--out", required=True)
    parser.add_argument("--must-include", default="", help="Semicolon-separated must-include phrases.")
    parser.add_argument("--no-generate", action="store_true", help="Skip image generation on approval.")
    parser.add_argument("--script", default="", help="File of newline-separated canned human responses.")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    must_include = [s.strip() for s in args.must_include.split(";") if s.strip()] or None

    scripted = iter(Path(args.script).read_text(encoding="utf-8").splitlines()) if args.script else None

    def ask(prompt_text: str) -> str:
        if scripted is not None:
            resp = next(scripted, "").strip()
            print(f"{prompt_text}{resp}   [scripted]")
            return resp
        return input(prompt_text).strip()

    session = {"brand": args.brand, "must_include": must_include, "started": _now(), "rounds": []}

    print("=== Step 1: Author tier-3 ===")
    brand_key = load_brand(args.brand)
    tier3 = author_tier3(brand_key, must_include=must_include)
    version = 1
    (out_dir / f"tier3_v{version}.json").write_text(json.dumps(tier3, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved tier3_v{version}.json")

    print("\n=== Step 2: Plain-language summary ===")
    summary = summarize_scene(tier3)
    print(f"\n{summary}\n")
    session["rounds"].append({"version": version, "timestamp": _now(), "summary": summary})

    approved = False
    for round_num in range(1, MAX_NUDGES + 2):
        if round_num > MAX_NUDGES:
            resp = ask("Max nudges reached — approve or abort? > ")
            if resp.lower() in APPROVALS:
                approved = True
            break
        resp = ask("Your call (approve, or describe a change) > ")
        if not resp:
            print("  No response — aborting.")
            break
        if resp.lower() in APPROVALS:
            approved = True
            break
        print(f"\n=== Applying nudge: \"{resp}\" ===")
        new_tier3, changed, restored = apply_nudge(tier3, resp)
        version += 1
        (out_dir / f"tier3_v{version}.json").write_text(
            json.dumps(new_tier3, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Saved tier3_v{version}.json  changed_fields={changed}")
        if restored:
            print(f"  [validation] model drifted untouched fields, restored from v{version-1}: {restored}")
        diff_line = summarize_diff(changed, tier3, new_tier3) if changed else "Updated: nothing — the scene already matched. Everything else unchanged."
        print(f"\n{diff_line}\n")
        session["rounds"].append({"version": version, "timestamp": _now(), "nudge": resp,
                                  "changed_fields": changed, "restored_fields": restored, "diff": diff_line})
        tier3 = new_tier3

    session["approved"] = approved
    session["final_version"] = version
    session["ended"] = _now()
    (out_dir / "session.json").write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved session.json ({len(session['rounds'])} rounds, approved={approved})")

    if not approved:
        print("Not approved — no image generated.")
        return
    print("\n=== Step 3: Assemble final prompt ===")
    final_prompt = assemble_final_prompt(brand_key, tier3)
    (out_dir / "final_prompt.txt").write_text(final_prompt, encoding="utf-8")
    print(f"  Saved final_prompt.txt ({len(final_prompt)} chars)")
    if args.no_generate:
        print("  --no-generate: skipping image generation.")
        return
    print("\n=== Step 4: Generate image via gpt-image-2 ===")
    from generate import generate_variant
    out_png = str(out_dir / "generated.png")
    generate_variant(final_prompt, LOGO_PATH, out_png, size="1536x1024", quality="high")
    print(f"  Saved {out_png}  ({Path(out_png).stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
