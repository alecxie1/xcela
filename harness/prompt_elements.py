#!/usr/bin/env python3
"""harness/prompt_elements.py — render-dialect-neutral mandatory/forbidden prompt clause.

Feature 002. Stdlib-only, ASSET-PROFILE-agnostic (no flat_graphic / die-cut assumptions), so the
SAME verbatim injection is reusable by the kit prompt now and the future photo/poster assembler
(D8). The brief's `mandatory_elements` / `forbidden_elements` pass through VERBATIM (FR-003/FR-004):
each item is placed exactly as the human typed it, never rephrased, reordered, or interpreted (so
`设计两种样式` is rendered as the instruction it is, never expanded into N generations).
"""


def elements_clause(mandatory, forbidden) -> str:
    """Build a prompt clause from the campaign mandatory/forbidden elements. Empty inputs -> empty
    string (nothing fabricated). Items are emitted VERBATIM."""
    mand = [str(m).strip() for m in (mandatory or []) if str(m).strip()]
    forb = [str(f).strip() for f in (forbidden or []) if str(f).strip()]
    parts = []
    if mand:
        parts.append("DESIGN REQUIREMENTS (the sign MUST satisfy each of these as a design / "
                     "illustration instruction — DEPICT or DO what each one describes; do NOT render "
                     "the instruction text itself as words anywhere on the sign): "
                     + "; ".join(mand) + ".")
    if forb:
        parts.append("FORBIDDEN elements (none of these may appear): " + "; ".join(forb) + ".")
    return "\n".join(parts)


def has_conflict(mandatory, forbidden):
    """Return the set of items that are BOTH required and forbidden (a brief contradiction the human
    must resolve, constitution V honest null). Empty set when there is no conflict."""
    mand = {str(m).strip() for m in (mandatory or []) if str(m).strip()}
    forb = {str(f).strip() for f in (forbidden or []) if str(f).strip()}
    return mand & forb
