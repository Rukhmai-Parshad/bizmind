# BizMind security audit, task SEC-1

Scope: secrets, environment variables, production settings, admin, authentication. This is one pass by an AI assistant over the zip you supplied. It is not a penetration test and it does not prove the site is secure. Other SEC items (authorization test matrix, pip-audit, exposed files in depth) are not covered here.

## What could not be verified (read this first)

1. **Git history was NOT scanned.** The zip has no `.git` folder, so I could not search past commits or other branches, and I could not confirm what is tracked. Run the commands in "What you must do" step 1 yourself.
2. Real Render settings (environment variable values, the admin accounts in the production database, whether Render's Postgres enforces SSL) are not visible to me.
3. Nothing was tested against PostgreSQL or behind Render's proxy. Tests ran on SQLite with Python 3.12 (the project uses 3.13.5).
4. The `DATABASE_SSL_REQUIRE` switch is covered by a unit test of the setting only, not by a real encrypted connection.
5. HSTS, secure cookies and redirects are checked as setting values and with `check --deploy`, not on the live site.
6. Dependency vulnerabilities (pip-audit) were not checked.

## Working tree scan (what I did verify)

- Searched all files except `static/` for private keys, cloud and GitHub tokens, `sk-` keys, URLs with embedded passwords, and hard-coded `password =` / `secret =` assignments. No real secret found. The only credential-like values are fake test fixtures (`strong-password-123`, a fake DB URL in `bizmind/test_security_settings.py`).
- No `.env`, `*.sqlite3`, `media/`, `staticfiles/`, `.pem` or `.key` file is inside the zip. `.gitignore` already listed `.env`, `*.sqlite3`, `media/`, `staticfiles/`. I added `.env.*` (but not `.env.example`), `*.pem`, `*.key`, `*.log`.
- `.env.example` holds placeholders only.
- No default credentials: no data migration, fixture or command creates a user (a test checks that a fresh database has zero users); `README.md`, `build.sh`, `render.yaml` contain no login. Accounts that exist in the Render database cannot be seen by me.

## Environment variables the code reads

| Variable | Where | Production | Default |
|---|---|---|---|
| SECRET_KEY | settings | **Required** (app stops with a clear message) | none |
| DATABASE_URL | settings | **Required when DEBUG is not True** (new) | sqlite only if DEBUG=True |
| DEBUG | settings | No | off; only the word `true` turns it on |
| ALLOWED_HOSTS | settings | No | RENDER_EXTERNAL_HOSTNAME |
| CSRF_TRUSTED_ORIGINS | settings | No | https://RENDER_EXTERNAL_HOSTNAME |
| RENDER_EXTERNAL_HOSTNAME | settings | Set by Render | none |
| NUM_PROXIES | settings | Should be 1 on Render | 0 |
| ADMIN_URL | settings | No (new) | `site-admin/` |
| DATABASE_SSL_REQUIRE | settings | No (new) | off |
| HSTS_SECONDS | settings | No (new) | 31536000 |
| DJANGO_SETTINGS_MODULE | manage.py, wsgi | set by code | bizmind.settings |

Not read by the code but read by tools: `PYTHON_VERSION` (Render), `WEB_CONCURRENCY` (gunicorn, see the throttle note).

## Findings

### High
- **Git history unchecked** (see above). If any secret was ever committed, rotating it is required even if it was later deleted.

No other high finding was found in the files I could read.

### Medium
| # | Finding | Status |
|---|---|---|
| M1 | Without DATABASE_URL production silently used a SQLite file, which loses data on a free Render deploy | Fixed in `bizmind/settings.py`: app stops unless DEBUG is True |
| M2 | Signup ignored AUTH_PASSWORD_VALIDATORS (a known gap) | Fixed in `accounts/forms.py` |
| M3 | Admin at the guessable `/admin/` with no brute-force limit | Fixed: `ADMIN_URL`, `accounts/admin_security.py`, `accounts/ratelimit.py` |
| M4 | DRF browsable API (HTML) was on in production | Fixed: JSON only when DEBUG is off |
| M5 | Database connection encryption is not enforced | Not enabled by default (switch added, see below) |
| M6 | Rate-limit counters are per process (see "Throttle limits") | Documented, not fixed |
| M7 | Only the token, login, signup and admin login endpoints are throttled. Normal API calls with a valid token are not | Not fixed |

### Low
- L1 Signup says "An account with this email already exists", so emails can be enumerated. Not fixed.
- L2 `/api/schema/` and `/api/docs/` are public. Not fixed.
- L3 There is no password change or reset feature, so a leaked password cannot be fixed by the user. Not fixed.
- L4 JWTs are signed with SECRET_KEY: changing the key logs everyone out. SimpleJWT warns if the key is shorter than 32 bytes. Use a long key.
- L5 `SECURE_PROXY_SSL_HEADER` trusts `X-Forwarded-Proto`. Safe only while the app is reachable through Render's proxy.
- L6 HSTS is sent with `includeSubDomains` and `preload` for one year. I did not submit the site to any preload list. Lower it with `HSTS_SECONDS` if you want.
- L7 Sessions last Django's default 14 days.
- L8 The admin path is hidden, not protected by the hiding. Real protection is staff-only access, the limit, and a strong password.
- L9 `.env.example` has a placeholder SECRET_KEY. If that exact text were used in production it would be a serious hole. A check for it was left out so no deploy can break.

## What I changed and where

- `bizmind/settings.py`: fail-fast for SECRET_KEY and DATABASE_URL; `ADMIN_URL`; `DATABASE_SSL_REQUIRE` and `database_config(url, ssl_require)`; HttpOnly and SameSite on session and CSRF cookies; Permissions-Policy setting; `HSTS_SECONDS`; JSON-only DRF renderers in production; SimpleJWT pins (HS256, UPDATE_LAST_LOGIN False, Bearer); clearer throttle comment. Already correct and left alone: DEBUG default off, ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS from env, SSL redirect, Secure cookies, HSTS, X-Frame-Options DENY, nosniff, Referrer-Policy, CSP.
- `bizmind/middleware.py`: `PermissionsPolicyMiddleware` (camera, microphone, geolocation, payment, usb, motion sensors off). CSP code is untouched.
- `bizmind/urls.py`, `accounts/admin_security.py`, `accounts/ratelimit.py`: admin moved, login wrapper counts failures per IP and per username (10 per 15 minutes each), answers 429.
- `accounts/forms.py`: SignupForm runs the password validators, using the email for the similarity check. No template change.
- Password hashing: Django's default list is used, PBKDF2-SHA256 first. No weak hasher is listed. (The test runner swaps in MD5 only inside tests.)
- JWT review: access 15 minutes, refresh 7 days, rotation and blacklist on. A deactivated user gets 401 on token, refresh and access (checked).
- Tests: `bizmind/test_security_settings.py`, `accounts/test_sec1_accounts.py`. Changed on purpose: `accounts/test_characterisation.py` (the "validators not applied" test now expects rejection) and `accounts/test_consent.py` (admin test uses `reverse()` instead of `/admin/`).
- `.env.example`, `.gitignore`, `docs/PROJECT_CONTEXT.md` (env list and open item updated).
- No migration, no UI change, no existing migration touched.

## Changes that could affect the Render deploy

1. **Admin moves** from `/admin/` to `/site-admin/` (or your `ADMIN_URL`) as soon as this is deployed. Update bookmarks. Control: `ADMIN_URL`.
2. **DATABASE_URL required when DEBUG is off.** Render already provides it (`render.yaml`), also during the build step. If it is ever missing, the build stops with a message instead of running on SQLite. No variable turns this off, by your request.
3. **CSRF cookie is HttpOnly.** Safe today because no script reads cookies and forms use the hidden token. Would break any future JavaScript that reads the CSRF cookie.
4. **DB SSL** is off unless `DATABASE_SSL_REQUIRE=true`.
5. **JSON-only API** when DEBUG is off. Swagger at `/api/docs/` still works (tested).

## Testing DATABASE_SSL_REQUIRE before turning it on

As far as I know, `migrate` runs in `build.sh` before the new version goes live, and Render keeps the old version running if the build fails. I could not confirm this on your account.

1. From your PC, take the **External** connection string of bizmind-db from the Render dashboard and run `psql "<that string>" -c "select ssl from pg_stat_ssl where pid = pg_backend_pid();"`. `t` means that connection is encrypted. Do not paste the string anywhere.
2. In the Render dashboard add `DATABASE_SSL_REQUIRE=true` and redeploy. Watch the build log: `migrate` must finish with no `SSL` or `connection` error.
3. Open the site, log in, open the dashboard (these hit the database).
4. If anything fails: delete the variable and redeploy. No code change is needed.

## What you must do manually

1. **Git history** (PowerShell, in your repo). If any command prints a hit, rotate that secret and tell me:
   - `git log --all --oneline -- .env db.sqlite3 media`
   - `git log --all --oneline -S "SECRET_KEY=" -- .`
   - `git log --all -p -G "postgres(ql)?://[^ ]+:[^ ]+@" --oneline`
   - `git ls-files | Select-String -Pattern "\.env$|sqlite3$|^media/"` must print nothing (`.env.example` is fine).
   - Better: run the free tools gitleaks or trufflehog over the full history.
2. Render dashboard: set `ADMIN_URL` to a private word; confirm `NUM_PROXIES=1` exists (it is not in `render.yaml`, so a Blueprint rebuild would lose it); confirm `SECRET_KEY` is long and is not the `.env.example` text; confirm `DEBUG` is not `true`.
3. List staff accounts in the production admin and remove any you do not recognise; give each a strong unique password.
4. Decide about `DATABASE_SSL_REQUIRE` using the steps above.
5. Do not commit until `python manage.py test` ends with OK and `collectstatic` succeeds. Commit named folders only.

## Throttle limits (one worker only)

Counters for login, signup, admin login and token endpoints live in `LocMemCache`, which belongs to one process. With one gunicorn worker (today's `Procfile`, no `--workers`) the limits are exact. Be aware: if `WEB_CONCURRENCY` or `--workers` is raised, each worker counts alone and the real limit is about N times higher; every restart or deploy and every free-plan spin-down empties the counters. Before adding workers move the counters to a shared cache.

## Verify

```
python manage.py test
python manage.py collectstatic --noinput
python manage.py makemigrations --check --dry-run
```
Expected: 367 tests OK on the machine I used (314 before, 53 added; your count may differ if you changed files), no migration changes.
