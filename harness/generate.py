"""generate.py — gpt-image-2 wrapper. images.edit with the brand logo as reference."""

import base64
import os
from pathlib import Path


def generate_variant(prompt: str, logo_path, out_path: str,
                     size: str = "1536x1024", quality: str = "high") -> dict:
    """One generation call. Returns metadata dict for the manifest.

    logo_path: a single path (str) or a list of paths — all are passed as
    reference images to images.edit in order (e.g. [logo, style_reference]).
    """
    from dotenv import load_dotenv
    load_dotenv(Path.home() / ".hermes" / ".env", override=True)
    from openai import OpenAI

    paths = [logo_path] if isinstance(logo_path, str) else list(logo_path)
    # Hard per-request timeout: a wedged HTTPS connection otherwise hangs the
    # whole pipeline indefinitely (observed 25min+ stall at Step 4). One retry.
    client = OpenAI(timeout=240.0, max_retries=1)
    refs = [open(p, "rb") for p in paths]
    try:
        resp = client.images.edit(
            model="gpt-image-2",
            image=refs,
            prompt=prompt,
            size=size,        # type: ignore[arg-type]
            quality=quality,  # type: ignore[arg-type]
        )
    finally:
        for r in refs:
            r.close()
    if not resp.data or not resp.data[0].b64_json:
        raise RuntimeError("gpt-image-2 returned no image data")
    b64 = resp.data[0].b64_json
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
    return {
        "model": "gpt-image-2",
        "endpoint": "images.edit",
        "size": size,
        "quality": quality,
        "reference_image": paths if len(paths) > 1 else paths[0],
        "output": out_path,
    }
