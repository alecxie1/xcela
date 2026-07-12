# Feature Specification: Deployment Readiness + Chinese-Ready UI

**Feature Branch**: `017-deployment-readiness`

**Created**: 2026-07-12

**Status**: Draft

**Input**: User description: "Make the tool deployable on a fresh Linux VM for Richard's team
in mainland China and usable by Chinese-speaking, non-technical testers, without waiting on the
open business questions (docs/DEPLOYMENT_QUESTIONS.md): the answer-independent slice. Portable
asset paths, reproducible environment + deploy artifacts, server config + guards, run browsing
for remote users, Chinese input robustness, Chinese UI chrome, and the served playbook."

## Why this feature (context that binds the design)

The tool works end to end (features 001-016) but exists only on the author's WSL2 machine.
Richard's team in mainland China is the first outside user group. The portability audit
(2026-07-10) found what breaks on any other machine: committed answer keys point at absolute
`/home/alecx/...` logo paths into a gitignored directory; the dependency set exists only inside
the local `.venv` (no requirements file); the server binds localhost with no configurability, no
upload cap, and no worker timeout; the browser UI loses the current run on any refresh (fatal on
flaky cross-border connections); and the whole operator surface is English while the testers
work in Chinese.

The open business questions (hosting account, auth handoff, feedback channel, timeline) are
Richard's to answer and stay OUT of this feature. Everything here is needed under every possible
answer set: after this feature, deployment day is provisioning plus the playbook's
feedback-channel line, no code.

A grounding fact for the Chinese-input work: the pipeline already handles Chinese VALUES
correctly wherever text flows verbatim (message lines have been Chinese in every CJXQ run;
asset_type/occasion/notes pass through untouched; the models handle Chinese). The gaps are the
two places free text feeds MATCHING logic: the usage-context keyword rules (English keywords
only, so Chinese phrasing always falls to the unmatched default and fires a gate assumption row)
and the size parser (Chinese IME typography: fullwidth digits, fullwidth ×, 厘米/公分 units).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A fresh machine serves the tool (Priority: P1)

An operator clones the repo onto a fresh Linux VM, runs the bootstrap from `deploy/`, provides
the two out-of-band items (the API key file and the brand asset directory), and the app serves
with zero code edits. Committed brand keys resolve their logo files wherever the repo lives; a
brand whose logo cannot be resolved fails loudly with a named error instead of silently
substituting anything.

**Why this priority**: without this nothing else matters; today a fresh clone cannot run a
single generation (dangling absolute paths, no installable dependency list).

**Independent Test**: free: bootstrap into a scratch directory (venv from the pinned
requirements, dirs created), start the server, render existing run dirs, run the full self-test
sweep; a fixture brand key with a repo-relative logo path resolves on a copied repo root; a key
with a missing logo fails with the named error.

**Acceptance Scenarios**:

1. **Given** a fresh clone plus the out-of-band key file and brands directory, **When** the
   operator runs the bootstrap and starts the service, **Then** the app serves and a browser
   run reaches the pre-spend gate with zero code edits.
2. **Given** a committed answer key with a repo-relative logo path, **When** a run executes on
   ANY repo location, **Then** the logo file resolves against the configured brands base
   (default: the repo's own brands directory) and feeds generation exactly as today.
3. **Given** a brand key whose logo file does not exist under the base, **When** a run starts,
   **Then** it refuses with a named error naming the missing path (never a silent substitute:
   the old hardcoded fallback path is gone).
4. **Given** the deploy artifacts, **Then** secrets and brand assets are documented as
   out-of-band handoffs and nothing secret is committed.

---

### User Story 2 - A remote tester never loses their run (Priority: P2)

A tester in China starts a run, their connection drops (or they refresh, or close the laptop),
and when they come back the same run is one click away: the page URL identifies the run, and a
recent-runs list shows every run on the server (newest first, with brand, state, and whether an
image/export exists). Two testers sharing the tool see each other's runs in the list and take
turns (one generation at a time; a busy answer means wait, and the playbook says so).

**Why this priority**: session-only state is the single biggest usability cliff for remote use;
today a refresh silently orphans a paid run.

**Independent Test**: free: the run-listing surface returns the expected entries for a fixture
output directory (newest first, correct state flags); the page with a run in its URL reopens
that run; the page without one behaves byte-identically to today.

**Acceptance Scenarios**:

1. **Given** a mid-flight run and a browser refresh, **When** the page reloads, **Then** it
   reopens the same run (URL-identified) with live progress, the gate, and the export stage
   intact.
2. **Given** several past runs on the server, **When** a tester opens the recent-runs list,
   **Then** they can reopen any of them (image, gate history, export state render from disk).
3. **Given** no run in the URL and no click on the list, **Then** the page renders exactly as
   before this feature.

---

### User Story 3 - A Chinese-speaking tester uses the tool in Chinese (Priority: P2)

A tester fills the run form entirely in Chinese: the labels, help text, buttons, and stage
titles read in simplified Chinese; free-text fields accept Chinese naturally; a usage context
like 朋友圈推广海报 derives the marketing lane directly (no assumption row to answer); a size
typed as ６０×４０厘米 (fullwidth digits, fullwidth ×, Chinese unit) parses to the same size as
"60x40cm". The gate panel's vocabulary (dimension names, option labels) renders in Chinese. The
playbook, in Chinese, is one click away inside the app and explains the whole journey, costs,
etiquette, and common English system messages.

**Why this priority**: the testers are non-technical and Chinese-speaking; an English form plus
gate rows firing on every Chinese brief would read as "broken" regardless of output quality.

**Independent Test**: free: Chinese usage-context phrasings derive their lanes with zero
assumption rows while every existing English derivation stays byte-identical (pinned against the
current literals); fullwidth/Chinese-unit sizes normalize to the same parse as their ASCII
equivalents while all current parses stay byte-identical; the form and playbook surfaces carry
the Chinese strings; select controls still submit the canonical English values.

**Acceptance Scenarios**:

1. **Given** usage_context 朋友圈推广海报 (or 小红书/海报/营销/宣传-class phrasing), **When**
   the register derives, **Then** the marketing lane matches directly as an explicit human
   statement and NO usage assumption row fires; 手举牌/活动-class phrasing derives the event
   lane the same way.
2. **Given** format_size ６０×４０厘米, **When** the size resolves, **Then** it equals the
   resolution of "60x40cm" with no clamped/unparseable assumption row.
3. **Given** any brief that derives a given profile today with English inputs, **When** the
   same brief runs after this feature, **Then** the derivation and prompt are byte-identical.
4. **Given** the run form in the browser, **Then** labels/help/buttons/stage titles are
   simplified Chinese, the select VALUES submitted are unchanged, and the gate panel's closed
   vocabulary renders in Chinese via a display mapping (server payloads unchanged).
5. **Given** the served playbook page, **Then** it covers the journey with costs (confirm
   ~$0.08 is the only spend; nudges re-derive free; layered export ~$0.5 opt-in), which fields
   accept free Chinese, single-flight etiquette, a common-messages table (English message to
   Chinese meaning), troubleshooting, and a feedback-channel placeholder.

---

### User Story 4 - The server survives remote misuse (Priority: P3)

A tester uploads an enormous file: the server refuses it with a named message instead of
swallowing it into memory. A generation worker wedges: a wall-clock timeout ends it, the failure
lands in the run's error surface, and the single-flight lock frees so the team is not locked out
until a restart. The service binds where its environment says (localhost behind the reverse
proxy by default) without code edits.

**Why this priority**: guards against the failure modes that only appear with remote,
non-technical, concurrent users; cheap to add, expensive to lack.

**Independent Test**: free: an over-cap upload gets the named refusal and no run dir; a stubbed
never-ending worker hits the timeout, the error surfaces, and the lock frees; bind/port come
from the environment with today's defaults byte-identical.

**Acceptance Scenarios**:

1. **Given** an upload larger than the cap, **When** it posts, **Then** a named 4xx returns,
   nothing is written, and the single-flight lock is untouched.
2. **Given** a worker exceeding the wall-clock timeout, **When** it fires, **Then** the worker
   ends, the run shows the named timeout error, and the next run can start without a server
   restart.
3. **Given** no environment overrides, **Then** the server binds exactly as today
   (localhost, same port).

---

### Edge Cases

- A run id in the URL that does not exist on disk: the page says so honestly and offers the
  recent-runs list; it never renders a phantom run.
- The recent-runs list on a fresh server (zero runs): an honest empty state, not an error.
- Mixed-language usage_context (中文 + English keywords): first match wins by the existing
  row-order semantics; the pinned English rows keep their precedence.
- Chinese keywords that could over-match (a single character like 墙 appearing inside an
  unrelated word): keyword choices favor multi-character terms; the blast radius is pinned by
  the byte-identity checks on all existing derivations.
- A fullwidth size string that is genuinely unparseable after normalization: the existing
  clamped/unparseable assumption row fires exactly as it does for ASCII garbage today.
- The brands base dir configured but missing at startup: runs refuse loudly at the logo
  resolution step with the named error; the server itself still serves (honest nulls, not a
  crash loop).
- Legacy answer keys with absolute paths (a user's local uncommitted key): absolute paths that
  exist still work (backward compatible); only dangling ones fail, with the named error.
- The worker timeout firing during a PAID generation: money is already spent; the error surface
  says the run may have partially completed and points at the run dir (honest, never silent).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Committed answer keys MUST reference brand assets by repo-relative paths resolved
  against a configurable brands base directory (default: the repo's brands directory);
  absolute paths that exist MUST keep working; the three committed keys are rewritten.
- **FR-002**: A brand whose logo cannot be resolved MUST fail loudly with an error naming the
  missing path; the hardcoded machine-specific fallback logo path is REMOVED (never a silent
  substitute).
- **FR-003**: The repository MUST carry a pinned dependency manifest sufficient to rebuild the
  runtime environment on a fresh Linux machine, with the Python version and any system-library
  prerequisites documented.
- **FR-004**: A committed deploy directory MUST provide: a bootstrap script (environment +
  directories), a service unit template (UTF-8 locale, key file from the environment, clean
  termination), a reverse-proxy template (TLS + access control in front; the app itself stays
  on localhost), and a README documenting the exact out-of-band handoff of secrets and brand
  assets. Nothing secret is committed.
- **FR-005**: The server's bind address and port MUST come from the environment (or arguments)
  with defaults byte-identical to today's behavior.
- **FR-006**: Uploads MUST be capped at a configurable size; an over-cap request receives a
  named 4xx refusal before any run state is created.
- **FR-007**: Spawned workers MUST have a wall-clock timeout; on expiry the worker ends, the
  run's error surface carries a named timeout message, and the single-flight lock frees.
- **FR-008**: A run-listing surface MUST enumerate runs newest-first with id, brand, creation
  time, gate state, and image/export presence; the UI MUST identify the current run in the URL
  and offer a recent-runs picker so a reload or reconnection reopens the run. With no run in
  the URL and no picker interaction, pre-017 behavior is byte-identical.
- **FR-009**: The register engine's usage rules MUST gain ADDITIVE Chinese keyword rows
  covering at least the marketing (朋友圈/小红书/海报/营销/宣传-class), event
  (手举牌/活动-class), wall-poster, and formal-document lanes; a Chinese match is an explicit
  human statement with the same standing as an English match (suppresses the vibe promotion per
  the 014 semantics). Every existing English derivation MUST stay byte-identical, pinned
  against the current literals.
- **FR-010**: Size input MUST normalize Chinese IME typography (fullwidth digits, fullwidth
  multiplication signs, 厘米/公分 units) before parsing; every currently-valid size string MUST
  parse byte-identically.
- **FR-011**: The run form and onboarding pages MUST present labels, help text, buttons, and
  stage titles in simplified Chinese; select controls MUST submit unchanged canonical values;
  the gate panel's closed server vocabulary MUST render in Chinese via a frontend display
  mapping. Server-side strings (errors, notes, traces) stay English in this feature.
- **FR-012**: A Chinese-primary playbook MUST be served from the app and sourced in docs/,
  covering: what the tool is (drafts a human finishes), the full journey with costs (the
  confirm click is the only spend, ~$0.08; nudges re-derive free; layered export ~$0.5,
  opt-in), field-by-field form guidance including which fields accept free Chinese,
  single-flight etiquette, a common-messages table (English message, Chinese meaning),
  troubleshooting, and a feedback-channel placeholder to fill when Richard answers.
- **FR-013**: Every change preserves byte-identity for untouched paths: English-input runs
  derive and render byte-identically; the existing self-test suite passes unchanged except
  where a pin gains an explicitly additive row.

### Key Entities

- **Brands base directory**: the configurable root under which committed keys' repo-relative
  asset paths resolve; provisioned out-of-band with the licensed/IP content.
- **Run listing entry**: id, brand, created, gate state, image present, export state; derived
  purely from the run dir on disk.
- **Chinese usage rows**: additive keyword-to-lane rows in the usage rules, same shape and
  precedence semantics as the existing rows.
- **Display mapping**: the frontend dictionary from the gate panel's closed English vocabulary
  to simplified Chinese display strings; server payloads unchanged.
- **Playbook page**: the served Chinese guide plus its markdown source.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A fresh clone on a scratch Linux directory bootstraps from the deploy artifacts
  and serves the app with zero code edits, given the two documented out-of-band items
  (provable free in a scratch dir/container).
- **SC-002**: A brief typed entirely in Chinese (usage_context 朋友圈推广海报, size ６０×４０厘米)
  derives the correct lane and size with ZERO gate assumption rows (provable free).
- **SC-003**: Every existing English derivation, prompt, and parse is byte-identical; the full
  self-test sweep stays green with only explicitly additive pin changes (provable free).
- **SC-004**: A browser refresh mid-run reopens the same run with its full state within one
  click; any past run on the server is reachable from the recent-runs list (provable free
  structurally; confirmed in the flow gate).
- **SC-005**: An over-cap upload and a wedged worker each produce their named error and leave
  the server usable without a restart (provable free with stubs).
- **SC-006**: The run form, onboarding, gate panel, and playbook read in simplified Chinese;
  submitted values are unchanged (provable free: form greps + payload assertions).
- **SC-007**: HUMAN FLOW GATE (the one paid step, never automated): one end-to-end run driven
  through the Chinese UI (form in Chinese, gate answered if fired, confirm, judge, export,
  download), ideally by a China-side tester over the deployed URL once provisioning happens;
  until then, driven locally through the Chinese UI by the operator. Verdict recorded in
  SYSTEM_MAP.

## Assumptions

- Hosting provisioning (provider, domain, credentials, who pays) is OUT of scope, blocked on
  docs/DEPLOYMENT_QUESTIONS.md answers; this feature is everything that does not depend on
  them.
- Single-flight (one generation at a time) remains the concurrency model; the playbook
  explains turn-taking. Richard's Q4 answer may spawn a future feature; nothing here forecloses
  it.
- Server-side strings stay English deliberately: they are contract-pinned by the falsifiable
  suite and edge-case-only; the playbook's common-messages table bridges them. Full server
  i18n is a possible later feature if testing shows the team hits those messages often.
- The Chinese keyword set ships as a starting vocabulary (finalized in plan), expected to grow
  from real team briefs; additions follow the same additive-row pattern.
- The kit/legacy paths and their machine-specific font fallbacks stay untouched (dormant);
  only the thin route must be portable.
- The existing single shared operator model continues (no accounts in this feature); access
  control lives in the reverse proxy per the deploy templates.
