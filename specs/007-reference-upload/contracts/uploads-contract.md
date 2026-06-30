# Contract: `frontend/uploads.py` - the shared save-upload helper

The ONE save-upload home, called by BOTH the 004 `/run` reference-save and the 006 `/onboard/save`
logo-save (DRY, FR-007). Stdlib only. Effectful (writes a file); kept separate from the PURE
`multipart.py` parser.

## `save_upload(file_tuple, dest_dir, name=None) -> str`

**Input**:
- `file_tuple`: a `(filename: str, bytes: bytes)` tuple as returned by
  `multipart.parse_multipart(...)["files"][name]`.
- `dest_dir`: a directory path (str or `Path`) to save into; created if missing.
- `name`: optional explicit save filename; if omitted, the uploaded `filename` is used.

**Behavior**:
1. Reduce the chosen name to its BASENAME (strip any directory components) - prevents path traversal
   from a crafted upload filename.
2. Ensure `dest_dir` exists (`mkdir parents=True, exist_ok=True`).
3. Write `file_tuple[1]` (the raw bytes) to `dest_dir/<basename>`.
4. Return the saved path as a string.

**Guarantees**:
- Bytes are written byte-for-byte (binary round-trip; reuse the `test_multipart.py` evidence that
  `multipart.py` preserves bytes, and assert the saved file equals the input bytes).
- No default substitution and no fabrication: an empty / missing `file_tuple` is the CALLER's
  fail-loud responsibility (the `/run` route rejects a missing reference with 400 before calling this;
  the onboard route already guards `logo and logo[1]`). The helper itself does not invent a file.

**Falsifiable test (`test_reference_upload.py`)**:
- Given `("ref.png", FILE_BYTES)` and a tmp dest dir, `save_upload(...)` returns a path that EXISTS and
  whose bytes EQUAL `FILE_BYTES` (a wrong build that truncates / re-encodes fails this).

## Call sites

| Caller | dest_dir | name | downstream |
|--------|----------|------|------------|
| `server.py` `/run` (004) | the per-run dir `output/run_*/` | `"reference"+ext` | path injected as `reference_image`, read by the conductor |
| `server.py` `_onboard_save` (006) | the onboard temp dir | the uploaded logo filename | path passed to `persist.place_logo` (behavior preserved) |
