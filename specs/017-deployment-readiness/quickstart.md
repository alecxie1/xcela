# Quickstart: Deployment Readiness + Chinese-Ready UI (017)

## 1. FREE structural validation (always first)
```bash
.venv/bin/python test_deploy_readiness.py       # the new suite, zero paid calls
# the no-regression sweep (all suites green; only explicitly additive pin changes):
for t in test_*.py; do .venv/bin/python "$t"; done
```

## 2. FREE fresh-clone bootstrap proof (SC-001, scratch dir)
```bash
git clone . /tmp/xcela-fresh && cd /tmp/xcela-fresh
bash deploy/bootstrap.sh          # venv + requirements + dirs; NAMED messages for the
                                  # two missing out-of-band items (keys file, brands dir)
# simulate the handoff: point at the real brands dir + existing keys
XCELA_BRANDS_DIR=/home/alecx/workspace/handyprint-design-tool/brands \
  .venv/bin/python frontend/server.py 8770
# expect: serves; /brands lists the three brands; a dry conductor plan resolves the logo
```

## 3. FREE Chinese-input proof (SC-002)
```bash
# usage_context 朋友圈推广海报 -> marketing lane, ZERO assumption rows;
# format_size ６０×４０厘米 -> same resolution as 60x40cm (both asserted in the suite);
# live check: fill the (now Chinese) form with the Chinese brief, launch, and read the
# 3b gate: derived register = marketing, no usage/size rows.
```

## 4. FREE resume proof (SC-004)
Open a run, copy the URL (now carrying #run_...), close the tab, reopen the URL: the same
run renders with gate/image/export state. The 最近的运行 (recent runs) panel lists past runs;
clicking one opens it.

## 5. Guards (SC-005, free)
Over-cap upload -> 413 named; stubbed never-ending worker -> named timeout error, lock free,
next run starts without a restart (both in the suite).

## 6. HUMAN FLOW GATE (SC-007, the one paid step, ~$0.08 + optional export)
One end-to-end run driven through the CHINESE UI: fill the form in Chinese, confirm at the
gate, judge the image, optionally export layers, download the zip, and reopen the run from
the URL after a deliberate refresh. Ideally driven by a China-side tester over the deployed
URL once provisioning happens; until then, locally by the operator. Verdict recorded in
SYSTEM_MAP + tasks.md.

## Deployment day (after Richard's answers; OUT of this feature)
Provision the VM (Singapore/Tokyo), run deploy/bootstrap.sh, scp the brands dir +
~/.hermes/.env, fill the Caddyfile placeholders (domain + hashed password), systemctl enable,
send the team the URL + password + /playbook link, fill the playbook's feedback-channel line.
