# 07. Prompts to give your AI coding tool (one at a time)

How to use these:
1. Put the files `00` to `06` in a `docs/` folder in the BizMind repo so the AI can read them.
2. Give **one prompt at a time**, in order. Do not move on until the done-when checks pass.
3. Before you commit, read the diff. For every changed file, write one line in your diary: what changed and why. If you cannot explain a change, ask the AI to explain it first.
4. After each milestone, run the Explain-Back prompt at the bottom. This is what prepares you for interviews.

---

## Prompt 0: Baseline
You are working on the BizMind Django project. First read every file in `docs/` (00 to 06) in full, then read the code. Do Milestone 0 only. Tasks: confirm the project runs, run the existing tests and report the result, make tests use a temporary MEDIA_ROOT and clean up after themselves, and write characterisation tests for current login, upload, ownership (another user's dataset must return 404) and the decision rules. Do not change application behaviour. Do not edit existing migrations. List any contradiction between the docs and the code before you start. At the end, give me: files changed, why, and the exact commands to verify.

## Prompt 1: Security fixes
Read `docs/` and the code. Do Milestone 1 only, using `00_Current_State_Audit.md` items S1, S2, S3, S4, S5, S7, S8. First confirm each item by pointing to the exact file and lines, and tell me if any is wrong. Then fix them one at a time, each with its own commit and its own test. Specifically: one shared upload validator for web and API, API role check (403), cleanup on failure, read-only record endpoints with server-computed revenue, POST-only logout, throttling and rate limiting on login/signup/token, SimpleJWT lifetimes with rotation and blacklist, Referrer-Policy and CSP, and the PATCH duplicate-check fix. Do not redesign the UI. Explain every change in plain language I can repeat in an interview.

## Prompt 2: Data model and processing
Read `docs/` and the code. Do Milestone 2 only. Add Dataset.status and row_count with a safe data migration (new migration only), replace iterrows with vectorised pandas and bulk_create in batches of 1000, add the 50,000-row limit, move decision thresholds into named, commented constants, and add a dataset delete action for owners with ADMIN or ANALYST role. Add tests. Show me before-and-after timing for a 10,000-row sample CSV. Do not touch templates or CSS.

## Prompt 3: Minimalist UI
Read `docs/`, especially `03_App_Flow.md` and `04_UI_UX_Design_Brief.md`. Do Milestone 3 only. Replace the current CSS with a single `static/css/app.css` using the palette, typography and rules in the brief. Rebuild base.html and every template for the screens in the inventory. Remove AOS, Font Awesome, the dark theme and about.jpg. Self-host a pinned Chart.js or use CSS bars. Merge About into Home. Add empty states, sample CSV downloads and 403/404/500 pages. No external CSS, JS or fonts, no inline styles, no animations beyond a 150 ms hover colour change. Do not change Python logic except what the templates strictly need. Tell me how to verify each screen, including keyboard navigation.

## Prompt 4: Tests and CI
Read `docs/`. Do Milestone 4 only. Add tests for accounts, datasets, every decision rule (above and below its threshold), dashboard queries, and the API (auth, ownership, roles, read-only records, throttling). Add a GitHub Actions workflow that installs dependencies, runs `manage.py check` and the tests with coverage, and fails on errors. Report coverage per app and fix gaps until accounts, datasets, decisions and api are at least 70%.

## Prompt 5: Docker and deployment
Read `docs/`. Do Milestone 5 only. Add a Dockerfile (python slim, non-root user, gunicorn), docker-compose.yml with Postgres, .dockerignore, and update .env.example and README with exact run steps. Keep render.yaml and build.sh working. Explain each Dockerfile line. Verify with `docker compose up` from a clean clone.

## Prompt 6: Release
Read `docs/`. Do Milestone 6 only. Add the owner-only usage metrics page or admin view (signups, datasets processed, decisions generated, no personal data), update the README to match what is really built (include limitations), and give me a smoke-test checklist and a rollback plan. Do not claim anything in the README that is not implemented.

---

## Explain-Back prompt (use after every milestone)
Act as an interviewer for a junior Django backend role. Based on the changes in this milestone, ask me 5 questions, one at a time, starting easy and getting harder. Wait for my answer each time. After each answer, tell me what was correct, what was missing, and give a better 30-second version. At the end, list the topics I should revise.
