#!/usr/bin/env python3
"""
Blind A/B test: Opus 4.8 SOLO vs MoA FUSION on a real open question from the
Handyprint design-tool SYSTEM_MAP (random-walk characterization).

Fairness design:
- Same question, same max reasoning effort (xhigh) for both arms.
- Solo arm = Opus 4.8 alone. Fusion arm's AGGREGATOR is also Opus 4.8, so the
  only variable is "one model vs panel+synthesis."
- Outputs randomly assigned to A/B; mapping written to a SEALED file the human
  does not read until after judging.
"""
import asyncio, json, os, random, time, sys
sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))
os.chdir(os.path.expanduser("~/.hermes/hermes-agent"))

from tools.openrouter_client import get_async_client
from agent.auxiliary_client import extract_content_or_reasoning
from tools.mixture_of_agents_tool import mixture_of_agents_tool

QUESTION = """Context: I'm building a tool that generates marketing design drafts using gpt-image-2 (a text-to-image diffusion model). I want to add a "multi-variation weight-honing" loop: generate 4 drafts with DIFFERENT prompt-weight configurations, a human picks the best, and the system nudges its weights toward the winner so future drafts inherit the learned preference.

The blocker: before this loop is legitimate, I must characterize the random-walk problem — separate how much output variation comes from my PROMPT/WEIGHT changes vs. how much is just the diffusion model's inherent SAMPLING NOISE (same prompt, different seed -> different image). If I skip this, I might "learn" a weight change that actually did nothing: the variation I saw was just noise, and I'd be fitting to randomness.

Design a concrete, falsifiable experimental protocol to characterize this. Tell me EXACTLY what to generate, what to measure, and what decision rule tells me "this weight dimension produces real, repeatable change above the noise floor" vs "this is indistinguishable from sampling noise." Assume I can generate images via API (I can set or vary seeds) and have standard image-similarity tools available (embeddings, SSIM, color histograms, etc.). Be specific enough that I could implement it this week. Call out the failure modes that would make my conclusion wrong."""

OUT = os.path.expanduser("~/workspace/handyprint-design-tool/moa_test")
os.makedirs(OUT, exist_ok=True)


async def opus_solo(prompt: str) -> str:
    params = {
        "model": "anthropic/claude-opus-4.8",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 32000,
        "temperature": 0.4,  # match aggregator temp for fairness
        "extra_body": {"reasoning": {"enabled": True, "effort": "xhigh"}},
    }
    r = await get_async_client().chat.completions.create(**params)
    return extract_content_or_reasoning(r)


async def main():
    print("Running both arms in parallel...", flush=True)
    t0 = time.time()
    solo_task = opus_solo(QUESTION)
    fusion_task = mixture_of_agents_tool(QUESTION)
    solo_text, fusion_json = await asyncio.gather(solo_task, fusion_task)
    fusion = json.loads(fusion_json)
    elapsed = round(time.time() - t0, 1)

    if not fusion.get("success"):
        print("FUSION FAILED:", fusion.get("error"))
        return
    fusion_text = fusion["response"]

    # Random blind assignment
    arms = [("SOLO_opus48", solo_text), ("FUSION_opus48+gpt55", fusion_text)]
    random.shuffle(arms)
    labels = ["A", "B"]
    mapping = {}
    for label, (arm_id, text) in zip(labels, arms):
        with open(f"{OUT}/answer_{label}.md", "w") as f:
            f.write(text)
        mapping[label] = arm_id

    with open(f"{OUT}/SEALED_mapping.json", "w") as f:
        json.dump({"mapping": mapping, "elapsed_sec": elapsed,
                   "solo_chars": len(solo_text), "fusion_chars": len(fusion_text),
                   "fusion_models": fusion["models_used"]}, f, indent=2)

    print(f"DONE in {elapsed}s")
    print(f"  answer_A.md  ({len(arms[0][1])} chars)")
    print(f"  answer_B.md  ({len(arms[1][1])} chars)")
    print("  SEALED_mapping.json written (do not open until judged)")


asyncio.run(main())
