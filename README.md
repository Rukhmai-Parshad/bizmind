# BizMind

BizMind is a Django-based decision intelligence platform that turns structured business datasets into explainable, rule-backed recommendations.

## What it does

1. A user creates an account and signs in.
2. The user uploads a CSV for Sales, Marketing, or Finance.
3. BizMind validates and processes the file with Pandas.
4. Processed records are stored in PostgreSQL/SQLite through Django ORM.
5. Domain-specific business rules evaluate the data.
6. The decision engine generates explainable decisions with confidence scores.
7. The dashboard presents decision metrics, recent activity, and interactive charts.

## Architecture

```text
Browser
   ↓
Django URL
   ↓
View
   ↓
Form / Service
   ↓
Pandas CSV Processing
   ↓
Django ORM
   ↓
Database
   ↓
Decision Engine
   ↓
Domain Rules
   ↓
Dashboard
```

### Apps

- `accounts` — custom email-based user model and authentication
- `datasets` — CSV upload, validation, and processing orchestration
- `sales` — sales records, queries, and rules
- `marketing` — marketing records, queries, and rules
- `finance` — finance records, queries, and rules
- `decisions` — decision model and central rule engine
- `dashboard` — user-specific metrics and analytics
- `core` — public-facing pages

## Decision Engine

BizMind currently uses deterministic, explainable business rules rather than a machine-learning model.

Examples:

- Sales revenue below a configured threshold
- Underperforming sales region
- Dominant/top-performing product
- Low marketing CTR
- Poor marketing ROAS
- Underperforming marketing channel
- Net loss
- High expense-to-income ratio
- Highest expense category

Each generated decision contains:

- domain
- rule name
- explanation
- recommendation
- action
- business impact
- confidence score

## CSV formats

### Sales

Required columns:

```text
date, product, region, units_sold, unit_price
```

### Marketing

Required columns:

```text
date, campaign, channel, impressions, clicks, conversions, spend, revenue
```

### Finance

Required columns:

```text
date, category, department, amount, type
```

For Finance, `type` must be `income` or `expense`.

## Local setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd "Unified Decision Intelligence Platform/bizmind"
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and set a strong `SECRET_KEY`.

For local development:

```text
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create an admin account

```bash
python manage.py createsuperuser
```

### 7. Run the application

```bash
python manage.py runserver
```

## Production deployment on Render

The repository includes `render.yaml` for a Render web service plus PostgreSQL database.

The deployment configuration:

- Python 3.13.5
- Django production settings
- PostgreSQL
- WhiteNoise for static files
- Gunicorn
- `collectstatic` + migrations during build
- HTTPS/security settings when `DEBUG=False`

For a portfolio/demo deployment, create a new Render Blueprint from the repository and apply the included `render.yaml`.

The free Render web and Postgres plans are suitable for a demo, but free instances have service/database limitations and are not intended for production workloads.

## Security notes

- Secrets are supplied through environment variables.
- `.env` is not committed.
- CSRF protection remains enabled.
- Production cookies are marked secure.
- HTTPS redirect and HSTS are enabled in production.
- Uploaded CSV files are validated before processing.
- User data is scoped to the authenticated user.
- Processed raw uploads are removed after successful processing because the application does not expose raw-file downloads.

## Testing

Run:

```bash
python manage.py test
```

## Tech stack

- Python
- Django
- Django ORM
- Pandas
- PostgreSQL / SQLite
- Chart.js
- HTML/CSS/JavaScript
- Gunicorn
- WhiteNoise
