#!/usr/bin/env python3
"""register/blind_score.py — blind VLM scoring on the Step-0 register rubric.

Scores image(s) on FORMALITY / PLAYFULNESS (the two axes Step-0 showed a VLM
discriminates register on; energy was dropped as a decoy) plus GRAB (the target
outcome: "would someone hold this for a photo?"). The scorer gets the image and
the rubric ONLY — no brand context, no group membership, no expected answer.

Usage:
  .venv/bin/python register/blind_score.py --image output/eventprop_sign1/final.png --n 3
"""

import argparse
import base64
import json
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
from runtime_env import load_runtime_env  # noqa: E402  (018: env > .env > legacy ~/.hermes)
load_runtime_env()

RUBRIC_PROMPT = (
    "You are scoring a single graphic-design image, completely blind — you have no context "
    "about who made it, for which brand, or why. Score it on three 0-10 axes:\n"
    "  formality: 0 = casual/playful register, 10 = official/corporate register\n"
    "  playfulness: 0 = serious/sober, 10 = fun/whimsical\n"
    "  grab: would someone at an event/festival want to pick this up, hold it, and pose for a "
    "photo with it? 0 = nobody would, 10 = irresistibly grabbable photo-prop\n"
    "Judge from the pixels only: shapes, color, type, icons, overall atmosphere.\n"
    "Output STRICT JSON only, no fences, no extra text:\n"
    '{"formality": <int>, "playfulness": <int>, "grab": <int>, "rationale": "<one sentence>"}'
)

MODELS = ["claude-opus-4-5", "claude-sonnet-4-6"]


def score_once(image_path: str) -> dict:
    import anthropic
    data = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
    media = "image/png" if image_path.lower().endswith("png") else "image/jpeg"
    client = anthropic.Anthropic()
    last_exc = None
    for model in MODELS:
        try:
            msg = client.messages.create(
                model=model, max_tokens=512,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}},
                    {"type": "text", "text": RUBRIC_PROMPT},
                ]}],
            )
            raw = msg.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rsplit("```", 1)[0].strip()
            out = json.loads(raw)
            out["_model"] = model
            return out
        except Exception as exc:  # noqa: BLE001 — fall through the model chain
            last_exc = exc
            print(f"  [warn] {model} failed: {exc}", file=sys.stderr)
    raise RuntimeError(f"all models failed: {last_exc}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Blind-score image(s) on the Step-0 register rubric.")
    ap.add_argument("--image", action="append", required=True, help="image path (repeatable)")
    ap.add_argument("--n", type=int, default=3, help="independent calls per image (default 3)")
    ap.add_argument("--out", default="", help="optional JSON output path")
    args = ap.parse_args()

    results = {}
    for img in args.image:
        runs = []
        for i in range(args.n):
            s = score_once(img)
            runs.append(s)
            print(f"{Path(img).name} call {i+1}: formality={s['formality']} "
                  f"playfulness={s['playfulness']} grab={s['grab']} [{s['_model']}]\n"
                  f"    {s.get('rationale','')}")
        mean = {k: sum(r[k] for r in runs) / len(runs) for k in ("formality", "playfulness", "grab")}
        results[img] = {"runs": runs, "mean": mean}
        print(f"{Path(img).name} MEAN: formality={mean['formality']:.2f} "
              f"playfulness={mean['playfulness']:.2f} grab={mean['grab']:.2f}\n")

    if args.out:
        Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
