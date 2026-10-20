# Code Standards

## Engineering Mindset

1. **Write for the next session, not just this one.** Code must be self-evident.
2. **Small, focused units.** Views validate/orchestrate, services talk to providers, models own persistence.
3. **Explicit over implicit.** Keep request/response shapes and provider contracts visible.
4. **Fail loudly in development, gracefully in production.** Log provider failures; return safe JSON errors.
5. **Don't build what isn't in the build plan.** Keep scope tight.
6. **Audio and WebSocket state is fragile.** Every connection, stream, and audio context must be explicitly opened and closed.

---

## Python / Django

- **Python 3.11**, Django 5.2.
- **Type hints on non-trivial functions** are encouraged; keep them accurate.
- **No business logic in templates.** Templates render context only.
- **Views are thin.** Validate input, check ownership, call a service or the ORM, return a response.
- **Provider calls live in `exams/services.py`.** Views must not build Groq prompts or parse SSE inline.
- **Use the ORM, not raw SQL.** Wrap multi-write operations in `transaction.atomic()`.
- **Scope every user-owned query** with `user=request.user` (or `Profile` lookups by `user`).
- **Use `JsonResponse` for API responses** and `StreamingHttpResponse` for streaming providers.
- **Return `401` JSON from APIs for anonymous users**, never an HTML login redirect.
- **CSRF is mandatory** on state-changing endpoints. Only the Stripe webhook is `csrf_exempt` (it verifies signatures).

```python
# Correct view shape
@require_POST
@api_login_required
def start_session(request):
    payload = _parse_json(request)
    if not isinstance(payload, dict):
        return _error('Invalid request body')
    # validate → transaction → create → JsonResponse
```

### Naming

- **Modules/functions/variables:** `snake_case`.
- **Classes/models:** `PascalCase`.
- **Constants:** `UPPER_SNAKE_CASE`.
- **URL names:** `snake_case` (`api_session_start`, `feedback`).
- **Templates:** `snake_case.html`, grouped in `auth/` where appropriate.

### Django app layout

- One concern per module: `models.py`, `forms.py`, `views.py`, `urls.py`, `services.py`, `admin.py`, `tests.py`.
- Signals belong in `signals.py` and are imported from `AppConfig.ready()`.
- Static assets live under `static/`; templates under `templates/`.

---

## Vanilla JavaScript

- ES modules only (`<script type="module">`), no bundler.
- One responsibility per file: capture, transcription, playback, page orchestration.
- Export classes/helpers; no globals except within the module.
- Always release resources: stop microphone tracks, close `AudioContext`, close WebSocket.
- Use `credentials: 'same-origin'` and the `csrfHeaders()` helper for JSON POSTs.
- Never hardcode provider URLs that need keys; call Django endpoints instead.
- Browser speech fallback is intentional: server TTS failures must not break the examiner turn.

### UI state

- Status strings are lowercase and mirror the visible UI: `idle`, `requesting`, `active`, `connecting`, `connected`, `loading`, `playing`, `error`.
- Update button disabled states from one `updateButtons()` function to avoid drift.

---

## Error Handling

API responses use one shape:

```python
# Success
return JsonResponse({'data': result})

# Expected/user-facing error
return JsonResponse({'error': 'limit_reached', 'message': 'Free session limit reached'}, status=403)

# Provider failure
return JsonResponse({'error': 'provider_error', 'message': str(exc)}, status=502)
```

Rules:

- Log provider failures with a source prefix (`STT token error`, `LLM error`, `TTS error`, `Evaluation error`).
- Never expose raw provider response bodies to the browser; return controlled messages.
- Audio/WebSocket errors must clean up resources before surfacing.
- The session page must never crash; errors appear inline in `#session-error`.
- Stripe signature failures return `400`, not `500`.

---

## Environment Variables

Loaded by `oral_exam/settings.py` from `.env.local`, then `.env` (existing process env wins).

| Variable | Used In | Secret? |
|---|---|---|
| `DJANGO_SECRET_KEY` | `settings.py` | Yes |
| `DJANGO_DEBUG` | `settings.py` | No |
| `DJANGO_ALLOWED_HOSTS` | `settings.py` | No |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `settings.py` | No |
| `DATABASE_URL` | `settings.py` (overrides `DB_*` when set) | Yes |
| `DB_NAME` | `settings.py` | No |
| `DB_USER` | `settings.py` | No |
| `DB_PASSWORD` | `settings.py` | Yes |
| `DB_HOST` | `settings.py` | No |
| `DB_PORT` | `settings.py` | No |
| `ELEVENLABS_API_KEY` | `exams/services.py` | Yes |
| `GROQ_API_KEY` | `exams/services.py` | Yes |
| `GROQ_MODEL` | `exams/services.py` | No |
| `OPENAI_API_KEY` | `exams/services.py` | Yes |
| `STRIPE_SECRET_KEY` | Stripe webhook | Yes |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook | Yes |
| `STRIPE_MONTHLY_PRICE_ID` | Stripe webhook | No |
| `STRIPE_ANNUAL_PRICE_ID` | Stripe webhook | No |

Never commit `.env.local` or `.env`. Keep `.env.example` in sync with variable names only.

---

## Dependencies

**Production (`requirements.txt`):**
- `Django` — framework, auth, ORM, templates
- `psycopg[binary]` — PostgreSQL driver
- `requests` — ElevenLabs, Groq, OpenAI HTTP calls
- `python-dotenv` — environment loading
- `stripe` — webhook signature verification and event handling

**Browser:** no third-party libraries. Native `fetch`, `WebSocket`, Web Audio API, AudioWorklet, `speechSynthesis`.

**Rules:**
- No frontend framework or CDN dependency.
- No HTTP client beyond `requests` on the server.
- No provider SDKs unless they add signature verification or another concrete benefit (Stripe uses the SDK).

---

## Testing

- `python manage.py test` must pass before a feature is considered complete.
- Provider calls are mocked in unit tests (`unittest.mock.patch`).
- Tests cover auth, registration, page access/ownership, free-tier limits, API auth, streaming endpoints, evaluation persistence, and feedback rendering.
- Live provider verification is separate from the test suite and must never print secrets.
