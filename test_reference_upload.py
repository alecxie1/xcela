#!/usr/bin/env python3
"""test_reference_upload.py - falsifiable self-test for the reference-image upload (feature 007).

No paid calls. Asserts VALUES a wrong build cannot satisfy (constitution §III), never `runner.launch`
/ generation. Exercises the REAL production helpers: `uploads.save_upload` (the shared save-upload
home) and the HTTP-free `server.parse_run_form` / `server.write_run_inputs` the `POST /run` route
calls. A synthetic multipart `/run`-style body stands in for the browser; nothing is launched.

Checks:
  1. save_upload round-trips bytes to a real file + sanitizes a traversal filename (US setup).
  2. a multipart /run body -> the inputs JSON's reference_image points at a file that EXISTS in the
     run dir, bytes match, and the uploaded extension is preserved (US1).
  3. the served index.html uses a file input for the reference, not a typed-path field (US1, SC-007).
  4. a /run body with NO reference file -> parse_run_form raises (fail loud), nothing launched (US2).
  5. the other brief fields (messages / mandatory_elements) pass through VERBATIM (US3, 002 invariant).
  6. the standalone thin-route contract is intact: test_thin_route.py stays green (US3, SC-006).

Run:  .venv/bin/python test_reference_upload.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "frontend"))
import uploads  # noqa: E402
import server  # noqa: E402  (defines parse_run_form / write_run_inputs; importing starts no server)

BOUNDARY = "----run-test-boundary-007"
CT = f"multipart/form-data; boundary={BOUNDARY}"
# a binary blob with CRLFs + boundary-ish bytes inside, to prove raw preservation
REF_BYTES = b"\x89PNG\r\n\x1a\n\x00\xffFAKE-PNG--not-a-boundary\r\ntail\x00"


def _run_body(form_dict, ref_name="ref.png", with_reference=True):
    """Build a synthetic multipart /run body: a `form` JSON field (+ optional `reference` file)."""
    b = BOUNDARY.encode()
    parts = [
        b"--" + b + b"\r\n"
        b'Content-Disposition: form-data; name="form"\r\n\r\n'
        + json.dumps(form_dict, ensure_ascii=False).encode("utf-8") + b"\r\n",
    ]
    if with_reference:
        parts.append(
            b"--" + b + b"\r\n"
            b'Content-Disposition: form-data; name="reference"; filename="' + ref_name.encode() + b'"\r\n'
            b"Content-Type: application/octet-stream\r\n\r\n" + REF_BYTES + b"\r\n"
        )
    parts.append(b"--" + b + b"--\r\n")
    return b"".join(parts)


def check1_save_upload_roundtrip_and_sanitize():
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "run"
        p = uploads.save_upload(("ref.png", REF_BYTES), dest)
        roundtrip = Path(p).exists() and Path(p).read_bytes() == REF_BYTES
        # a crafted traversal filename must be reduced to its basename INSIDE dest
        evil = uploads.save_upload(("../../evil.png", b"x"), dest)
        contained = Path(evil).parent == dest and Path(evil).name == "evil.png"
        passed = roundtrip and contained
        return passed, f"roundtrip={roundtrip} (path={p!r}); traversal_contained={contained} (evil={evil!r})"


def check2_run_assembly_points_at_saved_file():
    form_in = {"brand": "aia", "asset_type": "手举牌", "messages": ["守住钱袋子"],
               "reference_relationship": "template - extend this series"}
    body = _run_body(form_in, ref_name="myref.jpg")
    with tempfile.TemporaryDirectory() as d:
        run_dir = Path(d) / "run_test"
        form, ref, _prods = server.parse_run_form(body, CT)
        inputs_path = server.write_run_inputs(form, ref, run_dir)
        inputs = json.loads(Path(inputs_path).read_text(encoding="utf-8"))
        ref_path = inputs.get("reference_image")
        exists = bool(ref_path) and Path(ref_path).exists()
        bytes_ok = exists and Path(ref_path).read_bytes() == REF_BYTES
        ext_ok = exists and Path(ref_path).suffix == ".jpg"          # uploaded extension preserved (A2)
        in_run_dir = exists and Path(ref_path).parent == run_dir     # co-located with the run (FR-003)
        passed = exists and bytes_ok and ext_ok and in_run_dir
        return passed, (f"reference_image={ref_path!r}; exists={exists}; bytes_ok={bytes_ok}; "
                        f"ext_preserved={ext_ok}; in_run_dir={in_run_dir}")


def check3_page_uses_file_input():
    html = (REPO / "frontend" / "index.html").read_text(encoding="utf-8")
    has_file = 'type="file"' in html and 'id="reference_image"' in html
    no_typed_path = 'placeholder="/abs/path' not in html
    passed = has_file and no_typed_path
    return passed, f"file_input_present={has_file}; typed_path_field_gone={no_typed_path}"


def check4_missing_reference_fails_loud():
    body = _run_body({"brand": "aia"}, with_reference=False)
    raised = False
    try:
        server.parse_run_form(body, CT)  # the route's FIRST step; raises -> 400, before any mkdir/launch
    except ValueError:
        raised = True
    # falsifiable: a build that does not guard would return a (form, None) and proceed to launch
    return raised, f"parse_run_form raised on a missing reference={raised} (no run dir created, no launch)"


def check5_verbatim_other_fields():
    msgs = ["守住钱袋子", "护好幸福家"]
    mand = ["分别画叉"]
    body = _run_body({"brand": "aia", "messages": msgs, "mandatory_elements": mand})
    with tempfile.TemporaryDirectory() as d:
        form, ref, _prods = server.parse_run_form(body, CT)
        inputs = json.loads(Path(server.write_run_inputs(form, ref, Path(d) / "run")).read_text("utf-8"))
        msgs_ok = inputs["signs"][0]["messages"] == msgs
        mand_ok = inputs["mandatory_elements"] == mand
        passed = msgs_ok and mand_ok
        return passed, (f"messages_verbatim={msgs_ok} ({inputs['signs'][0]['messages']}); "
                        f"mandatory_verbatim={mand_ok} ({inputs['mandatory_elements']})")


def check6_standalone_cli_contract_intact():
    proc = subprocess.run([sys.executable, str(REPO / "test_thin_route.py")],
                          capture_output=True, text=True, cwd=str(REPO))
    passed = proc.returncode == 0
    last = (proc.stdout.strip().splitlines() or proc.stderr.strip().splitlines() or [""])[-1]
    return passed, f"test_thin_route.py exit={proc.returncode}; last_line={last!r}"


CHECKS = [
    ("save_upload round-trips bytes + sanitizes a traversal filename", check1_save_upload_roundtrip_and_sanitize),
    ("multipart /run -> inputs reference_image points at the saved file (ext preserved)", check2_run_assembly_points_at_saved_file),
    ("served page uses a file input, no typed-path field (SC-007)", check3_page_uses_file_input),
    ("missing reference fails loud (no run launched)", check4_missing_reference_fails_loud),
    ("other fields (messages/mandatory) pass through VERBATIM (002 invariant)", check5_verbatim_other_fields),
    ("standalone thin-route contract intact (test_thin_route.py green, SC-006)", check6_standalone_cli_contract_intact),
]


def main():
    print("=" * 78)
    print("test_reference_upload.py - falsifiable self-test (007, no paid calls)")
    print("=" * 78)
    passed = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        passed += int(ok)
        print(f"\nCHECK {i}/{len(CHECKS)} - {name}: {'PASS' if ok else 'FAIL'}")
        print(f"  {detail}")
    print("\n" + "=" * 78)
    print(f"RESULT: {passed}/{len(CHECKS)} checks passed")
    print("=" * 78)
    sys.exit(0 if passed == len(CHECKS) else 1)


if __name__ == "__main__":
    main()
