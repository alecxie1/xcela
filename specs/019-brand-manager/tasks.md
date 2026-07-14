# Tasks: 019-brand-manager

One task = one commit; tests named per task in spec.md's test section.

- [x] T001 keys_dir() + consumer wiring + XCELA_ANSWER_KEYS_DIR + suite repoints + the five
      demo keys move to tests_support/demo_keys/ + answer_keys/ gitignored (.gitkeep).
      Bar: FULL sweep green. Commit: `feat(019): answer keys become runtime state (T001)`.
- [x] T002 manage deciders + routes (GET /brands/detail, POST /brand/<id>/update|logo|delete
      with the inflight 409 guard) + test_brand_manager.py checks.
      Commit: `feat(019): brand manager routes (T002)`.
- [ ] T003 frontend/manage.html (品牌管理) + shared nav on all pages + run-form asset-status
      line + playbook section + greps. Commit: `feat(019): brand manager UI (T003)`.
- [ ] T004 shared logo format guard (wizard + manager) + tests; docs currency; full sweep;
      push origin + vm; VM ops (demo keys copied back as runtime state, restart).
      Commit: `feat(019): logo format guard + docs + ship (T004)`.
- [ ] T005 Kevin comms (paste-able Chinese) + HUMAN GATE: Kevin/designer manage brands
      unassisted; record the verdict here.
