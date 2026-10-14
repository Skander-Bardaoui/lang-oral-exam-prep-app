# Build Plan

## Core Principle

Every phase must be fully working before the next begins. Phase 1 establishes the project skeleton and auth. Phase 2 builds the voice pipeline end-to-end with a dumb examiner (no real prompt logic) so the audio plumbing is verified before any exam logic is added. Phase 3 makes the examiner smart — state machine, pause classification, intervention logic, proper prompts. Phase 4 adds evaluation and feedback. Phase 5 adds payments. Phase 6 adds the landing page and prepares for launch. Features are numbered sequentially across all phases.

---

## Phase 1 — Foundation

### 01 Project Scaffold
Initialize the Next.js 14 project with TypeScript strict mode, Tailwind CSS, ESLint, and the folder structure defined in architecture.md. Configure path aliases. Set up environment variable schema with validation.

**UI:** None.

**Logic:**
- `npx create-next-app` with TypeScript + Tailwind
- Configure `tsconfig.json` with strict mode and path aliases (`@/components`, `@/lib`, etc.)
- Create all empty folders from the architecture folder structure
- Add `.env.local` template with all required keys listed

**Exit criteria:** `npm run dev` starts without errors. `npm run build` completes. All folders exist.

---

### 02 Supabase Auth
Wire up Supabase Auth with email/password and Google OAuth. Protect the `(app)` route group via middleware.

**UI:**
- `/login` — email + password form, Google OAuth button, link to register
- `/register` — email + password form, Google OAuth button, link to login
- Both pages use the dark exam-room aesthetic (see ui-tokens.md)

**Logic:**
- Install `@supabase/ssr`
- Create `lib/supabase/client.ts` and `lib/supabase/server.ts`
- Implement `middleware.ts` — redirect unauthenticated users from `(app)` routes to `/login`
- Implement login and register server actions
- Create `profiles` table in Supabase with `sessions_used = 0` and `subscription_status = 'free'`
- Auto-create profile row on first sign-in via Supabase trigger

**Exit criteria:** User can register, log in, and be redirected to `/setup`. Unauthenticated access to `/setup` redirects to `/login`. Profile row is created in Supabase on registration.

---

### 03 Exam Configuration Screen
The setup flow where the user picks exam, level, and exercise type before starting a session.

**UI:**
- `/setup` — step-by-step selection: Language (locked to English for MVP) → Exam Type (IELTS / Cambridge B2 First) → Level (B1 / B2 / C1) → Exercise Type (Topic Discussion / Debate / Random)
- Each step is a full-screen card with large tap targets
- Selected state clearly indicated
- "Start session" button enabled only when all selections are made
- Selections stored in component state, not URL

**Logic:**
- Create `config/exams.ts` with all exam configs (types, levels, durations in seconds, display names)
- On "Start session": call `POST /api/session/start`
- `/api/session/start`: validate auth, check free tier limit (`sessions_used < 3` or `subscription_status === 'active'`), create session row in Supabase, return `sessionId` + full exam config
- If free tier exceeded: return 403 with `{ reason: 'limit_reached' }` — client redirects to `/account`

**Exit criteria:** User can complete all steps and click Start. API creates a session row. Free tier limit blocks a 4th session for unsubscribed users and returns the correct error.

---

## Phase 2 — Voice Pipeline (Dumb Examiner)

### 04 Microphone Capture + Deepgram Connection
Get audio from the browser microphone into Deepgram's streaming STT. No session logic yet — just verify the pipeline works.

**UI:**
- `/session` (stub) — a single "Connect" button and a raw transcript output area (dev only, will be replaced in Phase 3)
- Show connection status: Idle / Connecting / Connected / Error

**Logic:**
- Create `hooks/useAudioCapture.ts` — request mic permission, create MediaStream, expose audio data
- Create `hooks/useDeepgramStream.ts` — fetch token from `/api/deepgram/token`, open Deepgram WebSocket, pipe audio, emit transcript events
- Create `app/api/deepgram/token/route.ts` — authenticate user, issue short-lived Deepgram token using `DEEPGRAM_API_KEY`
- Deepgram config: Nova-2 model, `interim_results: true`, `vad_events: true`, `endpointing: 300`, `language: en`
- Log raw transcript events to console

**Exit criteria:** User clicks Connect, browser requests mic permission, Deepgram WebSocket connects, speaking produces live transcript output in the dev UI.

---

### 05 LLM Examiner Turn (Stub)
Send a transcript segment to Groq and get a text response back. No real prompting yet — just verify the Groq integration.

**UI:** Add a "Send to LLM" button in the dev session stub that sends the current transcript.

**Logic:**
- Create `lib/groq/client.ts` — Groq SDK wrapper, `getExaminerResponse(messages)` function
- Create `app/api/llm/route.ts` — receive `{ transcript, history }`, call Groq with a placeholder system prompt ("You are an English language examiner. Respond briefly."), return text
- Streaming response from Groq back to client

**Exit criteria:** Clicking "Send to LLM" with a transcript segment returns a Groq text response in under 3 seconds.

---

### 06 TTS Playback
Convert LLM text response to audio and play it in the browser.

**UI:** Dev session stub shows "Playing..." state while audio is playing.

**Logic:**
- Create `lib/tts/client.ts` — fetch wrapper for `/api/tts`
- Create `app/api/tts/route.ts` — receive `{ text, voice }`, call OpenAI TTS with `tts-1` model and `onyx` voice (English), stream audio back as `audio/mpeg`
- Client receives audio stream, creates `AudioContext`, plays via `AudioBufferSourceNode`
- Create `hooks/useWaveform.ts` — analyzes playing audio via `AnalyserNode`, exposes frequency data for visualization

**Exit criteria:** LLM response text is converted to audio and plays in the browser. Audio waveform data is available from the hook.

---

### 07 Waveform Visualization
The signature UI element — dual-color waveform showing user voice and examiner voice.

**UI:**
- `components/session/Waveform.tsx` — canvas-based waveform
- User voice: muted slate blue bars
- Examiner voice: white/light bars
- Idle state: flat line with subtle pulse
- Smooth animation at 60fps

**Logic:**
- `useWaveform.ts` exposes `userFrequencyData` and `examinerFrequencyData` as `Uint8Array`
- Waveform component reads data via `requestAnimationFrame` loop
- No state management needed — purely visual

**Exit criteria:** Waveform animates in response to user microphone input. Waveform animates differently when examiner audio is playing. Both are visually distinct.

---

## Phase 3 — Smart Examiner

### 08 Session State Machine
Implement the full session state machine that drives all session logic.

**UI:** None — this is pure logic.

**Logic:**
- Create `lib/session/state-machine.ts` — implement all states: `IDLE`, `SESSION_START`, `EXAMINER_INTRO`, `LISTENING`, `USER_SPEAKING`, `PROCESSING`, `EXAMINER_SPEAKING`, `INTERVENTION`, `SESSION_END`, `EVALUATION`, `FEEDBACK_DISPLAY`
- Export `useSessionMachine` hook from `hooks/useSessionMachine.ts` that wraps the state machine for React consumption
- State machine accepts events: `START`, `VAD_SPEECH_START`, `VAD_SPEECH_END`, `TURN_END`, `LLM_DONE`, `TTS_DONE`, `TIMER_TICK`, `USER_END`, `TIMER_EXPIRED`
- State machine is a pure function — no side effects, no async, no API calls

**Exit criteria:** All state transitions can be exercised in a unit test. State machine never enters an invalid state.

---

### 09 Pause Classification + Intervention Logic
Classify pause durations into action triggers and decide what intervention to apply.

**UI:** None.

**Logic:**
- Create `lib/session/pause-classifier.ts` — input: `pauseMs`, `level`, output: `'mid_utterance' | 'end_of_turn' | 'hesitation' | 'stuck'`
- Thresholds by level: B1 (more forgiving), B2 (standard), C1 (tighter)
- Create `lib/session/intervention.ts` — input: session state + history, output: `InterventionType` enum (`NONE`, `SOFT_PROMPT`, `REPHRASE`, `STEER_BACK`, `WRAP_UP`)
- Intervention decisions based on: pause type, turn count, time remaining, topic coverage

**Exit criteria:** `pause-classifier.ts` returns correct classification for all threshold cases at all three levels. `intervention.ts` returns correct intervention type for each scenario.

---

### 10 Prompt Builder + Exam Personas
Build the dynamic prompt construction system that makes the examiner behave correctly for each exam type, level, and exercise.

**UI:** None.

**Logic:**
- Create `lib/session/prompt-builder.ts`
- `buildSystemPrompt(config)` — constructs examiner system prompt from exam type, level, exercise type, language. Includes: examiner persona, exam format instructions, scoring awareness, level-appropriate language expectations, intervention instructions
- `buildTurnPrompt(transcript, history, interventionType)` — constructs the user message for each examiner turn
- `buildEvaluationPrompt(transcript, config)` — constructs the evaluation prompt for post-session feedback
- Add IELTS examiner persona to `config/exams.ts` with real format details (3 parts, timing, topic types)
- Add Cambridge B2 First examiner persona with real format details

**Exit criteria:** `buildSystemPrompt` produces a prompt that, when tested manually with Groq, results in the examiner staying in character and responding appropriately for the selected exam format.

---

### 11 Full Session Screen
Wire all pieces together into the real `/session` UI. Replace the dev stub.

**UI:**
- `components/session/ExaminerLabel.tsx` — examiner name + UK flag (IELTS) or Cambridge shield, top left
- `components/session/SessionTimer.tsx` — countdown from exam duration, top right
- `components/session/Waveform.tsx` — centered, full width, the main visual element
- `components/session/TranscriptPanel.tsx` — hidden by default, toggle button at bottom, scrolling panel slides up
- Status indicator: subtle text below waveform — "Listening...", "Examiner speaking...", "Processing..."
- "End session early" button — bottom right, requires confirmation

**Logic:**
- `session/page.tsx` reads `sessionId` from URL params, fetches session config from Supabase
- Orchestrates all hooks: `useAudioCapture` → `useDeepgramStream` → `useSessionMachine` → LLM call → TTS call → `useWaveform`
- Session timer counts down, fires `TIMER_EXPIRED` event at zero
- Transcript panel displays the accumulated session transcript

**Exit criteria:** A complete simulated session runs from examiner intro through multiple user turns to session end without manual intervention. The examiner stays in character. The timer counts down correctly. The waveform responds to both voices.

---

## Phase 4 — Evaluation & Feedback

### 12 Post-Session Evaluation
At session end, send the full transcript to Groq for structured evaluation.

**UI:** Loading state on `/session` after session ends — "Generating your feedback..." with a subtle animation.

**Logic:**
- Create `app/api/session/evaluate/route.ts`
- Receives `sessionId` — fetches full transcript from Supabase
- Calls `buildEvaluationPrompt` from prompt-builder
- Calls Groq with JSON mode — response must match `FeedbackSchema` type
- Saves structured feedback to `feedback` table in Supabase
- Returns `feedbackId`
- Update session row `status = 'completed'`, set `ended_at`

**Exit criteria:** After a completed session, the evaluate endpoint returns a valid structured feedback object with all 5 dimensions populated with real content from the transcript.

---

### 13 Feedback Report Screen
Display the structured feedback report.

**UI:**
- `/feedback/[sessionId]` — full feedback report
- Overall score badge at top: level + verdict ("B2 — Needs Work")
- Four score cards: Fluency, Vocabulary, Grammar, Task Achievement — each with score/10, bullet notes, specific transcript examples
- Pronunciation flags section: list of flagged words
- Recommended focus areas: numbered list
- Two CTAs: "Try again" (same config) and "New session" (back to setup)
- Session metadata footer: exam type, level, date, duration

**Logic:**
- Server component — fetch feedback from Supabase by `sessionId`
- Validate that `feedback.user_id` matches authenticated user
- `components/feedback/ScoreCard.tsx` — reusable score display component
- `components/feedback/FeedbackReport.tsx` — full report layout

**Exit criteria:** Feedback page displays all dimensions with real content. Transcript examples are quoted correctly. "Try again" pre-fills the setup with the same configuration.

---

## Phase 5 — Payments

### 14 Stripe Subscription
Wire up Stripe for monthly and annual subscriptions.

**UI:**
- `/account` — shows current plan (Free / Monthly / Annual), sessions used (for free tier), "Upgrade" button, "Manage billing" button (Stripe portal)
- Paywall modal — triggered when free tier limit is reached on `/setup`. Shows tier options, price, CTA to subscribe.

**Logic:**
- Create `lib/stripe/client.ts` — Stripe SDK wrapper
- `POST /api/stripe/create-checkout` — create Stripe Checkout session for selected tier, redirect to Stripe
- `POST /api/stripe/webhook` — handle `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted` — update `profiles.subscription_status` and `profiles.subscription_tier`
- `POST /api/stripe/portal` — create Stripe Customer Portal session for billing management
- Add `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_MONTHLY_PRICE_ID`, `STRIPE_ANNUAL_PRICE_ID` to env

**Exit criteria:** User can subscribe via Stripe Checkout. Webhook updates subscription status in Supabase. Subscribed user can complete a 4th session. Free user is blocked and shown the paywall. Stripe portal allows subscription cancellation.

---

## Phase 6 — Launch Prep

### 15 Landing Page
The public homepage at `/`.

**UI:**
- Hero: headline + one-line description + "Start practicing" CTA
- How it works: 3 steps (Select your exam → Speak with your AI examiner → Get feedback)
- Exam types supported: IELTS, Cambridge B2 First — with brief description of the oral component
- Pricing section: Free vs Monthly vs Annual tiers
- Footer: links to login, register, privacy policy

**Logic:**
- Static page, no data fetching
- "Start practicing" CTA → `/register` if not logged in, `/setup` if logged in

**Exit criteria:** Landing page renders correctly on mobile and desktop. All CTAs route correctly. Pricing is accurate.

---

### 16 Polish + Error States
Cover all error and empty states before launch.

**UI:**
- Mic permission denied state on `/session` — clear explanation + instructions
- Deepgram connection failure state — retry button
- LLM/TTS error during session — graceful degradation message
- Network offline detection
- 404 page
- All loading states have appropriate skeletons or spinners

**Logic:**
- Add error boundaries around session components
- Add retry logic to Deepgram connection (3 attempts with backoff)
- Log errors to console (structured) — no external error tracking for MVP

**Exit criteria:** All error states render correctly. A Deepgram connection failure does not crash the session page. Mic denial shows a helpful message.
