# 01. Product Requirements Document (PRD): BizMind v2

**Product name and one-sentence idea:** BizMind turns a business CSV (sales, marketing or finance) into a short list of clear, explained decisions. It solves the gap between "I have a spreadsheet" and "what should I do about it".

**Target users:**
- Small-business owners and analysts who keep data in CSV/Excel and have no BI team.
- Needs: upload a file, see what matters, understand why, and know what to do next.
- Secondary: developers or recruiters who read the public API docs (portfolio value).

**Problem and current workaround:** Users open the CSV in Excel, build pivot tables and guess the next step. Dashboards show numbers but do not say what to do. BizMind adds rule-based decisions with an explanation and a confidence value.

**Goal and success measure:**
- Product: a user goes from signup to first decision in under 3 minutes.
- Engineering targets: processing a 10,000-row CSV in under 10 seconds; at least 70% automated test coverage on accounts, datasets, decisions and api; zero known high-severity items from `00_Current_State_Audit.md` (S1, S2 closed).
- Adoption (tracked from the database, reported honestly): number of signups, number of datasets processed, number of decisions generated. A target of 20 real users is a goal, not a claim.

**Core features (feature, benefit, priority):**
| Feature | User benefit | Priority |
|---|---|---|
| Email signup, login, logout | Private workspace | Must |
| CSV upload with validation and clear error messages | Trust that bad data is caught early | Must |
| Automatic processing for Sales, Marketing, Finance | No manual work | Must |
| Decision list: title, insight, recommendation, explanation, action, impact, confidence, confidence reason | Know what to do and why | Must |
| Dashboard summary (counts, confidence split, decisions by domain) | One-glance view | Must |
| Dataset history and detail page | Revisit past results | Must |
| Filter decisions by domain and confidence | Focus on what is urgent | Should |
| JWT REST API + Swagger docs | Integrate and showcase | Should |
| Sample CSV download per domain | Try the product with no own data | Should |
| Usage metrics view for the owner (admin only) | Honest numbers for the resume | Should |

**Out of scope for version one:** AI/LLM-generated insights, teams or shared workspaces, payments, Excel (.xlsx) upload, email notifications, password reset by email (decide later), React front end, mobile app, scheduled data syncs.

**User stories:**
- As an analyst, I want to upload a sales CSV, so I can see which region or product needs attention.
- As an analyst, I want each decision to explain how it was calculated, so I can trust it.
- As a viewer, I want read-only access, so I cannot change or upload data by mistake.
- As a developer, I want a documented JWT API, so I can fetch my decisions programmatically.
- As the owner, I want usage counts, so I can report real adoption.

**Acceptance criteria:**
- Given a logged-in analyst, when they upload a valid sales CSV, then the dataset is processed, 0 to 3 decisions are created and the user lands on the dataset list with a success message.
- Given a CSV with a missing required column, when uploaded, then nothing is saved and the error names the missing columns.
- Given a viewer (web or API), when they try to upload, then the request is refused (web: message and redirect; API: HTTP 403).
- Given user A, when they request user B's dataset or decisions by ID (web or API), then they get 404.
- Given the API, when records are listed, then results are read-only and any POST/PUT/PATCH/DELETE on record endpoints returns 405.
- Given a logout link, when it is requested with GET, then the user stays logged in (logout is POST only).

**Open questions (owner decides):**
1. Should new signups default to ANALYST (current) or VIEWER?
2. Keep or remove the public `/stats/` page (audit S6)?
3. Keep Contact and About pages, or merge into the home page? (Recommendation: merge.)
4. Is password reset by email needed before real users arrive?
