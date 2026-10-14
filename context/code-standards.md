# Code Standards

## Engineering Mindset

1. **Write for the next session, not just this one.** The agent reading this tomorrow has no memory of today. Code must be self-evident.
2. **Small, focused units.** Every function does one thing. Every file owns one concern.
3. **Explicit over implicit.** No magic, no clever tricks. If it isn't obvious, it needs a comment.
4. **Fail loudly in development, gracefully in production.** Throw hard errors during dev. Catch and handle them for the user in prod.
5. **Don't build what isn't in the build plan.** If a feature isn't in `build-plan.md`, it doesn't exist yet.
6. **Audio and WebSocket state is fragile.** Every connection, stream, and audio context must be explicitly opened and closed. No dangling resources.

---

## Language — TypeScript

- **Strict mode is non-negotiable.** `tsconfig.json` has `"strict": true`. Never disable it.
- **No `any`.** If the type is unknown, use `unknown` and narrow it. If a third-party library forces `any`, wrap it at the boundary and re-type the result.
- **Explicit return types on all functions** except trivial one-liners where the return is obvious.
- **Use `type` for everything.** Reserve `interface` only when declaration merging is explicitly needed (it won't be in this project).
- **Discriminated unions for state.** Session state, pause classification output, intervention types — all modeled as discriminated unions, not string literals with no type.
- **Enums are banned.** Use `const` objects with `as const` and derive the type: `type PauseType = typeof PAUSE_TYPES[keyof typeof PAUSE_TYPES]`.
- **No non-null assertions (`!`).** Narrow properly or handle the null case.

```typescript
// Correct
type PauseClassification = 'mid_utterance' | 'end_of_turn' | 'hesitation' | 'stuck'

type SessionState =
  | { status: 'IDLE' }
  | { status: 'LISTENING'; sessionId: string }
  | { status: 'USER_SPEAKING'; sessionId: string; partialTranscript: string }
  | { status: 'PROCESSING'; sessionId: string; transcript: string }
  | { status: 'EXAMINER_SPEAKING'; sessionId: string }
  | { status: 'SESSION_END'; sessionId: string }

// Wrong
enum SessionStatus { IDLE, LISTENING }   // banned
const state: any = {}                    // banned
const text = response!.text              // banned
```

---

## Framework — Next.js 14 App Router

- **Server Components by default.** Only add `'use client'` when the component needs browser APIs, event handlers, or React hooks. If you're unsure, try Server Component first.
- **Data fetching lives in Server Components and API routes.** Client components never fetch data directly — they receive it as props or call API routes via fetch.
- **Server Actions for mutations.** Form submissions and user-triggered data writes use Server Actions, not client-side fetch to an API route.
- **API routes for external service calls.** Groq, OpenAI TTS, Deepgram token issuance, Stripe — all called from `app/api/` routes, never from the client.
- **Route groups enforce auth boundaries.** `(auth)` is public. `(app)` is protected. `middleware.ts` is the gatekeeper — no auth checks inside individual pages.
- **No `useEffect` for data fetching.** Data needed at render time belongs in Server Components. `useEffect` is for side effects: setting up WebSocket connections, starting audio capture, registering event listeners.

```typescript
// Correct — Server Component fetches data
// app/(app)/feedback/[sessionId]/page.tsx
export default async function FeedbackPage({ params }: { params: { sessionId: string } }) {
  const supabase = createServerClient()
  const feedback = await getFeedback(supabase, params.sessionId)
  return <FeedbackReport feedback={feedback} />
}

// Wrong — client fetching data on mount
'use client'
export default function FeedbackPage() {
  const [feedback, setFeedback] = useState(null)
  useEffect(() => { fetch('/api/feedback').then(...) }, [])  // wrong
}
```

- **Streaming responses from API routes.** TTS and LLM routes use `ReadableStream` with `TransformStream`. Never buffer a full audio or LLM response before sending.
- **`next/navigation` for redirects inside Server Components.** `useRouter` only in Client Components.

---

## File and Folder Naming

- **Folders:** `kebab-case` — `state-machine.ts`, `pause-classifier.ts`, `prompt-builder.ts`
- **React components:** `PascalCase` files — `Waveform.tsx`, `SessionTimer.tsx`, `ScoreCard.tsx`
- **Hooks:** `camelCase` prefixed with `use` — `useAudioCapture.ts`, `useSessionMachine.ts`
- **Utilities and lib files:** `camelCase` — `client.ts`, `server.ts`
- **Route files:** always `page.tsx`, `layout.tsx`, `route.ts` — Next.js conventions, never deviate
- **Type files:** `camelCase` — `session.ts`, `feedback.ts`, `exam.ts`
- **Config files:** `camelCase` — `exams.ts`

---

## Component / Module Structure

All files follow this order:

```typescript
// 1. External imports (npm packages)
import { useState, useCallback } from 'react'
import { createClient } from '@supabase/ssr'

// 2. Internal imports (project files, path aliases)
import { useSessionMachine } from '@/hooks/useSessionMachine'
import type { SessionConfig } from '@/types/session'

// 3. Types local to this file
type WaveformProps = {
  userFrequencyData: Uint8Array | null
  examinerFrequencyData: Uint8Array | null
}

// 4. Constants local to this file
const CANVAS_HEIGHT = 80
const BAR_COUNT = 48

// 5. The component or function (one per file)
export default function Waveform({ userFrequencyData, examinerFrequencyData }: WaveformProps) {
  // ...
}

// 6. Named exports if needed (helper functions, sub-components)
export function normalizeFrequencyData(data: Uint8Array): number[] {
  // ...
}
```

- **One component per file.** Never export two components from the same file.
- **Props types are always `type`, never inlined.** Define them above the component, not inline in the function signature.
- **Default export for pages and components. Named exports for utilities and hooks.**

---

## Error Handling

**Pattern: explicit error types returned from API routes, not thrown.**

API routes return a consistent shape:

```typescript
// Success
return Response.json({ data: result }, { status: 200 })

// Expected error (user-facing)
return Response.json({ error: 'limit_reached', message: 'Free session limit reached' }, { status: 403 })

// Unexpected error (log it, return generic message)
console.error('[api/llm] Groq call failed:', error)
return Response.json({ error: 'internal_error', message: 'Something went wrong' }, { status: 500 })
```

**Client-side error handling in hooks:**

```typescript
type HookResult<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; message: string }
```

**Rules:**
- Never let an error propagate silently. Every `catch` block either logs or surfaces the error.
- Log errors with a prefix identifying the source: `[api/tts]`, `[useDeepgramStream]`, `[state-machine]`.
- Audio and WebSocket errors must clean up their resources before surfacing — no dangling `AudioContext` or open WebSocket on error.
- The session must never crash the page. Errors during a session surface as a status message in the UI; the session ends gracefully.
- Validation errors from Stripe webhooks are logged and return `400` — never `500`.

---

## Environment Variables

All environment variables are validated at startup. If a required variable is missing, the app must fail loudly in development.

```typescript
// lib/env.ts — validate all variables at module load
function requireEnv(key: string): string {
  const value = process.env[key]
  if (!value) throw new Error(`Missing required environment variable: ${key}`)
  return value
}
```

| Variable | Used In | Public? |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `lib/supabase/client.ts` | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `lib/supabase/client.ts` | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | `lib/supabase/server.ts` (API routes only) | No |
| `DEEPGRAM_API_KEY` | `app/api/deepgram/token/route.ts` | No |
| `GROQ_API_KEY` | `lib/groq/client.ts` | No |
| `OPENAI_API_KEY` | `lib/tts/client.ts` | No |
| `STRIPE_SECRET_KEY` | `lib/stripe/client.ts` | No |
| `STRIPE_WEBHOOK_SECRET` | `app/api/stripe/webhook/route.ts` | No |
| `STRIPE_MONTHLY_PRICE_ID` | `app/api/stripe/create-checkout/route.ts` | No |
| `STRIPE_ANNUAL_PRICE_ID` | `app/api/stripe/create-checkout/route.ts` | No |

**Rules:**
- `NEXT_PUBLIC_` prefix only for variables that are safe to expose in the browser bundle. Currently only the Supabase URL and anon key.
- Never access `process.env` directly in components. Go through `lib/env.ts`.
- Never commit `.env.local`. The `.env.local.example` file lists all keys with empty values.

---

## Dependencies

The approved dependency list. The agent must not install packages not on this list without noting the addition.

**Production:**
- `next` — framework
- `react`, `react-dom` — UI
- `typescript` — language
- `tailwindcss` — styling
- `@supabase/ssr` — Supabase auth + DB (server-side)
- `@supabase/supabase-js` — Supabase client (browser)
- `groq-sdk` — Groq LLM API
- `openai` — OpenAI TTS API
- `@deepgram/sdk` — Deepgram STT token issuance
- `stripe` — Stripe server-side SDK
- `@stripe/stripe-js` — Stripe client-side (redirect to checkout)
- `zod` — runtime validation for API responses and env vars

**Development:**
- `eslint`, `eslint-config-next` — linting
- `@types/node`, `@types/react`, `@types/react-dom` — types

**Rules:**
- No UI component libraries (no shadcn, no radix, no MUI). Components are built from scratch using Tailwind.
- No state management libraries (no Redux, no Zustand, no Jotai). React state + context is sufficient.
- No date libraries for MVP (no date-fns, no dayjs). Native `Date` and `Intl` are sufficient.
- No HTTP client libraries (no axios). Native `fetch` only.
