# Memory — Phase 1 Foundation (Feature 01 Scaffold)

Last updated: 2026-06-09

## What was built

**Feature 01 — Project Scaffold**
- Initialized Next.js 16.2.7 with TypeScript strict, Tailwind CSS v4, ESLint flat config
- Full folder structure per architecture.md (all app/ route groups, API routes, lib/ modules, types/, config/, components/ subdirs, hooks/)
- `app/globals.css` with all 22 design tokens from ui-tokens.md as Tailwind v4 `@theme` variables
- Root `app/layout.tsx` with `Inter` font from `next/font/google`
- Route group stubs: login, register, setup, session, feedback/`[sessionId]`, account
- API route stubs: session/start, session/evaluate, deepgram/token, tts, llm, stripe/webhook
- `lib/supabase/client.ts` and `lib/supabase/server.ts` — stubbed without `@supabase/ssr` import
- `lib/env.ts` — `requireEnv` validation function per code-standards.md
- All other lib stubs: deepgram, groq, tts, stripe, session/state-machine, session/pause-classifier, session/intervention, session/prompt-builder
- Type stubs: session.ts, feedback.ts, exam.ts
- Config stub: exams.ts
- `.env.local.example` with all 11 required keys
- `middleware.ts` removed (Next.js 16 deprecated in favor of `proxy`)

## Decisions made

- Scaffolded with Next.js 16 (not 14) — `create-next-app` defaults to latest stable. API surface compatible with MVP needs.
- Tailwind CSS v4 with `@tailwindcss/postcss` and `@theme inline` — no separate `tailwind.config.js`.
- Supabase client stubs use `export {}` only — `@supabase/ssr` will be installed in Phase 2.
- Used `rounded-xl` (Tailwind v4's 12px radius) per ui-tokens.md card spec.
- Dynamic route params use `params: Promise<{ sessionId: string }>` pattern (Next.js 16 convention).

## Problems solved

- `create-next-app` timed out during npm install — ran `npm install` separately after scaffold.
- ESLint flat config doesn't honor underscore-prefix convention for unused vars — removed unused params from API stubs entirely.
- `rounded-12` is invalid in Tailwind v4 — replaced with `rounded-xl` across 6 stub pages (caught by review).
- Missing `lib/env.ts` — created per code-standards.md pattern (caught by review).

## Current state

- Feature 01 complete. Build passes (0 errors). Lint passes (0 warnings).
- All 13 routes render with dark exam-room theme.
- No business logic, no external service integrations, no real UI components yet.
- Stubs return `501 Not Implemented` for API routes.

## Next session starts with

**Feature 02 — Supabase Auth:**
1. Install `@supabase/ssr`, `@supabase/supabase-js`
2. Implement `lib/supabase/client.ts` and `lib/supabase/server.ts` properly
3. Create login page with email/password + Google OAuth
4. Create register page
5. Add auth middleware (`proxy.ts` for Next.js 16)
6. Create `profiles` table in Supabase
7. Auto-create profile row on first sign-in via trigger or server action

## Open questions

- None
