# Tasks: 021-auth-multitenancy (IN PROGRESS; spec.md is the approved plan)

- [x] T001 frontend/auth.py core (scrypt store, disk sessions, CLI add/remove/list) +
      asset_paths.users_file()/XCELA_USERS_FILE + gitignore + test_auth.py core checks.
      DONE 2026-07-14: test_auth 6/6 (hermetic tmp XCELA_USERS_FILE); re-add = the
      password reset; removing the last user deletes users.json (auth deactivates,
      never a lockout); removed users lose live sessions via the role() check.
- [x] T002 the gate: _send optional headers, do_GET/do_POST choke points, /login /logout
      /whoami + login.html + jf() 401 wrapper + nav user chips + THE PIN (no users file =
      open access byte-identical, ephemeral-server proven).
      DONE 2026-07-14: test_auth 9/9 (checks 7-8 are LIVE ephemeral-server round trips:
      the pin, 302/401, cookie set/opens/logout-kills); the two pinned form-greps that
      named raw fetch() moved to the jf() values dated in place (brand_manager,
      deploy_readiness); XCELA_USERS_FILE documented in .env.example (the deploy sweep
      enforces coverage, so it moved up from T004); full sweep green.
- [x] T003 ownership: run_meta owner + list filters + per-run 403 guards; brand owner
      (onboard threading, manager permissions, super-only owner assign) + the
      userA/userB/super x owned-A/owned-B/unowned matrix tests BY VALUE.
      DONE 2026-07-14: test_auth 13/13 (checks 10-12 by value, check 13 a live-server
      matrix incl. foreign-brand launch refused as unknown before any run dir);
      visible_to/write_allowed in brand_manager (one policy home, separately named);
      run_meta_payload pure + pinned byte-identical with auth off; owner column in the
      manager (sent only when edited), owner label in the runs picker; full sweep green.
- [ ] T004 docs (.env.example, README, deploy/README, playbook 登录 section) + full sweep +
      ship origin+vm (VM stays auth-OFF) + Kevin enable-guide (Chinese).
- [ ] T005 HUMAN GATE: Kevin creates users; his team verifies isolation unassisted.
