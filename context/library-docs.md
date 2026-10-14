# Library Docs

This file documents the exact usage patterns for every third-party library in this project. The agent reads this before touching any library — it overrides general knowledge.

---

## Supabase

### Setup / Initialisation

Two clients: one for the browser, one for the server. Never mix them.

```typescript
// lib/supabase/client.ts — browser client (use in Client Components and hooks)
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

```typescript
// lib/supabase/server.ts — server client (use in API routes and Server Components)
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export function createClient() {
  const cookieStore = cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        },
      },
    }
  )
}
```

### Common Patterns

**Querying with user scope (always filter by user_id):**
```typescript
const supabase = createClient()
const { data, error } = await supabase
  .from('sessions')
  .select('*')
  .eq('user_id', userId)
  .order('started_at', { ascending: false })

if (error) throw new Error(`[supabase] query failed: ${error.message}`)
```

**Inserting a row:**
```typescript
const { data, error } = await supabase
  .from('sessions')
  .insert({
    user_id: userId,
    exam_type: config.examType,
    level: config.level,
    exercise_type: config.exerciseType,
    language: 'en',
    duration_seconds: config.durationSeconds,
    status: 'active',
  })
  .select('id')
  .single()

if (error) throw new Error(`[supabase] insert failed: ${error.message}`)
return data.id
```

**Updating a row:**
```typescript
const { error } = await supabase
  .from('sessions')
  .update({ status: 'completed', ended_at: new Date().toISOString() })
  .eq('id', sessionId)
  .eq('user_id', userId)  // always scope updates to the authenticated user

if (error) throw new Error(`[supabase] update failed: ${error.message}`)
```

**Getting the current user in an API route:**
```typescript
const supabase = createClient()
const { data: { user }, error } = await supabase.auth.getUser()
if (error || !user) return Response.json({ error: 'unauthorized' }, { status: 401 })
```

### Rules
- **Always use the server client in API routes.** The browser client is only for hooks and Client Components.
- **Always scope queries to the authenticated user.** Every query on `sessions`, `feedback`, and `profiles` must include `.eq('user_id', userId)`. Never query without a user scope.
- **Never use the service role key in client-side code.** Service role key bypasses row-level security — only use it in server contexts where RLS bypass is explicitly needed (e.g. Stripe webhook updating a profile).
- **Check for errors after every query.** Supabase returns `{ data, error }` — always check `error` before using `data`.
- **`profiles` table is the source of truth for subscription state.** Never cache subscription status in session storage or local state.

---

## Groq

### Setup / Initialisation

```typescript
// lib/groq/client.ts
import Groq from 'groq-sdk'

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY })

export { groq }
```

### Common Patterns

**Streaming examiner response:**
```typescript
// app/api/llm/route.ts
import { groq } from '@/lib/groq/client'

const stream = await groq.chat.completions.create({
  model: 'llama-3.3-70b-versatile',
  messages: [
    { role: 'system', content: systemPrompt },
    ...history,
    { role: 'user', content: userTurn }
  ],
  temperature: 0.7,
  max_tokens: 300,   // examiner responses are short — never let them run long
  stream: true,
})

const encoder = new TextEncoder()
const readable = new ReadableStream({
  async start(controller) {
    for await (const chunk of stream) {
      const text = chunk.choices[0]?.delta?.content ?? ''
      if (text) controller.enqueue(encoder.encode(text))
    }
    controller.close()
  }
})

return new Response(readable, {
  headers: { 'Content-Type': 'text/plain; charset=utf-8' }
})
```

**Non-streaming evaluation call (JSON mode):**
```typescript
const response = await groq.chat.completions.create({
  model: 'llama-3.3-70b-versatile',
  messages: [
    { role: 'system', content: evaluationSystemPrompt },
    { role: 'user', content: evaluationUserPrompt }
  ],
  temperature: 0.3,   // lower temperature for consistent structured output
  max_tokens: 1000,
  response_format: { type: 'json_object' },
  stream: false,
})

const raw = response.choices[0]?.message?.content
if (!raw) throw new Error('[groq] empty evaluation response')

const feedback = JSON.parse(raw) as FeedbackSchema
```

### Rules
- **Model string:** always `'llama-3.3-70b-versatile'`. Never substitute a different model without updating this file.
- **`max_tokens: 300` for examiner turns.** Examiners speak in short, focused sentences. A 300-token ceiling prevents rambling. The evaluation call uses `max_tokens: 1000`.
- **`temperature: 0.7` for examiner, `0.3` for evaluation.** The examiner needs some variation to feel natural; the evaluation needs consistency.
- **Always stream examiner responses.** Never wait for the full response before sending to TTS — latency is a UX killer.
- **Never call Groq from a Client Component or hook.** All Groq calls happen in `app/api/llm/route.ts` and `app/api/session/evaluate/route.ts`.
- **Parse evaluation JSON with a try/catch.** Groq's JSON mode is reliable but not perfect. If parsing fails, log the raw response and return a 500.

---

## Deepgram

### Setup / Initialisation

Deepgram is used in two places:
1. **Server-side:** issue short-lived tokens via `@deepgram/sdk` in the token API route.
2. **Client-side:** open a WebSocket directly to Deepgram using the token (raw WebSocket, not the SDK — the SDK's browser support is limited).

```typescript
// app/api/deepgram/token/route.ts — server-side token issuance
import { createClient } from '@deepgram/sdk'

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!)

export async function GET(request: Request) {
  const { data: tokenData, error } = await deepgram.auth.grantToken()
  if (error) return Response.json({ error: 'token_failed' }, { status: 500 })
  return Response.json({ token: tokenData.access_token })
}
```

### Common Patterns

**Opening the Deepgram WebSocket from the browser:**
```typescript
// hooks/useDeepgramStream.ts
const tokenRes = await fetch('/api/deepgram/token')
const { token } = await tokenRes.json()

const ws = new WebSocket(
  `wss://api.deepgram.com/v1/listen?` +
  `model=nova-2&` +
  `language=en&` +
  `encoding=linear16&` +
  `sample_rate=16000&` +
  `interim_results=true&` +
  `vad_events=true&` +
  `endpointing=300`,
  ['token', token]
)
```

**Handling Deepgram messages:**
```typescript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data as string)

  if (msg.type === 'Results') {
    const transcript = msg.channel.alternatives[0].transcript
    const isFinal = msg.is_final
    const confidence = msg.channel.alternatives[0].confidence
    const words = msg.channel.alternatives[0].words  // word-level confidence scores

    if (transcript.trim()) {
      onTranscript({ transcript, isFinal, confidence, words })
    }
  }

  if (msg.type === 'SpeechStarted') {
    onSpeechStart()
  }

  if (msg.type === 'UtteranceEnd') {
    onUtteranceEnd()
  }
}
```

**Sending audio data:**
```typescript
// Audio must be PCM linear16, 16kHz, mono
// Use AudioWorklet or ScriptProcessor to extract raw PCM from the MediaStream
if (ws.readyState === WebSocket.OPEN) {
  ws.send(pcmBuffer)  // ArrayBuffer of Int16Array PCM data
}
```

**Closing cleanly:**
```typescript
// Always send a close message before closing the WebSocket
ws.send(JSON.stringify({ type: 'CloseStream' }))
ws.close()
```

### Rules
- **Tokens are short-lived (1 hour).** Issue a new token at the start of each session. Never reuse tokens across sessions.
- **Audio format must be PCM linear16 at 16kHz mono.** Deepgram will silently fail or produce garbage with the wrong format. Use `AudioWorklet` with a 16kHz resampler.
- **`endpointing: 300`** — 300ms of silence signals utterance end. Do not change this without testing.
- **Always handle `UtteranceEnd` events**, not just `Results` with `is_final: true`. `UtteranceEnd` is the more reliable signal for pause classification.
- **Close cleanly.** Always send `{ type: 'CloseStream' }` before `ws.close()`. A hard close without this message may cause Deepgram to not flush the final transcript.
- **The Deepgram SDK is only used server-side for token issuance.** The browser connects via raw WebSocket using the token.

---

## OpenAI (TTS)

### Setup / Initialisation

```typescript
// lib/tts/client.ts
import OpenAI from 'openai'

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

export { openai }
```

### Common Patterns

**Streaming TTS audio from an API route:**
```typescript
// app/api/tts/route.ts
import { openai } from '@/lib/tts/client'

export async function POST(request: Request) {
  const { text } = await request.json()

  const response = await openai.audio.speech.create({
    model: 'tts-1',
    voice: 'onyx',     // English examiner voice — professional, neutral, male
    input: text,
    response_format: 'mp3',
  })

  const audioStream = response.body
  return new Response(audioStream, {
    headers: { 'Content-Type': 'audio/mpeg' }
  })
}
```

**Playing streamed audio in the browser:**
```typescript
const res = await fetch('/api/tts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: examinerText })
})

const arrayBuffer = await res.arrayBuffer()
const audioContext = new AudioContext()
const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
const source = audioContext.createBufferSource()

// Wire through AnalyserNode for waveform visualization
const analyser = audioContext.createAnalyser()
analyser.fftSize = 256
source.connect(analyser)
analyser.connect(audioContext.destination)

source.start()
source.onended = () => onExaminerFinished()
```

### Rules
- **Model:** always `'tts-1'` (not `'tts-1-hd'`). The HD model is slower and the quality difference isn't noticeable in a voice conversation.
- **Voice:** `'onyx'` for the English examiner. Professional, clear, neutral male voice. Do not change without updating this file.
- **Response format:** `'mp3'`. Browsers handle it natively, file size is small.
- **Always reuse the `AudioContext`** across a session — create one per session, not one per TTS call. Creating multiple `AudioContext` instances will hit browser limits.
- **Never call OpenAI TTS from the client.** The API key must stay server-side. All TTS calls go through `/api/tts`.
- **Text length limit:** OpenAI TTS accepts up to 4096 characters. Examiner responses are always under 300 tokens (~250 words) so this won't be hit, but validate input length in the route.

---

## Stripe

### Setup / Initialisation

```typescript
// lib/stripe/client.ts
import Stripe from 'stripe'

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-06-20',
  typescript: true,
})
```

### Common Patterns

**Creating a checkout session:**
```typescript
const session = await stripe.checkout.sessions.create({
  customer: stripeCustomerId ?? undefined,
  customer_email: stripeCustomerId ? undefined : userEmail,
  mode: 'subscription',
  payment_method_types: ['card'],
  line_items: [{ price: priceId, quantity: 1 }],
  success_url: `${process.env.NEXT_PUBLIC_APP_URL}/account?upgraded=true`,
  cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/account`,
  metadata: { userId },
})

return Response.json({ url: session.url })
```

**Handling webhook events:**
```typescript
// app/api/stripe/webhook/route.ts
export async function POST(request: Request) {
  const body = await request.text()
  const sig = request.headers.get('stripe-signature')!

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch (err) {
    console.error('[stripe/webhook] signature verification failed:', err)
    return new Response('Webhook error', { status: 400 })
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session
      const userId = session.metadata?.userId
      // update profiles.subscription_status = 'active', store stripe_customer_id
      break
    }
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted': {
      // update profiles.subscription_status accordingly
      break
    }
  }

  return new Response(null, { status: 200 })
}
```

**Creating a billing portal session:**
```typescript
const portalSession = await stripe.billingPortal.sessions.create({
  customer: stripeCustomerId,
  return_url: `${process.env.NEXT_PUBLIC_APP_URL}/account`,
})

return Response.json({ url: portalSession.url })
```

### Rules
- **Webhook signature must always be verified.** Never process a Stripe event without `stripe.webhooks.constructEvent`. Return `400` on failure, not `500`.
- **Raw body is required for webhook verification.** Use `request.text()`, not `request.json()`. Next.js must not parse the body before Stripe sees it.
- **`profiles.subscription_status` is only ever written by the webhook handler.** No other code path updates subscription state.
- **Add `NEXT_PUBLIC_APP_URL` to env vars.** Needed for success/cancel URLs in checkout sessions.
- **Test webhooks locally with `stripe listen --forward-to localhost:3000/api/stripe/webhook`.**

---

## Zod

### Setup / Initialisation

No global setup needed. Import directly where used.

```typescript
import { z } from 'zod'
```

### Common Patterns

**Validating Groq evaluation response:**
```typescript
const FeedbackSchema = z.object({
  overall_level: z.enum(['B1', 'B2', 'C1']),
  overall_verdict: z.enum(['Ready', 'Needs Work', 'Not Ready']),
  fluency_score: z.number().int().min(1).max(10),
  vocabulary_score: z.number().int().min(1).max(10),
  grammar_score: z.number().int().min(1).max(10),
  task_achievement_score: z.number().int().min(1).max(10),
  fluency_notes: z.array(z.string()),
  vocabulary_notes: z.array(z.string()),
  grammar_notes: z.array(z.string()),
  task_achievement_notes: z.array(z.string()),
  pronunciation_flags: z.array(z.object({ word: z.string(), timestamp: z.number() })),
  recommendations: z.array(z.string()).min(1).max(5),
})

export type FeedbackSchema = z.infer<typeof FeedbackSchema>

// Usage
const result = FeedbackSchema.safeParse(JSON.parse(raw))
if (!result.success) {
  console.error('[evaluate] invalid feedback schema:', result.error)
  return Response.json({ error: 'invalid_feedback' }, { status: 500 })
}
```

**Validating API request bodies:**
```typescript
const StartSessionSchema = z.object({
  examType: z.enum(['ielts', 'cambridge_b2']),
  level: z.enum(['b1', 'b2', 'c1']),
  exerciseType: z.enum(['topic_discussion', 'debate', 'random']),
})

const body = await request.json()
const result = StartSessionSchema.safeParse(body)
if (!result.success) {
  return Response.json({ error: 'invalid_request' }, { status: 400 })
}
```

### Rules
- **Use `safeParse`, not `parse`.** `parse` throws; `safeParse` returns a result object. In API routes, always use `safeParse` and return a proper HTTP error on failure.
- **Derive TypeScript types from schemas with `z.infer`.** Never define a type and a schema separately — they'll drift.
- **Schemas for all LLM response parsing.** Groq's JSON mode is mostly reliable but not guaranteed. Always validate.
- **Schemas for all incoming API route bodies.** Never trust `request.json()` without validation.
