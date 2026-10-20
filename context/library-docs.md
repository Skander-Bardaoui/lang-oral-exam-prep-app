# Library Docs

This file documents the exact usage patterns for every third-party library in this project. The agent reads this before touching any library — it overrides general knowledge.

The stack is **Django 5.2 + `requests` + python-dotenv + Stripe**, with vanilla ES modules in the browser (no frontend framework, no bundler). All provider calls happen server-side in `exams/services.py`; secrets never reach the browser.

---

## Django

### Setup / Initialisation

Project package: `oral_exam/`. Apps: `accounts`, `exams`.

```python
# oral_exam/settings.py
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env.local')
load_dotenv(BASE_DIR / '.env')  # does not override already-set values

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'exams',
]

TEMPLATES = [{'DIRS': [BASE_DIR / 'templates'], ...}]
STATICFILES_DIRS = [BASE_DIR / 'static']
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/setup/'
LOGOUT_REDIRECT_URL = '/login/'
```

### Common Patterns

**Protected page:**
```python
from django.contrib.auth.decorators import login_required

@login_required
def setup(request):
    ...
```

**Protected JSON endpoint (never redirect to HTML):**
```python
# exams/views.py
def api_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'unauthorized'}, status=401)
        return view(request, *args, **kwargs)
    return wrapped
```

**Reading a JSON body:**
```python
def _parse_json(request):
    try:
        return json.loads(request.body or '{}')
    except (TypeError, ValueError):
        return None
```

**Streaming a provider response:**
```python
from django.http import StreamingHttpResponse

return StreamingHttpResponse(
    services.stream_examiner_reply(transcript, history),
    content_type='text/plain; charset=utf-8',
)
```

**CSRF for JS fetches:** `templates/base.html` exposes `<meta name="csrf-token" content="{{ csrf_token }}">`, and `static/js/csrf.js` adds `X-CSRFToken` to every non-GET request.

**Stripe webhook:** `@csrf_exempt` + `@require_POST` (Stripe cannot send a CSRF token). Signature fails → `400`, never `500`.

### Rules
- **Authentication is Django's built-in `User`.** Email is stored as `username` (normalized lowercase). Do not add a custom user model.
- **Always scope object lookups to `request.user`** — `get_object_or_404(ExamSession, pk=..., user=request.user)`.
- **Use `JsonResponse`, not `Response.json`.** Errors use `{'error': 'code', 'message': 'human text'}`.
- **Validate at the boundary.** `_parse_json` + explicit field checks before touching models or providers.
- **Never access provider keys outside `settings`.** They are loaded from `.env.local`; never print or return them.
- **Templates only.** No JSON API for page rendering. Page data is passed as template context.
- **The session must never crash the page.** Provider failures become user-facing status messages; resources are torn down first.

---

## PostgreSQL / psycopg

### Setup

`psycopg[binary]` 3.2 is installed; Django uses `django.db.backends.postgresql` automatically. Configuration lives in `settings._database_config()`:

```python
# Priority 1: a single connection URL
DATABASE_URL=postgres://user:password@127.0.0.1:5432/oral_exam?sslmode=require

# Priority 2: individual variables (used when DATABASE_URL is blank)
DB_NAME=oral_exam
DB_USER=postgres
DB_PASSWORD=...
DB_HOST=127.0.0.1
DB_PORT=5432
```

### Common commands

```bash
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py shell -c "from django.db import connection; print(connection.vendor)"
.venv/Scripts/python.exe manage.py test
```

### Rules
- **PostgreSQL is required; there is no SQLite fallback.** If the server is unreachable, fail loudly at startup/request time.
- **`DATABASE_URL` wins** over the `DB_*` variables. Hosted providers should use `?sslmode=require`.
- **Never print or commit `DB_PASSWORD` or `DATABASE_URL`.**
- **Tests create and destroy `test_oral_exam`** on the same server; the configured role needs `CREATEDB`.
- **Use `transaction.atomic()` + `select_for_update()`** for counter updates (the free-tier limit). Do not read-modify-write outside a transaction.
- **Run migrations after every model change:** `makemigrations` then `migrate`. Never edit applied migrations.

---

## `requests` (ElevenLabs, Groq, OpenAI TTS)

All HTTP calls to providers live in `exams/services.py`. Use `requests.post` with explicit timeouts and `raise`-free error handling — convert every failure into `ProviderError`.

### Setup

```python
import requests
from django.conf import settings

class ProviderError(Exception):
    """Raised when an external provider rejects or fails a request."""
```

### Common Patterns

**Short-lived token issuance (ElevenLabs):**
```python
response = requests.post(
    'https://api.elevenlabs.io/v1/single-use-token/realtime_scribe',
    headers={'xi-api-key': settings.ELEVENLABS_API_KEY},
    timeout=20,
)
if response.status_code != 200:
    raise ProviderError('Could not start a transcription session')
token = response.json()['token']  # `token` key, not `token` wrapper object
```

**Streaming SSE (Groq):**
```python
response = requests.post(
    'https://api.groq.com/openai/v1/chat/completions',
    headers={'Authorization': f'Bearer {settings.GROQ_API_KEY}'},
    json=payload,
    stream=True,
    timeout=60,
)

def generate():
    try:
        for raw in response.iter_lines():
            line = raw.decode('utf-8') if isinstance(raw, bytes) else raw
            if not line.startswith('data:'):
                continue
            data = line[5:].strip()
            if not data or data == '[DONE]':
                continue
            chunk = json.loads(data)['choices'][0].get('delta', {}).get('content')
            if chunk:
                yield chunk
    finally:
        response.close()
return generate()
```

**Streaming binary (OpenAI TTS):**
```python
for chunk in response.iter_content(chunk_size=8192):
    if chunk:
        yield chunk
```

### Rules
- **Every request has a timeout.** Token 20s, LLM stream 60s, TTS 60s, evaluation 90s.
- **Close the response** in a `finally` block when wrapping it in a generator.
- **Status errors:** log `[provider]` + status + first 500 chars; raise a generic `ProviderError` with a user-safe message.
- **`requests.RequestException`** (network/DNS/timeout) is always caught and converted to `ProviderError`.
- **Never buffer a full audio or LLM stream before returning it.** Stream with `StreamingHttpResponse`.

---

## Groq

### Endpoint and model

`POST https://api.groq.com/openai/v1/chat/completions`

Model: **`qwen/qwen3.8-27b`** (from `settings.GROQ_MODEL`). The originally planned `llama-3.3-70b-versatile` is **not available** on this account (Groq returns `404 model_not_found`). Never hardcode another model; change `GROQ_MODEL` if the account changes.

### Examiner turn (streaming)

```python
payload = {
    'model': settings.GROQ_MODEL,
    'temperature': 0.7,
    'max_tokens': 300,
    'stream': True,
    'messages': [
        {'role': 'system', 'content': PLACEHOLDER_SYSTEM_PROMPT},
        *history,
        {'role': 'user', 'content': transcript},
    ],
}
```

`PLACEHOLDER_SYSTEM_PROMPT` is intentionally a stub until Feature 10 (prompt builder + personas).

### Evaluation (non-streaming JSON)

```python
payload = {
    'model': settings.GROQ_MODEL,
    'temperature': 0.3,
    'max_tokens': 2000,
    'response_format': {'type': 'json_object'},
    'messages': [
        {'role': 'system', 'content': EVALUATION_SYSTEM_PROMPT},
        {'role': 'user', 'content': prompt},
    ],
}
```

If the model rejects `response_format` with `400`, retry once **without** it and parse the JSON object from the text (first `{` → last `}`).

### Normalizing the result

`_normalize_feedback` clamps scores to `0–9`, validates `overall_level` (`B1|B2|C1`), validates the verdict (`Ready|Needs Work|Not Ready`), coerces notes/recommendations to string lists, and truncates pronunciation flags to 50.

### Rules
- **Examiner turn: temperature 0.7, `max_tokens` 300, always streamed.**
- **Evaluation: temperature 0.3, `max_tokens` 2000, never streamed.**
- **Groq is called only from `exams/services.py`, which is only reached from Django views.** No provider key or call ever reaches the client.
- **Treat model output as untrusted.** Parse defensively; never assume keys exist.

---

## ElevenLabs Scribe v2 Realtime (STT)

Two halves:

1. **Server** (`exams/services.py::create_realtime_token`) issues a single-use token via REST.
2. **Browser** (`static/js/transcription.js`) opens a raw WebSocket to ElevenLabs using that token.

### Server — token route

```python
# exams/views.py
@api_login_required
def stt_token(request):
    try:
        token = services.create_realtime_token()
    except services.ProviderError as exc:
        return _error(str(exc), status=502, code='provider_error')
    return JsonResponse({'token': token})
```

### Client — WebSocket

```js
const res = await fetch('/api/stt/token/', { credentials: 'same-origin' })
const { token } = await res.json()

const params = new URLSearchParams({
  model_id: 'scribe_v2_realtime',
  token,
  audio_format: sampleRateToFormat(actualRate), // pcm_16000 etc.
  commit_strategy: 'vad',
  language_code: sessionLanguage, // 'en' or 'fr', from the session config
})
const ws = new WebSocket(`wss://api.elevenlabs.io/v1/speech-to-text/realtime?${params}`)
```

Send one message per audio chunk:

```js
ws.send(JSON.stringify({
  message_type: 'input_audio_chunk',
  audio_base_64: base64Pcm,
  commit: false,
  sample_rate: actualRate,
}))
```

Incoming messages handled: `partial_transcript`, `committed_transcript`, `committed_transcript_with_timestamps`, `error`, `auth_error`. Anything else is ignored.

### Rules
- **Tokens are single-use and expire after 15 minutes.** Issue one per session start; never cache or reuse.
- **The API key never reaches the browser.** Only the single-use token does.
- **`audio_format` must match the real sample rate.** `AudioCapture` requests 16000Hz; the actual rate is mapped to `pcm_8000/16000/22050/24000/44100/48000`.
- **`commit_strategy: 'vad'`** — ElevenLabs segments speech by silence; the client never sends `commit: true`.
- **Close the socket in `stop()` and on `pagehide`.** Reject with a clear error on `auth_error` so the UI can recover.
- **Word confidence** (for pronunciation flags) is available in `committed_transcript_with_timestamps` → `words[].logprob`, but only when timestamps are enabled.

---

## OpenAI TTS

`POST https://api.openai.com/v1/audio/speech` — model `tts-1`, voice `onyx`, format `mp3`.

```python
response = requests.post(
    'https://api.openai.com/v1/audio/speech',
    headers={'Authorization': f'Bearer {settings.OPENAI_API_KEY}'},
    json={'model': 'tts-1', 'voice': 'onyx', 'input': text, 'response_format': 'mp3'},
    stream=True,
    timeout=60,
)
```

The Django view streams bytes as `audio/mpeg`; the browser fetches the full response, decodes it with `AudioContext.decodeAudioData`, and plays it through an `AnalyserNode`.

### Rules
- **Model `tts-1` (not `tts-1-hd`); voice `onyx`.** Do not change without updating this file.
- **Validate length server-side** (< 4096 chars) and reject empty text.
- **429 / insufficient quota:** the API currently has no credits. `services.open_tts_stream` raises `ProviderError('OpenAI TTS has no remaining credits')`; the view returns `502`.
- **Browser fallback is required:** `static/js/tts.js` catches the failure and speaks the same text with `window.speechSynthesis` so the examiner turn still works. Keep this fallback.
- **One `AudioContext` per session.** Reuse it for every utterance; creating one per call hits browser limits.
- **Always stop/cancel the previous source** before playing a new one.

---

## Stripe

Uses the official `stripe` Python SDK (v16).

### Setup

```python
# exams/views.py — inside the webhook handler
stripe.api_key = settings.STRIPE_SECRET_KEY
```

### Webhook

```python
@csrf_exempt
@require_POST
def stripe_webhook(request):
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.headers.get('Stripe-Signature', ''),
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return _error('Invalid webhook payload', status=400, code='invalid_signature')
```

Handled events:

- `checkout.session.completed` → `subscription_status = 'active'`, store `stripe_customer_id`, set tier from `metadata.tier`.
- `customer.subscription.updated` / `.deleted` → update status based on `obj.status` (`active`/`trialing` → active, `canceled` → cancelled) and tier from the price ID.

### Rules
- **Verify the signature on every event.** Use `request.body`, never `request.json()`.
- **`stripe.SignatureVerificationError`** (top-level) — `stripe.error` is not importable in v16.
- **Invalid signature → 400.** Unconfigured webhook → 503. Never 500.
- **`profiles.subscription_status` is written only by the webhook.** No other code path changes subscription state.
- **Local testing:** `stripe listen --forward-to localhost:8000/api/stripe/webhook/`.
- **Missing price/webhook IDs** keep checkout disabled until `STRIPE_MONTHLY_PRICE_ID`, `STRIPE_ANNUAL_PRICE_ID`, and `STRIPE_WEBHOOK_SECRET` are set.

---

## python-dotenv

```python
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env.local')
load_dotenv(BASE_DIR / '.env')
```

### Rules
- `.env.local` wins over `.env` (first loader sets values; later loads do not override).
- `.env.local` is git-ignored and contains live secrets. Never print, log, or commit its contents.
- Keep `.env.example` as the key list with empty values.
- Provider keys are consumed only through `django.conf.settings`.

---

## Browser APIs (no libraries)

### Microphone — `static/js/audio-capture.js`

- `navigator.mediaDevices.getUserMedia({ audio: {...} })`
- `new AudioContext({ sampleRate: 16000 })`, then `audioWorklet.addModule(workletUrl)`
- Worklet `public/worklets/pcm-processor.js` posts 1600-sample Float32 frames
- Main thread converts Float32 → Int16 → base64
- `stop()` disconnects nodes, stops tracks, closes the context

### TTS playback — `static/js/tts.js`

- `fetch('/api/tts/')` → `arrayBuffer()` → `AudioContext.decodeAudioData`
- `createBufferSource` → `AnalyserNode` → destination
- Fallback: `speechSynthesis.speak(new SpeechSynthesisUtterance(text))`
- `stop()` cancels both the buffer source and browser speech

### Fetch + CSRF — `static/js/csrf.js`

```js
export function csrfHeaders() {
  return { 'X-CSRFToken': getCsrfToken(), 'Content-Type': 'application/json' }
}
```

All state-changing fetches use `credentials: 'same-origin'` and these headers. JSON endpoints return `401` for unauthenticated requests; client code redirects to `/login/`.

---

## Testing

```bash
.venv/Scripts/python.exe manage.py test
.venv/Scripts/python.exe manage.py check
```

- Provider calls are patched with `unittest.mock.patch('exams.views.services.<fn>')`.
- Streaming responses are consumed with `b''.join(response.streaming_content)`.
- 32 tests cover auth, pages, session start/free limit, provider endpoints, evaluation persistence, feedback rendering, and Stripe webhook signature handling.
