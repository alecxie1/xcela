# deploy/ — everything a fresh Linux VM needs (except your secrets)

Written for a THIRD-PARTY deployer (018). TWO equivalent paths: the root Dockerfile +
docker-compose.yml (any container platform; remember the three state volumes: output/,
brands/, answer_keys/), or the bare-VM path below (bootstrap + systemd + Caddy). Either way:
clone, add YOUR OWN API keys via env or .env, serve.
Region constraint: the OpenAI/Anthropic APIs are blocked from mainland China and unsupported
in Hong Kong, so host where both work AND your team can reach (Singapore or Tokyo are the
proven sweet spots). Access model is your call: the app has no login; put Caddy's basic_auth
or your own gateway in front, or rely on an unguessable hostname for a small trusted group.

## The exact handoff (in order)

1. **Clone + bootstrap** (no secrets involved):
   ```bash
   git clone <repo> /opt/xcela/handyprint-design-tool
   cd /opt/xcela/handyprint-design-tool && bash deploy/bootstrap.sh
   # system prerequisite for opencv (kit/legacy paths): apt install libgl1 libglib2.0-0
   ```
2. **Out-of-band item 1: YOUR API keys.** Standard precedence (harness/runtime_env.py):
   real environment variables win; else `<repo>/.env`; else the legacy `~/.hermes/.env`.
   Simplest: `cp .env.example .env` in the repo root and fill in `OPENAI_API_KEY` +
   `ANTHROPIC_API_KEY`. Never commit `.env` (gitignored).
3. **Out-of-band item 2 (now OPTIONAL): brand assets.** The designer onboards brands himself
   via `/onboard` (the wizard writes `brands/<brand>/` + the key). To make the committed demo
   brands (CJXQ etc.) work day one, `scp -r` our `brands/` directory into the repo root (or
   anywhere, exporting `XCELA_BRANDS_DIR=<path>`); a committed key whose logo is absent
   refuses loudly at run time and lists in bootstrap's resolution report.
4. **Service:** `sudo cp deploy/xcela.service /etc/systemd/system/`, edit User/paths,
   `sudo systemctl daemon-reload && sudo systemctl enable --now xcela`.
5. **Proxy:** fill YOUR_DOMAIN in `deploy/Caddyfile` with an UNGUESSABLE subdomain (the
   no-login decision makes the URL the only gate), then run caddy as a service. The app
   itself stays on localhost.
6. **Hand the designer**: the URL and the in-app playbook link (`/playbook`).

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

## REFERENCE DEPLOYMENT (ours, deployed 2026-07-12; not required for yours)

- **URL**: https://xcela-17ad22.xcela.net (the unguessable hostname IS the access gate; no login)
- **VM**: DigitalOcean SGP1, 188.166.238.61, Ubuntu 24.04, user `xcela`, repo at
  `/opt/xcela/handyprint-design-tool`, bare repo at `/opt/xcela/repo.git`
- **SSH**: `ssh -i ~/.ssh/xcela_deploy root@188.166.238.61` (the deploy key lives on Alec's WSL)
- **Update procedure** (from the dev machine):
  ```bash
  GIT_SSH_COMMAND="ssh -i ~/.ssh/xcela_deploy" git push vm master
  ssh -i ~/.ssh/xcela_deploy root@188.166.238.61 \
    'cd /opt/xcela/handyprint-design-tool && sudo -u xcela git pull -q && systemctl restart xcela'
  ```
- Known missing on the VM (honest, per bootstrap's report): logos for the historical keys
  chajiuxingqiu/taichi/xiucai (CJXQ + aia resolve; new brands arrive via the wizard).
- Fonts (brands/*/fonts) deliberately NOT copied (kit/legacy only; 188MB).
