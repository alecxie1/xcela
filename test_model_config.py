#!/usr/bin/env python3
"""test_model_config.py - falsifiable self-test for feature 020 (env-configured,
provider-agnostic model client). NO paid calls: both provider clients are FAKES injected
through model_client.CLIENT_FACTORIES.

Run:  .venv/bin/python test_model_config.py
"""

import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "harness"))
sys.path.insert(0, str(REPO))

import model_client as mc  # noqa: E402


class FakeAnthropic:
    def __init__(self, log, fail_models=()):
        self.log, self.fail = log, set(fail_models)

        class _Msgs:
            def create(_s, **kw):
                self.log.append(("anthropic", kw))
                if kw["model"] in self.fail:
                    raise RuntimeError(f"fake refusal for {kw['model']}")
                class _C:  # noqa: N801
                    text = '{"ok": 1}'
                class _M:  # noqa: N801
                    content = [_C()]
                return _M()
        self.messages = _Msgs()


class FakeOpenAI:
    def __init__(self, log):
        self.log = log

        class _Comp:
            def create(_s, **kw):
                self.log.append(("openai", kw))
                class _Msg:  # noqa: N801
                    content = "gpt says hi"
                class _Ch:  # noqa: N801
                    message = _Msg()
                class _R:  # noqa: N801
                    choices = [_Ch()]
                return _R()

        class _Chat:  # noqa: N801
            completions = _Comp()
        self.chat = _Chat()


def _inject(log, fail_models=()):
    mc.CLIENT_FACTORIES["anthropic"] = lambda: FakeAnthropic(log, fail_models)
    mc.CLIENT_FACTORIES["openai"] = lambda: FakeOpenAI(log)


def _restore():
    mc.CLIENT_FACTORIES["anthropic"] = mc._anthropic_client
    mc.CLIENT_FACTORIES["openai"] = mc._openai_client
    os.environ.pop("XCELA_TEXT_MODELS", None)
    os.environ.pop("XCELA_IMAGE_MODEL", None)


def _png(tmp):
    from PIL import Image
    p = Path(tmp) / "img.png"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(p)
    return str(p)


def check1_env_defaults():
    """Empty env = today's EXACT models (pinned literals); overrides parse (csv, trimmed;
    image model swap). A build that renames a default silently fails here."""
    _restore()
    a = (mc.text_models() == ["claude-opus-4-5", "claude-sonnet-4-6"]
         and mc.image_model() == "gpt-image-2")
    os.environ["XCELA_TEXT_MODELS"] = " gpt-5.5 , claude-sonnet-4-6 "
    os.environ["XCELA_IMAGE_MODEL"] = "gpt-image-3"
    try:
        b = mc.text_models() == ["gpt-5.5", "claude-sonnet-4-6"]
        c = mc.image_model() == "gpt-image-3"
    finally:
        _restore()
    ok = a and b and c
    return ok, f"defaults-pinned={a}; csv-override={b}; image-override={c}"


def check2_routing_and_payloads():
    """Routing BY VALUE: claude-* hits the anthropic fake with the pre-020 content-block
    shape (base64 image source first, text second, max_tokens); gpt-* hits the openai fake
    with a data-URI image_url part and max_completion_tokens; anthropic-style message lists
    translate their image blocks for openai."""
    log = []
    _inject(log)
    try:
        with tempfile.TemporaryDirectory() as td:
            img = _png(td)
            out = mc.call_text_model("claude-opus-4-5", "score this", 512, image_path=img)
            prov, kw = log[-1]
            content = kw["messages"][0]["content"]
            a = (prov == "anthropic" and out == '{"ok": 1}' and kw["max_tokens"] == 512
                 and content[0]["type"] == "image"
                 and content[0]["source"]["media_type"] == "image/png"
                 and content[1] == {"type": "text", "text": "score this"})

            out2 = mc.call_text_model("gpt-5.5", "score this", 512, image_path=img)
            prov2, kw2 = log[-1]
            c2 = kw2["messages"][0]["content"]
            b = (prov2 == "openai" and out2 == "gpt says hi"
                 and kw2["max_completion_tokens"] == 512 and "max_tokens" not in kw2
                 and c2[0]["type"] == "image_url"
                 and c2[0]["image_url"]["url"].startswith("data:image/png;base64,"))

            # anthropic-style messages list with an image block, routed to openai
            msgs = [{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                             "data": "QUJD"}},
                {"type": "text", "text": "hi"}]}]
            mc.call_text_model("gpt-5.5", msgs, 64)
            _p3, kw3 = log[-1]
            c3 = kw3["messages"][0]["content"]
            c = (c3[0]["type"] == "image_url"
                 and c3[0]["image_url"]["url"] == "data:image/jpeg;base64,QUJD"
                 and c3[1] == {"type": "text", "text": "hi"})
    finally:
        _restore()
    ok = a and b and c
    return ok, f"anthropic-shape={a}; openai-shape={b}; block-translation={c}"


def check3_chain_semantics():
    """The chain: first model fails -> second used, the warn names the failed model; ALL
    fail -> RuntimeError naming the last failure (today's exact semantics); the returned
    model name is the one that succeeded."""
    import io
    import contextlib
    log = []
    _inject(log, fail_models={"claude-opus-4-5"})
    try:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            text, model = mc.call_text_chain("hello", 64)
        a = (model == "claude-sonnet-4-6" and text == '{"ok": 1}'
             and "claude-opus-4-5 failed" in err.getvalue())

        _inject(log, fail_models={"claude-opus-4-5", "claude-sonnet-4-6"})
        b = False
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                mc.call_text_chain("hello", 64)
            except RuntimeError as exc:
                b = "all models failed" in str(exc)
    finally:
        _restore()
    ok = a and b
    return ok, f"fallback+warn={a}; all-fail-raises={b}"


def check4_site_wiring():
    """No bare anthropic client remains outside model_client in live code; the five sites
    route through it (scene_author chain w/ parse-in-loop preserved, blind_score, calibrate
    chain, approve tier mapping, generate's image_model in BOTH the call and the manifest);
    .env.example documents both vars."""
    import subprocess
    live = subprocess.run(["grep", "-rn", "anthropic.Anthropic()", "harness", "register",
                           "frontend", "brand_intake"], cwd=REPO, capture_output=True,
                          text=True).stdout
    a = all("model_client.py" in line for line in live.strip().splitlines() if line)

    sa = (REPO / "harness" / "scene_author.py").read_text(encoding="utf-8")
    b = "from model_client import call_text_model, text_models" in sa and "for model in text_models():" in sa
    bs = (REPO / "register" / "blind_score.py").read_text(encoding="utf-8")
    c = "call_text_model(model, RUBRIC_PROMPT, 512, image_path=image_path)" in bs
    cal = (REPO / "register" / "calibrate_from_reference.py").read_text(encoding="utf-8")
    e = "call_text_chain(prompt, 768, image_path=image_path, models=MODELS)" in cal
    gen = (REPO / "harness" / "generate.py").read_text(encoding="utf-8")
    f = gen.count("image_model()") >= 2 and '"gpt-image-2"' not in gen.replace("gpt-image-2 wrapper", "")
    ap = (REPO / "harness" / "approve.py").read_text(encoding="utf-8")
    g = "text_models()[-1]" in ap and "text_models()[0]" in ap and "claude-sonnet-4-6" not in ap
    env = (REPO / ".env.example").read_text(encoding="utf-8")
    h = "XCELA_TEXT_MODELS" in env and "XCELA_IMAGE_MODEL" in env
    ok = a and b and c and e and f and g and h
    return ok, (f"no-bare-clients={a}; scene={b}; blind={c}; calibrate={e}; generate={f}; "
                f"approve={g}; env-example={h}")


def check5_base_url_env():
    """yaoyj merge (2026-07-14): a deployment can point BOTH providers at a custom
    endpoint via the SDKs' native env vars (OPENAI_BASE_URL / ANTHROPIC_BASE_URL). By
    value against the REAL client factories (no network: constructing a client makes no
    call): the env base URL lands on the client, and with the env absent the pinned
    defaults are the official endpoints. Guards a future refactor from passing an
    explicit base_url that would clobber the env (Kevin's Alicloud relay depends on it)."""
    saved = {k: os.environ.get(k) for k in
             ("OPENAI_BASE_URL", "ANTHROPIC_BASE_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")}
    try:
        os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY") or "sk-selftest"
        os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY") or "sk-selftest"
        os.environ["OPENAI_BASE_URL"] = "https://relay.example.cn/v1"
        os.environ["ANTHROPIC_BASE_URL"] = "https://arelay.example.cn"
        a = str(mc._openai_client().base_url).rstrip("/") == "https://relay.example.cn/v1"
        b = str(mc._anthropic_client().base_url).rstrip("/") == "https://arelay.example.cn"
        os.environ.pop("OPENAI_BASE_URL")
        os.environ.pop("ANTHROPIC_BASE_URL")
        c = ("api.openai.com" in str(mc._openai_client().base_url)
             and "api.anthropic.com" in str(mc._anthropic_client().base_url))
        env = (REPO / ".env.example").read_text(encoding="utf-8")
        d = "OPENAI_BASE_URL" in env and "ANTHROPIC_BASE_URL" in env
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    ok = a and b and c and d
    return ok, f"openai-env={a}; anthropic-env={b}; default-endpoints={c}; env-example={d}"


CHECKS = [
    ("020 env: pinned defaults, csv/image overrides", check1_env_defaults),
    ("020 routing: provider payload shapes by value, block translation", check2_routing_and_payloads),
    ("020 chain: fallback + warn + all-fail raise", check3_chain_semantics),
    ("020 wiring: no bare clients, five sites, env docs", check4_site_wiring),
    ("yaoyj: custom base URLs reach both real clients via env", check5_base_url_env),
]


def main():
    print("=" * 78)
    print("test_model_config.py - falsifiable self-test (020, no paid calls)")
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
