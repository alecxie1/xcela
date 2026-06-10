"""
assemble_prompt.py — THE EXPERIMENT.

A pure function: render(template, fields) -> prompt string.
No branching on judgment. No brand knowledge outside the answer key.
Every template slot must trace to a field in the answer key (tripwire-tested).

The function also returns the field->slot binding WITH PROVENANCE, so the
manifest records how much of the prompt rests on low-confidence fields.
"""

import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    undefined=StrictUndefined,   # missing field = hard error, not silent blank
    trim_blocks=True,
    lstrip_blocks=True,
)


def _rgb_to_hex(rgb):
    r, g, b = rgb[:3]
    return "%02X%02X%02X" % (int(r), int(g), int(b))


def build_context(answer_key: dict) -> tuple[dict, dict]:
    """Pure dict assembly from the answer key. Returns (context, provenance_log).

    provenance_log maps each template slot -> {value, source, confidence, needs_review}
    so the manifest can quantify how much of the prompt is hard fact vs soft guess.
    """
    f = answer_key["fields"]
    ctx = {}
    prov = {}

    def take(slot, value, *, source, confidence=None, needs_review=False):
        ctx[slot] = value
        prov[slot] = {"value": value, "source": source,
                      "confidence": confidence, "needs_review": needs_review}

    take("brand_name_cn", f["brand_name_cn"]["value"], source="objective_printed", confidence=1.0)
    take("brand_name_en", f.get("brand_name_en", {}).get("value"), source="objective_printed", confidence=1.0)
    take("category", f.get("category", {}).get("value", ""), source="objective_printed", confidence=1.0)
    take("slogan", f.get("slogan", {}).get("value"), source="objective_printed", confidence=1.0)

    colors = []
    for c in f.get("colors", {}).get("items", []):
        hexv = c.get("printed_html") or (_rgb_to_hex(c["rgb"]) if c.get("rgb") else None)
        if not hexv:
            continue
        colors.append({
            "role": c.get("role", "secondary"),
            "name_cn": c.get("name_cn") or "",
            "name_en": c.get("name_en"),
            "hex": hexv.upper().lstrip("#"),
            "pantone": c.get("pantone"),
        })
    take("colors", colors, source="objective_printed", confidence=1.0)

    motifs_field = f.get("motifs", {})
    take("motifs", motifs_field.get("items", []), source=motifs_field.get("type", "objective_printed"), confidence=0.95)

    img = f.get("imagery_style", {})
    take("imagery_description", img.get("description"),
         source="vision_model" if img.get("_status") == "candidate_unverified" else "verified",
         confidence=0.6 if img.get("_status") == "candidate_unverified" else 0.9,
         needs_review=img.get("_status") == "candidate_unverified")

    tone = f.get("tone", {})
    take("tone_descriptors", tone.get("descriptors", []),
         source="vision_model" if tone.get("_status") == "candidate_unverified" else "verified",
         confidence=0.6 if tone.get("_status") == "candidate_unverified" else 0.9,
         needs_review=tone.get("_status") == "candidate_unverified")

    return ctx, prov


def assemble_prompt(answer_key: dict, asset_type: str, variant_modifier: str) -> tuple[str, dict]:
    """Pure function. Same inputs -> same prompt, always."""
    ctx, prov = build_context(answer_key)
    ctx["asset_type"] = asset_type
    ctx["variant_modifier"] = variant_modifier
    template = _env.get_template("poster.txt.j2")
    prompt = template.render(**ctx)
    # collapse blank-line runs from optional blocks
    lines = [ln.rstrip() for ln in prompt.splitlines()]
    out, prev_blank = [], False
    for ln in lines:
        blank = (ln == "")
        if not (blank and prev_blank):
            out.append(ln)
        prev_blank = blank
    return "\n".join(out).strip(), prov


if __name__ == "__main__":
    import sys
    key_path = sys.argv[1] if len(sys.argv) > 1 else "answer_keys/aia.json"
    key = json.loads(Path(key_path).read_text(encoding="utf-8"))
    prompt, prov = assemble_prompt(key, "wide horizontal poster", "hero composition, generous negative space.")
    print(prompt)
    print("\n--- provenance ---")
    for slot, p in prov.items():
        flag = " ⚠️" if p["needs_review"] else ""
        print(f"  {slot}: source={p['source']} conf={p['confidence']}{flag}")
