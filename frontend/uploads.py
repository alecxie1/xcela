#!/usr/bin/env python3
"""frontend/uploads.py - the one save-upload home (feature 007).

The 006 logo-save and the 004 reference-save both do the SAME step: take a parsed multipart
(filename, bytes) tuple and land it on disk so a path-consuming back-half (the conductor reads
`reference_image` as a path; `persist.place_logo` copies a logo path) can use it. Factor that step
here, called by BOTH call sites (DRY). Stdlib only; effectful (writes a file), deliberately SEPARATE
from the PURE `frontend/multipart.py` parser so the parser stays unit-testable without a filesystem.

Honest-null discipline: this helper NEVER substitutes a default and NEVER fabricates a file. A missing
/ empty upload is the CALLER's fail-loud responsibility (the `/run` route rejects a missing reference
with a 400 before calling here; the onboard route guards `logo and logo[1]`).
"""

import os
from pathlib import Path


def save_upload(file_tuple, dest_dir, name=None) -> str:
    """Write a multipart (filename, bytes) tuple into dest_dir and return the saved path.

    `file_tuple` is `(filename, raw_bytes)` as returned by `multipart.parse_multipart(...)["files"][k]`.
    The save name is `name` (if given) else the uploaded filename, reduced to its BASENAME so a crafted
    upload filename like "../evil.png" cannot escape dest_dir (path-traversal guard). Bytes are written
    byte-for-byte. Returns the saved path as a string.
    """
    filename, data = file_tuple
    chosen = name if name else filename
    safe = os.path.basename(str(chosen))
    out_dir = Path(dest_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / safe
    dest.write_bytes(data)
    return str(dest)
