#!/usr/bin/env python3
"""model_client.py — feature 020: model choice is deployment CONFIGURATION, not code.

The ONE place text/vision model calls happen. Deployments pick models in .env (see
.env.example); the provider is inferred from the model name, so swapping Claude for a GPT
model is a config line, never a fork:

  XCELA_TEXT_MODELS   comma-separated fallback chain; default claude-opus-4-5,claude-sonnet-4-6
  XCELA_IMAGE_MODEL   default gpt-image-2 (consumed by harness/generate.py)

Routing: claude-* -> Anthropic messages.create (content blocks, base64 image sources);
anything else -> OpenAI chat.completions.create (data-URI image_url parts,
max_completion_tokens). Both return the raw text; callers keep their own parsing (fence
stripping, JSON) so behavior under the default env is byte-identical to pre-020.

The client factories are module-level and injectable so the self-tests exercise routing and
payload mapping with fakes (never a paid call in tests).
"""

import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_env import load_runtime_env  # noqa: E402

TEXT_MODELS_DEFAULT = ("claude-opus-4-5", "claude-sonnet-4-6")
IMAGE_MODEL_DEFAULT = "gpt-image-2"


def text_models() -> list:
    raw = os.environ.get("XCELA_TEXT_MODELS", "")
    models = [m.strip() for m in raw.split(",") if m.strip()]
    return models or list(TEXT_MODELS_DEFAULT)


def image_model() -> str:
    return os.environ.get("XCELA_IMAGE_MODEL", "").strip() or IMAGE_MODEL_DEFAULT


def _provider(model: str) -> str:
    return "anthropic" if model.startswith("claude") else "openai"


def _anthropic_client():
    load_runtime_env()
    import anthropic
    return anthropic.Anthropic()


def _openai_client():
    load_runtime_env()
    from openai import OpenAI
    return OpenAI()


# injectable for the free self-tests (each maps provider -> zero-arg client factory)
CLIENT_FACTORIES = {"anthropic": _anthropic_client, "openai": _openai_client}


def _image_part(image_path: str, provider: str) -> dict:
    data = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
    media = "image/png" if str(image_path).lower().endswith("png") else "image/jpeg"
    if provider == "anthropic":
        return {"type": "image",
                "source": {"type": "base64", "media_type": media, "data": data}}
    return {"type": "image_url", "image_url": {"url": f"data:{media};base64,{data}"}}


def _as_messages(prompt_or_messages, image_path, provider) -> list:
    """Accept a plain prompt string OR an anthropic-style messages list; normalize per
    provider. Image (optional) is prepended as the first content part, matching the
    pre-020 payload shapes exactly on the anthropic branch."""
    if isinstance(prompt_or_messages, str):
        parts = []
        if image_path:
            parts.append(_image_part(image_path, provider))
        parts.append({"type": "text", "text": prompt_or_messages})
        return [{"role": "user", "content": parts if image_path else prompt_or_messages}]
    # a messages list: translate any anthropic image blocks when routing to openai
    if provider == "anthropic":
        return prompt_or_messages
    out = []
    for m in prompt_or_messages:
        content = m.get("content")
        if isinstance(content, list):
            parts = []
            for part in content:
                if part.get("type") == "image" and "source" in part:
                    src = part["source"]
                    parts.append({"type": "image_url", "image_url": {
                        "url": f"data:{src['media_type']};base64,{src['data']}"}})
                else:
                    parts.append(part)
            out.append({"role": m["role"], "content": parts})
        else:
            out.append(m)
    return out


def call_text_model(model: str, prompt_or_messages, max_tokens: int,
                    image_path: str | None = None) -> str:
    """ONE call to ONE model; raises on failure (the chain handles fallback)."""
    provider = _provider(model)
    client = CLIENT_FACTORIES[provider]()
    messages = _as_messages(prompt_or_messages, image_path, provider)
    if provider == "anthropic":
        msg = client.messages.create(model=model, max_tokens=max_tokens, messages=messages)
        return msg.content[0].text.strip()
    resp = client.chat.completions.create(model=model, max_completion_tokens=max_tokens,
                                          messages=messages)
    return (resp.choices[0].message.content or "").strip()


def call_text_chain(prompt_or_messages, max_tokens: int, image_path: str | None = None,
                    models: list | None = None) -> tuple[str, str]:
    """Today's exact chain semantics: try each model in order, warn per failure to stderr,
    RuntimeError naming the last failure when every model fails. Returns (text, model)."""
    last_exc = None
    for model in (models or text_models()):
        try:
            return call_text_model(model, prompt_or_messages, max_tokens, image_path), model
        except Exception as exc:  # noqa: BLE001 — fall through the model chain
            last_exc = exc
            print(f"  [warn] {model} failed: {exc}", file=sys.stderr)
    raise RuntimeError(f"all models failed: {last_exc}")
