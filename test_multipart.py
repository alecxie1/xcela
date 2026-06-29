#!/usr/bin/env python3
"""test_multipart.py — falsifiable self-test for frontend/multipart (feature 006).

No paid calls. Builds a synthetic multipart/form-data body (one text field + one binary file part) and
asserts parse_multipart round-trips: the field value AND the file's filename + EXACT bytes, with binary
content preserved byte-for-byte. A malformed/empty body yields empty dicts (no crash).

Run:  .venv/bin/python test_multipart.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "frontend"))
import multipart  # noqa: E402

BOUNDARY = "----testboundary123"
CT = f"multipart/form-data; boundary={BOUNDARY}"
# a binary blob with CRLFs + the boundary-ish bytes inside, to prove raw preservation
FILE_BYTES = b"\x89PNG\r\n\x1a\n\x00\xff--not-a-real-boundary\r\ntail\x00"


def _body():
    b = BOUNDARY.encode()
    parts = [
        b"--" + b + b"\r\n"
        b'Content-Disposition: form-data; name="brand"\r\n\r\n'
        b"chajiuxingqiu\r\n",
        b"--" + b + b"\r\n"
        b'Content-Disposition: form-data; name="pdf"; filename="vi.pdf"\r\n'
        b"Content-Type: application/pdf\r\n\r\n" + FILE_BYTES + b"\r\n",
        b"--" + b + b"--\r\n",
    ]
    return b"".join(parts)


def check1_field_roundtrip():
    r = multipart.parse_multipart(_body(), CT)
    passed = r["fields"].get("brand") == "chajiuxingqiu"
    return passed, f"fields={r['fields']}"


def check2_file_filename_and_exact_bytes():
    r = multipart.parse_multipart(_body(), CT)
    f = r["files"].get("pdf")
    passed = bool(f) and f[0] == "vi.pdf" and f[1] == FILE_BYTES
    detail = (f"filename={f[0]!r}; bytes match={f[1] == FILE_BYTES}; len={len(f[1])} (want {len(FILE_BYTES)})"
              if f else "no 'pdf' file part parsed")
    return passed, detail


def check3_malformed_no_crash():
    empty = multipart.parse_multipart(b"", CT)
    nobound = multipart.parse_multipart(b"garbage", "application/json")
    passed = empty == {"fields": {}, "files": {}} and nobound == {"fields": {}, "files": {}}
    return passed, f"empty body -> {empty}; no-boundary -> {nobound}"


CHECKS = [
    ("Text field round-trips", check1_field_roundtrip),
    ("File filename + EXACT binary bytes preserved", check2_file_filename_and_exact_bytes),
    ("Malformed / empty body -> empty dicts (no crash)", check3_malformed_no_crash),
]


def main():
    print("=" * 78)
    print("test_multipart.py — falsifiable self-test (006, no paid calls)")
    print("=" * 78)
    passed = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        passed += int(ok)
        print(f"\nCHECK {i}/{len(CHECKS)} — {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed}/{len(CHECKS)} checks passed")
    print("=" * 78)
    sys.exit(0 if passed == len(CHECKS) else 1)


if __name__ == "__main__":
    main()
