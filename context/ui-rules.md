# UI Rules

## The One Rule That Governs All Others

This UI is an exam room. Every design decision — layout, color, animation, copy — should pass the question: "Does this belong in an exam room?" If it feels like a game, a social app, or a marketing page, it's wrong.

---

## Layout

**Page max-width:** `896px` — centered, generous side padding. Not full-bleed, not ultra-wide.

**Page padding:** `px-6` on mobile, `px-8` on desktop. Never go edge-to-edge.

**Vertical rhythm:** sections are separated by `gap-12` (48px). Inside sections, components are separated by `gap-6` (24px). Inside components, elements are separated by `gap-4` (16px).

**Session screen is the exception:** full viewport height, no scroll. Everything fits on one screen. The waveform is centered vertically. This is not a document — it is a room.

**Feedback screen:** scrollable long-form document. Generous padding, clear hierarchy. No sidebars.

---

## Navigation

There is no persistent navigation. The app has intentional one-way flow:
```
Landing → Login/Register → Setup → Session → Feedback
```
The only persistent navigation element is a minimal header on authenticated screens:
- Left: wordmark (text only, no logo)
- Right: account icon → `/account`

The session screen has **no header**. Nothing competes with the exam.

Active states: underline only, no background pills, no bold.

---

## Cards

The standard content container. All cards follow the component token exactly:
- Background: `#1A1D24`
- Border: `1px solid #2A2D35`
- Border-radius: `12px`
- Padding: `24px`

Cards are **never nested more than one level deep**. If you need a section inside a card, use a horizontal rule (`border-t border-[#2A2D35]`) or tighter internal spacing — not a card inside a card.

Cards never have drop shadows. Elevation is communicated by border color, not shadow.

---

## Typography Hierarchy

Every page has exactly one `heading-1`. Sections within a page use `heading-2`. Subsections use `heading-3`. Never skip levels.

`body` text is used for explanatory copy and instructions. `body-secondary` is used for metadata, dates, and supporting context.

`label` style is used above input fields and for table headers. Always sentence case, never all-caps.

No text alignment other than left. No centered body text. Centered heading on landing page hero only.

---

## Buttons

**Primary button:** One per screen. It's the next action. "Start session" on setup. "Continue" on each setup step. "View feedback" after session.

**Secondary button:** For alternatives and escapes. "End session early." "Try again." "Back to setup."

**Destructive button:** For dangerous or irreversible actions only. "End session" (confirms via a short confirmation state — button text changes to "Confirm end?" for 3 seconds, then resets if not clicked again).

Buttons are **never disabled** if the reason isn't obvious. If an action isn't available, hide the button or explain why inline.

Button text is imperative: "Start session", not "Session start". "View feedback", not "Feedback".

---

## Forms

Label above input, never inside. Labels use `label` typography style.

Input fields are full width within their container.

Error messages appear below the input in `status-error` color (`#D9534F`), `caption` size. One line only.

Submit button is always the rightmost / bottommost element in a form. Never floated left.

No asterisks for required fields — in this app, all fields in a form are required unless explicitly labeled optional.

---

## Setup Flow

The setup screen is a vertical stack of selection steps. Each step is a card. Steps are always visible — not hidden tabs, not a wizard that hides previous steps. The user can see what they've selected.

Selected option: `active-bg`, `active-border`, `active-text` tokens from component tokens.

Unselected options: `inactive` tokens.

"Start session" button appears only after all steps have a selection. It does not fade in — it appears suddenly once the last selection is made.

---

## Session Screen

**The session screen layout:**
```
┌─────────────────────────────────────────────────┐
│  Examiner Name + Flag        [TIMER: 14:32]      │
│                                                   │
│                                                   │
│              [WAVEFORM ——————————]                │
│                                                   │
│                   Listening...                    │
│                                                   │
│                                          [End ↗]  │
│                                                   │
│  [▼ Show transcript]                             │
└─────────────────────────────────────────────────┘
```
The waveform is centered vertically in the available space. Nothing competes with it.

The status text beneath the waveform cycles through: `Listening...` / `Processing...` / `Examiner speaking...`. It transitions with a simple opacity fade (200ms). Never uses a spinner — just the text.

The transcript panel slides up from the bottom when toggled. It uses `bg-card` background, `border-t` separator, max-height `40vh`, scrollable.

The "End session" button is small, secondary style, bottom-right. Clicking it changes the text to "Confirm end?" for 3 seconds. If the user clicks again within 3 seconds, the session ends. If not, it resets. No modal.

---

## Feedback Screen

The feedback report is a long-form document. It reads top to bottom:

1. Overall verdict badge + score
2. Four score cards in a 2×2 grid (desktop) or single column (mobile)
3. Pronunciation flags section
4. Recommended focus areas (numbered list)
5. Session metadata footer
6. Two CTAs: "Try again" + "New session"

Score cards each contain: score number (`score` typography), dimension name (`heading-2`), bullet notes (`body-secondary`), and optionally a quoted transcript example (blockquote style, left border `2px solid accent`).

The overall verdict badge uses `score-badge` component token, level-matched color.

---

## Empty States

Every section that can be empty has a quiet, honest empty state:
- No illustration, no mascot
- One line of `body-secondary` text explaining what will appear here
- Example: "Your transcript will appear here during the session."

---

## Loading States

No spinners except for the post-session evaluation ("Generating your feedback...").

For the evaluation loading state: full-screen overlay on the session screen, `bg-page` background, centered text in `body` style. A subtle animated ellipsis after the text (CSS `::after` animation). No spinner, no progress bar.

For page-level data loading (server components): use Next.js `loading.tsx` with skeleton blocks — `bg-card` rectangles at the expected dimensions of each content section, no shimmer animation.

---

## Do Nots

1. **No gamification.** No streaks, no XP, no level-up animations, no confetti, no score change animations. Scores are presented statically.
2. **No emoji in UI.** Flags are the only exception (examiner nationality). Use SVG flag icons from a library, not emoji.
3. **No chat bubbles.** The transcript is a plain monospace transcript — `[Examiner]` and `[You]` labels, no speech bubbles.
4. **No tooltips.** If something needs a tooltip to be understood, the label or UI is wrong.
5. **No hover cards or popovers.** This design has no overlapping interactive elements. Keep it flat.
6. **No color gradients.** Solid fills only. The waveform bars use solid colors, not gradients.
7. **No border-radius above 12px.** The design is not "rounded friendly" — it is controlled and formal.
8. **No placeholder text that starts with "Enter your..."** Labels do that job. Placeholder text is either an example value or empty.
9. **No inline success states that say "Success!".** Successes are communicated by routing to the next screen, not a green toast.
10. **No skeleton loading states that pulse or shimmer.** Static skeleton blocks only.
