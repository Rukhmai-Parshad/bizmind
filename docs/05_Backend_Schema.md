# 05. Backend Schema: BizMind v2

Current models are taken from the codebase. Items marked **(proposed)** are changes. Everything else must stay compatible with the existing migrations.

**Entities:**
- `User` (accounts): an account, email is the login.
- `Dataset` (datasets): one uploaded CSV and its processing state.
- `SalesRecord`, `MarketingRecord`, `FinanceRecord`: parsed rows, one table per domain.
- `Decision` (decisions): a rule result generated for a dataset.

**Tables and fields:**

`accounts.User` (extends AbstractUser, `username` removed)
- `email` EmailField, unique, required (login field). `role` CharField(10) in ADMIN / ANALYST / VIEWER, default VIEWER (the signup form currently sets ANALYST). Standard Django fields: password, first_name, last_name, is_active, is_staff, is_superuser, last_login, date_joined.

`datasets.Dataset`
- `uploaded_by` FK User (CASCADE, related_name `datasets`), required.
- `name` CharField(255), required. `type` CharField(20) in sales / marketing / finance, required.
- `file` FileField(upload_to `datasets/`), cleared after processing.
- `uploaded_at` DateTimeField(auto_now_add). `is_processed` bool (False). `decisions_generated` bool (False). `error_message` TextField, nullable.
- **(proposed)** `status` CharField in pending / processing / processed / failed, default pending (replaces the two booleans, keep them until migrated). **(proposed)** `row_count` PositiveIntegerField, nullable.
- Constraint: unique (`uploaded_by`, `name`, `type`). Ordering: newest first. Add index on (`uploaded_by`, `-uploaded_at`) **(proposed)**.

`sales.SalesRecord`
- `dataset` FK (CASCADE, related_name `sales_records`), `date` DateField, `product` CharField(100), `region` CharField(100), `units_sold` PositiveIntegerField, `unit_price` FloatField, `revenue` FloatField (editable=False), `created_at` DateTimeField(default now).
- Indexes: dataset, date. **(proposed)** Change money fields to DecimalField(12, 2) in a careful migration, or keep Float and document the rounding rule. Revenue is always `units_sold * unit_price`, computed server-side.

`marketing.MarketingRecord`
- `dataset` FK (CASCADE, related_name `marketing_records`), `date`, `campaign`, `channel`, `impressions`, `clicks`, `conversions`, `spend`, `revenue`, `created_at`. Exact types: read `marketing/models.py` and `marketing/csv.py` and keep them.

`finance.FinanceRecord`
- `dataset` FK (CASCADE, related_name `finance_records`), `date` DateField, `category` CharField(100), `department` CharField(100), `amount` FloatField, `type` in income / expense, `created_at`.
- Indexes: dataset, date, department.

`decisions.Decision`
- `dataset` FK (CASCADE, related_name `decisions`), `title` CharField(255), `rule_name` CharField(100, indexed), `domain` in sales / marketing / finance (indexed), `insight` CharField(255), `recommendation` TextField, `explanation` TextField, `action` CharField(255), `impact` CharField(255, blank), `confidence` FloatField 0.0 to 1.0 (validators), `confidence_reason` CharField(255), `created_at`.
- Constraint: unique (`dataset`, `domain`, `rule_name`). Index: (`dataset`, `domain`). Ordering: newest first.

**Relationships:** User 1-to-many Dataset; Dataset 1-to-many each record table; Dataset 1-to-many Decision. Deleting a user or dataset cascades down.

**User ownership:** All data belongs to `Dataset.uploaded_by`. Records and decisions inherit ownership through their dataset. No shared or team data in v1.

**Authentication flow:** Sign up (email + password, role set server-side, never from the client), log in (session), log out (POST). API: `POST /api/auth/token/` returns access and refresh, `POST /api/auth/token/refresh/` rotates the refresh token. Access lifetime 15 minutes, refresh 7 days, blacklist after rotation **(proposed)**. Session cookies are secure in production.

**Authorization rules:**
| Entity | Read | Create | Update | Delete |
|---|---|---|---|---|
| Dataset | Owner | Owner with role ADMIN or ANALYST | Not allowed (re-upload instead) **(proposed)** | Owner with role ADMIN or ANALYST |
| Sales / Marketing / Finance records | Owner (via dataset) | Only by the processor | Not allowed | Only via dataset delete |
| Decision | Owner (via dataset) | Only by the decision engine | Not allowed | Only via dataset delete |
| User role | Admin panel only | Role never accepted from signup input | Admin only | Admin only |
API behaviour: other users' objects return 404; role violations return 403; disallowed methods return 405.

**Data validation (CSV and fields):**
- File: .csv only, max 10 MB, max 50,000 rows **(proposed)**, UTF-8 with BOM tolerated, headers trimmed and lower-cased, no duplicate headers.
- Sales: date, product, region, units_sold, unit_price all required. units_sold is a positive whole number, unit_price is positive, dates parse, exact duplicates of (date, product, region) are dropped.
- Marketing and Finance: required columns come from each domain's `csv.py`. Finance `type` must be income or expense, amounts must be numeric.
- Any invalid value fails the whole file with a message naming the problem. Nothing is saved on failure.

**Retention and deletion:** The uploaded CSV is deleted right after successful processing and on failure. Parsed records and decisions stay until the dataset is deleted. No export in v1.

**Migration and seed data:** Existing migrations in each app are kept and never edited. New changes are new migrations. Data migration for `status`: processed datasets get `processed`, others `pending`. Seed data: three sample CSVs in `static/samples/` (not loaded into the database). No fixtures.
