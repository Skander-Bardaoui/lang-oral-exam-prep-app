# UI Tokens

## Philosophy

The visual language is an exam room: formal, quiet, purposeful. One accent color. One animated element (the waveform). Everything else is static and restrained. No decoration that doesn't carry meaning.

---

## Colors

### Accent / Brand
| Token | Hex | Usage |
|---|---|---|
| `accent` | `#4A6FA5` | Primary CTA buttons, active states, score highlights |
| `accent-dark` | `#35527A` | Button hover/pressed state |
| `accent-muted` | `#2A3F5C` | Subtle accent backgrounds (active step in setup flow) |
| `accent-faint` | `#1A2535` | Barely-there accent tint on cards |

### Backgrounds
| Token | Hex | Usage |
|---|---|---|
| `bg-page` | `#111318` | Root page background — near black, not pure |
| `bg-card` | `#1A1D24` | Cards, panels, form containers |
| `bg-card-secondary` | `#20242D` | Nested card surfaces, input backgrounds |
| `bg-overlay` | `#0D0F13` | Modal/dialog backdrops |

### Text
| Token | Hex | Usage |
|---|---|---|
| `text-primary` | `#E8EAED` | Headings, labels, primary body |
| `text-secondary` | `#9AA0AC` | Sub-labels, metadata, placeholder text |
| `text-muted` | `#5C6370` | Disabled states, fine print |
| `text-inverse` | `#111318` | Text on accent-colored button backgrounds |

### Status
| Token | Hex | Usage |
|---|---|---|
| `status-success` | `#4CAF7D` | Ready verdict, successful connection |
| `status-warning` | `#D4A017` | Needs Work verdict, caution states |
| `status-error` | `#D9534F` | Not Ready verdict, connection errors, form errors |
| `status-info` | `#4A6FA5` | Same as accent — informational states |

### Borders
| Token | Hex | Usage |
|---|---|---|
| `border` | `#2A2D35` | Card borders, input borders, dividers |
| `border-focus` | `#4A6FA5` | Input focus ring |
| `border-subtle` | `#1E2128` | Subtle separators |

### Waveform
| Token | Hex | Usage |
|---|---|---|
| `waveform-user` | `#4A6FA5` | User voice bars (same as accent) |
| `waveform-examiner` | `#E8EAED` | Examiner voice bars (same as text-primary) |
| `waveform-idle` | `#2A2D35` | Flat line idle state |

---

## Typography

**Font:** `Inter` — clean, slightly condensed at heavier weights, legible at small sizes. The stack is declared as `--font-sans` in `static/css/app.css` with system fallbacks; no webfont is bundled for MVP (add a Google Fonts `<link>` in `templates/base.html` if exact Inter rendering is required).

| Style | Size | Weight | Line Height | Color Token | Usage |
|---|---|---|---|---|---|
| `display` | 36px | 600 | 1.15 | `text-primary` | Hero headline on landing page |
| `heading-1` | 28px | 600 | 1.2 | `text-primary` | Page titles (Feedback report title) |
| `heading-2` | 20px | 600 | 1.25 | `text-primary` | Section headings, score card titles |
| `heading-3` | 16px | 600 | 1.3 | `text-primary` | Sub-section labels, card headers |
| `body` | 15px | 400 | 1.6 | `text-primary` | Body text, instructions |
| `body-secondary` | 14px | 400 | 1.5 | `text-secondary` | Metadata, descriptions, notes |
| `label` | 13px | 500 | 1.4 | `text-secondary` | Form labels, table headers, step labels |
| `caption` | 12px | 400 | 1.4 | `text-muted` | Fine print, timestamps, footnotes |
| `mono` | 13px | 400 | 1.5 | `text-secondary` | Transcript text, session IDs |
| `timer` | 28px | 300 | 1 | `text-primary` | Session countdown timer — light weight, tabular |
| `score` | 40px | 700 | 1 | `text-primary` | Large score numbers (7/10) |

**CSS implementation (`static/css/app.css`):**
- `display` → `.display` / hero `h1`
- `heading-1` → page `h1` (24px base)
- `heading-2` → `.card h2`, section headings
- `heading-3` → `.card h3`
- `body` → `body` base
- `body-secondary` → `.muted`
- `label` → `.field label`, `.section-label`
- `caption` → small text / metadata
- `mono` → `.mono`, transcript entries
- `timer` → tabular numerals, light weight
- `score` → `.score-value`

---

## Spacing

Base unit: **4px**. All spacing is a multiple of 4.

| Token | Value | CSS usage | Usage |
|---|---|---|---|
| `space-1` | 4px | `4px` | Tight internal padding (icon + label) |
| `space-2` | 8px | `8px` | Compact spacing within components |
| `space-3` | 12px | `12px` | Default internal card padding (tight) |
| `space-4` | 16px | `16px` | Standard spacing — most common |
| `space-5` | 20px | `20px` | Section internal padding |
| `space-6` | 24px | `24px` | Card padding standard |
| `space-8` | 32px | `32px` | Generous card padding, section gaps |
| `space-12` | 48px | `48px` | Page section separation |
| `space-16` | 64px | `64px` | Hero padding, major vertical rhythm |

---

## Component Tokens

### Card
```
background:    #1A1D24   (var(--bg-card))
border:        1px solid #2A2D35   (var(--border))
border-radius: 12px
padding:       24px   (space-6)
shadow:        none — no drop shadows in this design
```

### Button — Primary (CTA)
```
background:       #4A6FA5   (var(--accent))
background-hover: #35527A   (var(--accent-dark))
text-color:       #111318   (var(--text-inverse))
font-size:        15px
font-weight:      500
border-radius:    8px
padding:          12px 24px
border:           none
transition:       background 150ms ease
```

### Button — Secondary (Ghost)
```
background:       transparent
background-hover: #1A2535   (accent-faint)
text-color:       #9AA0AC   (var(--text-secondary))
text-hover-color: #E8EAED   (var(--text-primary))
font-size:        15px
font-weight:      500
border-radius:    8px
padding:          12px 24px
border:           1px solid #2A2D35   (var(--border))
transition:       all 150ms ease
```

### Button — Destructive
```
background:       transparent
background-hover: rgba(217, 83, 79, 0.1)
text-color:       #D9534F   (status-error)
font-size:        14px
font-weight:      500
border-radius:    8px
padding:          10px 20px
border:           1px solid rgba(217, 83, 79, 0.3)
```

### Input
```
background:     #20242D   (var(--bg-card-secondary))
border:         1px solid #2A2D35   (var(--border))
border-focus:   1px solid #4A6FA5   (border-focus)
border-radius:  8px
padding:        12px 16px
font-size:      15px
color:          #E8EAED   (var(--text-primary))
placeholder:    #5C6370   (var(--text-muted))
```

### Score Badge (feedback screen)
```
background:    level-dependent — see below
border-radius: 8px
padding:       8px 16px
font-size:     13px
font-weight:   600

B1: background #2A3F5C, color #4A6FA5
B2: background #2D3A2A, color #4CAF7D
C1: background #3A2A1A, color #D4A017
```

### Setup Step (active / inactive)
```
active-bg:       #1A2535   (accent-faint)
active-border:   #4A6FA5   (var(--accent))
active-text:     #E8EAED   (var(--text-primary))
inactive-bg:     #1A1D24   (var(--bg-card))
inactive-border: #2A2D35   (var(--border))
inactive-text:   #5C6370   (var(--text-muted))
border-radius:   10px
padding:         20px 24px
```

### Waveform Canvas
```
height:          80px
width:           100%
bar-width:       3px
bar-gap:         2px
bar-count:       ~48 bars (fills available width)
border-radius:   2px per bar
idle-bar-height: 3px (flat line)
animation:       requestAnimationFrame at 60fps
```

### Status Pill (session screen)
```
background:  transparent
text-color:  #9AA0AC   (var(--text-secondary))
font-size:   13px
font-weight: 400
— no border, no background. Just quiet text beneath the waveform.
```
