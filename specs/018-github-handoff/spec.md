# Feature Specification: GitHub Handoff (env-configurable keys + a legible repo)

**Feature Branch**: `018-github-handoff`

**Created**: 2026-07-13

**Status**: Draft

**Input**: Richard's team decision (meeting, relayed by Alec): everything goes to GitHub and
THEIR CTO deploys it himself. The keys must be theirs (env-configurable, e.g. their own
OpenAI/Anthropic keys), and the codebase must be well organized and easy for an outsider to
understand.

## Why this feature

Until now the deployer was us: keys lived at the hardcoded `~/.hermes/.env`, loaded with
`override=True` (the FILE beats real environment variables, the opposite of every standard
deployment convention), the repo root carries ~28 legacy one-off scripts from the early
research era, and the only orientation documents (CLAUDE.md, SYSTEM_MAP) are dense
operator/agent briefs. A CTO cloning from GitHub needs: standard configuration (his keys, his
env, documented), a root that shows the live system at a glance, and a README written for him.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The CTO configures with his own keys, the standard way (P1)

He sets `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` as real environment variables (systemd unit,
Docker, shell) OR copies `.env.example` to `<repo>/.env` and fills it in. Real environment
variables ALWAYS win over files; the legacy `~/.hermes/.env` keeps working as the
last-resort fallback so our own machines and the reference VM change nothing.

**Independent Test**: free: one loader function with the documented precedence (process env >
repo .env > ~/.hermes/.env, never overriding), proven by value with temp files + env vars;
exactly zero `override=True` dotenv loads remain in live code; every live module loads
through the ONE loader.

**Acceptance Scenarios**:
1. **Given** a real env var and a conflicting `.env` value, **Then** the real env var wins.
2. **Given** only `<repo>/.env`, **Then** its values load; **given** only `~/.hermes/.env`,
   **Then** those load (legacy compatibility).
3. **Given** the repo, **Then** `.env.example` documents every variable the system reads
   (both API keys + every XCELA_* knob) and `.env` is gitignored.

### User Story 2 - The CTO opens the repo and understands it (P1)

The root README (English; he can translate) says what the tool is, shows the repo layout,
gives the quickstart (bootstrap, .env, serve, tests), tables every environment variable, and
points into deploy/ and docs/ARCHITECTURE.md. The repo root contains only the live system:
the early-research one-off scripts live under `legacy/` with a short README, and nothing the
test suite or runtime imports moves.

**Independent Test**: free: the full suite stays green after the moves (proof nothing live
moved); README exists with the env table and quickstart; the legacy scripts are gone from
the root and present under legacy/.

### User Story 3 - Everything is on GitHub for him (P1)

`master` is pushed to the existing private origin (github.com/alecxie1/xcela); the CTO gets
repo access (a GitHub-UI action for Alec). Secrets and brand assets remain out-of-band by
design (gitignored; the handoff documented in deploy/README + README).

**Independent Test**: `git ls-remote origin master` equals local HEAD after the push (the
push itself needs Alec's credentials; the feature makes the tree ready).

## Requirements

- **FR-001**: ONE loader (`harness/runtime_env.py`) with precedence process-env > repo `.env`
  > `~/.hermes/.env`, never overriding existing variables; every live dotenv call site
  (harness/approve, generate, scene_author; register/blind_score, calibrate_from_reference,
  reference_style_to_prompt) switches to it; zero `override=True` remains outside legacy/.
- **FR-002**: `.env.example` documents every read variable; `.env` gitignored; deploy/
  (bootstrap check, unit EnvironmentFile, README) updated to the repo-root `.env` as the
  primary home with `~/.hermes/.env` as legacy fallback.
- **FR-003**: A root `README.md` for outsiders: purpose, layout, quickstart, env table,
  tests, deploy pointer, docs pointers.
- **FR-004**: Legacy one-off scripts and their legacy manual tests move to `legacy/` with a
  README; nothing imported by live code or the green suites moves (extract_colors,
  extract_text_layer stay); the full suite passes unchanged.
- **FR-005**: Byte-identity where it matters: key loading still succeeds on our machines and
  the reference VM without any local change (the fallback chain); all XCELA_* semantics
  unchanged.

## Success Criteria

- **SC-001**: With ONLY exported env vars (no files), a paid-path module resolves both keys;
  with a conflicting `.env`, the exported values still win (provable free by value).
- **SC-002**: The full suite is green after the loader switch and the legacy moves.
- **SC-003**: The repo root's Python files are exactly the live surface (the suites +
  extractors); everything else is under legacy/.
- **SC-004**: origin/master == local HEAD (after Alec authenticates the push).
- **SC-005**: HUMAN GATE: the CTO (or Alec simulating him) goes clone -> README quickstart ->
  .env with his keys -> serve -> one gated run, without asking us anything. (Effectively a
  re-run of 017's SC-001 from GitHub instead of a local clone.)

## Assumptions

- The repo stays private under alecxie1/xcela; access via GitHub invite (Alec's UI action).
  A transfer to their org later is a GitHub operation, not a code change.
- The reference VM stays up as OUR staging until the CTO's deployment works, then can be
  torn down (their call).
- CLAUDE.md/SYSTEM_MAP remain the agent/operator briefs (unmoved); README is additive.
- The precedence change (env now beats file) is the deliberate new contract; the old
  override=True behavior was an implementation accident, not a promise.
