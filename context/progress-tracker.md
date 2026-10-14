# Progress Tracker

## Current Status

**Phase:** Phase 1 — Foundation
**Last completed:** 02 Supabase Auth
**Next:** 03 Exam Configuration Screen

---

## Progress

### Phase 1 — Foundation

- [x] 01 Project Scaffold
- [x] 02 Supabase Auth
- [ ] 03 Exam Configuration Screen

### Phase 2 — Voice Pipeline (Dumb Examiner)

- [ ] 04 Microphone Capture + Deepgram Connection
- [ ] 05 LLM Examiner Turn (Stub)
- [ ] 06 TTS Playback
- [ ] 07 Waveform Visualization

### Phase 3 — Smart Examiner

- [ ] 08 Session State Machine
- [ ] 09 Pause Classification + Intervention Logic
- [ ] 10 Prompt Builder + Exam Personas
- [ ] 11 Full Session Screen

### Phase 4 — Evaluation & Feedback

- [ ] 12 Post-Session Evaluation
- [ ] 13 Feedback Report Screen

### Phase 5 — Payments

- [ ] 14 Stripe Subscription

### Phase 6 — Launch Prep

- [ ] 15 Landing Page
- [ ] 16 Polish + Error States

---

## Decisions Made During Build

- Scaffolded with Next.js 16 (not 14) — `create-next-app` defaults to latest stable. Code standards reference Next.js 14 but the API surface is the same for MVP needs.
- Tailwind CSS v4 with `@tailwindcss/postcss` and `@theme` inline — no separate `tailwind.config.js`.
- `proxy.ts` replaces `middleware.ts` (Next.js 16 convention). The Supabase SSR auth pattern uses `createServerClient` with cookie management inside proxy.
- Google OAuth: Full-page redirect flow via `app/auth/callback/route.ts`. Button renders but shows config-needed message until Google OAuth is set up in Supabase dashboard.
- Email confirmation disabled for MVP. Sign-up redirects straight to login with a success message.
- Folder structure created in full per architecture.md specs.

---

## Notes

_Add notes here as the build progresses._
