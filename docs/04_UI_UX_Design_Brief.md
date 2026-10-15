# 04. UI and UX Design Brief: BizMind v2 (Minimalist)

**Audience and tone:** Small-business owners and analysts. Three adjectives: calm, precise, uncluttered. The interface should feel like a clean report, not a marketing site.

**Reference products:** Linear and Stripe Dashboard (borrow: whitespace, thin borders, restrained colour), plain GOV.UK style forms (borrow: clear labels and error text). Avoid: gradients, glassmorphism, neon accents, animated counters, scroll animations, stock illustrations.

**Design rules (hard):**
1. Light theme only in v1. White background, dark text.
2. One accent colour. Everything else is grey.
3. No shadows, no gradients, no animations except a 150 ms colour change on hover/focus.
4. 1 px borders separate content. Cards are bordered boxes, not floating.
5. No icon fonts. Text labels only (a few inline SVGs are allowed if essential).
6. No third-party CSS, fonts or animation libraries. System font stack.

**Color palette (CSS variables on `:root`):**
| Token | Value | Use |
|---|---|---|
| `--bg` | #FFFFFF | Page background |
| `--surface` | #FAFAFA | Table header, subtle panels |
| `--text` | #111111 | Body text |
| `--muted` | #6B7280 | Secondary text |
| `--border` | #E5E7EB | All borders |
| `--accent` | #2563EB | Primary button, links, focus ring |
| `--accent-hover` | #1D4ED8 | Hover |
| `--success` | #15803D | Success messages, high-confidence label text |
| `--warning` | #B45309 | Medium confidence, warnings |
| `--danger` | #B91C1C | Errors, low-priority-to-fix labels, delete |

**Typography:** `font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`. Base 16 px, line-height 1.6. Scale: h1 28 px / 600, h2 20 px / 600, h3 16 px / 600, small 14 px. Numbers in tables use `font-variant-numeric: tabular-nums`.

**Components:**
- Buttons: primary (accent fill, white text), secondary (white, 1 px border), danger (text and border in danger colour). 40 px high, 6 px radius.
- Forms: label above input, 1 px border, 6 px radius, visible focus ring (2 px accent outline), error text in danger colour under the field.
- Cards/panels: 1 px border, 8 px radius, 20 px padding, no shadow.
- Tables: full width, `--surface` header, row dividers only, no zebra stripes.
- Navigation: single top bar, brand name left, text links right, 1 px bottom border.
- Messages: a bordered bar under the nav with a coloured left border (4 px).
- Confidence labels: plain text pill ("High 0.82") with coloured text on a white background and a 1 px border. Never rely on colour alone, always show the word.
- Charts: at most two on the Dashboard (confidence split as horizontal bars, decisions by domain as bars). Greys plus the accent colour only.

**Layout rules:** Content max-width 960 px, centred, 24 px side padding. Spacing scale based on 8 px (8, 16, 24, 32, 48). One column on screens under 720 px; stat cards stack. Tables scroll horizontally inside their own container on small screens. Breakpoints: 720 px and 1024 px.

**Screen notes (hierarchy):**
- Home: one h1 sentence, one paragraph, two buttons (Sign up, Log in), then a 3-step "how it works" list. About text is merged here. No hero image.
- Dashboard: h1, row of four stat boxes (datasets, processed, pending, decisions), then two small charts, then "Recent decisions" table (5 rows). First-use strip when empty.
- Datasets: table of name, type, status, uploaded date, decision count, link. Upload button top right (hidden for viewers).
- Upload: single column form, a required-columns hint that changes with the selected type, and a "Download sample CSV" link.
- Dataset detail: dataset facts line, then decisions as stacked bordered blocks.
- Decision block order: title, confidence label, insight, recommendation, explanation, action, impact, confidence reason (in small muted text).
- Decisions: filters in one row (domain, confidence), then the same decision blocks.
- Auth screens: centred 400 px form, no side imagery.
- Error pages: one sentence plus a link back.

**Accessibility:** Text contrast at least 4.5:1 (all tokens above meet this on white). Every input has a visible `<label>`. Full keyboard operation with a visible focus style. Touch targets at least 40 px. Use semantic HTML (`nav`, `main`, `table`, `th scope`). Do not rely on colour alone. Respect `prefers-reduced-motion` (there is almost no motion anyway). Page `lang="en"` and a unique `<title>` per page.

**Interaction states:** Hover: darker accent or `--surface` background. Focus: 2 px accent outline, 2 px offset. Disabled: 50% opacity, `not-allowed` cursor. Loading: button text changes ("Processing...") and the button is disabled. Error: danger text and a 1 px danger border on the field. Success: green left-border message bar.

**Assets needed:** A text wordmark "BizMind" (no logo file). Favicon as a simple inline SVG or a 32 px PNG. Sample CSVs for sales, marketing and finance in `static/samples/`. Remove `static/img/about.jpg` and the dark-theme CSS.
