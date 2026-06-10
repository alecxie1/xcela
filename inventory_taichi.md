# Page-by-Page Content Inventory — 太极堡 (TAICHI BURGER) VI Manual

**Source:** 32 pre-rendered page images at `/tmp/inv_taichi/page_01.png` … `page_32.png`
**Document:** 太极堡品牌视觉识别系统管理手册 (Taichi Burger Brand Visual Identity System Management Manual)
**Method:** Each page read via vision OCR. Where vision OCR disagreed with the **human-verified answer key** (`answer_keys/taichi.json`, verified by Alec 2026-06-05), the human-verified value is used and the discrepancy is flagged. OCR on small Chinese body text was unreliable in several places — those are explicitly marked "OCR uncertain."

**Content-type legend:** COVER, TOC, BRAND_STORY, LOGO_CONSTRUCTION, LOGO_USAGE_RULES, LOGO_COLOR_VARIANTS, COLOR_SPEC, TYPOGRAPHY, MOTIF_PATTERN, IMAGERY_EXAMPLES, APPLICATIONS_MOCKUP, DISCOURSE_NARRATIVE, OTHER (section divider).

**Generation-relevance legend (for GPT Image 2):**
- **HIGH** = changes pixels the model produces: exact colors, imagery style, logo appearance, motif shapes.
- **MEDIUM** = somewhat useful: color-on-background pairings, logo construction/lockups.
- **LOW** = layout/governance rules an image generator cannot honor: clear-space in mm, min-size in px, improper-use prohibitions, pure cultural-narrative text.

---

## Full Inventory Table

| Pg | Section title (CN / EN) | Content type | Exact printed values | What the page shows | Gen-relevance |
|----|-------------------------|--------------|----------------------|---------------------|---------------|
| 01 | 太极堡品牌视觉识别系统管理手册 / TAICHI BURGER | COVER | — | Front cover. Black ground with large burgundy organic curves; white "TAICHI BURGER" wordmark; red circular logo with white yin-yang/swirl mark; "太极堡" below. | MEDIUM (logo appearance + color mood) |
| 02 | 目录 / CONTENTS | TOC | Page refs 04–31 | Bilingual table of contents listing 6 chapters: 图形标志 (Graphic Logo), 标志应用 (Logo Application), 品牌话语 (Brand Discourse), 品牌专用字体 (Typography), 品牌色彩 (Brand Colors), 品牌纹样 (Brand Patterns). | LOW |
| 03 | 图形标志 / BRAND LOGO | OTHER (section divider) | refs 04 总览, 05 标志图形, 06 标准字, 07 标志组合, 08 标志英文组合 | Chapter-1 divider, black ground, lists subsections 04–08. | LOW |
| 04 | 总览 / Overview | LOGO_CONSTRUCTION | — | "太极堡品牌识别要素是什么" — defines 3 identity elements: 图形标志 (graphic mark), 品牌名称 (brand name), 标准组合 (standard combination). Shows the red circular logo + bilingual wordmark variations. | MEDIUM |
| 05 | 标志图形 / LOGO | LOGO_CONSTRUCTION | — | Explains the graphic mark meaning + 3 usage modes (standalone logo / standalone graphic / combined with typeface). Shows the red circular badge with white animal/swirl silhouette in negative space. | MEDIUM (logo appearance) |
| 06 | 标准字 / (Wordmark) | TYPOGRAPHY | — | Standard wordmark page: 中文标准字 "太极堡" (heavy bold), 英文标准字 "TAICHI BURGER" (sans-serif), and the bilingual lockup. Monochrome on white. | MEDIUM (wordmark style) |
| 07 | 标志组合 / Logo Combination | LOGO_CONSTRUCTION | — | Bilingual logo lockups: 竖式组合(双语版) vertical and 横式组合(双语版) horizontal arrangements of mark + TAICHI BURGER + 太极堡. No measurements printed on this page. | MEDIUM |
| 08 | 标志英文组合 / Logo Combination | LOGO_CONSTRUCTION | — | English-only logo lockups: 立式组合(英文版) vertical and 横式组合(英文版) horizontal + compact variant. Red mark, black "TAICHI BURGER", white ground. No numeric measurements. | MEDIUM |
| 09 | 标志应用 / IN USE | OTHER (section divider) | refs 10 最小尺寸, 11/12 安全距离, 12/13 标志颜色, 13/14 空间应用, 14/15 背景, 15/16 标志错误使用 | Chapter-2 divider, black ground. (TOC numbering and divider numbering differ slightly; divider lists items 10–16.) | LOW |
| 10 | 最小尺寸 / Minimum Scale | LOGO_USAGE_RULES | Min sizes in **mm**: 25mm, 46mm, 50mm, 20mm, 46mm; one compact variant 16mm | Print minimum-size rules for each lockup variant. **mm clear/min-size = NOT honorable by an image generator.** | LOW |
| 11 | 最小尺寸 / Minimum Scale | LOGO_USAGE_RULES | Min widths in **px**: 115px, 80px, 220px, 240px (screen-display minimums) | Screen/digital minimum-size rules for the lockups. Pixel governance, not pixel content. | LOW |
| 12 | 安全距离 / Safe Distance | LOGO_USAGE_RULES | Clear space expressed as proportional unit **"X"** on all 4 sides (no absolute mm/px) | Clear-space / safe-distance diagrams: dotted bounding boxes around 4 logo variants, gray protected zones, "X" margin on each side. **Clear-space rule = not honorable.** | LOW |
| 13 | 标志颜色 / Logo Color | LOGO_COLOR_VARIANTS | Logo red ≈ primary VERMILION (see p24 for exact: `D70321`) | 常规应用 (standard, red mark + black text on white) vs 反白应用 (reverse, white mark on red/dark). Color-on-background pairing guidance. | MEDIUM |
| 14 | 空间应用 / Space Applications | APPLICATIONS_MOCKUP | — | 空间特殊用法: logo rendered for spatial/3D use. Examples: 金属浮雕 (metal relief, gold/bronze emboss) and 镜空玻璃贴 (mirror glass decal). Shows material/finish treatments. | MEDIUM (material/finish style) |
| 15 | 背景 / Background | LOGO_COLOR_VARIANTS | Background palette = brand colors **excluding red** | Logo-on-background pairing matrix: white→red mark/black text; black→white mark; gold/tan→red mark/black text; red→white mark; dark brown→white mark; plus a photographic (food) background. Rule: keep primary colors visible; don't put red mark on red. | **HIGH** (explicit color-on-background pairings = direct generation guidance) |
| 16 | 标志错误使用示意 / Logo Improper Use | LOGO_USAGE_RULES | — | 2×4 grid of 8 prohibited treatments: distort proportions, separate mark from text, alter the mark, rotate/flip, add elements, move text, recolor (shows blue), rescale elements. Pure prohibitions. | LOW |
| 17 | 品牌话语 / BRAND DISCOURSE | OTHER (section divider) | refs 18 品牌价值观主张, 19 品牌品类, 20 品牌广告语 | Chapter-3 divider, black ground. | LOW |
| 18 | 品牌价值观主张 / Brand Value Proposition | DISCOURSE_NARRATIVE | English tagline **"Two Worlds ❤ One Dream"** (red heart replaces the "o" in "One") | Employee-first values narrative (respect/grow employees → serve customers). Center tagline "Two Worlds One Dream". | LOW (narrative text); tagline itself is MEDIUM if used as on-image text |
| 19 | 品牌品类 / Brand Category | DISCOURSE_NARRATIVE | Category = **东方汉堡** (Oriental Burger) | "品类是什么 / 品类名称" — defines the brand category. Large center characters print the category. **NOTE: vision OCR misread center as "索芳汉堡"; human-verified ground truth is 东方汉堡.** | LOW (text); category value already extracted |
| 20 | 品牌广告语 / Brand Slogan | DISCOURSE_NARRATIVE | Slogan = **手作多汁，东方汉堡** ("Handmade & juicy, Oriental burger") | Explains slogan importance; center prints the slogan in large bold type. | LOW (text); slogan value already extracted |
| 21 | 品牌专用字体 / TYPOGRAPHY | OTHER (section divider) | ref 22 品牌字体库 | Chapter-4 divider, black ground. | LOW |
| 22 | 品牌字体库 / Brand Typeface | TYPOGRAPHY | CN display: **锦华明朝体**; CN body: **汉仪旗黑** (weights 55s / 65s / 75s); EN: **Helvetica** (Thin/Light/Regular/Medium/Bold). Specimen text: 手作多汁，东方汉堡 / TWO WORLDS ONE DREAM | Font library specimen sheet. **NOTE: vision OCR read display font as "绸华明朝体"; human-verified ground truth is 锦华明朝体.** | MEDIUM (fonts) — already extracted |
| 23 | (Typography continued — see note) | TYPOGRAPHY | — | NOTE: TOC lists only `22 品牌字体库` for the typography chapter; the page rendered as page_23 appears to be a continuation/specimen of the font section. OCR did not surface distinct new values. Treat as low-novelty typography spread. | LOW |
| 24 | 品牌标准色 / Primary Color | COLOR_SPEC | **银朱红 / VERMILION** — RGB **215/3/33**, HTML **D70321**, CMYK **0/97/100/3**, PANTONE **2035C** | Primary brand color swatch + color-system note (RGB screen / CMYK print / Pantone spot). **NOTE: vision OCR read "D73321 / 215/33/33"; human-verified ground truth is 215/3/33 = D70321.** | **HIGH** (exact primary color) — already extracted |
| 25 | 品牌辅助色 / Secondary Color | COLOR_SPEC | **大地金/EARTH GOLD** RGB 215/165/105, HTML D7A569, CMYK 5/31/63/5, PANTONE 7509C · **墨澜黑/INK BLACK** RGB 0/0/0, CMYK 60/40/40/100, Pantone n/a · **珍珠白/PEARL WHITE** RGB 236/220/200, HTML ECDCC8, CMYK 10/17/21/0, PANTONE 9182C | Three auxiliary color swatches with full specs. **NOTE: vision OCR garbled several values (e.g. "TS90C", "D7A169", "E3D6DC"); values above are human-verified ground truth.** | **HIGH** (exact secondary palette) — already extracted |
| 26 | 品牌纹样 / BRAND PATTERN | OTHER (section divider) | refs 27 纹样, 28 四方连续纹样, 29 纹样应用规范, 30 纹样错误使用, 31 空间装置应用 | Chapter-6 divider, black ground. | LOW |
| 27 | 纹样 / (Pattern) | MOTIF_PATTERN | Motif names: **八角 · 花椒 · 桂皮 · 胡椒 · 香叶** (five spices) | Five individual decorative motifs shown as black silhouettes on white — symmetric, traditional/Chinese ornamental style, each named after a spice. **NOTE: vision OCR read one as "花瓣"; human-verified motif set is 八角/花椒/桂皮/胡椒/香叶.** | **HIGH** (motif shapes + style) — already extracted |
| 28 | 四方连续纹样 / Four-way Continuous Pattern | MOTIF_PATTERN | — | Seamless tiling repeat built from the motifs: four-petal flowers, 45° diamonds with lattice/star fills, small star/plus accents; monochrome charcoal on cream, woodblock/engraving look. | **HIGH** (pattern tiling style) |
| 29 | 纹样应用规范 / Pattern Usage Guidelines | MOTIF_PATTERN / LOGO_USAGE_RULES | Footnote: 灰色部分为建议裁剪部分 (gray = suggested trim/crop area) | Two demo boxes showing approved pattern density/spacing for application; gray areas mark trim boundaries. Mix of governance (spacing) + style reference. | MEDIUM (shows applied pattern density/style) |
| 30 | 纹样错误使用 / Pattern Misuse | MOTIF_PATTERN / LOGO_USAGE_RULES | — | 3 prohibited pattern treatments: don't arbitrarily alter the motif, don't flatten to solid color, don't randomly rotate. Prohibitions. | LOW |
| 31 | 空间装置应用 / Space Installation Application | APPLICATIONS_MOCKUP / IMAGERY_EXAMPLES | — | Spatial-installation textures/finishes: leather grain, automotive-paint gloss, colored-glaze, dragon sculpture in red+gold; large red gradient backdrop with pink cloud/flower motifs + diamond pattern; 6×6 motif grid. Rich luxury/ornamental Chinese aesthetic mockup. OCR of the materials list was partly unreliable. | **HIGH** (imagery style, color+finish mood, applied motif look) |
| 32 | Two Worlds ❤ One Dream | COVER (back/closing) | English tagline "Two Worlds One Dream" (red heart for the "o" in One) | Closing page: black ground, white tagline with red heart, red circular logo + TAICHI BURGER + 太极堡 below. (Vision guessed "front cover," but by position it is the closing/back cover.) | MEDIUM (logo + tagline as on-image text) |

---

## Summary

### Pages containing generation-HIGH content
These directly change the pixels GPT Image 2 would produce:

- **p15 — 背景 / Background:** explicit **logo-on-background color pairings** (which brand color goes on which, red-on-red forbidden). The most generation-relevant "rules" page in the book.
- **p24 — 品牌标准色:** exact **primary color** 银朱红 / VERMILION = `D70321` (RGB 215/3/33). *Already extracted.*
- **p25 — 品牌辅助色:** exact **secondary palette** EARTH GOLD `D7A569`, INK BLACK `000000`, PEARL WHITE `ECDCC8`. *Already extracted.*
- **p27 — 纹样:** the **five named motifs** (八角/花椒/桂皮/胡椒/香叶) and their silhouette style. *Already extracted.*
- **p28 — 四方连续纹样:** the **seamless tiling style** (how motifs repeat — density, charcoal-on-cream, engraving look).
- **p31 — 空间装置应用:** **applied imagery / material-finish style** — red gradient + cloud/flower motifs, gold-and-red ornamental luxury aesthetic, embossed/glazed finishes.

Secondary (MEDIUM) generation value: p01/p32 (logo+mood), p04–08 (logo construction/lockups), p13 (standard vs reverse color use), p14 (material finishes), p22 (fonts), p29 (applied pattern density).

LOW / not generation-honorable (confirming the user's hypothesis about pp.10–12, 16, 30): minimum-size mm (p10), minimum-size px (p11), clear-space "X" units (p12), logo improper-use grid (p16), pattern improper-use grid (p30), and the pure narrative pages (p18–20). An image generator cannot honor "25mm min size" or "X clear space," and prohibition grids describe what NOT to draw rather than supplying style.

### Recommended NEW extractable fields (beyond color / fonts / motifs / slogan / category)
Ranked by generation impact:

1. **`color_on_background_pairings` (from p15) — highest new value.** A small table of allowed background→{mark color, text color} pairs, plus the explicit constraint "never place the red mark on a red background." This is the one *rule* in the manual that is genuinely generation-honorable and would stop GPT Image 2 from producing red-on-red or low-contrast lockups.
2. **`pattern_tiling_style` (from p28/p29):** describe the four-way seamless repeat — motif density, charcoal-on-cream/monochrome rendering, woodblock/engraving texture. Lets the generator reproduce the surface pattern, not just isolated motifs.
3. **`imagery_style` / `applied_aesthetic` (from p31, supported by p14):** a style descriptor — "luxury Chinese ornamental: red+gold, gloss automotive paint, colored-glaze, embossed metal relief, dragon/cloud/flower ornament." Strong steer for background and mood.
4. **`logo_appearance` structured descriptor (from p01/p05/p13):** circular badge, vermilion red field, white negative-space animal/swirl silhouette, yin-yang/rotational feel, plus the standard vs reverse (white-on-red) variants. Richer than the current subjective `logo` rubric and usable as a generation prompt fragment.
5. **`tagline_en` (from p18/p32):** "Two Worlds One Dream" (heart replaces "o" in One). Distinct from the Chinese slogan; useful when the generator needs on-image English copy.
6. **`material_finishes` (from p14/p31):** enumerated finishes — metal relief, mirror-glass decal, gloss car-paint, colored glaze. Useful for product/packaging/signage mockup generation.
7. **`logo_lockups` (from p07/p08):** which lockups exist (vertical/horizontal, bilingual/English-only) — MEDIUM value; helps pick a composition but less about pixels than the above.

**Explicitly NOT recommended for extraction** (cannot influence generation): clear-space "X" units (p12), minimum sizes in mm/px (p10–11), and the improper-use prohibition grids (p16, p30). These are governance/QA rules, valuable to a human designer but inert to an image-generation model.

### Data-quality caveats
- Vision OCR on small Chinese body text and on dense color-spec numerals was **unreliable**. Several raw OCR readings were wrong and have been corrected against the human-verified `answer_keys/taichi.json`: primary color (`D70321`, not `D73321`), the category/center glyphs on p19 (`东方汉堡`, not "索芳汉堡"), the display font (`锦华明朝体`, not "绸华明朝体"), and one motif (`花椒`, not "花瓣").
- TOC numbering (p02) and the chapter-divider numbering (p09) differ by one in a couple of spots; the table notes this. Page_23 appears to be a typography-section continuation with no distinct new printed values surfaced by OCR — flagged as uncertain rather than invented.
