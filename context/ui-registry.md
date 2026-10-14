# UI Registry

_Written by `/imprint` after building any UI component. Read this before building a new one — never duplicate a pattern that already exists here._

---

## Components

### Auth Card

File: `app/(auth)/login/page.tsx`, `app/(auth)/register/page.tsx`
Last updated: 2026-06-09

| Property | Class |
|---|---|
| Background | `bg-bg-card` |
| Border | `border border-border` |
| Border radius | `rounded-xl` |
| Text — heading | `text-2xl font-semibold text-text-primary` |
| Text — subtitle | `text-sm text-text-secondary` |
| Spacing | `p-6`, form gap `gap-4`, section margin `mt-6` |
| Max width | `max-w-sm` |

**Pattern notes:** Auth card is the standard card container for centered single-form pages. All auth screens share this same shell. Children inside use `mt-6` for major section spacing and `mt-4` for alert spacing below the heading.

---

### Form Input

File: `app/(auth)/login/page.tsx`, `app/(auth)/register/page.tsx`
Last updated: 2026-06-09

| Property | Class |
|---|---|
| Background | `bg-bg-card-secondary` |
| Border | `border border-border` |
| Border focus | `focus:border-border-focus focus:outline-none` |
| Border radius | `rounded-lg` |
| Text | `text-[15px] text-text-primary` |
| Placeholder | `placeholder:text-text-muted` |
| Padding | `px-4 py-3` |
| Width | `w-full` |
| Label | `text-[13px] font-medium text-text-secondary` |
| Label spacing | `mt-1` between label and input |

**Pattern notes:** All text inputs share this exact class set. `w-full` always applied. The `mt-1` on the input itself creates the gap from the label above (not `gap-` on the parent). No shadow, no focus ring — only border color change.

---

### Primary Button (CTA)

File: `app/(auth)/login/page.tsx`, `app/(auth)/register/page.tsx`
Last updated: 2026-06-09

| Property | Class |
|---|---|
| Background | `bg-accent` |
| Background hover | `hover:bg-accent-dark` |
| Text | `text-[15px] font-medium text-text-inverse` |
| Border radius | `rounded-lg` |
| Padding | `px-6 py-3` |
| Transition | `transition-colors` |

**Pattern notes:** Primary buttons are the main CTA on a page. Always solid accent background with inverse text. Used for submit actions. `mt-2` above the button to separate from preceding input or section.

---

### Secondary Button (Outline/Ghost)

File: `app/(auth)/login/page.tsx`, `app/(auth)/register/page.tsx`
Last updated: 2026-06-09

| Property | Class |
|---|---|
| Background | `bg-transparent` |
| Border | `border border-border` |
| Border hover | `hover:border-text-muted` |
| Text | `text-[15px] font-medium text-text-secondary` |
| Text hover | `hover:text-text-primary` |
| Border radius | `rounded-lg` |
| Padding | `px-6 py-3` |
| Width | `w-full` |
| Transition | `transition-all` |

**Pattern notes:** Secondary buttons are outline-style with muted text that brightens on hover. Used for Google OAuth and other non-primary actions. Full width when stacking below the primary form section.

---

### Status Message (Error / Success)

File: `app/(auth)/login/page.tsx`, `app/(auth)/register/page.tsx`
Last updated: 2026-06-09

| Property | Class (Error) | Class (Success) |
|---|---|---|
| Background | `bg-status-error/10` | `bg-status-success/10` |
| Border | `border border-status-error/30` | `border border-status-success/30` |
| Text | `text-sm text-status-error` | `text-sm text-status-success` |
| Border radius | `rounded-lg` | `rounded-lg` |
| Padding | `px-3 py-2` | `px-3 py-2` |

**Pattern notes:** Status messages appear inline within the card, below the heading/subtitle and above the form. Uses semi-transparent backgrounds and borders to keep the dark theme. `/10` for bg, `/30` for border, solid for text.

---

### Auth Layout

File: `app/(auth)/layout.tsx`
Last updated: 2026-06-09

| Property | Class |
|---|---|
| Container | `flex flex-1 items-center justify-center bg-bg-page` |

**Pattern notes:** Full-viewport centered layout for auth pages. The `flex-1` (inherited from root layout's `flex flex-col`) stretches to fill remaining height. The child auth card sits centered both vertically and horizontally.

---

### App Header

File: `app/(app)/layout.tsx`
Last updated: 2026-06-09

| Property | Class |
|---|---|
| Layout | `flex items-center justify-between` |
| Border bottom | `border-b border-border` |
| Padding | `px-6 py-4` |
| Wordmark | `text-base font-semibold text-text-primary no-underline` |
| Nav link | `text-sm text-text-secondary no-underline transition-colors hover:text-text-primary` |
| Nav gap | `gap-4` between nav items |

**Pattern notes:** The app header is minimal — wordmark on left, nav links on right. No logo, just text. Links use secondary text that brightens on hover. No active state indicator. Sign Out is rendered as a form button styled identically to nav links.

---

### Text Link (Inline)

File: `app/(auth)/login/page.tsx`, `app/(auth)/register/page.tsx`
Last updated: 2026-06-09

| Property | Class |
|---|---|
| Text | `font-medium text-accent` |
| Hover | `hover:text-accent-dark` |
| Text decoration | `no-underline` |
| Transition | `transition-colors` |

**Pattern notes:** Inline links within paragraphs use accent color, medium weight, no underline — only color change on hover. Used for "Register" / "Log In" links in the footer area of auth cards.
