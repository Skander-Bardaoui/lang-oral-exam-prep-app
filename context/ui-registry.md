# UI Registry

_Written by `/imprint` after building any UI component. Read this before building a new one — never duplicate a pattern that already exists here._

**Implementation:** Django templates in `templates/`, styles in `static/css/app.css`, CSS variables from `ui-tokens.md`. No Tailwind, no component library. Components are plain HTML + CSS classes; behavior lives in `static/js/` modules.

---

## Components

### Auth Card

File: `templates/auth/base.html`, `auth/login.html`, `auth/register.html`
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Page background | `.auth-page` (`var(--bg-page)`, centered flex) |
| Card | `.auth-card` (`var(--bg-card)`, `1px solid var(--border)`, 12px radius, 24px padding) |
| Brand | `.auth-brand` |
| Heading | `.auth-title` |
| Subtitle | `.auth-subtitle` |
| Footer link | `.auth-switch` |

**Pattern notes:** All auth screens share this shell. Forms use `.form-stack` with 16px gaps; alerts sit directly below the title.

---

### Form Input

File: `templates/auth/login.html`, `auth/register.html`
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Field wrapper | `.field` |
| Label | `.field label` (13px, 500, `var(--text-secondary)`) |
| Input | `.input` (`var(--bg-card-secondary)`, `1px solid var(--border)`, 8px radius, `12px 16px`) |
| Focus | `.input:focus` → border `var(--border-focus)`, no outline/ring |
| Placeholder | `var(--text-muted)` |
| Error text | `.field-error` (`var(--status-error)`) |

**Pattern notes:** Inputs are full width. Labels sit above the input with a small gap. No shadows, no focus ring — border color only.

---

### Primary Button (CTA)

File: `static/css/app.css` (`.btn`, `.btn-primary`); used in auth, setup, session
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Base | `.btn` — inline-flex, 15px/500, 8px radius, `12px 24px` |
| Primary | `.btn-primary` — `var(--accent)` background, `var(--text-inverse)` text |
| Hover | `.btn-primary:hover:not(:disabled)` → `var(--accent-dark)` |
| Disabled | `.btn:disabled` → muted, `cursor: not-allowed` |
| Full width | `.btn-block` |

**Pattern notes:** One primary CTA per screen. Disabled state is used on setup until all selections are made.

---

### Secondary Button (Ghost)

File: `static/css/app.css` (`.btn-ghost`, `.btn-danger`)
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Ghost | `.btn-ghost` — transparent, `1px solid var(--border)`, `var(--text-secondary)` text |
| Ghost hover | border `var(--text-muted)`, text `var(--text-primary)` |
| Danger | `.btn-danger` — transparent with `var(--status-error)` border/text |

**Pattern notes:** Secondary actions only. `.btn-danger` is reserved for ending a session; no filled red buttons anywhere.

---

### Status Message (Error / Success)

File: `static/css/app.css` (`.alert`, `.alert-error`, `.alert-success`); used in auth, setup, session
Last updated: 2026-10-20

| Property | Error | Success |
|---|---|---|
| Background | `rgba(217, 83, 79, 0.1)` | `rgba(76, 175, 125, 0.1)` |
| Border | `var(--status-error)` at 30% | `var(--status-success)` at 30% |
| Text | `var(--status-error)`, 14px | `var(--status-success)`, 14px |

**Pattern notes:** Inline alert blocks; `.hidden` toggles visibility from JS. Never use browser `alert()`.

---

### App Header

File: `templates/app_base.html`; styles `.app-shell`, `.app-header`, `.brand`, `.app-nav`
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Layout | `.app-header` — flex, space-between, bottom border `var(--border)`, `24px` horizontal padding |
| Wordmark | `.brand` — 16px/600, `var(--text-primary)`, no logo |
| Nav links | `.app-nav a` — 14px, `var(--text-secondary)`, hover `var(--text-primary)` |
| Sign out | POST form + `.nav-button` styled identically to nav links |

**Pattern notes:** Minimal header on authenticated pages only. The session room keeps the header but nothing else competes with the exam. Sign-out is a POST form (CSRF), never a GET link.

---

### Text Link (Inline)

File: `static/css/app.css` (`a`, `.auth-switch a`)
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Color | `var(--accent)` |
| Hover | `#6D8FBE` |
| Decoration | none |

**Pattern notes:** Inline links use accent color with no underline. Used for auth switches and in-page navigation.

---

### Setup Page Container

File: `templates/setup.html`; styles `.page`, `.page-wide`, `.page-head`, `.config-section`
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Container | `.page.page-wide` — max-width 896px, centered, `24px` / `32px` padding |
| Heading block | `.page-head` — page title + supporting text |
| Section | `.config-section` with 32px gap |
| Section label | `.section-label` — 13px/500, `var(--text-secondary)` |

**Pattern notes:** Setup is a single scrollable page with always-visible sections in fixed order: language, exam, level, exercise. No wizard, no steps hidden behind navigation.

---

### Setup Option Card

File: `templates/setup.html`; styles `.option-list`, `.option-grid`, `.option-grid-3`, `.option-card`
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Base | `.option-card` — `10px` radius, `1px solid var(--border)`, `var(--bg-card)`, 20px padding, left-aligned |
| Selected | `.is-selected` — `var(--accent-faint)` bg, `var(--accent)` border, primary text |
| Static/locked | `.is-static` — selected styling on a `<div>`, no hover, no pointer |
| Hover (unselected) | border `var(--text-muted)`, text `var(--text-secondary)` |
| Title | `.option-title` — 15px/500 |
| Description | `.option-description` — 14px, muted |

**Pattern notes:** Selection is communicated only by border + background + text color — no checkmarks, no shadows. Every option is a `<button type="button" aria-pressed>`; selection state is owned by `static/js/setup.js`, which also enables the Start button.

---

### Status Read-out (Definition List)

File: `templates/session.html`; styles `.status-grid` (`<dl>`)
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Layout | `.status-grid` — two-column grid, 12px gap |
| Label | `dt` — 13px, `var(--text-muted)` |
| Value | `dd` — 15px/500, `var(--text-primary)` |

**Pattern notes:** Compact label/value pairs for microphone and transcription status. Values are plain words (`idle`, `requesting`, `active`, `connected`, `error`) — never badges or pills. JS updates `dd[data-status]` text only.

---

### Transcript Line (Mono)

File: `templates/session.html`; styles `.transcript-list`, `.transcript-speaker`, `.mono`
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| List | `.transcript-list` — flex column, 8px gap, hidden until toggled |
| Speaker label | `.transcript-speaker` — 12px, muted |
| Text | `.mono` — 13px monospace |
| Live partial | `.mono.muted` — secondary text until committed |
| Empty state | `.muted` — 14px secondary line |

**Pattern notes:** The transcript is a plain transcript, never chat bubbles. Live text is muted and replaced by committed entries. The panel is toggled by a ghost button and is scrollable.

---

### Session Controls

File: `templates/session.html`; behavior `static/js/session.js`
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Connect / Disconnect | `.btn.btn-primary` / `.btn.btn-ghost`, toggled by `hidden` |
| Examiner reply | `.btn.btn-ghost` — streams the LLM reply into the status area |
| Speak reply | `.btn.btn-ghost` — plays TTS (falls back to browser speech) |
| End session | `.btn.btn-danger` — evaluates, then navigates to `/feedback/<id>/` |
| Status text | `.mono` + `aria-live="polite"` |
| Error alert | `.alert.alert-error.hidden` |

**Pattern notes:** Buttons disable while an operation is in flight. All streams and audio sources are stopped on end, disconnect, and `pagehide`.

---

### Feedback Summary

File: `templates/feedback.html`; styles `.feedback-summary`, `.feedback-level`, `.verdict`
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Summary card | `.card` + `.feedback-summary` |
| Level | `.feedback-level` — large level label (B1/B2/C1) |
| Verdict | `.verdict` plus `.verdict-ready` / `.verdict-needs-work` / `.verdict-not-ready` |
| Score grid | `.score-grid` + `.score-card` (`2×2`, collapsing to one column) |
| Score label | `.score-label` — 13px muted |
| Score value | `.score-value` — 40px/700; denominator in `small` |

**Pattern notes:** Verdict color is the only semantic color on the page: success / warning / error. Scores are static — no count-up animations. Notes use `.notes-grid` + `.note-list`; recommendations and pronunciation flags use `.tag-list` + `.tag`. The full transcript closes the report in a `.card`.

---

### Account / Session History

File: `templates/account.html`; styles `.detail-list`, `.session-history`, `.session-title`, `.session-meta`
Last updated: 2026-10-20

| Property | Implementation |
|---|---|
| Plan details | `.detail-list` (`<dl>`) — label/value pairs |
| History list | `.session-history` — divided `<ul>`, separators `var(--border)` |
| Session title | `.session-title` — 15px/500 |
| Metadata | `.session-meta` — 13px muted |
| Result link | Accent inline link to feedback when a report exists |

**Pattern notes:** History lists the most recent sessions, newest first. Completed sessions link to feedback; active/abandoned sessions show status text instead.
