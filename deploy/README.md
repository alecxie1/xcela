# deploy/ — feature 017: everything a fresh Linux VM needs (except the two secrets)

The provisioning decisions (provider, region, domain, who holds the password) are driven by
`docs/DEPLOYMENT_QUESTIONS.md`. This directory is answer-independent: it works wherever those
answers land. Region constraint: the OpenAI/Anthropic APIs are blocked from mainland China
and unsupported in Hong Kong, so host where both work AND the team can reach (Singapore or
Tokyo are the proven sweet spots).

## The exact handoff (in order)

1. **Clone + bootstrap** (no secrets involved):
   ```bash
   git clone <repo> /opt/xcela/handyprint-design-tool
   cd /opt/xcela/handyprint-design-tool && bash deploy/bootstrap.sh
   # system prerequisite for opencv (kit/legacy paths): apt install libgl1 libglib2.0-0
   ```
2. **Out-of-band item 1: API keys.** Copy the key file to the service user's home,
   NEVER into the repo:
   ```
   ~/.hermes/.env    ->  OPENAI_API_KEY=...  ANTHROPIC_API_KEY=...
   ```
3. **Out-of-band item 2: brand assets.** `scp -r` the `brands/` directory (logos, licensed
   fonts) into the repo root (or anywhere, exporting `XCELA_BRANDS_DIR=<path>`). Re-run
   `bash deploy/bootstrap.sh` to confirm "all committed brand keys resolve their logos".
4. **Service:** `sudo cp deploy/xcela.service /etc/systemd/system/`, edit User/paths,
   `sudo systemctl daemon-reload && sudo systemctl enable --now xcela`.
5. **Proxy:** fill the two placeholders in `deploy/Caddyfile` (domain; hashed password from
   `caddy hash-password`), then run caddy as a service. The app itself stays on localhost.
6. **Hand the team**: the URL, the password, and the in-app playbook link (`/playbook`).

## Operations notes

- **Restart after every update**: `server.py` loads once; `git pull` without
  `systemctl restart xcela` serves stale code (the known reload gotcha).
- **Disk**: run dirs live in `output/` (2.5-50MB each; a layered export is the big one).
  Prune old `output/run_*` dirs or mount a data disk; nothing else grows.
- **Spend**: every confirmed run is ~$0.08; a layered export ~$0.5. The pre-spend gate makes
  all spend explicit; watch the provider dashboards for totals.
- **One at a time**: the app is single-flight by design (a busy click answers 409 "a run is
  already in flight"); the playbook tells the team to take turns.
- **Env knobs** (all optional): `XCELA_BIND`, `XCELA_PORT`, `XCELA_MAX_UPLOAD_MB` (32),
  `XCELA_WORKER_TIMEOUT_S` (1800), `XCELA_BRANDS_DIR`.
