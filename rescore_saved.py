#!/usr/bin/env python3
"""rescore_saved.py — DETERMINISTIC honest re-score of the #20 analyzer artifacts that
are ALREADY on disk (NO fresh vision calls). Applies the HARDENED checks to the exact
style_descriptor.json + aligned_prompt.txt that Alec's eye judged, so the honest score
is reproducible and isolates "is the test honest" from "does the vision read vary".

Usage:  .venv/bin/python rescore_saved.py
"""
import json
from pathlib import Path

from test_refstyle_selftest import evaluate, register_inverted

for tag in ("crop1", "crop2"):
    d = Path(f"output/refstyle_{tag}")
    descriptor = json.loads((d / "style_descriptor.json").read_text(encoding="utf-8"))
    prompt = (d / "aligned_prompt.txt").read_text(encoding="utf-8")
    checks = evaluate(prompt, descriptor)
    captured = sum(1 for _, ok in checks if ok)
    print(f"\n=== {tag}  (saved artifact, deterministic) ===")
    for label, ok in checks:
        print(f"  [{'OK ' if ok else 'XX '}] {label}")
    print(f"  CAPTURED {captured}/8 (honest)")
    inv = register_inverted(descriptor, prompt)
    print(f"  REGISTER: {'!! INVERTED (official/authoritative read - danger zone)' if inv else 'OK (playful/prop read held)'}")
