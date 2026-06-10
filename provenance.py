"""
Provenance wrapper — Step 3 of the re-architecture.

Every extracted leaf value carries HOW it was obtained and HOW trustworthy it is,
so the pipeline can quarantine the uncertain minority instead of silently shipping
guesses. Matches brand_dna_schema.json's field_wrapper_convention.

    { "value": <any>, "source": <enum>, "confidence": 0.0-1.0,
      "evidence": {...}, "needs_review": bool }

source enum:
  text_layer       parsed from the PDF text layer (exact, but can be garbled)
  ocr_caption      OCR of printed caption text (exact spec value)
  ocr_rgb_derived  hex derived from an OCR'd RGB triple (no hex printed)
  pixel_cluster    sampled/clustered from rendered pixels (approximate)
  vision_model     VLM interpretation (semantics/tone, not exact values)
  derived          computed/reconciled from other fields
  human            manually corrected
"""

DEFAULT_REVIEW_THRESHOLD = 0.75

SOURCE_BASE_CONF = {
    "text_layer":      0.95,
    "ocr_caption":     0.97,
    "ocr_rgb_derived": 0.90,
    "pixel_cluster":   0.70,
    "vision_model":    0.60,
    "derived":         0.85,
    "human":           1.00,
}


def field(value, source, confidence=None, evidence=None,
          review_threshold=DEFAULT_REVIEW_THRESHOLD, force_review=False):
    """Build a provenance-wrapped field.

    confidence defaults to the source's base reliability. needs_review trips when
    confidence is below threshold, when the value is empty/None, or when forced.
    """
    if confidence is None:
        confidence = SOURCE_BASE_CONF.get(source, 0.5)
    empty = value is None or value == "" or value == [] or value == {}
    needs_review = force_review or empty or confidence < review_threshold
    return {
        "value": value,
        "source": source,
        "confidence": round(confidence, 2),
        "evidence": evidence or {},
        "needs_review": needs_review,
    }
