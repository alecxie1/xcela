# xcela — Handyprint brand design tool

Turns a messy brief (Chinese or English copy, a style reference image, a brand's visual
identity) into a **handoff-quality design DRAFT**: a human designer judges and finishes every
output. The operator surface is a small Chinese-language web app; the pipeline underneath is
deterministic Python orchestrating two model APIs (Anthropic Claude for planning and analysis,
OpenAI gpt-image-2 for the paid image generation).

Three principles shape everything here:

1. **No spend without an explicit click.** Every browser run stops at a free "confirm before
   paying" gate that shows the derived plan and every assumption the system made; generating
   an image (~$0.08) and exporting layers (~$0.5) are separate, labeled, opt-in clicks.
2. **The human eye is the only judge of pixels.** Automated tests prove structure, never
   beauty; the app is built around approve/nudge loops.
3. **Honest failures.** When a step cannot do its job it says so by name; it never silently
   substitutes an asset, invents geometry, or fabricates a result.

## Quickstart

```bash
git clone <this repo> && cd handyprint-design-tool
bash deploy/bootstrap.sh          # Python 3.11 venv + pinned deps + checks (names anything missing)
cp .env.example .env              # then fill in YOUR OpenAI + Anthropic keys
.venv/bin/python frontend/server.py    # serves http://127.0.0.1:8765
```

Open the app, onboard a brand once via 录入品牌 (upload its VI PDF + logo), then run briefs
from the main form. The in-app manual lives at `/playbook` (Chinese). For a real deployment
(systemd + TLS proxy), follow `deploy/README.md`.

Note: the app calls `api.openai.com` and `api.anthropic.com` directly, so the server must run
where both are reachable (they are blocked from mainland China and unsupported in Hong Kong;
Singapore and Tokyo both work well).

## Configuration

Loader: `harness/runtime_env.py`. Precedence: **real environment variables > `<repo>/.env` >
`~/.hermes/.env` (legacy)**; files never override the environment.

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `OPENAI_API_KEY` | yes | - | gpt-image-2 (image generation, the paid step) |
| `ANTHROPIC_API_KEY` | yes | - | Claude (prompt authoring, reference analysis) |
| `XCELA_BIND` | no | `127.0.0.1` | server bind address (keep local; proxy in front) |
| `XCELA_PORT` | no | `8765` | server port (a CLI argument wins) |
| `XCELA_MAX_UPLOAD_MB` | no | `32` | reject larger uploads before reading them |
| `XCELA_WORKER_TIMEOUT_S` | no | `1800` | kill a wedged worker, free the one-at-a-time lock |
| `XCELA_BRANDS_DIR` | no | `<repo>/brands` | where brand assets (logos) live |

## Repo layout

```
frontend/        the web app: stdlib HTTP server + three vanilla-HTML pages
                 (run form / onboarding wizard / playbook), run listing, pre-spend gate UI
harness/         the pipeline: conductor.py (orchestrator), scene_author.py (prompt engine),
                 generate.py (gpt-image-2 wrapper), export_layers.py (per-element layer
                 export), format_size.py, asset_paths.py, runtime_env.py, ...
register/        the reconciliation engine: brand DNA vs task needs, per dimension
                 (derive_register.py), plus reference calibration
brand_intake/    brand onboarding: VI-PDF extraction, key assembly/validation, persistence
answer_keys/     committed brand DNA (one JSON per onboarded brand)
kits/ config/    optional per-brand data for the dormant kit path
deploy/          bootstrap script, systemd unit, Caddyfile template, deployer README
docs/            ARCHITECTURE.md (the full map), playbook pointer, deployment notes
specs/           the feature specs that built this system (spec-driven history, 001-018)
test_*.py        the free self-test suites (30 files; run any of them directly)
legacy/          pre-rebuild research scripts; unmaintained, kept for provenance
brands/ output/  GITIGNORED: brand assets (logos/fonts) and run outputs; never committed
```

Two orientation documents go deeper: `docs/ARCHITECTURE.md` (modules, pipeline, pitfalls) and
`SYSTEM_MAP.md` (the living build status, feature by feature). `CLAUDE.md` is the working
brief for AI-assisted development sessions.

## Tests

Every suite is free (no API calls; model boundaries are stubbed, image keying runs on
synthetic fixtures):

```bash
.venv/bin/python test_conductor.py          # orchestrator self-test
.venv/bin/python test_deploy_readiness.py   # deployment/config/i18n surface
for t in test_*.py; do .venv/bin/python "$t" || break; done   # the full sweep
```

The one intentionally unautomated check is a human looking at a generated image; the test
suites will never spend money.

## Costs

Per confirmed design: one gpt-image-2 call (~$0.08) plus cents of Claude usage during
planning. The optional layered export is one extra call per design element (~$0.5 for a
typical five-element design). Both prices are shown in the UI before the click that spends.
