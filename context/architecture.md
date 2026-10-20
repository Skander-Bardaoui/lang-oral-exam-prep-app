# Architecture

## Stack

| Layer | Tool | Purpose |
|---|---|---|
| Framework | Django 5.2 | Server-rendered pages, auth, ORM, API endpoints |
| Language — server | Python 3.11 | Views, models, provider clients |
| Language — client | Vanilla ES modules | Microphone capture, WebSocket, streaming, playback |
| Templates | Django Templates | Server-rendered UI |
| Styling | Hand-written CSS in `static/css/app.css` | Dark exam-room design using CSS tokens |
| Auth | Django auth | Email + password, session cookies, CSRF protection |
| Database | PostgreSQL 18 (`psycopg` 3) | Profiles, sessions, feedback |
| STT + VAD | ElevenLabs Scribe v2 Realtime | Real-time speech-to-text, VAD segmentation, word confidence |
| LLM | Groq (OpenAI-compatible REST) | AI examiner during session + evaluator at session end |
| TTS | OpenAI TTS (server) + browser SpeechSynthesis (fallback) | Examiner voice audio |
| Payments | Stripe | Webhook handling for subscription state |
| Deployment | WSGI host (Gunicorn/uWSGI) | Standard long-running Python process |

## Folder Structure

```
/
├── manage.py
├── requirements.txt
├── .env.example                 # Variable names only — no secrets
├── .env.local                   # Local credentials, git-ignored
├── oral_exam/                   # Django project package
│   ├── settings.py              # Env loading, apps, templates, static, providers
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                    # Auth and user profile domain
│   ├── models.py                # Profile (subscription + usage counters)
│   ├── forms.py                 # Login/registration validation
│   ├── views.py                 # login, register, logout, account
│   ├── urls.py
│   ├── signals.py               # Auto-create Profile on User creation
│   ├── admin.py
│   └── tests.py
├── exams/                       # Exam sessions, feedback, provider integrations
│   ├── config.py                # Exam types, levels, durations, labels
│   ├── models.py                # ExamSession, Feedback
│   ├── services.py              # ElevenLabs, Groq, OpenAI TTS clients
│   ├── views.py                 # Pages + JSON/streaming API endpoints
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
├── templates/
│   ├── base.html                # HTML shell, CSRF meta tag
│   ├── landing.html
│   ├── auth/base.html
│   ├── auth/login.html
│   ├── auth/register.html
│   ├── app_base.html            # Authenticated header + layout
│   ├── setup.html
│   ├── session.html
│   ├── account.html
│   └── feedback.html
├── static/
│   ├── css/app.css              # Design tokens + all component styles
│   ├── js/csrf.js               # CSRF header helper
│   ├── js/audio-capture.js      # AudioWorklet microphone pipeline
│   ├── js/transcription.js      # ElevenLabs realtime WebSocket
│   ├── js/tts.js                # Server TTS + browser-voice fallback
│   ├── js/setup.js              # Setup flow + session start
│   ├── js/session.js            # Exam room orchestration
│   └── worklets/pcm-processor.js
├── context/                     # Project documentation (updated for Django)
└── legacy-next/                 # Archived Next.js implementation (git-ignored)
```

The database is an external PostgreSQL 18 server (`oral_exam` database, default `127.0.0.1:5432`), configured through `DATABASE_URL` or the `DB_*` environment variables. No database files live in the repository.

## System Boundaries

| Layer | Owns | Must Never |
|---|---|---|
| `accounts/` | User auth, profile, subscription fields, usage counter | Call exam providers, construct prompts |
| `exams/models.py` | Exam session and feedback persistence | Call external APIs, render UI |
| `exams/services.py` | ElevenLabs, Groq, OpenAI HTTP calls, prompt strings | Touch request/response objects or the ORM |
| `exams/views.py` | Auth checks, validation, ownership checks, orchestration | Contain raw provider SDK logic |
| `templates/` | Rendering and static markup | Query the database or call external APIs |
| `static/js/` | Browser API lifecycle (mic, WebSocket, audio) and UI state | Hold provider API keys or make direct provider calls (STT WebSocket excepted) |
| `exams/config.py` | Static exam definitions and labels | Contain runtime state |

## Data Flow

**Session Start**
1. User submits the setup screen → `POST /api/session/start/`
2. Django validates JSON, auth, and config.
3. An `ExamSession` row is created; sessions are unlimited and free.
4. The browser navigates to `/session/?sessionId=<uuid>`.
5. The page requests a single-use ElevenLabs token from `GET /api/stt/token/`.
6. The browser opens the ElevenLabs realtime WebSocket directly.
7. The browser posts committed turns to `POST /api/llm/` (Groq streaming).
8. The browser posts examiner text to `POST /api/tts/` (OpenAI streaming). If server TTS is unavailable, the browser speaks the text with `speechSynthesis`.

**User Turn → Examiner Response**
1. ElevenLabs VAD segments speech and emits `partial_transcript` / `committed_transcript`.
2. The session screen appends the committed segment to the transcript list.
3. "Send to LLM" posts the segment plus chat history to `/api/llm/`.
4. Django streams the Groq reply back as `text/plain`.
5. "Speak reply" posts the reply to `/api/tts/` and plays the MP3. Browser voice is the fallback.

**Session End + Evaluation**
1. "End session" posts the transcript to `POST /api/session/evaluate/`.
2. Django checks session ownership, calls Groq for structured JSON, and normalizes scores/notes.
3. A `Feedback` row is created, the session is marked `completed`, and the transcript is stored.
4. The browser redirects to `/feedback/<sessionId>/`.

## Database Schema

```sql
-- Django auth_user handles accounts (username = normalized email)

CREATE TABLE profiles (
  id INTEGER PRIMARY KEY,
  user_id INTEGER UNIQUE NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
  stripe_customer_id VARCHAR(255) NOT NULL DEFAULT '',
  subscription_status VARCHAR(20) NOT NULL DEFAULT 'free',  -- free | active | cancelled
  subscription_tier VARCHAR(20) NULL,                       -- monthly | annual | NULL
  sessions_used INTEGER NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL
);

CREATE TABLE sessions (
  id CHAR(32) PRIMARY KEY,                                  -- UUID
  user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
  exam_type VARCHAR(32) NOT NULL,                           -- ielts | cambridge_b2
  level VARCHAR(8) NOT NULL,                                -- b1 | b2 | c1
  exercise_type VARCHAR(32) NOT NULL,                       -- topic_discussion | debate
  language VARCHAR(8) NOT NULL DEFAULT 'en',
  duration_seconds INTEGER NOT NULL,
  transcript JSON NOT NULL DEFAULT '[]',
  status VARCHAR(20) NOT NULL DEFAULT 'active',             -- active | completed | abandoned
  started_at DATETIME NOT NULL,
  ended_at DATETIME NULL
);

CREATE TABLE feedback (
  id CHAR(32) PRIMARY KEY,
  session_id CHAR(32) UNIQUE NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
  overall_level VARCHAR(8) NOT NULL DEFAULT '',
  overall_verdict VARCHAR(32) NOT NULL DEFAULT '',
  fluency_score SMALLINT NOT NULL DEFAULT 0,
  vocabulary_score SMALLINT NOT NULL DEFAULT 0,
  grammar_score SMALLINT NOT NULL DEFAULT 0,
  task_achievement_score SMALLINT NOT NULL DEFAULT 0,
  fluency_notes JSON NOT NULL DEFAULT '[]',
  vocabulary_notes JSON NOT NULL DEFAULT '[]',
  grammar_notes JSON NOT NULL DEFAULT '[]',
  task_achievement_notes JSON NOT NULL DEFAULT '[]',
  pronunciation_flags JSON NOT NULL DEFAULT '[]',
  recommendations JSON NOT NULL DEFAULT '[]',
  created_at DATETIME NOT NULL
);
```

## Authentication

- Provider: Django auth (`django.contrib.auth`).
- Credential: email address stored as `username` (normalized to lowercase) plus password.
- Protected pages use `@login_required` and redirect to `/login/?next=...`.
- JSON endpoints use `@api_login_required`, which returns `401 {"error": "unauthorized"}` instead of redirecting.
- CSRF: Django's CSRF middleware is enabled. The base template exposes a CSRF meta tag; `static/js/csrf.js` sends `X-CSRFToken` on JSON requests.
- Registration redirects to `/login/?registered=true`; login redirects to `/setup/`.
- Google OAuth is intentionally not wired (the original Supabase flow was a placeholder).

## Invariants

1. **Speech audio never passes through Django** — the browser connects directly to ElevenLabs using a short-lived token from `/api/stt/token/`.
2. **Provider API keys stay server-side** — Groq, OpenAI, ElevenLabs, and Stripe keys are read from the environment and never rendered into templates or static JS.
3. **Session ownership is enforced server-side** — every session/feedback lookup filters by `user=request.user`.
4. **Sessions are unlimited** — `/api/session/start/` does not enforce a session cap or paywall.
6. **Transcripts are append-only during a session** — the client appends committed turns; the server stores the final list at evaluation time.
7. **Prompt and provider logic lives in `exams/services.py`** — views validate and orchestrate, but do not build prompts or parse provider streams inline.
7. **All state-changing endpoints are CSRF-protected**, except the Stripe webhook which uses signature verification.
8. **No secret values in the repository** — `.env.local` / `.env` are git-ignored; `.env.example` lists names only.
