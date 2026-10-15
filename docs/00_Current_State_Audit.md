# 00. BizMind Current-State Audit

Source: review of the BizMind.zip codebase (Django 5.2.9, DRF 3.18, SimpleJWT, drf-spectacular, pandas, WhiteNoise, gunicorn, PostgreSQL on Render). Every item below was found by reading the code. Nothing was run, so the AI coding tool must confirm each item before changing it.

## What already works well (do not break)
- Custom email-based User model with roles ADMIN / ANALYST / VIEWER.
- Per-user data isolation in web views and API querysets (`uploaded_by=request.user`).
- CSV validation in the web form (extension, 10 MB limit, required columns).
- Atomic processing, decisions generated exactly once (`select_for_update`), uploaded CSV deleted after processing.
- Production settings: required SECRET_KEY, HTTPS redirect, secure cookies, HSTS, DEBUG defaults to False.
- Git history is clean: `.env` was never committed, only `.env.example`.

## Security and correctness findings (ID, severity, where, fix)
| ID | Severity | Where | Problem | Fix |
|---|---|---|---|---|
| S1 | High | api/views.py `DatasetViewSet` | The API upload has no role check (web blocks VIEWER, API does not), no .csv check, no size limit and no required-column check. Those rules live only in the web form. | Move all upload validation into one shared service/validator used by both web form and API serializer. API must enforce the same role rule. |
| S2 | High | api/views.py Sales/Marketing/Finance viewsets | These are full ModelViewSets, so any authenticated user can create, edit and delete processed records. `SalesRecordSerializer` also accepts a client-supplied `revenue`, so revenue can disagree with units_sold x unit_price. Decisions are not regenerated after edits, so they go stale. | Make record endpoints read-only. Compute revenue on the server only. |
| S3 | Medium | accounts/views.py `user_logout` | Logout works on GET, so it can be triggered by a cross-site request. | Require POST (with CSRF token). |
| S4 | Medium | settings / login / signup / JWT | No throttling or lockout on login, signup or token endpoints. | Add DRF throttling for the token endpoints and rate-limit login/signup (django-axes or equivalent). |
| S5 | Medium | api/views.py `perform_create` | If processing fails, the dataset row and file stay behind (the web view cleans up, the API does not). | Wrap create + process in one transaction and delete the stored file on any failure. |
| S6 | Low | core/views.py `/stats/` | Public page shows platform-wide user, dataset and decision counts. | Decide: remove, or show only non-sensitive marketing numbers. |
| S7 | Low | api/serializers.py `DatasetSerializer.validate` | Duplicate check does not exclude the current instance, so PATCH/PUT of an existing dataset can fail. | Exclude `self.instance`. |
| S8 | Low | settings.py | SimpleJWT uses defaults (no refresh rotation or blacklist). No CSP or Referrer-Policy header. TIME_ZONE is UTC. | Configure SIMPLE_JWT lifetimes, rotation and blacklist. Add Referrer-Policy and a CSP. Set the time zone deliberately. |
| S9 | Low | repo hygiene | The zip contains db.sqlite3, media/datasets/*.csv test files and .git. They are gitignored, but tests leave CSVs in media/. | Make tests use a temporary MEDIA_ROOT and clean up. Never ship db.sqlite3 or media. |

## Quality and design findings
- Tests are minimal: roughly one test per app, none for the API, views, permissions or decision rules.
- `iterrows()` is used to build records (slow on large files). Use vectorised pandas and `bulk_create` in batches.
- Dataset state is two booleans (`is_processed`, `decisions_generated`) plus `error_message`. A single `status` field (pending / processing / processed / failed) would be clearer.
- Decision rules use hard-coded thresholds in code (for example revenue 10000, region 20%, product 40%). Move them to named constants/settings and explain them in the UI.
- Front end loads AOS (unpkg), Font Awesome 5 (cdnjs) and an unpinned Chart.js (jsDelivr). The dark theme and animations do not match the new minimalist direction.
- No Dockerfile, no docker-compose, no CI.
