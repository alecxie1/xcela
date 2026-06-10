"""generate.py — gpt-image-2 wrapper. images.edit with the brand logo as reference."""

import base64
import os
from pathlib import Path


def generate_variant(prompt: str, logo_path: str, out_path: str,
                     size: str = "1536x1024", quality: str = "high") -> dict:
    """One generation call. Returns metadata dict for the manifest."""
    from dotenv import load_dotenv
    load_dotenv(Path.home() / ".hermes" / ".env", override=True)
    from openai import OpenAI

    client = OpenAI()
    with open(logo_path, "rb") as ref:
        resp = client.images.edit(
            model="gpt-image-2",
            image=[ref],
            prompt=prompt,
            size=size,        # type: ignore[arg-type]
            quality=quality,  # type: ignore[arg-type]
        )
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
        "reference_image": logo_path,
        "output": out_path,
    }
