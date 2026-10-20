# Progress Tracker

## Current Status

**Phase:** Django conversion complete — full MVP feature set implemented
**Last completed:** Django conversion + PostgreSQL migration; all pages and provider endpoints working
**Next:** Browser-based QA of the voice pipeline, then Feature 14 Stripe polish (checkout + portal are not built)

---

## Progress

### Phase 1 — Foundation

- [x] 01 Project Scaffold (Django 5.2)
- [x] 02 Authentication (Django auth, email-as-username)
- [x] 03 Exam Configuration Screen

### Phase 2 — Voice Pipeline (Dumb Examiner)

- [x] 04 Microphone Capture + ElevenLabs Realtime STT
- [x] 05 LLM Examiner Turn (Stub)
- [x] 06 TTS Playback (OpenAI + browser speech fallback)
- [ ] 07 Waveform Visualization

### Phase 3 — Smart Examiner

- [ ] 08 Session State Machine
- [ ] 09 Pause Classification + Intervention Logic
- [ ] 10 Prompt Builder + Exam Personas (currently a placeholder system prompt)
- [x] 11 Full Session Screen (functional room; smart-examiner behaviors still pending)

### Phase 4 — Evaluation & Feedback

- [x] 12 Post-Session Evaluation
- [x] 13 Feedback Report Screen

### Phase 5 — Payments

- [ ] 14 Stripe Subscription (webhook updates profiles; checkout/portal not built)
- [x] Free-tier limit (3 sessions) enforced server-side

### Phase 6 — Launch Prep

- [x] 15 Landing Page
- [ ] 16 Polish + Error States

---

## Decisions Made During Build

- **Stack conversion:** Next.js 16 + Supabase replaced with Django 5.2 + PostgreSQL 18 + Django templates + vanilla ES modules. Old source archived in `legacy-next/`; production docs (`architecture.md`, `code-standards.md`, `library-docs.md`) describe the Django stack.
- **Auth:** Django's built-in `User`; email is normalized lowercase and stored in `username`. `accounts.Profile` is created by a `post_save` signal. No custom user model.
- **Database:** PostgreSQL 18 at `127.0.0.1:5432`, database `oral_exam`, driver `psycopg[binary]` 3.2.10. Configured via `DATABASE_URL` or the `DB_*` variables in `.env.local`. UUID primary keys; tables named `profiles`, `sessions`, `feedback`. Migrations are standard Django migrations (`accounts/migrations/`, `exams/migrations/`).
- **Free-tier accounting:** `sessions_used` increments at session start inside `transaction.atomic()` with `Profile.objects.select_for_update()`. Subscribed users bypass the limit. Roll back the transaction if session creation fails.
- **Random exercise:** resolved server-side; `ExamSession.exercise_type` always stores `topic_discussion` or `debate`.
- **Session URL:** `/session/?sessionId=<uuid>` — ownership enforced server-side; sessions that already have feedback redirect to the report.
- **API shape:** JSON errors are `{'error': '<code>', 'message': '<human text>'}`. Page routes redirect unauthenticated users to `/login/`; API routes return `401` JSON via `api_login_required`.
- **STT:** ElevenLabs Scribe v2 Realtime. Server issues a single-use token (`POST https://api.elevenlabs.io/v1/single-use-token/realtime_scribe`); browser connects directly over WebSocket. Audio path: `AudioWorklet` → Float32→Int16 → base64 → `input_audio_chunk`.
- **LLM:** Groq OpenAI-compatible REST endpoint, model `qwen/qwen3.8-27b` (`llama-3.3-70b-versatile` is not available on the account). Examiner replies stream as plain text; evaluation uses JSON mode with a no-JSON-mode retry.
- **TTS:** OpenAI `tts-1` / `onyx` / mp3. The OpenAI account currently has **no credits** (429), so `static/js/tts.js` falls back to browser `speechSynthesis` automatically. ElevenLabs library voices were tried and rejected (free plan: `402 paid_plan_required`).
- **Evaluation:** Post-session Groq call with a structured prompt, normalized server-side (scores clamped 0–9, enums validated) and persisted via `Feedback.objects.update_or_create`. The session is marked `completed` with `ended_at` and the transcript saved.
- **Stripe:** Webhook signature verification uses `stripe.SignatureVerificationError` (top-level; `stripe.error` does not exist in SDK v16). Only the webhook writes `subscription_status`.
- **Static assets:** `static/css/app.css` contains the full design-token stylesheet; JS modules in `static/js/`; worklet at `static/worklets/pcm-processor.js`. Served by Django staticfiles in dev; run `manage.py collectstatic` for deployment.
- **Docs:** `architecture.md`, `code-standards.md`, and `library-docs.md` were rewritten for Django/Python/vanilla JS. `build-plan.md` keeps the original feature roadmap with a conversion note.

---

## Notes

- Run: `.venv/Scripts/python.exe manage.py runserver`
- Tests: `.venv/Scripts/python.exe manage.py test` — 32 tests passing.
- `.env.local` holds the Django secret key, PostgreSQL credentials, and the Groq, ElevenLabs, OpenAI, and Stripe test keys. `OPENAI_API_KEY` is present but the account has no credits. `SUPABASE_*` variables are legacy and unused.
- The old Next.js app remains in `legacy-next/` (git-ignored) for reference only. It is not part of the running app.
- Browser microphone/WebSocket behavior still needs a manual pass in Chrome/Edge — HTTP endpoints and static modules were verified with a full request smoke test.
