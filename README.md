# BizMind

BizMind is a Django-based Business Decision Intelligence Platform that transforms business datasets into structured insights and actionable decisions.

It allows users to upload Sales, Marketing, and Finance datasets, process the data, analyze business performance, and generate decision recommendations through a centralized dashboard.

## Live Demo

[Live Application →](https://bizmind-4un7.onrender.com)

---

## Overview

Businesses often have large amounts of data but struggle to turn that data into clear decisions.

BizMind provides a centralized workflow:

**Dataset Upload → Data Processing → Analysis → Insights → Decisions**

The platform separates business domains into Sales, Marketing, and Finance and applies domain-specific analysis and decision rules to generate meaningful recommendations.

---

## Key Features

### Authentication

- User registration and login
- Secure authentication
- User-specific dataset management
- Logout functionality

### Dataset Management

- Upload CSV datasets
- Dataset type classification
- Dataset validation
- Dataset processing
- Dataset history and details
- User-specific dataset access

### Sales Analysis

- Process sales datasets
- Calculate revenue
- Analyze products and regions
- Generate sales-related insights
- Apply decision rules

### Marketing Analysis

- Process marketing datasets
- Analyze impressions, clicks, and conversions
- Analyze campaign and channel performance
- Calculate marketing performance metrics
- Generate marketing decisions

### Finance Analysis

- Process income and expense datasets
- Analyze financial transactions
- Analyze departments and categories
- Identify financial patterns
- Generate finance-related decisions

### Decision Intelligence

BizMind converts processed business data into structured decisions.

Each decision can include:

- Business domain
- Action
- Insight
- Impact
- Confidence
- Confidence reason

### Dashboard

The dashboard provides a centralized view of:

- Uploaded datasets
- Business domains
- Key metrics
- Generated decisions
- Business insights

---

## Application Workflow

```text
User
  ↓
Authentication
  ↓
Upload Dataset
  ↓
Dataset Validation
  ↓
Data Processing
  ↓
Domain Analysis
  ↓
Decision Engine
  ↓
Insights & Recommendations
  ↓
Dashboard
```

---

## Project Architecture

```text
BizMind/
│
├── accounts/              # Authentication and user management
├── bizmind/               # Main Django project configuration
├── core/                  # Public pages and common functionality
├── dashboard/             # Dashboard functionality
├── datasets/              # Dataset upload, validation and processing
├── sales/                 # Sales models, analysis and rules
├── marketing/             # Marketing models, analysis and rules
├── finance/               # Finance models, analysis and rules
├── decisions/             # Decision engine and decision management
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

## Technology Stack

### Backend

- Python
- Django
- Django ORM

### Data Processing

- Pandas
- NumPy

### Database

- SQLite for local development
- PostgreSQL for production

### Frontend

- HTML5
- CSS3
- JavaScript
- Django Templates

### Deployment

- Render
- Gunicorn
- WhiteNoise
- PostgreSQL

### Development Tools

- Git
- GitHub
- VS Code

---

## Data Domains

BizMind currently supports three major business domains.

### Sales

Expected fields:

```text
date
product
region
units_sold
unit_price
revenue
```

### Marketing

Expected fields:

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

### Finance

Expected fields:

```text
date
category
department
amount
type
```

Where `type` represents:

```text
income
expense
```

---

## Decision Engine

The decision engine converts processed business metrics into actionable recommendations.

The general flow is:

```text
Raw Data
   ↓
Validation
   ↓
Processing
   ↓
Business Metrics
   ↓
Domain Rules
   ↓
Decision
   ↓
Confidence & Impact
```

The decision layer is separated from the individual business domains so that domain-specific analysis and decision generation remain maintainable.

---

## Database Design

The application uses Django models and relationships to connect uploaded datasets with their corresponding business records.

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

This structure allows each uploaded dataset to maintain its own processed records and generated decisions.

---

## Local Development

### 1. Clone the Repository

```bash
git clone https://github.com/Rukhmai-Parshad/bizmind.git
cd bizmind
```

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```text
SECRET_KEY=your-secret-key
DEBUG=True
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Start the Development Server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Production Deployment

BizMind is deployed on **Render**.

Production setup includes:

- Django application
- Gunicorn
- PostgreSQL
- WhiteNoise for static files
- Environment-based configuration
- Automated deployment from GitHub

Deployment configuration is defined in:

```text
render.yaml
build.sh
Procfile
```

### Live Application

[https://bizmind-4un7.onrender.com](https://bizmind-4un7.onrender.com)

---

## Security

Production configuration keeps sensitive values outside the source code through environment variables.

Sensitive files and development artifacts are excluded using `.gitignore`.

Examples:

```text
.env
venv/
*.sqlite3
media/
staticfiles/
__pycache__/
```

---

## Future Improvements

Planned improvements include:

- Django REST Framework APIs
- Advanced filtering and search
- More business decision rules
- Automated testing
- Improved analytics
- Role-based access control
- Advanced dashboard visualizations
- Production monitoring
- More intelligent recommendation capabilities

---

## Project Goal

The goal of BizMind is to demonstrate how a Django application can combine:

```text
Web Development
       +
Database Management
       +
Data Processing
       +
Business Logic
       +
Decision Intelligence
```

into a complete end-to-end business application.

---

## Author

**Rukhmai Parshad**

Full Stack Python / Django Developer

[GitHub Profile →](https://github.com/Rukhmai-Parshad)

---

## License

This project is developed for learning, portfolio, and demonstration purposes.
