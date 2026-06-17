# Automation Gap Analysis — AIA Live Trial (2026-06-10)

**The realization (Alec's, end of session):** the first real trial run reveals how much
**Hermes did manually** that the *tool* does not yet automate. The live AIA sign task was
done almost entirely by Hermes-the-orchestrator — our proven component (`scene_author.py`)
was **bypassed**. This file is the honest inventory of that gap = tomorrow's build roadmap.

---

## What Hermes did BY HAND in the AIA run (and the tool does NOT do)

| # | Manual step Hermes performed | Tool status | What we'd need to build |
|---|---|---|---|
| 1 | **Brief intake** — read the Chinese WeChat-style request, saw "6个手举牌", parsed specs (60×40cm, 合规字体), picked task #1 | none | A brief parser: messy Chinese marketing request → structured Tier-2 intent + task list |
| 2 | **Reference-image analysis** — vision_analyze forensic breakdown of the 参考图 into style tokens (flat design, red+gold, money-bag icon, rounded cards) | none | A reference-style analyzer (distinct from VI-PDF analysis — this reads a *finished design*, not a brand book) → tokens that feed the scene-author |
| 3 | **Prompt authoring** — HAND-WROTE both gpt-image-2 prompts | ⚠️ `scene_author.py` exists & proven, but was **NOT USED** | Wire scene_author into the live path; extend it beyond food-poster to **signage/graphic** asset types |
| 4 | **Visual-metaphor invention** — "money bag in cupped hands", "shield over home + heart" | partial (scene_author could, untested on this) | Test scene_author on metaphor-driven slogans, not just product scenes |
| 5 | **Two-style differentiation** — designed the axes (white-card vs red-dominant; 守钱 vs 护家 metaphor) | none | A "give me N distinct directions" mode (not N random draws — deliberate variation) |
| 6 | **Asset assembly** — chose logo + reference, ordered them into images.edit | ⚠️ config reference-selection is **STUBBED** | De-stub reference selection in the harness |
| 7 | **Grading** — vision_analyze orchestration + honest human-calibrated re-grade | partial | (Known: VLM grader over-scores; needs human anchor) |
| 8 | **Font-compliance awareness** — flagged 用友邦合规字体 gap | none | The real-font compositing step (the known architecture boundary) |

---

## The one-line takeaway
`scene_author.py` proved the **prompt-authoring** box can be automated — but the live task showed
that box sits inside a **much larger manual pipeline** (brief intake → reference analysis →
asset selection → multi-task batching → compositing) that is still 100% Hermes. **The tool
automates one link of a chain Hermes is still hand-running end-to-end.**

---

## Tomorrow (2026-06-10 + 1)
1. Run remaining 4 sign tasks (#2 远离非法金融抵制高息诱惑, #3 珍惜一生血汗远离非法金融,
   #4 金融传销/虚拟货币骗局 分别画叉, #5 非法集资/网络金融诈骗 分别画叉) — measure pipeline hit-rate.
2. **Use scene_author.py on at least one of them** — close the "Hermes bypassed the tool" gap; see if the
   tool-authored prompt matches the hand-authored quality on a signage task.
3. Build the highest-leverage missing link (likely #1 brief-intake or #2 reference-analyzer).
4. Font-compliance compositing step (the deliverable-vs-draft boundary).

## Today's deliverables (done)
- `output/aia_sign1_qiandaizi.png` (Style 1, ~8, text perfect)
- `output/aia_sign1_qiandaizi_style2.png` (Style 2, ~8, text perfect, genuinely distinct)
- Approval loop built + verified: `harness/approve.py`, `output/approve_run1/`, `output/approve_run2/`
