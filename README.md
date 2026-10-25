# BizMind

BizMind turns a business CSV (sales, marketing or finance) into a short list of decisions. You upload a file, fixed and documented rules check the data, and each decision comes with a recommendation, an action, the reason it was raised and a confidence score.

**Live site:** https://bizmind-4un7.onrender.com
The site runs on Render's free plan, so the first request after a quiet period can take up to a minute to wake the server.

**Try it in two minutes:** create an account, open *Upload*, and use one of the sample files in `static/samples/` (`sales_sample.csv`, `marketing_sample.csv`, `finance_sample.csv`).

## What it does

- Accepts CSV files of three types: sales, marketing and finance.
- Validates the file before saving anything: extension, size (10 MB), row count (50,000), required columns and values.
- Parses the rows into the database, then runs nine rules and stores the decisions.
- Deletes the uploaded CSV file as soon as processing finishes or fails. Only parsed rows and decisions are kept.
- Shows a dashboard, a dataset history, and a filterable list of decisions.
- Offers a JWT-secured REST API with Swagger documentation.
- Lets a user delete their own account and all of its data.

## How decisions are made

There is no machine learning. Each rule is a plain function with a documented threshold, so every result can be explained.

| Area | Rule | Fires when |
|---|---|---|
| Sales | Revenue Risk Detected | Total revenue is below 10,000 |
| Sales | Underperforming Sales Region | A region contributes less than 20% of revenue |
| Sales | Top Performing Product | One product contributes at least 40% of revenue |
| Marketing | Low Click-Through Rate | Click-through rate is below 1% |
| Marketing | Poor Marketing ROI | Return on ad spend is below 2.0 |
| Marketing | Underperforming Marketing Channel | A channel is well below the average channel |
| Finance | Company Operating at a Loss | Expenses exceed income |
| Finance | High Expense-to-Income Ratio | Expenses reach 80% of income or more |
| Finance | Significant Expense Category | One category is at least 40% of expenses |

Each decision stores a confidence value from 0 to 1 with a one-line reason, shown as High, Medium or Low.

## CSV formats

| Type | Required columns |
|---|---|
| Sales | `date, product, region, units_sold, unit_price` |
| Marketing | `date, campaign, channel, impressions, clicks, conversions, spend, revenue` |
| Finance | `date, category, department, amount, type` (`type` is income or expense) |

Extra columns are ignored. A file with a missing column or an invalid value is rejected as a whole and nothing is saved.

## Tech stack

- Python 3.13, Django 5.2, Django REST Framework
- SimpleJWT (with refresh token rotation and blacklist), drf-spectacular for the OpenAPI schema and Swagger UI
- pandas for CSV parsing
- PostgreSQL in production (SQLite for local development)
- WhiteNoise and gunicorn, deployed on Render
- Django templates with one hand-written stylesheet and a small amount of vanilla JavaScript. No front-end framework and no third-party scripts or fonts.

## Security

Implemented and covered by automated tests:

- Every dataset, record and decision belongs to the account that uploaded it. Another user's object returns 404 in the web app and in the API.
- Roles: admin, analyst and viewer. Viewers cannot upload or delete, in the web app or in the API.
- One shared upload validator is used by the web form and the API.
- Sales, marketing and finance records are read-only through the API, so decisions cannot drift from the data.
- Rate limiting on web login, sign-up, admin login and API token endpoints.
- Short-lived JWT access tokens (15 minutes), rotating refresh tokens (7 days) with a blacklist.
- Content Security Policy that allows only the site's own resources, plus HSTS, secure and HttpOnly cookies, `X-Frame-Options`, `nosniff`, `Referrer-Policy` and `Permissions-Policy`.
- Logout and account deletion are POST-only and CSRF protected. Django's password validators apply at sign-up.
- The admin site lives at a configurable path (`ADMIN_URL`).
- The application refuses to start in production without `SECRET_KEY` and `DATABASE_URL`.
- Dependencies are pinned and checked with `pip-audit`.

The full audit, with what was fixed and what could not be verified, is in [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md). This is a personal project and has not had an independent penetration test.

## Privacy

The site has a Privacy Policy, Terms and a Cookie Policy written from what the code actually does (`/privacy/`, `/terms/`, `/cookies/`). Sign-up asks for explicit consent and stores the time of consent. Only essential cookies are used (session, CSRF and a short-lived messages cookie), and there are no analytics or advertising scripts. These pages are not legal advice and have not been reviewed by a lawyer.

## REST API

Interactive documentation is at `/api/docs/`.

| Endpoint | Methods | Notes |
|---|---|---|
| `/api/auth/token/` | POST | Get access and refresh tokens (rate limited) |
| `/api/auth/token/refresh/` | POST | Rotate the refresh token |
| `/api/datasets/` | GET, POST, PATCH, DELETE | Writes need the admin or analyst role |
| `/api/sales/`, `/api/marketing/`, `/api/finance/` | GET | Read-only, filter with `?dataset=<id>` |
| `/api/decisions/` | GET | Read-only |

Lists are paginated (10 per page). Send the access token as `Authorization: Bearer <token>`.

## Testing

The project has 367 automated tests (Django's test runner). They cover the upload validator, every decision rule at and around its threshold, ownership and role checks for each page and API endpoint, rate limits, security headers, consent and account deletion, and a set of guard tests that fail if the site starts loading external resources.

```
python manage.py test
```

## Run it locally (Windows PowerShell)

```
git clone https://github.com/Rukhmai-Parshad/bizmind.git
cd bizmind
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `SECRET_KEY` to a long random value (generate one with `python -c "import secrets; print(secrets.token_urlsafe(50))"`). Keep `DEBUG=True` for local work. Then:

```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/. The admin site is at `/site-admin/` unless you set `ADMIN_URL`.

## Configuration

All settings come from environment variables. `.env.example` lists them with comments.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Required |
| `DEBUG` | `True` only on your own machine |
| `DATABASE_URL` | Required when `DEBUG` is off (set by Render) |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Optional, Render's hostname is used when empty |
| `NUM_PROXIES` | Number of trusted proxies in front of the app (1 on Render) |
| `ADMIN_URL` | Admin path, default `site-admin/` |
| `DATABASE_SSL_REQUIRE` | Require SSL to the database, default off |

## Deployment

`render.yaml` and `build.sh` describe the Render deployment: install dependencies, collect static files, run migrations, and clear expired sessions and token records. Deploys run automatically when `main` changes.

## Project layout

```
accounts/    custom user (email login, roles), sign-up, login, account deletion
datasets/    upload form, shared validator, atomic processing service
sales/, marketing/, finance/    CSV schema, records, queries and rules for each area
decisions/   decision model, engine and confidence logic
dashboard/   summary page
core/        landing page, privacy, terms, cookies
api/         serializers, viewsets, permissions, throttles
bizmind/     settings, URLs, middleware
docs/        requirements, design brief, security audit
```

## Known limitations

- Rate-limit counters are kept in memory, so they assume a single gunicorn worker.
- Existing accounts created before the consent feature have no consent record.
- There is no password reset or password change page yet.
- Not yet containerised, and there is no CI pipeline.
- Age is self-declared at sign-up and is not verified.

## Author

Rukhmai Parshad
GitHub: https://github.com/Rukhmai-Parshad
LinkedIn: https://www.linkedin.com/in/rukhmaiparshad
