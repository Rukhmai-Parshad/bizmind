# 04. UI and UX Design Brief: BizMind (warm, quiet, product style)

**Audience and tone:** Small-business owners and analysts. Calm, spacious, precise. The interface borrows the structure of tools such as Notion and Linear (sidebar, breadcrumbs, keyboard hints, status chips, empty states with one action) and gives it a warm, paper-like look.

**Never use:** gradients of any kind, glow or glass effects, pill-shaped buttons, emoji, photographs or generated images, testimonials, fake metrics, user counts or logos, star ratings, animated counters, scroll animation, parallax, custom cursors, marquees, "built with" badges, vague hero text, and em or en dashes in any visible text, template, comment or document. Every claim on the site must be true and traceable to code.

**Hard technical rules:**
1. Django templates, one stylesheet (`static/css/app.css`), one script (`static/js/app.js`). No Tailwind, no React, no icon fonts.
2. Content-Security-Policy is `'self'` only: no external fonts, CSS, JS, images or CDN, no inline `<script>`, no `<style>` block and no `style=""` attribute.
3. System font stacks only. No downloads.
4. Logout is always a POST form with a CSRF token.
5. Every page works without JavaScript. JavaScript only adds toasts that dismiss, the mobile menu, page search, a type filter, the selected file name and button loading text.
6. Rules for the stylesheet are enforced by tests in `core/test_redesign.py`.

## Palette (CSS variables on `:root`, exact values)
| Token | Value | Use |
|---|---|---|
| `--bg` | #F3EEE6 | Page background |
| `--oatmeal` | #E9E2D7 | Panels, table header, chips, secondary surfaces |
| `--surface` | #FBF8F3 | Cards, inputs |
| `--sand` | #DCC8B5 | Borders, dividers, active tint |
| `--ink` | #4D362B | Body text, sidebar and closing band background, bars |
| `--muted` | #6B5546 | Secondary text |
| `--coffee` | #8C6F5D | Form field borders, icons. Never small text |
| `--primary` | #611E2F | Primary buttons, links, active items |
| `--primary-hover` | #4A1623 | Hover |
| `--sage` | #A7B19A | Highest bar, decorative accents. Never text on light backgrounds |
| `--success-text` | #4A5D3F | Success text, high confidence border |
| `--warning-text` | #8A5A12 | Warning text, medium confidence border |
| `--danger-text` | #A12B2B | Error text, low confidence border |

Text on primary buttons is `--surface`. Sidebar text is `--oatmeal`. The active sidebar item is a `--primary` background with `--oatmeal` text and a 3px `--sand` bar on the left. No other colour values are used in rules (only a translucent ink for the mobile scrim and sidebar hover).

## Contrast (checked with a script, values are ratios)
Text, minimum 4.5:1:
- ink on bg 9.68, on surface 10.55, on oatmeal 8.69, on sand 6.91
- muted on bg 6.03, on surface 6.58, on oatmeal 5.42
- primary on bg 10.48, on surface 11.43, on oatmeal 9.41; primary-hover on bg 12.71, on oatmeal 11.41
- surface on primary 11.43, on primary-hover 13.86
- oatmeal on ink 8.69, on primary 9.41; sand on ink 6.91
- success-text on surface 6.77, on oatmeal 5.57, on bg 6.21
- warning-text on surface 5.58, on oatmeal 4.60, on bg 5.12
- danger-text on surface 6.85, on oatmeal 5.64, on bg 6.28

Non-text, minimum 3:1: coffee on surface 4.36, on bg 4.00, on oatmeal 3.59 (field and button borders); ink bar on oatmeal track 8.69; confidence borders on surface 6.77, 5.58 and 6.85.
Known exceptions: the sage fill of the highest bar is 1.74:1 on its track, so it carries a 1px ink outline (5.00:1 against the fill) and every bar also shows its number; sand dividers (1.40:1 on the page) are decorative, not component boundaries.

## Typography
- Headings: `"Iowan Old Style", Charter, Georgia, serif`, weight 600, tight letter-spacing. Wordmark and large numbers too.
- Body and UI: `system-ui` sans, 16px with 1.6 line height (15px in tables, forms and the app shell chrome).
- Page title 34px (30px on phones), section title 20px, small text 14px. Small uppercase labels, 12px, letter-spaced, for section names. Tabular numbers for all figures.

## Look and feel
- 1px borders, no shadows, no gradients. Radius: buttons and inputs 6px, chips 4px, cards 8px, the landing mockup frame 10px. Nothing larger.
- Motion: 120 to 150ms colour changes on hover and focus, a 150ms fade on toasts, nothing else. `prefers-reduced-motion` removes it.
- Focus: 2px ink ring with 2px offset (oatmeal on dark surfaces).
- Spacing scale of 8px. Content max width 1100px.
- Icons: inline SVG, 1.5px stroke, `currentColor`, kept as template partials in `templates/icons/`.

## Pages
- **Landing (`/`):** sticky top bar (serif wordmark, How it works, Features, API docs, Log in as text, Sign up as primary button; logged-in visitors see app links and Logout instead). Left-aligned hero with the label "Decision intelligence for small business", a headline, one sentence, "Get started" and "See how it works", and a static dashboard mockup labelled "Example data". Then: Works with your CSV, How it works (three numbered steps with thin dividers), Features (six items), Anatomy of a decision (large example card with labelled parts), a privacy strip with three facts, and a closing band in ink. All example values come from the three files in `static/samples/`.
- **Auth:** split layout. Form on the left, an ink panel with one privacy sentence on the right, stacked on phones. Signup has a required, unticked consent checkbox, "I am 18 or older and agree to the Terms and Privacy Policy", with links to both and an inline error if it is not ticked. Both auth pages end with small Privacy, Terms and Cookies links.
- **App shell (logged in):** 240px ink sidebar (Dashboard, Datasets, Decisions, Upload for analysts and admins; email, role chip and Logout at the bottom), icon-only on tablets, off-canvas drawer with a menu button on phones. Top bar with breadcrumbs, a page filter field (press `/` to focus it) and a primary "Upload CSV" button.
- **Dashboard:** date, greeting, four stat blocks, "Confidence split" and "Decisions by domain" bars (ink, highest in sage), recent decisions, and a first-use checklist with sample CSV links until a dataset exists.
- **Datasets:** table with sticky header on oatmeal, type chip, status chip with a dot, rows, decisions, date and a hover-revealed Open link. A type filter (All, Sales, Marketing, Finance) appears when JavaScript is available.
- **Upload:** form with a dashed file area (solid and named once a file is chosen) beside a "Required columns" panel and sample links.
- **Dataset detail and Decisions:** decision cards with a 4px left border by confidence, serif title, labelled Insight, Recommendation, Action and Impact, and the explanation and confidence reason behind a native "Why?" toggle. The Decisions page has domain and confidence filters and removable active-filter chips.
- **Errors (403, 404, 500):** calm message and a link back. The 500 page is standalone.
- **Privacy Policy, Terms and Cookie Policy (`/privacy/`, `/terms/`, `/cookies/`):** plain language, written for the Digital Personal Data Protection Act 2023, with Rukhmai Parshad and rukhmaiparshad@gmail.com as the only business details and a fixed "Last updated" date. Linked from every footer and from the signup page. Every figure in them (session length, token lifetime, counter windows, hosting region) is checked by a test against the settings or config.
- **Settings (`/accounts/settings/`):** shows the account email, role, creation date, consent record and counts, with a danger-zone panel. "Delete my account" leads to a confirmation page (what will be deleted, password, confirmation tick, danger button) and ends with a logout and a toast. Staff accounts see an explanation instead of the button. Linked from the sidebar.

## Accessibility
Semantic landmarks, a skip link, one `h1` and a unique title per page, a label on every input, visible focus, 40px or larger controls, tables that scroll inside their own container on small screens, `progress` bars with labels, status shown as words and not colour alone, readable without JavaScript.

## Assets
Text wordmark. Favicon `static/img/favicon.svg` (a "B" monogram in primary on oatmeal), also served at `/favicon.ico`. Sample CSVs in `static/samples/`.
