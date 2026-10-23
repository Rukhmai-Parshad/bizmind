# BizMind: project context for any AI assistant

Read this file first. It replaces the whole earlier chat history. Where this file and the code disagree, trust the code and tell the owner.

## 1. What BizMind is
A Django web app and REST API. A user uploads a sales, marketing or finance CSV. Fixed rules produce "decisions" (title, insight, recommendation, explanation, action, impact, confidence score and reason). It is a portfolio project of Rukhmai Parshad (entry-level Python/Django developer, India) and must be accurate, honest and professional.

- Live site: https://bizmind-4un7.onrender.com (Render free plan, Singapore)
- GitHub: Rukhmai-Parshad/bizmind. Branch `main` is deployed. Work happens on feature branches and is merged by Pull Request.
- Contact used on legal pages: Rukhmai Parshad, rukhmaiparshad@gmail.com. Do not invent any other business detail.

## 2. Stack
Python 3.13.5, Django 5.2.9, Django REST Framework, SimpleJWT (with token blacklist), drf-spectacular plus drf-spectacular-sidecar (Swagger served from /static/), pandas, WhiteNoise, gunicorn. PostgreSQL on Render (DATABASE_URL), SQLite locally. No Vite, no React, no Tailwind, no JS framework.

Deploy: `render.yaml` and `build.sh` (collectstatic, migrate). Environment variables read by settings (SEC-1 added ADMIN_URL, DATABASE_SSL_REQUIRE, HSTS_SECONDS; the admin now lives at /site-admin/ by default; DATABASE_URL is required when DEBUG is off): SECRET_KEY (required), DEBUG, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, DATABASE_URL, NUM_PROXIES (set to 1 on Render), RENDER_EXTERNAL_HOSTNAME. See `.env.example`.

## 3. Apps and key files
- `accounts`: custom User (email is the login, roles ADMIN / ANALYST / VIEWER, signup sets ANALYST), login/signup/logout views, `ratelimit.py`.
- `datasets`: Dataset model, upload form, `validators.py` (one shared upload validator for web and API), `services.py` (all-or-nothing save and process with cleanup).
- `sales`, `marketing`, `finance`: record models, CSV processors, queries.
- `decisions`: Decision model, rule engine, confidence logic.
- `dashboard`, `core` (home, privacy, terms, favicon route).
- `api`: serializers, viewsets, `permissions.py`, `throttles.py`, `auth_views.py`.
- `bizmind`: settings, urls, `middleware.py` (CSP and Referrer-Policy), `test_runner.py`, `testing.py`.
- `templates/`: `base.html`, `base_public.html`, `base_app.html`, page templates, `icons/` partials, `partials/toasts.html`.
- `static/css/app.css`, `static/js/app.js`, `static/img/favicon.svg`, `static/samples/*.csv`.
- `docs/`: 00 audit, 01 PRD, 02 TRD, 03 app flow, 04 UI/UX brief, 05 schema, 06 plan, 07 prompts, this file.

## 4. What is already done (do not redo or undo)
- Milestone 0: test safety net. Isolated temporary media root for tests. Characterisation tests.
- Milestone 1 (security): shared upload validator and API role check (viewer gets 403); cleanup on failed API upload; Sales/Marketing/Finance API endpoints are read-only and revenue is computed on the server; logout is POST only; throttling on login, signup and token endpoints; JWT access 15 min, refresh 7 days with rotation and blacklist; CSP and Referrer-Policy; PATCH duplicate-check fix.
- Milestone 3 (design): warm minimalist redesign (landing, auth split layout, sidebar app shell, dashboard, datasets, upload, dataset detail, decisions, 403/404/500), /privacy/ and /terms/ pages, SVG favicon. Guard tests in `core/test_redesign.py` enforce the design rules below.
- Current test count on the owner's machine: 250, all passing.

## 5. Hard constraints (never break these)
- Django templates only. CSP is `'self'` only: no external fonts, CSS, JS, images or CDN; no inline `style=`, no `<style>`, no inline `<script>`.
- Logout stays a POST form with a CSRF token.
- Never edit existing migrations. New migrations only.
- Design rules: no gradients, no emoji, no pill-shaped buttons (radius 6px buttons and inputs, 4px chips, nothing above 10px), no em dashes or en dashes in visible text or docs, no scroll animations, parallax or cursor effects, no AI stock images, no "made with AI" tag. Only 120 to 150ms colour transitions.
- No fake reviews, testimonials, logos, metrics, counters or unverifiable claims. Every claim on the site must be true in the code.
- Palette tokens on `:root`: bg #F3EEE6, oatmeal #E9E2D7, surface #FBF8F3, sand #DCC8B5, ink #4D362B, muted #6B5546, coffee #8C6F5D, primary #611E2F, primary-hover #4A1623, sage #A7B19A (decorative only), success-text #4A5D3F, warning-text #8A5A12, danger-text #A12B2B. Text contrast at least 4.5:1.
- Fonts: system stacks only (serif headings, sans body).
- Do not add: dark mode, cookie banner (unless a real need is found), analytics, UTM tracking, loading animations, scroll progress bar, floating contact button, refund policy (no payments), LocalBusiness schema, site-wide search.

## 6. Known open items
- Signup password validators: fixed in SEC-1 (see docs/SECURITY_AUDIT.md).
- TIME_ZONE is UTC.
- Throttle counters use a local-memory cache, so they assume one gunicorn worker.
- PATCH or PUT of a dataset with a file stores a CSV that is never processed or deleted.
- Datasets list runs one extra query per row. No delete-dataset button yet. DRF lists give an unordered-pagination warning. drf-spectacular prints schema warnings.
- Legal pages (/privacy/, /terms/) are written from the code and are not legal advice; a lawyer should review them.

## 7. Planned tasks (do ONE per chat)
- L1: DPDP consent checkbox at signup (new migration `consented_at`) and /privacy/ update.
- L2: /cookies/ page, /terms/ accuracy, footer links on every page, "Last updated" dates.
- L3: self-service account deletion (settings page with confirmation, POST, deletes account and all data, then logout).
- A1: accessibility pass (labels, aria-describedby, error summary, password show/hide button, skip link, contrast list).
- A2: small details (mobile menu check, sticky header, back-to-top anchor, print stylesheet, FAQ with details/summary, footer year via `{% now "Y" %}`).
- S1: SEO (unique titles and meta descriptions, one H1 per page, canonical from a SITE_URL env variable, noindex on logged-in pages, robots.txt, sitemap.xml, llms.txt, JSON-LD for WebSite and SoftwareApplication only, breadcrumbs).
- SEC: full security audit (secrets in git history, env vars, production settings, admin URL, password validators, authorization test matrix, dependency audit with pip-audit, exposed files) written to `docs/SECURITY_AUDIT.md`.
- D1: Docker (Dockerfile, docker-compose with Postgres, .dockerignore, README steps). Keep Render working.
- M2: processing cleanup (vectorised pandas, bulk_create in batches, Dataset.status, row limit).

## 8. How the owner works (follow this)
- Windows, PowerShell, a Python venv, Git. The owner is a beginner with Git and explains things best in Hinglish, but prompts and code are in English. Be clear and brief.
- The owner cannot receive pasted whole files easily. Deliver ONLY the changed or new files, in a zip that keeps full folder paths. The owner applies it with `Expand-Archive -Path <zip> -DestinationPath . -Force`. State which old files must be deleted (the owner uses `git rm`) and the name of any new migration.
- Do not print whole files back in the chat. Give a 5-line summary, the list of changed files, and the commands to verify.
- Everything must pass `python manage.py test` and `python manage.py collectstatic --noinput` before the owner commits. Tell the owner not to commit until the test output ends with OK.
- The owner commits only named folders, never `git add .` (many files show CRLF line-ending noise).
- The owner may have hand-edited files after your last delivery. If you did not just read the file from the attached zip, ask for a fresh zip instead of guessing.
- Tell the owner honestly what you could not verify. Never claim zero mistakes. No legal advice claims.
- Work on one task only. If it grows too large, stop and say so before writing code.
