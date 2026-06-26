"""tests_support/make_pdf.py — synthetic multi-page PDF fixture for the 005 free tests.

Builds a small PDF in a temp dir from per-page text via PyMuPDF (fitz), so the page-finder and
extractor-reconcile tests run with NO external file and NO model. CJK is written with fitz's built-in
`china-s` CJK font so the text layer round-trips (get_text returns the characters).
"""

import fitz


def make_pdf(pages, path):
    """pages: list[str], one block of text per page. Writes a PDF to `path`. Returns `path`."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        # china-s carries Latin + CJK glyphs, so a single font handles "#31B4E7" and "汉仪旗黑".
        page.insert_text((72, 72), text, fontname="china-s", fontsize=14)
    doc.save(str(path))
    doc.close()
    return str(path)


# The canonical fixture the 005 tests assert against:
#   page 1 (1-indexed): mentions "color" in prose, NO hex token  -> must NOT be the color page
#   page 2: prints a real hex token "#31B4E7"                    -> the color page
#   page 3: a typography page with font-name tokens              -> the fonts page
DEFAULT_PAGES = [
    "Brand color palette and color usage guidelines for the brand.",
    "主色 Primary color\n#31B4E7\nRGB 49 180 231",
    "品牌专用字体 Typography\n汉仪旗黑\nHelvetica Neue Bold",
]


def make_default(path):
    return make_pdf(DEFAULT_PAGES, path)
