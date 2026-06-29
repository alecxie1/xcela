# Contract: stdlib multipart parser (`frontend/multipart.py`)

The one genuinely-new server capability: the 004 server reads JSON bodies only; real file upload needs
multipart/form-data. Hand-rolled stdlib (no `cgi`, deprecated + removed in 3.13; no new dependency).
PURE (bytes in, dict out), so it is unit-testable without HTTP.

## `parse_multipart(body: bytes, content_type: str) -> {fields: dict, files: dict}`
- `content_type` carries the boundary (`multipart/form-data; boundary=...`); split the body on it.
- `fields[name] = value` for plain text parts (decoded UTF-8).
- `files[name] = (filename, bytes)` for file parts (raw bytes preserved, e.g. the PDF / the logo).
- Tolerate CRLF line endings + the trailing `--boundary--`; ignore parts without a `name`.

## Rules (falsifiable)
1. Given a synthetic multipart body with one text field and one file part, `parse_multipart` returns
   the field value AND the file's filename + EXACT bytes (round-trip, no corruption).
2. It uses no `cgi` and adds no dependency (stdlib only).
3. Binary file bytes are preserved unmodified (a PDF/PNG survives the round-trip byte-for-byte).
4. A malformed / empty body yields empty `fields` + `files` (no crash) -- the route then fails loud on
   the missing required file.
