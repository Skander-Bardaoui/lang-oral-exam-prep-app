# Memory — Django Conversion

Last updated: 2026-10-20

## What was built

**Full Next.js → Django conversion**, preserving the product's existing surface:

- **Project:** `oral_exam/` (Django 5.2.18, Python 3.11.9, PostgreSQL 18), apps `accounts` and `exams`.
- **Auth:** register/login/logout/account using Django's built-in `User` (email stored as `username`), `Profile` auto-created via `post_save` signal, `@login_required` on pages, JSON `401` for API endpoints.
- **Models:** `accounts.Profile` (subscription status/tier, `stripe_customer_id`, `sessions_used`); `exams.ExamSession` (UUID, config, JSON transcript, status/timestamps); `exams.Feedback` (UUID, scores 0–9, JSON notes/flags/recommendations). Tables: `profiles`, `sessions`, `feedback`.
- **Pages/templates:** landing, login, register, setup, session room, account, feedback report — all server-rendered with the dark design system in `static/css/app.css`.
- **APIs:** `/api/session/start/`, `/api/session/evaluate/`, `/api/stt/token/`, `/api/llm/` (streaming), `/api/tts/` (streaming), `/api/stripe/webhook/`, `/health/`.
- **Voice pipeline:** `AudioWorklet` → Int16 PCM → base64 → ElevenLabs realtime WebSocket (single-use token); Groq streaming examiner replies; OpenAI TTS with browser `speechSynthesis` fallback.
- **Evaluation:** Groq JSON-mode evaluation, normalized and stored in `Feedback`; session marked completed; report rendered server-side.
- **Stripe:** webhook signature verification and profile subscription updates; checkout/portal routes are not built yet.

**Old code archived** to `legacy-next/` (git-ignored). `context/architecture.md`, `context/code-standards.md`, and `context/library-docs.md` were rewritten for Django.

## Decisions made

- Server-rendered Django templates + vanilla ES modules — no React, no bundler, no Supabase.
- All provider calls are server-side in `exams/services.py`; only the ElevenLabs single-use token reaches the browser.
- Groq model is `qwen/qwen3.8-27b` — the account does not have `llama-3.3-70b-versatile`.
- OpenAI TTS is the intended provider, but the account has no credits. The client falls back to browser speech automatically; the API returns `502` with a clear error.
- `stripe.SignatureVerificationError` is the correct exception in stripe v16 (`stripe.error` does not exist).

## Problems solved

- Stripe 16 import incompatibility fixed in `exams/views.py`; webhook tests added (unconfigured → 503, invalid signature → 400).
- OpenAI TTS 429 (`insufficient_quota`) handled without breaking the session via `speechSynthesis` fallback.
- ElevenLabs TTS fallback rejected (free plan cannot use library voices) — browser fallback retained instead.
- Template static loading fixed with `{% load static %}` in `setup.html` and `session.html`.
- Env loading supports `.env.local` first, then `.env`; Django secret generated and stored locally.

## Current state

- `manage.py check` clean; **32 tests pass** (`manage.py test`).
- Full HTTP smoke test passed: register → login → setup → start session → session page → account → static assets → STT token → LLM stream → TTS (502 by design, credits) → evaluation → feedback page.
- Database is PostgreSQL 18 on `127.0.0.1:5432` (`oral_exam`), configured through `DATABASE_URL` or `DB_*` in `.env.local`; migrations applied and all 32 tests pass against Postgres.
- Background dev server previously ran on `127.0.0.1:8001` for testing; normal dev command is `manage.py runserver`.
- Microphone and WebSocket behavior were not verified headlessly; needs a manual browser pass.
- `.env.local` contains live secrets and remains git-ignored — never print or commit it.

## Next session starts with

1. Manual browser QA of mic capture, ElevenLabs transcripts, LLM reply, and TTS fallback.
2. Remaining roadmap: waveform visualization (07), smart-examiner state machine/pause logic/personas (08–10), Stripe checkout + portal (14), error-state polish (16).
3. Read `context/progress-tracker.md` and `context/architecture.md` before changing anything.

## Open questions

- Does the OpenAI account get credits, or should the browser voice become the permanent MVP TTS?
