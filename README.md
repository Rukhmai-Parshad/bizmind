# BizMind

**BizMind is a Django-based Business Decision Intelligence Platform that transforms raw business datasets into structured analysis, actionable insights, and data-driven decisions.**

Built as an end-to-end **Python + Django + SQL + Data Processing + REST API** application, BizMind demonstrates how business data can move from dataset ingestion and validation to domain analysis, decision rules, recommendations, and a centralized dashboard.

**Core Workflow:**  
`Dataset Upload → Validation → Data Processing → Domain Analysis → Decision Engine → Insights & Recommendations`

## Live Application

**Live Demo:**  
https://bizmind-4un7.onrender.com

**Interactive API Documentation (Swagger):**  
https://bizmind-4un7.onrender.com/api/docs/

---

## Why BizMind?

Many business applications can store data, while analytics tools can display metrics. BizMind focuses on the layer between **data and action**.

It provides a structured workflow for:

- Ingesting business datasets
- Validating uploaded data
- Processing domain-specific records
- Calculating business metrics
- Applying business decision rules
- Generating structured insights
- Producing recommendations with impact and confidence information
- Presenting results through a centralized Django dashboard
- Exposing processed data through a secured REST API

The project is designed to demonstrate practical backend engineering, database modeling, data processing, business logic, authentication, API development, and production deployment in one application.

---

## Key Capabilities

### 🔐 Authentication & User Management

- User registration and login
- Custom Django user model
- Email-based authentication
- Role-based user structure
- Secure session authentication for the web application
- JWT authentication for REST APIs
- Authenticated API access
- User-specific data isolation
- Logout functionality

### 📂 Dataset Management

- CSV dataset upload
- Sales, Marketing, and Finance dataset classification
- Dataset validation
- Automatic dataset processing
- Dataset-specific processing status
- Dataset history and details
- Duplicate dataset validation
- User-owned dataset management
- Processing error handling

### 📊 Sales Intelligence

- Sales dataset processing
- Revenue calculation and analysis
- Product performance analysis
- Regional performance analysis
- Sales performance insights
- Domain-specific decision rules
- Actionable sales recommendations

### 📣 Marketing Intelligence

- Marketing dataset processing
- Campaign performance analysis
- Channel performance analysis
- Impressions, clicks, and conversions analysis
- Marketing performance metrics
- Domain-specific marketing insights
- Marketing decision generation

### 💰 Finance Intelligence

- Income and expense processing
- Financial transaction analysis
- Department-level analysis
- Category-level analysis
- Financial pattern identification
- Finance-specific business rules
- Financial decision recommendations

### 🧠 Decision Intelligence

BizMind separates **analysis** from **decision generation**.

Processed business data is evaluated through domain-specific rules to generate structured decisions containing information such as:

- Domain
- Title
- Insight
- Recommendation
- Explanation
- Action
- Impact
- Confidence
- Confidence reason

This creates a clear separation between:

`Data → Metrics → Business Rules → Decision`

### ⚙️ REST API

BizMind includes a production-oriented REST API built with **Django REST Framework**.

The API provides:

- Dataset CRUD operations
- Sales record CRUD operations
- Marketing record CRUD operations
- Finance record CRUD operations
- Read-only decision endpoints
- JWT access-token authentication
- JWT refresh-token authentication
- Authentication-protected endpoints
- Ownership-based data isolation
- Request validation
- Pagination
- Dataset-based filtering
- OpenAPI schema generation
- Interactive Swagger documentation

### 📈 Centralized Dashboard

The Django dashboard provides a centralized business view of:

- Uploaded datasets
- Business domains
- Key business metrics
- Generated decisions
- Business insights
- Recommendations

---

# Application Architecture

```text
                         ┌─────────────────────┐
                         │       User          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Authentication      │
                         │ Django + JWT API    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Dataset Management  │
                         │ Upload + Validation │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Data Processing     │
                         │ Pandas + Django ORM │
                         └──────────┬──────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
                 ┌────────┐    ┌─────────┐    ┌─────────┐
                 │ Sales  │    │Marketing│    │ Finance │
                 └────┬───┘    └────┬────┘    └────┬────┘
                      │              │              │
                      └──────────────┼──────────────┘
                                     ▼
                         ┌─────────────────────┐
                         │ Business Metrics    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Decision Engine     │
                         │ Domain Rules        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Insights &          │
                         │ Recommendations     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Django Dashboard    │
                         │ + REST API          │
                         └─────────────────────┘
```

---

# Application Workflow

```text
User
  ↓
Authentication
  ↓
Upload Business Dataset
  ↓
Dataset Validation
  ↓
Automatic Data Processing
  ↓
Domain-Specific Analysis
  ↓
Business Metrics
  ↓
Decision Rules
  ↓
Generated Decision
  ↓
Insight + Recommendation
  ↓
Dashboard / REST API
```

---

# Project Architecture

```text
BizMind/
│
├── accounts/              # Custom user model, authentication and user management
├── bizmind/               # Django project configuration, settings and URLs
├── core/                  # Public pages and shared functionality
├── dashboard/             # Business dashboard and metrics presentation
├── datasets/              # Dataset upload, validation and processing services
├── sales/                 # Sales models, analysis and business rules
├── marketing/             # Marketing models, analysis and business rules
├── finance/               # Finance models, analysis and business rules
├── decisions/             # Decision models and decision-generation logic
├── api/                   # DRF serializers, viewsets and API routing
│
├── static/
│   ├── css/
│   ├── dashboard/
│   └── img/
│
├── templates/
│   ├── accounts/
│   ├── core/
│   ├── dashboard/
│   ├── datasets/
│   └── decisions/
│
├── manage.py
├── requirements.txt
├── render.yaml
├── build.sh
├── Procfile
├── .env.example
└── README.md
```

---

# Technology Stack

## Backend

- **Python**
- **Django 5.2**
- **Django ORM**
- **Django REST Framework**

## Data Processing

- **Pandas**
- **NumPy**

## API & Authentication

- **Django REST Framework**
- **Simple JWT**
- **drf-spectacular**
- **OpenAPI 3**
- **Swagger UI**

## Database

- **SQLite** for local development
- **PostgreSQL** for production

## Frontend

- **HTML5**
- **CSS3**
- **JavaScript**
- **Django Templates**

## Production & Deployment

- **Render**
- **Gunicorn**
- **WhiteNoise**
- **PostgreSQL**
- Environment-based configuration
- Automated GitHub deployment

## Development Tools

- **Git**
- **GitHub**
- **VS Code**

---

# Data Domains

BizMind currently supports three business domains.

## Sales

Expected CSV fields:

```text
date
product
region
units_sold
unit_price
revenue
```

Sales processing supports product-level and region-level performance analysis and generates sales-related decisions.

## Marketing

Expected CSV fields:

```text
date
campaign
channel
impressions
clicks
conversions
spend
revenue
```

Marketing processing supports campaign and channel performance analysis using metrics such as impressions, clicks, conversions, spend, and revenue.

## Finance

Expected CSV fields:

```text
date
category
department
amount
type
```

The `type` field supports:

```text
income
expense
```

Finance processing supports transaction, department, and category-level analysis.

---

# Decision Engine

The **Decision Engine** is one of the core backend components of BizMind.

Instead of stopping at data processing or dashboard metrics, BizMind applies business rules to processed information and converts analytical results into structured decisions.

## Decision Pipeline

```text
Raw Dataset
     ↓
Validation
     ↓
Data Processing
     ↓
Business Records
     ↓
Domain Metrics
     ↓
Decision Rules
     ↓
Decision Generation
     ↓
Insight
     ↓
Recommendation
     ↓
Impact + Confidence
```

The decision layer is separated from individual business domains so that domain-specific analysis and decision generation remain organized and maintainable.

---

# REST API

BizMind exposes its core business data through a secured REST API.

## API Base URL

```text
https://bizmind-4un7.onrender.com/api/
```

## Authentication

### Obtain JWT Token

```http
POST /api/auth/token/
```

### Refresh JWT Token

```http
POST /api/auth/token/refresh/
```

## Dataset Endpoints

```http
GET    /api/datasets/
POST   /api/datasets/
GET    /api/datasets/{id}/
PATCH  /api/datasets/{id}/
DELETE /api/datasets/{id}/
```

## Sales Endpoints

```http
GET    /api/sales/
POST   /api/sales/
GET    /api/sales/{id}/
PATCH  /api/sales/{id}/
DELETE /api/sales/{id}/
```

## Marketing Endpoints

```http
GET    /api/marketing/
POST   /api/marketing/
GET    /api/marketing/{id}/
PATCH  /api/marketing/{id}/
DELETE /api/marketing/{id}/
```

## Finance Endpoints

```http
GET    /api/finance/
POST   /api/finance/
GET    /api/finance/{id}/
PATCH  /api/finance/{id}/
DELETE /api/finance/{id}/
```

## Decision Endpoints

Decisions are read-only through the API because they are generated by the application's decision engine.

```http
GET /api/decisions/
GET /api/decisions/{id}/
```

## Filtering

Business records can be filtered by dataset:

```text
/api/sales/?dataset=5
/api/marketing/?dataset=5
/api/finance/?dataset=5
```

## Pagination

API list endpoints use page-based pagination to keep record retrieval manageable.

Example:

```text
/api/sales/?page=1
```

## Interactive API Documentation

Explore and test the API through Swagger UI:

**https://bizmind-4un7.onrender.com/api/docs/**

---

# API Design Highlights

The REST API follows practical backend development patterns including:

- Resource-oriented endpoints
- ModelSerializer-based serialization
- ViewSet-based CRUD operations
- JWT authentication
- Authenticated API access
- Ownership validation
- User-scoped querysets
- Request validation
- Pagination
- Query-parameter filtering
- Read-only generated decisions
- OpenAPI schema generation
- Interactive Swagger documentation

---

# Database Design

BizMind uses Django ORM relationships to connect users, uploaded datasets, processed records, and generated decisions.

```text
User
 │
 └── Dataset
       │
       ├── SalesRecord
       ├── MarketingRecord
       ├── FinanceRecord
       └── Decision
```

This relationship structure ensures that processed business records and generated decisions remain associated with their source dataset.

---

# Data Isolation & Security

Security and data ownership are treated as backend concerns rather than only frontend restrictions.

BizMind implements:

- Authentication-protected API endpoints
- JWT-based API authentication
- User-scoped dataset querysets
- Ownership validation for related records
- User-specific dataset access
- Environment-based secret management
- Production HTTPS configuration
- Secure cookies in production
- CSRF trusted-origin configuration
- Secure HTTP headers
- Sensitive file exclusion through `.gitignore`

Sensitive and generated files are excluded from source control:

```text
.env
venv/
*.sqlite3
media/
staticfiles/
__pycache__/
```

---

# Validation & Error Handling

The application validates incoming data at multiple layers.

Examples include:

- Dataset type validation
- Duplicate dataset validation
- Required field validation
- Numeric field validation
- Date validation
- Minimum-value validation
- Dataset ownership validation
- API request validation
- Processing error capture

Invalid requests return appropriate HTTP `400` responses through Django REST Framework validation.

---

# Local Development

## 1. Clone the Repository

```bash
git clone https://github.com/Rukhmai-Parshad/bizmind.git
cd bizmind
```

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```text
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000
```

For production:

```text
DEBUG=False
```

Use a strong secret key and configure the production database and allowed hosts through environment variables.

## 5. Run Migrations

```bash
python manage.py migrate
```

## 6. Start the Development Server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Swagger documentation locally:

```text
http://127.0.0.1:8000/api/docs/
```

---

# Production Deployment

BizMind is deployed as a production Django application on **Render**.

Production architecture includes:

```text
GitHub
   ↓
Render
   ↓
Gunicorn
   ↓
Django
   ↓
PostgreSQL
```

Production configuration includes:

- Environment-based configuration
- Production `DEBUG=False`
- PostgreSQL database
- Gunicorn WSGI server
- WhiteNoise static-file handling
- HTTPS
- Secure cookies
- HSTS configuration
- Automated GitHub deployment

Deployment configuration is maintained through:

```text
render.yaml
build.sh
Procfile
```

## Live URLs

**Application:**  
https://bizmind-4un7.onrender.com

**Swagger API Docs:**  
https://bizmind-4un7.onrender.com/api/docs/

---

# Engineering Highlights

BizMind demonstrates practical implementation of:

- Django application architecture
- Custom user model
- Django ORM and relational data modeling
- CRUD operations
- CSV ingestion and validation
- Pandas-based data processing
- Domain-driven business logic
- Rule-based decision generation
- REST API development
- JWT authentication
- API permissions
- User-level data isolation
- Serializer validation
- ViewSet architecture
- Pagination
- Query-parameter filtering
- OpenAPI documentation
- Swagger UI
- Environment variable management
- Production PostgreSQL configuration
- Static file handling with WhiteNoise
- Gunicorn deployment
- Render deployment
- Git/GitHub workflow

---

# What This Project Demonstrates

BizMind was built to demonstrate the ability to develop a complete backend-oriented web application rather than an isolated CRUD project.

The project brings together:

```text
Python
   +
Django
   +
Django ORM
   +
SQL / PostgreSQL
   +
Pandas
   +
Business Logic
   +
REST APIs
   +
JWT Authentication
   +
Data Validation
   +
Decision Engine
   +
Production Deployment
```

The result is an end-to-end application that connects **data ingestion, processing, analysis, business rules, API services, and decision support** in a single Django system.

---

# Project Highlights

| Area | Implementation |
|---|---|
| Backend | Django |
| API | Django REST Framework |
| Authentication | Django Authentication + JWT |
| API Documentation | OpenAPI + Swagger UI |
| Data Processing | Pandas + NumPy |
| ORM | Django ORM |
| Database | SQLite / PostgreSQL |
| Business Domains | Sales, Marketing, Finance |
| Decision Layer | Rule-based Decision Engine |
| Frontend | Django Templates, HTML, CSS, JavaScript |
| Production Server | Gunicorn |
| Static Files | WhiteNoise |
| Deployment | Render |
| Source Control | Git + GitHub |

---

# Repository

**GitHub:**  
https://github.com/Rukhmai-Parshad/bizmind

---

# Author

**Rukhmai Parshad**

Full Stack Python / Django Developer

**GitHub:**  
https://github.com/Rukhmai-Parshad

---

# License

This project is developed for learning, portfolio, and demonstration purposes.
