import json
import logging
import random
from functools import wraps

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Profile

from . import services
from .config import (
    EXAMS,
    EXERCISE_DESCRIPTIONS,
    EXERCISE_LABELS,
    EXERCISE_SELECTIONS,
    EXERCISE_TYPES,
    LANGUAGES,
    LANGUAGE_CODES,
    LEVEL_LABELS,
    LEVELS,
)
from .models import ExamSession, Feedback
from .prompts import build_examiner_system_prompt, opening_instruction

logger = logging.getLogger(__name__)


def api_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'unauthorized', 'message': 'Vous devez être connecté'},
                status=401,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def _parse_json(request):
    try:
        return json.loads(request.body or b'{}')
    except (ValueError, TypeError):
        return None


def _error(message, status=400, code='invalid_request'):
    return JsonResponse({'error': code, 'message': message}, status=status)


def landing(request):
    if request.user.is_authenticated:
        return redirect('setup')
    return render(request, 'landing.html')


@login_required
def setup(request):
    exam_options = [
        {
            'value': key,
            'name': value['name'],
            'description': value['description'],
        }
        for key, value in EXAMS.items()
    ]
    level_options = [{'value': key, 'label': LEVEL_LABELS[key]} for key in LEVELS]
    language_options = [
        {
            'value': code,
            'label': data['label'],
            'description': data['description'],
        }
        for code, data in LANGUAGES.items()
    ]
    exercise_options = [
        {
            'value': value,
            'label': 'Aléatoire' if value == 'random' else EXERCISE_LABELS[value],
            'description': EXERCISE_DESCRIPTIONS[value],
        }
        for value in EXERCISE_SELECTIONS
    ]
    return render(
        request,
        'setup.html',
        {
            'exam_options': exam_options,
            'level_options': level_options,
            'language_options': language_options,
            'exercise_options': exercise_options,
        },
    )


@login_required
def session_room(request):
    session_id = request.GET.get('sessionId')
    if not session_id:
        return redirect('setup')

    try:
        exam_session = ExamSession.objects.get(id=session_id, user=request.user)
    except (ExamSession.DoesNotExist, ValidationError, ValueError):
        return redirect('setup')

    if Feedback.objects.filter(session=exam_session).exists():
        return redirect('feedback', session_id=exam_session.id)

    language = LANGUAGES.get(exam_session.language, LANGUAGES['en'])
    return render(
        request,
        'session.html',
        {
            'exam_session': exam_session,
            'exam': EXAMS.get(exam_session.exam_type, {'name': exam_session.exam_type}),
            'language': language,
            'level_label': LEVEL_LABELS.get(exam_session.level, exam_session.level),
            'exercise_label': EXERCISE_LABELS.get(
                exam_session.exercise_type, exam_session.exercise_type
            ),
        },
    )


@login_required
def feedback_view(request, session_id):
    exam_session = get_object_or_404(ExamSession, id=session_id, user=request.user)
    feedback = Feedback.objects.filter(session=exam_session).first()
    language = LANGUAGES.get(exam_session.language, LANGUAGES['en'])
    return render(
        request,
        'feedback.html',
        {
            'exam_session': exam_session,
            'exam': EXAMS.get(exam_session.exam_type, {'name': exam_session.exam_type}),
            'language': language,
            'level_label': LEVEL_LABELS.get(exam_session.level, exam_session.level),
            'exercise_label': EXERCISE_LABELS.get(
                exam_session.exercise_type, exam_session.exercise_type
            ),
            'feedback': feedback,
        },
    )


@require_POST
@api_login_required
def start_session(request):
    payload = _parse_json(request)
    if not isinstance(payload, dict):
        return _error('Corps de requête invalide')

    exam_type = payload.get('examType')
    level = payload.get('level')
    language = payload.get('language')
    exercise_selection = payload.get('exerciseType')

    if exam_type not in EXAMS:
        return _error('Configuration de session invalide')
    if level not in LEVELS:
        return _error('Configuration de session invalide')
    if language not in LANGUAGE_CODES:
        return _error('Configuration de session invalide')
    if exercise_selection not in EXERCISE_SELECTIONS:
        return _error('Configuration de session invalide')

    exercise_type = (
        random.choice(EXERCISE_TYPES)
        if exercise_selection == 'random'
        else exercise_selection
    )
    exam = EXAMS[exam_type]

    exam_session = ExamSession.objects.create(
        user=request.user,
        exam_type=exam_type,
        level=level,
        exercise_type=exercise_type,
        language=language,
        duration_seconds=exam['duration_seconds'],
        status=ExamSession.Status.ACTIVE,
    )

    return JsonResponse(
        {
            'data': {
                'sessionId': str(exam_session.id),
                'config': {
                    'examType': exam_type,
                    'level': level,
                    'exerciseType': exercise_type,
                    'language': language,
                    'durationSeconds': exam['duration_seconds'],
                },
            }
        }
    )


@require_GET
@api_login_required
def stt_token(request):
    try:
        token = services.create_realtime_token()
    except services.ProviderError as exc:
        logger.error('STT token error: %s', exc)
        return _error(str(exc), status=502, code='token_failed')
    return JsonResponse({'token': token})


@require_POST
@api_login_required
def llm_reply(request):
    payload = _parse_json(request)
    if not isinstance(payload, dict):
        return _error('Corps de requête invalide')

    session_id = payload.get('sessionId')
    opening = payload.get('opening') is True
    transcript = payload.get('transcript')
    history = payload.get('history', [])

    if not isinstance(session_id, str) or not session_id.strip():
        return _error('Requête invalide')
    if not opening:
        if not isinstance(transcript, str) or not transcript.strip():
            return _error('Requête invalide')
        if len(transcript) > 8000:
            return _error('Requête invalide')
    if not isinstance(history, list):
        return _error('Requête invalide')

    try:
        exam_session = ExamSession.objects.get(id=session_id, user=request.user)
    except (ExamSession.DoesNotExist, ValidationError, ValueError):
        return _error('Session introuvable', status=404, code='not_found')

    cleaned_history = []
    for item in history[:50]:
        if not isinstance(item, dict):
            continue
        role = item.get('role')
        content = item.get('content')
        if role in ('user', 'assistant') and isinstance(content, str):
            cleaned_history.append({'role': role, 'content': content[:4000]})

    system_prompt = build_examiner_system_prompt(
        exam_session.exam_type,
        exam_session.level,
        exam_session.exercise_type,
        exam_session.id.int,
        exam_session.language,
    )
    user_content = (
        opening_instruction(exam_session.language) if opening else transcript.strip()
    )

    try:
        stream = services.stream_examiner_reply(system_prompt, user_content, cleaned_history)
    except services.ProviderError as exc:
        logger.error('LLM error: %s', exc)
        return _error(str(exc), status=502, code='provider_error')

    response = StreamingHttpResponse(stream, content_type='text/plain; charset=utf-8')
    response['Cache-Control'] = 'no-store'
    return response


@require_POST
@api_login_required
def tts(request):
    payload = _parse_json(request)
    if not isinstance(payload, dict):
        return _error('Corps de requête invalide')

    text = payload.get('text')
    language = payload.get('language', 'en')

    if not isinstance(text, str) or not text.strip():
        return _error('Requête invalide')
    if len(text) > 4096:
        return _error('Requête invalide')
    if not isinstance(language, str) or language not in LANGUAGES:
        return _error('Requête invalide')

    try:
        stream = services.open_tts_stream(
            text.strip(), voice=LANGUAGES[language]['tts_voice']
        )
    except services.ProviderError as exc:
        logger.error('TTS error: %s', exc)
        return _error(str(exc), status=502, code='provider_error')

    response = StreamingHttpResponse(stream, content_type='audio/mpeg')
    response['Cache-Control'] = 'no-store'
    return response


@require_POST
@api_login_required
def evaluate_session(request):
    payload = _parse_json(request)
    if not isinstance(payload, dict):
        return _error('Corps de requête invalide')

    session_id = payload.get('sessionId')
    transcript = payload.get('transcript')

    if not isinstance(transcript, list):
        return _error('Transcription invalide')
    if not transcript:
        return _error('Aucune transcription à évaluer')

    try:
        exam_session = ExamSession.objects.get(id=session_id, user=request.user)
    except (ExamSession.DoesNotExist, ValidationError, ValueError):
        return _error('Session introuvable', status=404, code='not_found')

    existing = Feedback.objects.filter(session=exam_session).first()
    if existing:
        return JsonResponse(
            {'data': {'feedbackId': str(existing.id), 'sessionId': str(exam_session.id)}}
        )

    cleaned_transcript = []
    for entry in transcript[:500]:
        if not isinstance(entry, dict):
            continue
        text = entry.get('text') or entry.get('content')
        if not isinstance(text, str) or not text.strip():
            continue
        cleaned_transcript.append(
            {
                'speaker': str(entry.get('speaker') or entry.get('role') or 'user'),
                'text': text.strip()[:4000],
                'timestamp': entry.get('timestamp'),
                'confidence': entry.get('confidence'),
            }
        )

    if not cleaned_transcript:
        return _error('Aucune transcription à évaluer')

    try:
        result = services.evaluate_transcript(exam_session, cleaned_transcript)
    except services.ProviderError as exc:
        logger.error('Evaluation error: %s', exc)
        return _error(str(exc), status=502, code='provider_error')

    with transaction.atomic():
        feedback, _ = Feedback.objects.update_or_create(
            session=exam_session,
            defaults={'user': request.user, **result},
        )
        exam_session.transcript = cleaned_transcript
        exam_session.status = ExamSession.Status.COMPLETED
        exam_session.ended_at = timezone.now()
        exam_session.save(update_fields=['transcript', 'status', 'ended_at'])

    return JsonResponse(
        {'data': {'feedbackId': str(feedback.id), 'sessionId': str(exam_session.id)}}
    )


def _stripe_get(obj, key, default=None):
    if obj is None:
        return default
    try:
        return obj.get(key, default)
    except AttributeError:
        return getattr(obj, key, default)


def _find_profile(customer_id, user_id):
    if customer_id:
        profile = Profile.objects.filter(stripe_customer_id=customer_id).first()
        if profile:
            return profile
    if user_id:
        return Profile.objects.filter(user_id=user_id).first()
    return None


def _tier_from_price(price_id):
    if price_id and price_id == settings.STRIPE_MONTHLY_PRICE_ID:
        return Profile.SubscriptionTier.MONTHLY
    if price_id and price_id == settings.STRIPE_ANNUAL_PRICE_ID:
        return Profile.SubscriptionTier.ANNUAL
    return None


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return _error('Stripe webhook is not configured', status=503, code='not_configured')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.headers.get('Stripe-Signature', ''),
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return _error('Invalid webhook payload', status=400, code='invalid_signature')

    event_type = event['type']
    obj = event['data']['object']
    metadata = _stripe_get(obj, 'metadata') or {}
    customer_id = _stripe_get(obj, 'customer')
    user_id = _stripe_get(obj, 'client_reference_id') or _stripe_get(metadata, 'user_id')

    profile = _find_profile(customer_id, user_id)
    if profile is None:
        return JsonResponse({'received': True, 'updated': False})

    if event_type == 'checkout.session.completed':
        profile.subscription_status = Profile.SubscriptionStatus.ACTIVE
        if customer_id:
            profile.stripe_customer_id = customer_id
        tier = _stripe_get(metadata, 'tier')
        if tier in Profile.SubscriptionTier.values:
            profile.subscription_tier = tier
        profile.save(
            update_fields=['subscription_status', 'stripe_customer_id', 'subscription_tier']
        )
    elif event_type in (
        'customer.subscription.created',
        'customer.subscription.updated',
        'customer.subscription.deleted',
    ):
        status = _stripe_get(obj, 'status')
        if event_type == 'customer.subscription.deleted' or status in (
            'canceled',
            'unpaid',
            'incomplete_expired',
        ):
            profile.subscription_status = Profile.SubscriptionStatus.CANCELLED
        elif status in ('active', 'trialing'):
            profile.subscription_status = Profile.SubscriptionStatus.ACTIVE
        else:
            profile.subscription_status = Profile.SubscriptionStatus.FREE

        items = _stripe_get(obj, 'items') or {}
        item_rows = _stripe_get(items, 'data') or []
        price_id = None
        if item_rows:
            price = _stripe_get(item_rows[0], 'price') or {}
            price_id = _stripe_get(price, 'id')

        tier = _tier_from_price(price_id) or _stripe_get(metadata, 'tier')
        if tier in Profile.SubscriptionTier.values:
            profile.subscription_tier = tier
        if customer_id:
            profile.stripe_customer_id = customer_id
        profile.save(
            update_fields=['subscription_status', 'subscription_tier', 'stripe_customer_id']
        )

    return JsonResponse({'received': True, 'updated': True})


@require_GET
def health(request):
    return JsonResponse({'status': 'ok'})
