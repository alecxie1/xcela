# Tasks: GitHub Handoff (018)

Plan-lite feature (mechanical scope, verified inventory): the spec doubles as the plan; the
binding facts are in the spec's FRs. Tests live in `test_deploy_readiness.py` (extended: this
is deployment-readiness work) plus the full-sweep proof. One task = one commit.

- [x] T001 `harness/runtime_env.py` (`load_runtime_env()`: process env > `<repo>/.env` >
      `~/.hermes/.env`, override=False both loads) + switch the SIX live call sites
      (harness/approve.py, harness/generate.py, harness/scene_author.py,
      register/blind_score.py, register/calibrate_from_reference.py,
      register/reference_style_to_prompt.py); `.env.example` at root; `.env` in .gitignore.
      Tests (test_deploy_readiness check10): precedence by VALUE with temp files/env; zero
      `override=True` outside legacy/; all six sites import the loader; `.env.example`
      covers every var the code reads (grep-derived). Commit:
      `feat(018): one env loader, standard precedence, .env.example (T001)`.

- [x] T002 deploy/ updates: bootstrap's out-of-band check accepts `<repo>/.env` OR
      `~/.hermes/.env` (names both); xcela.service gains
      `EnvironmentFile=-/opt/xcela/handyprint-design-tool/.env`; README rewritten for a
      THIRD-PARTY deployer (their keys, their VM; our PRODUCTION section marked as the
      reference deployment). Commit: `feat(018): deploy artifacts for a third-party deployer (T002)`.

- [x] T003 Legacy sweep: `git mv` the 21 root one-off scripts (analyze_*, baseline_*,
      benchmark_*, build_font_index, extract_typography, make_contact_sheet*, ocr_alec_batch,
      ocr_readback, proto_root_a, provenance, psd_to_cutout, rescore_saved, score_*, viewer)
      + the 7 legacy manual tests (test_brand_analysis, test_brand_gen, test_full_pipeline,
      test_psd_to_cutout, test_reffeed, test_reffeed_AUTO, test_refstyle_selftest) into
      `legacy/` with `legacy/README.md`; extract_colors.py + extract_text_layer.py STAY
      (live imports); fix legacy-internal imports minimally or note as unmaintained. FULL
      suite green after. Commit: `chore(018): legacy scripts to legacy/ (T003)`.

- [x] T004 Root `README.md` for outsiders (purpose, layout, quickstart, env table, tests,
      deploy + docs pointers) + CLAUDE.md/SYSTEM_MAP currency. Commit:
      `docs(018): outsider README + currency (T004)`.

- [ ] T005 Push `master` to origin (needs Alec's GitHub credentials: run
      `git push origin master` in the session shell or paste a token); verify
      `git ls-remote origin master` == local HEAD; Alec invites the CTO in the GitHub UI.
      HUMAN GATE (SC-005): the CTO's clone-to-first-run without questions.
