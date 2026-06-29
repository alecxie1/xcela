#!/usr/bin/env python3
"""frontend/multipart.py — minimal stdlib multipart/form-data parser (feature 006).

The 004 server reads JSON bodies only; real file upload (a designer picks a PDF + a logo in the
browser) needs multipart/form-data. Hand-rolled boundary parsing: stdlib only, no `cgi` (deprecated,
removed in 3.13), no new dependency. PURE (bytes in, dict out) so it is unit-testable without HTTP.
Binary file bytes are preserved byte-for-byte.
"""

import re


def _boundary(content_type: str):
    m = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', content_type or "")
    if not m:
        return None
    return (m.group(1) or m.group(2)).strip()


def _split_headers(part: bytes):
    """Split a part into its header block (decoded) and body bytes. Returns (headers_text, body)."""
    sep = part.find(b"\r\n\r\n")
    if sep == -1:
        return "", b""
    return part[:sep].decode("utf-8", "replace"), part[sep + 4:]


def parse_multipart(body: bytes, content_type: str) -> dict:
    """Parse a multipart/form-data body into {fields: {name: str}, files: {name: (filename, bytes)}}.

    Plain parts -> fields[name] = utf-8 text. File parts (a filename in Content-Disposition) ->
    files[name] = (filename, raw bytes). Malformed / empty body -> empty dicts (no crash)."""
    out = {"fields": {}, "files": {}}
    boundary = _boundary(content_type)
    if not boundary or not body:
        return out
    delim = b"--" + boundary.encode("utf-8")
    # split; drop the preamble (before the first delim) and the closing "--" epilogue
    for raw in body.split(delim):
        part = raw.strip(b"\r\n")
        if not part or part == b"--":
            continue
        headers, content = _split_headers(part)
        disp = next((ln for ln in headers.splitlines()
                     if ln.lower().startswith("content-disposition")), "")
        nm = re.search(r'name="([^"]*)"', disp)
        if not nm:
            continue
        name = nm.group(1)
        fn = re.search(r'filename="([^"]*)"', disp)
        if fn is not None:
            out["files"][name] = (fn.group(1), content)
        else:
            out["fields"][name] = content.decode("utf-8", "replace")
    return out
