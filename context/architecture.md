# Architecture

## Stack

| Layer | Tool | Purpose |
|---|---|---|
| Framework | Next.js 14 (App Router) | Frontend UI + API routes + server actions |
| Language | TypeScript (strict) | Full-stack type safety |
| Styling | Tailwind CSS | Utility-first styling |
| Auth | Supabase Auth | Email/password + Google OAuth, session management |
| Database | PostgreSQL via Supabase | Users, sessions, feedback, subscription state |
| STT + VAD | Deepgram Nova-2 (streaming) | Real-time speech-to-text, voice activity detection, word confidence scores |
| LLM | Groq (llama-3.3-70b) | AI examiner during session + evaluator at session end |
| TTS | OpenAI TTS (streaming) | Examiner voice audio, streamed to browser |
| Payments | Stripe | Subscription management, webhooks, billing portal |
| Deployment | Railway | Long-running Node.js process, persistent WebSocket support |

## Folder Structure

```
/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth route group (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (app)/                    # Authenticated route group
│   │   ├── setup/page.tsx        # Exam configuration screen
│   │   ├── session/page.tsx      # Live session screen
│   │   ├── feedback/
│   │   │   └── [sessionId]/page.tsx
│   │   └── account/page.tsx
│   ├── api/                      # API routes (server-side only)
│   │   ├── session/
│   │   │   ├── start/route.ts    # Initialize session, return config
│   │   │   └── evaluate/route.ts # Post-session evaluation call to Groq
│   │   ├── deepgram/
│   │   │   └── token/route.ts    # Issue short-lived Deepgram token to client
│   │   ├── tts/
│   │   │   └── route.ts          # Proxy OpenAI TTS, stream audio to client
│   │   ├── llm/
│   │   │   └── route.ts          # Examiner turn: send transcript to Groq, return text
│   │   └── stripe/
│   │       └── webhook/route.ts  # Handle subscription events
│   ├── layout.tsx
│   └── page.tsx                  # Landing page
├── components/                   # React components, UI only
│   ├── session/
│   │   ├── Waveform.tsx          # Dual-color live audio waveform
│   │   ├── SessionTimer.tsx      # Countdown timer
│   │   ├── TranscriptPanel.tsx   # Toggleable transcript display
│   │   └── ExaminerLabel.tsx     # Examiner name + flag
│   ├── feedback/
│   │   ├── ScoreCard.tsx
│   │   └── FeedbackReport.tsx
│   ├── setup/
│   │   └── SetupFlow.tsx
│   └── ui/                       # Shared primitives (Button, Card, etc.)
├── lib/                          # Pure logic, no React
│   ├── session/
│   │   ├── state-machine.ts      # Session state machine + transitions
│   │   ├── pause-classifier.ts   # Pause duration → pause type classification
│   │   ├── intervention.ts       # Intervention decision logic
│   │   └── prompt-builder.ts     # Construct LLM system/user prompts from session config
│   ├── deepgram/
│   │   └── client.ts             # Deepgram WebSocket connection manager
│   ├── groq/
│   │   └── client.ts             # Groq API wrapper
│   ├── tts/
│   │   └── client.ts             # OpenAI TTS wrapper
│   ├── supabase/
│   │   ├── client.ts             # Browser Supabase client
│   │   └── server.ts             # Server Supabase client
│   └── stripe/
│       └── client.ts             # Stripe helpers
├── hooks/                        # React hooks
│   ├── useAudioCapture.ts        # Microphone access + Web Audio API
│   ├── useDeepgramStream.ts      # Deepgram WebSocket lifecycle
│   ├── useSessionMachine.ts      # Session state machine hook
│   └── useWaveform.ts            # Audio analysis for waveform visualization
├── types/                        # Shared TypeScript types
│   ├── session.ts
│   ├── feedback.ts
│   └── exam.ts
├── config/                       # Static configuration
│   └── exams.ts                  # Exam types, levels, durations, prompts config
└── middleware.ts                 # Auth protection for (app) routes
```

## System Boundaries

| Layer | Owns | Must Never |
|---|---|---|
| `components/` | UI rendering, user interaction, visual state | Call external APIs directly, contain business logic, manage session state |
| `hooks/` | Browser API lifecycle (mic, WebSocket, audio), React state | Call Groq or Supabase directly, contain exam/session logic |
| `lib/session/` | Session state machine, pause classification, intervention decisions, prompt construction | Import React, touch the DOM, make HTTP requests |
| `app/api/` | External API calls (Groq, Deepgram, OpenAI TTS, Stripe), auth validation | Contain UI logic, be called from other API routes |
| `lib/supabase/` | Database reads/writes, auth token handling | Be imported by components directly (always go through server actions or API routes) |
| `config/exams.ts` | Static exam configuration (durations, levels, prompt templates) | Contain runtime logic or state |

## Data Flow

**Session Start**
1. User submits setup form → `POST /api/session/start`
2. API validates auth + session count (enforce free tier limit)
3. API creates session row in Supabase, returns `sessionId` + exam config
4. Client requests Deepgram token → `GET /api/deepgram/token`
5. API issues short-lived Deepgram token, returns to client
6. Client opens Deepgram WebSocket using token
7. Client calls `POST /api/llm` with examiner intro prompt
8. API calls Groq, returns examiner intro text
9. Client calls `POST /api/tts` with intro text
10. API streams OpenAI TTS audio back to client, client plays it

**User Turn → Examiner Response**
1. Deepgram VAD detects speech start → client sets state to `USER_SPEAKING`
2. Deepgram streams partial transcripts to client in real time
3. Deepgram VAD detects speech end → client records pause start time
4. `pause-classifier.ts` classifies pause type based on duration + level config
5. If end-of-turn: client sends transcript segment to `POST /api/llm`
6. `prompt-builder.ts` constructs examiner prompt from exam config + session history
7. API calls Groq, streams text response back to client
8. Client sends LLM text to `POST /api/tts`, streams audio, plays it
9. State transitions to `EXAMINER_SPEAKING` → then back to `LISTENING`

**Intervention**
1. `pause-classifier.ts` returns `STUCK` or other intervention trigger
2. `intervention.ts` decides intervention type based on session state + level
3. Client calls `POST /api/llm` with intervention-specific prompt
4. Response streamed through TTS and played

**Session End + Evaluation**
1. Timer expires or user ends session → state transitions to `SESSION_END`
2. Client calls `POST /api/session/evaluate` with full transcript + session metadata
3. API constructs evaluation prompt, calls Groq
4. Groq returns structured JSON feedback report
5. API saves feedback to Supabase, returns `feedbackId`
6. Client redirects to `/feedback/[sessionId]`

## Database Schema

```sql
-- Users handled by Supabase Auth (auth.users table)

CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  stripe_customer_id TEXT,
  subscription_status TEXT DEFAULT 'free', -- 'free' | 'active' | 'cancelled'
  subscription_tier TEXT,                  -- 'monthly' | 'annual' | null
  sessions_used INT DEFAULT 0,             -- lifetime free sessions used
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  exam_type TEXT NOT NULL,        -- 'ielts' | 'cambridge_b2'
  level TEXT NOT NULL,            -- 'b1' | 'b2' | 'c1'
  exercise_type TEXT NOT NULL,    -- 'topic_discussion' | 'debate'
  language TEXT NOT NULL DEFAULT 'en',
  duration_seconds INT,
  transcript JSONB,               -- array of { speaker, text, timestamp, confidence }
  status TEXT DEFAULT 'active',   -- 'active' | 'completed' | 'abandoned'
  started_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at TIMESTAMPTZ
);

CREATE TABLE feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id),
  user_id UUID REFERENCES profiles(id),
  overall_level TEXT,             -- 'B1' | 'B2' | 'C1'
  overall_verdict TEXT,           -- 'Ready' | 'Needs Work' | 'Not Ready'
  fluency_score INT,
  vocabulary_score INT,
  grammar_score INT,
  task_achievement_score INT,
  fluency_notes JSONB,
  vocabulary_notes JSONB,
  grammar_notes JSONB,
  task_achievement_notes JSONB,
  pronunciation_flags JSONB,      -- array of { word, timestamp }
  recommendations JSONB,          -- array of strings
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Authentication

- Provider: Supabase Auth
- Methods: email/password, Google OAuth
- Protected routes: all routes under `(app)/` group via `middleware.ts`
- Public routes: `/`, `/login`, `/register`
- Session handling: Supabase session cookie, refreshed automatically
- After login: redirect to `/setup`
- After register: redirect to `/setup` (no email verification for MVP)

## Invariants

1. **Deepgram is never called from the server** — the client connects directly to Deepgram using a short-lived token issued by `/api/deepgram/token`. Audio never passes through the Next.js server.
2. **All Groq calls happen in API routes** — the Groq API key is never exposed to the browser. Components never call Groq directly.
3. **All OpenAI TTS calls are proxied through `/api/tts`** — the OpenAI key is never in the client bundle.
4. **Session state machine lives in `lib/session/state-machine.ts`** — components and hooks read state, they never transition it directly. All transitions go through the state machine.
5. **Intervention decisions are made by `lib/session/intervention.ts`**, not by the LLM. The LLM only generates intervention content once the decision has been made.
6. **Prompt construction happens only in `lib/session/prompt-builder.ts`** — no prompt strings are constructed inline in API routes or components.
7. **Free tier enforcement happens server-side in `/api/session/start`** — the client never determines whether a session is allowed. A user with `sessions_used >= 3` and `subscription_status !== 'active'` is rejected at the API level.
8. **Stripe webhook is the only source of truth for subscription status** — subscription state is never updated from the client. Only `/api/stripe/webhook` writes to `profiles.subscription_status`.
9. **Transcript is append-only during a session** — turns are added, never edited or deleted mid-session.
10. **No component imports from `lib/supabase/server.ts`** — server Supabase client is only used in API routes and server actions.
