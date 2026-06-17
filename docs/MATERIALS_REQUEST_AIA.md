# Materials Request — AIA Trial Run
**For:** Richard & team (AIA brand)
**From:** Alec (Handyprint)
**Purpose:** Next validation run of the AI brand-asset generation tool. We want to test whether the tool can produce on-brand AIA marketing material from a short brief, and grade it honestly against AIA's real, finished work.

---

## How to read this request

Each item below maps to a specific job in the tool. We've noted **why** we need each one so the right version is easy to pick — and flagged **P0 (essential to run the trial)** vs **P1 (improves accuracy, not blocking)**. If time is tight, the four P0 items alone let us run a real test.

---

## P0 — Essential to run the trial

### 1. Official AIA logo files (clean assets)
- **What:** Vector format preferred — `.AI`, `.EPS`, `.SVG`, or `.PDF`. If vector isn't available, a **high-resolution transparent PNG (≥1500px wide)**.
- **Variants:** all approved versions you'd actually use — primary, white-reverse, horizontal/stacked, and any standard lockups.
- **Why:** The tool feeds the *real* logo into the image generator as a reference. We proved that feeding the actual file reproduces the logo faithfully, while merely *describing* it makes the AI hallucinate a wrong mark. A flat JPEG with a background causes artifacts — vector or transparent PNG is what we need.

### 2. Three to five real, finished AIA marketing pieces (the grading targets)
- **What:** Actual published campaign executions — posters, key visuals, or social creatives. High resolution (print export or full-res digital, **not** a phone photo of a screen).
- **Spread:** ideally across different occasions, e.g. **one product/plan launch, one seasonal/holiday piece, one brand-awareness/evergreen piece.**
- **Why:** This is our answer key. The entire method is "generate, then grade against the *real* thing." Without genuine finished pieces we have nothing honest to measure against. Variety matters because we're testing whether the tool handles different campaign types, not just one.

### 3. The brief or key message behind each of those pieces
- **What:** For each piece in #2, a sentence or two on **what it was for** — the campaign, the occasion, the core message/headline, the target audience. The original creative brief if one exists.
- **Why:** This is the highest-value item and the one most often overlooked. If we know the brief *and* see the finished poster, we can feed the tool the same short intent and compare its output to AIA's real output — a true apples-to-apples test of whether the tool reaches professional quality from a normal brief.

### 4. Latest AIA brand guidelines / VI manual (PDF)
- **What:** The current brand standards document. (We're working from "AIA Brand Standards V2.0" — please confirm that's current or share the latest.)
- **Why:** It's the locked source of truth for exact colors, fonts, logo rules, and motifs. We extract these automatically; we just need to be sure we're on the current version.

---

## P1 — Improves accuracy, not blocking

### 5. Brand font files — **UPGRADED TO P0** (June 11)
- **What:** The actual licensed font files the VI mandates. From AIA Brand Standards V2.0 these are, specifically:
  - **AIA Everest** (English custom font) — OTF, **all weights** (Thin → Bold)
  - **汉仪甄选37款字体库** (the licensed HanYi library, license valid to 2027-07-31 per the VI) — at minimum the display faces used in promotional work, e.g. **汉仪雅酷黑 (55/85/95简)**, 汉仪元隆黑, 汉仪玄宋, **in every licensed weight** (each weight is a separate file)
- **Why this is now P0:** the 合规字体 (compliant font) requirement on live tasks cannot be met any other way. Our generator can *approximate* the look, but compliance means the licensed typeface is actually used — we composite real text with the real files. We tested with a system fallback font and the visual register is wrong (too thin for call-to-action material); only the licensed files close this. Handyprint operates under the partner font license agreement, so sharing the files is covered.
- **Important: send every weight.** A font family ships as multiple files (e.g. 雅酷黑-55简 / -85简 / -95简 are three files). Headlines need the heavy weights; body text the regular ones. "The font" usually means 3–6 files per family.

### 6. A sample of the real imagery library
- **What:** A handful of the actual photography/illustration AIA uses — the lifestyle/people shots, the layered-mountain motif renders, signature visual assets.
- **Why:** AIA's "hero" isn't a physical product, it's people and the mountain motif. Real examples of what AIA considers on-brand imagery let the tool stage scenes the way AIA actually does, instead of inventing generic stock looks.

### 7. A "best vs off-brand" gut-check (optional, very helpful)
- **What:** If easy — one or two examples your team considers *excellent* on-brand work, and (if you're willing) one that felt *off*.
- **Why:** It calibrates our quality bar to AIA's eye, not ours. It tells the tool what "good" means *to you*.

---

## What we already have (no need to resend)
- AIA Brand Standards V2.0 PDF (118 pages) — extracted colors: AIA Red #D31145, Charcoal #333D47, White; slogan 健康长久好生活; mountain-peak motif.
- Logo *appearance* documented (red circle, mountain peaks above AIA letters) — but **we need the actual file (#1 above)**, not the description.

## What we'll send back
After the run we'll share the generated pieces side-by-side with your real ones, plus an honest per-piece score and notes on where the tool matched and where it fell short. This is a test, not a pitch — the misses are as useful to us as the hits.
