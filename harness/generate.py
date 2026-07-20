"""generate.py — gpt-image-2 wrapper. images.edit with the brand logo as reference."""

import base64
import os
from pathlib import Path


def generate_variant(prompt: str, logo_path, out_path: str,
                     size: str = "1536x1024", quality: str = "high",
                     mask_path=None) -> dict:
    """One generation call. Returns metadata dict for the manifest.

    logo_path: a single path (str) or a list of paths — all are passed as
    reference images to images.edit in order (e.g. [logo, style_reference]).
    mask_path (023, optional): an images.edit mask PNG (transparent = editable)
    for region-scoped edits; None keeps the pre-023 call byte-identical.
    """
    from runtime_env import load_runtime_env  # 018: env > .env > legacy ~/.hermes
    load_runtime_env()
    from model_client import image_model  # 020: the image model is deployment config
    from openai import OpenAI

    paths = [logo_path] if isinstance(logo_path, str) else list(logo_path)
    # Hard per-request timeout: a wedged HTTPS connection otherwise hangs the
    # whole pipeline indefinitely (observed 25min+ stall at Step 4). One retry.
    client = OpenAI(timeout=240.0, max_retries=1)
    refs = [open(p, "rb") for p in paths]
    mask = open(mask_path, "rb") if mask_path else None
    try:
        kwargs = {"mask": mask} if mask else {}
        resp = client.images.edit(
            model=image_model(),
            image=refs,
            prompt=prompt,
            size=size,        # type: ignore[arg-type]
            quality=quality,  # type: ignore[arg-type]
            **kwargs,
        )
    finally:
        for r in refs:
            r.close()
        if mask:
            mask.close()
    if not resp.data or not resp.data[0].b64_json:
        raise RuntimeError("gpt-image-2 returned no image data")
    b64 = resp.data[0].b64_json
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
    meta = {
        "model": image_model(),
        "endpoint": "images.edit",
        "size": size,
        "quality": quality,
        "reference_image": paths if len(paths) > 1 else paths[0],
        "output": out_path,
    }
    if mask_path:  # 023: additive, absent on every pre-023 call (manifests byte-identical)
        meta["mask"] = str(mask_path)
    return meta
