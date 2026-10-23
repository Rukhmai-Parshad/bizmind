# 02. Technical Requirements Document (TRD): BizMind v2

**Platforms:** Responsive web app (desktop first, works on mobile browsers) plus a REST API. No native apps.

**Frontend and hosting:** Server-rendered Django templates, one hand-written CSS file (no framework, no CDN fonts or icon packs), small vanilla JS only where needed. Charts: Chart.js pinned to an exact version and self-hosted in `static/` (or replaced by plain CSS/SVG bars). Hosting: Render (Singapore) now, using the existing `render.yaml`. Containerised with Docker for local and later AWS use.

**Backend and database:** Python 3.13, Django 5.2.x, DRF, SimpleJWT, drf-spectacular, pandas, WhiteNoise, gunicorn. PostgreSQL in production (Render managed DB), SQLite only for local quick runs via `DATABASE_URL`. The existing `database_config()` parser in settings stays.

**Authentication and roles:**
- Web: email + password, Django sessions, CSRF protected. API: JWT (access + refresh).
- Roles: ADMIN (everything, admin panel), ANALYST (upload, view own data), VIEWER (view own data only).
- Role checks must live in one reusable place (permission class for API, decorator/mixin for views), never copy-pasted.

**External services and APIs:** None required for v1. (An LLM provider is explicitly deferred. When added later, its key goes in an environment variable and is never committed.)

**Architecture:**
- Apps: `accounts` (user, auth), `datasets` (upload, validation, processing orchestration), `sales` / `marketing` / `finance` (records, CSV schema, queries, rules), `decisions` (Decision model, engine, confidence), `dashboard`, `core` (public pages), `api` (serializers, viewsets).
- Data flow: Upload (form or API) -> shared validator -> store file -> `process_dataset` in one transaction -> domain CSV processor -> bulk-create records -> decision engine runs domain rules -> Decision rows -> dashboard/API read them.
- Principle: analysis (metrics) is separate from decision rules, which are separate from presentation.

**Security and privacy:**
- Sensitive data: users' business CSV contents and email addresses. Uploaded files are deleted after processing; only parsed records and decisions are stored.
- Every query that returns user data is filtered by owner. Object access by another user's ID returns 404.
- Required: SECRET_KEY from environment (already), DEBUG default False, HTTPS redirect, secure cookies, HSTS (already). To add: throttling on login/signup/token endpoints, POST-only logout, SimpleJWT rotation + blacklist and short access lifetime (15 minutes), Referrer-Policy and a Content-Security-Policy that allows only self-hosted assets.
- Retention and privacy (DPDP Act 2023): signup requires a ticked consent box ("I am 18 or older and agree to the Terms and Privacy Policy") and stores `User.consented_at`. The user model keeps only email, password hash, role, `date_joined` and `consented_at`; `first_name`, `last_name` and `last_login` were removed (migration `accounts/0004_consent_and_data_minimisation`). A user can delete a dataset, which cascades to its records and decisions, and can delete their whole account in Settings (`/accounts/settings/delete/`, password and tick required, POST with CSRF). Account deletion removes datasets, rows, decisions, API refresh-token records, all login sessions and any stored CSV file. `build.sh` runs `clearsessions` and `flushexpiredtokens` on each deploy. Logs carry the dataset type and user id, never dataset names. Legal pages: `/privacy/`, `/terms/`, `/cookies/`. Only three cookies exist (`sessionid`, `csrftoken`, `messages`), all strictly necessary, so there is no cookie banner. A test fails if the app ever sets another cookie.
- Secrets: never commit `.env`, `db.sqlite3` or `media/`.

**Performance and reliability targets:**
- 10,000-row CSV processed in under 10 s on the Render free plan; 50,000-row limit per file for v1 (reject larger with a clear message).
- Use vectorised pandas and `bulk_create(batch_size=1000)`, no `iterrows()`.
- Dashboard queries use aggregation and `select_related`; no N+1 queries.
- Uptime: best effort on free tier. Backups: Render managed DB defaults.

**Environments and delivery:**
- Development: Docker Compose (web + Postgres) or local venv with SQLite.
- Production: Render using `render.yaml` (`build.sh` runs collectstatic and migrate).
- CI: GitHub Actions on every push and PR: install, `python manage.py check`, run tests with coverage, fail if tests fail.
- Branching: feature branches, small commits, PR to `main`.

**Key technical decisions and tradeoffs:**
| Decision | Reason | Alternative |
|---|---|---|
| Keep Django templates, no React | Faster to finish, easier to explain in interviews | React SPA |
| Rule-based decisions, no ML/LLM in v1 | Deterministic, testable, explainable | LLM insights (later milestone) |
| One shared upload validator for web and API | Fixes audit S1 permanently | Separate validators (current, error-prone) |
| Make record endpoints read-only | Keeps decisions consistent with data (audit S2) | Allow edits and regenerate decisions |
| Self-host assets, drop AOS and Font Awesome | Minimal design, faster, CSP-friendly | Keep CDNs |
| Docker for local and deployment | Reproducible, resume-relevant | Plain venv only |
