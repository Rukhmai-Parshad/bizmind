# 06. Implementation Plan: BizMind v2

Rules for every milestone: work on a new Git branch, make small commits, run the tests before and after, and explain each change in plain language (what, why, how to verify). Do not touch files outside the milestone. Never edit existing migrations. Before moving on: run the app, verify the acceptance criteria in `01_PRD.md`, and record any unresolved issue at the bottom of this file.

**Milestone 0: Baseline and safety net**
- Inputs: the current code, `00_Current_State_Audit.md`.
- Tasks: create `.env` from `.env.example`, run migrations, run the existing tests, remove nothing yet. Add `pytest-django` or keep Django's runner, add a test settings tweak so tests use a temporary `MEDIA_ROOT` and clean up (S9). Write characterisation tests for the current web and API behaviour (login, upload, ownership 404, decision rules).
- Output: passing test suite, a list of anything that already fails.
- Done when: `python manage.py test` passes from a clean clone and leaves no files in `media/`.
- Dependency: none.

**Milestone 1: Security fixes (audit S1 to S5, S7, S8)**
- Tasks: one shared upload validator used by the web form and API serializer (extension, size, row limit, required columns, role); API upload role check (403); transaction and file cleanup on failure in the API; make Sales/Marketing/Finance endpoints read-only and compute revenue server-side; POST-only logout; DRF throttling plus login/signup rate limiting; SimpleJWT lifetimes, rotation and blacklist; Referrer-Policy and CSP headers; fix the PATCH duplicate check.
- Output: code plus tests for each fix (viewer upload via API returns 403, other user's object returns 404, record POST returns 405, GET logout does not log out, throttle triggers).
- Done when: every S1 to S5, S7, S8 item has a passing test and the PRD acceptance criteria on roles and ownership pass.
- Dependency: Milestone 0.

**Milestone 2: Data model and processing cleanup**
- Tasks: add `Dataset.status` and `row_count` with a data migration; replace `iterrows()` with vectorised processing and `bulk_create(batch_size=1000)`; add the 50,000-row limit; move decision thresholds into named constants with comments; add a dataset delete action (owner and role checks).
- Done when: a 10,000-row sample processes in under 10 seconds locally, and migrations apply cleanly on an empty PostgreSQL database and on a copy of existing data.
- Dependency: Milestone 1.

**Milestone 3: Minimalist UI redesign**
- Tasks: replace `static/css/style.css` and `static/dashboard/main.css` with one `static/css/app.css` following `04_UI_UX_Design_Brief.md`; rebuild `base.html` and all templates to the screen inventory in `03_App_Flow.md`; remove AOS, Font Awesome, the dark theme and `about.jpg`; self-host a pinned Chart.js or use CSS bars; merge About into Home and remove Contact unless the owner decides otherwise; add sample CSV downloads and empty states; add 403/404/500 pages.
- Done when: no external CSS/JS/font requests, all screens match the brief, keyboard navigation works, contrast passes, and no template has inline styles.
- Dependency: Milestone 2.

**Milestone 4: Quality, tests and CI**
- Tasks: tests for accounts, datasets, decisions rules (each rule above and below its threshold), dashboard queries and the API; GitHub Actions workflow running checks and tests with coverage; fix any flake8/ruff findings.
- Done when: coverage on accounts, datasets, decisions and api is at least 70%, CI is green on a pull request.
- Dependency: Milestone 3 (can overlap with 2 and 3 for tests).

**Milestone 5: Docker and deployment**
- Tasks: `Dockerfile` (python slim, non-root user, gunicorn), `docker-compose.yml` (web + Postgres + env file), `.dockerignore`, README run instructions; keep Render working with `render.yaml`; update `.env.example` for every new variable; confirm collectstatic and migrate run in `build.sh`.
- Done when: `docker compose up` gives a working app with Postgres from a clean clone, and the Render deploy succeeds.
- Dependency: Milestone 4.

**Milestone 6: Release**
- Tasks: owner-only usage metrics (signups, datasets processed, decisions generated) in the admin panel or a staff-only page; update README (screenshots, architecture, security notes, honest limitations); tag `v2.0.0`; smoke-test on production; document rollback (redeploy the previous Render deploy).
- Done when: the production site passes the PRD acceptance criteria and the README matches what is built.
- Dependency: Milestone 5.

**Deferred (not in v2):** LLM-generated insights, AWS deployment, password reset by email, Excel upload, teams.

## Unresolved issues log
(Add anything unfinished here, with the milestone and date.)

**Milestone 1 (2026-10-16), left open on purpose:**
- Production (Render): set `NUM_PROXIES` to the real number of proxies in front of the app (check `X-Forwarded-For` in a log). Until then IP-based limits see all users as one address. Owner: Milestone 5.
- Throttle counters use the per-process cache. Fine for the single gunicorn worker used today; if workers are added, move to a shared cache (Redis or database cache). Owner: Milestone 5.
- The CSP still allows `'unsafe-inline'` and three CDN hosts (unpkg, cdnjs, jsDelivr) because the current templates need them. Remove them when assets are self-hosted. Owner: Milestone 3.
- `PATCH`/`PUT` on `/api/datasets/` with a `file` stores a new CSV that is never processed or deleted (retention gap). `05_Backend_Schema.md` says dataset updates should not be allowed. Decide and fix. Owner: Milestone 2.
- The 50,000-row limit was added to the shared validator in Milestone 1 (so the web form and API share it). Milestone 2 should reuse `datasets.validators.MAX_ROWS`, not add a second one.
- A duplicate-name race (two identical uploads at the same instant) can still leave a stored file behind, because the file is written before the database constraint fires. Very narrow; revisit with the Milestone 2 status field.
- Audit S8 also asks for a deliberate `TIME_ZONE` (still `UTC`). Not in the Milestone 1 list; needs an owner decision.
- Open owner questions from `01_PRD.md` are still open: signup default role (ANALYST vs VIEWER), public `/stats/` (S6), and signup does not apply Django's password validators (docs/03 says it should).
- Check by eye in a browser: both Logout buttons look like before, `/api/docs/` (Swagger) loads, and the dashboard charts load, with no CSP errors in the console.

