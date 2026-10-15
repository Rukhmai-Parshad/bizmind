# 03. App Flow: BizMind v2

**Entry points:** Home page `/`, direct login/signup links, Swagger docs at `/api/docs/`, shared dataset links are NOT supported (all data is private).

**Screen inventory:**
| Screen | URL | Purpose | Required data |
|---|---|---|---|
| Home | `/` | Explain the product in one screen, link to signup/login, about text merged here | none |
| Sign up | `/accounts/signup/` | Create account | email, password |
| Log in | `/accounts/login/` | Sign in | email, password |
| Dashboard | `/dashboard/` | Summary: dataset counts, decision counts, confidence split, decisions by domain, recent items | user's datasets and decisions |
| Datasets | `/datasets/` | History list with status | user's datasets |
| Upload | `/datasets/upload/` | Upload a CSV (analyst/admin only) | name, type, file |
| Dataset detail | `/datasets/<id>/` | Dataset status plus its decisions | dataset, decisions |
| Decisions | `/decisions/filtered/` | All decisions with domain and confidence filters | user's decisions |
| 404 / 403 / 500 | n/a | Calm error pages with a way back | none |

**Primary journey:** Home -> Sign up -> (success message) Log in -> Dashboard (empty state with "Upload your first CSV") -> Upload -> choose type, name, file -> Submit -> Datasets list with success message -> open Dataset detail -> read decisions.

**Alternate journeys:**
- Missing columns: Upload -> error under the file field listing missing columns -> fix file -> resubmit.
- Viewer tries upload: redirected to Dashboard with a read-only message; the Upload link is hidden for viewers.
- Duplicate name and type: error "You already uploaded a dataset with this name and type."
- Cancel: Upload -> back to Datasets with no changes.
- Logout: button in the nav submits a POST -> Login page with message.

**For each action, specify (trigger, validation, loading, success, error, next):**
| Action | Trigger | Validation | Loading state | Success | Error | Next screen |
|---|---|---|---|---|---|---|
| Sign up | Submit form | Valid email, unique email, password min 8 plus Django validators | Button disabled, text "Creating..." | "Account created. Please log in." | Field errors inline | Login |
| Log in | Submit form | Credentials valid, throttled after repeated failures | Button disabled | Redirect to Dashboard | "Invalid email or password." or throttle message | Dashboard |
| Upload CSV | Submit form | Role allowed, .csv, <= 10 MB, <= 50,000 rows, required columns for type, no duplicate columns, valid dates and numbers, no duplicate name/type | Button disabled, text "Processing..." | "Dataset processed. N decisions created." | Inline file error; unexpected errors show a generic message and are logged | Datasets list |
| Delete dataset (new) | Confirm button | Owner only | Button disabled | "Dataset deleted." | 404 if not owner | Datasets list |
| Filter decisions | Change select, submit | Domain in allowed list, confidence in high/medium/low | none | List updates | Unknown values are ignored | Same screen |
| Log out | POST button | CSRF | none | "You have been logged out." | n/a | Login |

**Navigation rules:** Top bar only, text links, no icons. Logged out: Home, Log in, Sign up. Logged in: Dashboard, Datasets, Decisions, Upload (analyst/admin only), Log out. Back button always returns to the previous list. API docs link in the footer.

**Empty and blocked states:**
- No datasets: "No datasets yet." plus a link to upload and a link to sample CSVs.
- No decisions: "No decisions yet. Your data is within the expected ranges." (a processed dataset may legitimately produce none).
- Permission denied: 403 page for forbidden role actions; 404 for another user's objects.
- Offline or server error: plain 500 page with a retry link.

**First-use journey:** After the first login the Dashboard shows a short three-step strip: 1 Download a sample CSV, 2 Upload it, 3 Read your decisions. The strip disappears once a dataset exists.
