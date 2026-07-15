# Tasks: 021-auth-multitenancy (IN PROGRESS; spec.md is the approved plan)

- [x] T001 frontend/auth.py core (scrypt store, disk sessions, CLI add/remove/list) +
      asset_paths.users_file()/XCELA_USERS_FILE + gitignore + test_auth.py core checks.
      DONE 2026-07-14: test_auth 6/6 (hermetic tmp XCELA_USERS_FILE); re-add = the
      password reset; removing the last user deletes users.json (auth deactivates,
      never a lockout); removed users lose live sessions via the role() check.
- [ ] T002 the gate: _send optional headers, do_GET/do_POST choke points, /login /logout
      /whoami + login.html + jf() 401 wrapper + nav user chips + THE PIN (no users file =
      open access byte-identical, ephemeral-server proven).
- [ ] T003 ownership: run_meta owner + list filters + per-run 403 guards; brand owner
      (onboard threading, manager permissions, super-only owner assign) + the
      userA/userB/super x owned-A/owned-B/unowned matrix tests BY VALUE.
- [ ] T004 docs (.env.example, README, deploy/README, playbook 登录 section) + full sweep +
      ship origin+vm (VM stays auth-OFF) + Kevin enable-guide (Chinese).
- [ ] T005 HUMAN GATE: Kevin creates users; his team verifies isolation unassisted.
