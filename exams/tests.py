import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from exams import services
from exams.models import ExamSession, Feedback
from exams.prompts import build_examiner_system_prompt, opening_instruction

User = get_user_model()


def make_user(email='candidate@example.com'):
    return User.objects.create_user(username=email, email=email, password='secret1')


def post_json(client, url, payload):
    return client.post(
        url,
        data=json.dumps(payload),
        content_type='application/json',
    )


class PageTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_landing_redirects_authenticated_user(self):
        response = self.client.get(reverse('landing'))
        self.assertRedirects(response, reverse('setup'))

    def test_anonymous_landing_renders(self):
        self.client.logout()
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oral Exam Prep')

    def test_setup_page_renders_all_options(self):
        response = self.client.get(reverse('setup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anglais')
        self.assertContains(response, 'Français')
        self.assertContains(response, 'data-group="language"')
        self.assertContains(response, 'IELTS')
        self.assertContains(response, 'Cambridge B2 First')
        self.assertContains(response, 'Discussion thématique')
        self.assertContains(response, 'Débat')
        self.assertContains(response, 'Aléatoire')

    def test_session_page_requires_owned_session(self):
        response = self.client.get(reverse('session'))
        self.assertRedirects(response, reverse('setup'))

        other_user = make_user('other@example.com')
        foreign_session = ExamSession.objects.create(
            user=other_user,
            exam_type='ielts',
            level='b2',
            exercise_type='topic_discussion',
            duration_seconds=840,
        )

        response = self.client.get(
            reverse('session'), {'sessionId': str(foreign_session.id)}
        )
        self.assertRedirects(response, reverse('setup'))

    def test_session_and_feedback_pages_render(self):
        exam_session = ExamSession.objects.create(
            user=self.user,
            exam_type='ielts',
            level='b2',
            exercise_type='debate',
            language='fr',
            duration_seconds=840,
        )

        response = self.client.get(
            reverse('session'), {'sessionId': str(exam_session.id)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Salle d’examen')
        self.assertContains(response, 'Question de l’examinateur')
        self.assertContains(response, 'Envoyer la réponse')
        self.assertContains(response, 'Français')
        self.assertContains(response, f'data-session-id="{exam_session.id}"')
        self.assertContains(response, 'data-language="fr"')
        self.assertContains(response, 'data-language-locale="fr-FR"')

        response = self.client.get(reverse('feedback', args=[exam_session.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pas encore de bilan')

    def test_health_endpoint(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})


class SessionStartTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_start_session_creates_row(self):
        response = post_json(
            self.client,
            reverse('api_session_start'),
            {
                'language': 'en',
                'examType': 'ielts',
                'level': 'b2',
                'exerciseType': 'debate',
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        exam_session = ExamSession.objects.get(id=data['sessionId'])
        self.assertEqual(exam_session.user, self.user)
        self.assertEqual(exam_session.exam_type, 'ielts')
        self.assertEqual(exam_session.level, 'b2')
        self.assertEqual(exam_session.exercise_type, 'debate')
        self.assertEqual(exam_session.language, 'en')
        self.assertEqual(exam_session.duration_seconds, 840)
        self.assertEqual(data['config']['language'], 'en')

    def test_random_exercise_is_resolved(self):
        response = post_json(
            self.client,
            reverse('api_session_start'),
            {
                'language': 'en',
                'examType': 'cambridge_b2',
                'level': 'c1',
                'exerciseType': 'random',
            },
        )

        self.assertEqual(response.status_code, 200)
        exam_session = ExamSession.objects.get(id=response.json()['data']['sessionId'])
        self.assertIn(exam_session.exercise_type, {'topic_discussion', 'debate'})

    def test_start_session_persists_french_language(self):
        response = post_json(
            self.client,
            reverse('api_session_start'),
            {
                'language': 'fr',
                'examType': 'ielts',
                'level': 'b2',
                'exerciseType': 'topic_discussion',
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['config']['language'], 'fr')
        exam_session = ExamSession.objects.get(id=data['sessionId'])
        self.assertEqual(exam_session.language, 'fr')

    def test_invalid_configuration_is_rejected(self):
        response = post_json(
            self.client,
            reverse('api_session_start'),
            {
                'language': 'en',
                'examType': 'delf',
                'level': 'b2',
                'exerciseType': 'debate',
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_language_is_rejected(self):
        response = post_json(
            self.client,
            reverse('api_session_start'),
            {
                'language': 'de',
                'examType': 'ielts',
                'level': 'b2',
                'exerciseType': 'debate',
            },
        )
        self.assertEqual(response.status_code, 400)

        response = post_json(
            self.client,
            reverse('api_session_start'),
            {'examType': 'ielts', 'level': 'b2', 'exerciseType': 'debate'},
        )
        self.assertEqual(response.status_code, 400)

    def test_sessions_are_unlimited(self):
        payload = {
            'language': 'en',
            'examType': 'ielts',
            'level': 'b1',
            'exerciseType': 'debate',
        }
        for _ in range(6):
            response = post_json(self.client, reverse('api_session_start'), payload)
            self.assertEqual(response.status_code, 200)

        self.assertEqual(ExamSession.objects.filter(user=self.user).count(), 6)

    def test_anonymous_user_gets_json_401(self):
        self.client.logout()
        response = post_json(
            self.client,
            reverse('api_session_start'),
            {
                'language': 'en',
                'examType': 'ielts',
                'level': 'b1',
                'exerciseType': 'debate',
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'unauthorized')


class ProviderEndpointTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.exam_session = ExamSession.objects.create(
            user=self.user,
            exam_type='ielts',
            level='b2',
            exercise_type='topic_discussion',
            duration_seconds=840,
        )

    def test_stt_token_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse('api_stt_token'))
        self.assertEqual(response.status_code, 401)

    @patch('exams.views.services.create_realtime_token', return_value='test-token')
    def test_stt_token_returns_token(self, mocked):
        response = self.client.get(reverse('api_stt_token'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'token': 'test-token'})
        mocked.assert_called_once()

    def test_llm_requires_auth(self):
        self.client.logout()
        response = post_json(
            self.client, reverse('api_llm'), {'transcript': 'Hello', 'history': []}
        )
        self.assertEqual(response.status_code, 401)

    @patch('exams.views.services.stream_examiner_reply')
    def test_llm_streams_plain_text(self, mocked_stream):
        mocked_stream.return_value = iter(['Hello ', 'there.'])
        response = post_json(
            self.client,
            reverse('api_llm'),
            {
                'sessionId': str(self.exam_session.id),
                'transcript': 'I like music.',
                'history': [],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            b''.join(response.streaming_content).decode('utf-8'),
            'Hello there.',
        )
        system_prompt, user_content, _history = mocked_stream.call_args.args
        self.assertIn('IELTS', system_prompt)
        self.assertIn('B2', system_prompt)
        self.assertEqual(user_content, 'I like music.')

    @patch('exams.views.services.stream_examiner_reply')
    def test_llm_opening_question(self, mocked_stream):
        mocked_stream.return_value = iter(['Good morning. Let us begin.'])
        response = post_json(
            self.client,
            reverse('api_llm'),
            {'sessionId': str(self.exam_session.id), 'opening': True},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            b''.join(response.streaming_content).decode('utf-8'),
            'Good morning. Let us begin.',
        )
        _system_prompt, user_content, _history = mocked_stream.call_args.args
        self.assertIn('Begin the speaking exam now', user_content)

    @patch('exams.views.services.stream_examiner_reply')
    def test_llm_uses_french_session_language(self, mocked_stream):
        mocked_stream.return_value = iter(['Bonjour.'])
        french_session = ExamSession.objects.create(
            user=self.user,
            exam_type='ielts',
            level='b2',
            exercise_type='topic_discussion',
            language='fr',
            duration_seconds=840,
        )

        response = post_json(
            self.client,
            reverse('api_llm'),
            {'sessionId': str(french_session.id), 'opening': True},
        )

        self.assertEqual(response.status_code, 200)
        system_prompt, user_content, _history = mocked_stream.call_args.args
        self.assertIn('français', system_prompt)
        self.assertIn('Commencez', user_content)

    def test_llm_requires_session_id(self):
        response = post_json(
            self.client, reverse('api_llm'), {'transcript': 'Hello', 'history': []}
        )
        self.assertEqual(response.status_code, 400)

    def test_llm_rejects_another_users_session(self):
        other = make_user(email='other@example.com')
        other_session = ExamSession.objects.create(
            user=other,
            exam_type='ielts',
            level='b2',
            exercise_type='topic_discussion',
            duration_seconds=840,
        )
        response = post_json(
            self.client,
            reverse('api_llm'),
            {'sessionId': str(other_session.id), 'transcript': 'Hello', 'history': []},
        )
        self.assertEqual(response.status_code, 404)

    def test_llm_rejects_empty_transcript(self):
        response = post_json(
            self.client,
            reverse('api_llm'),
            {
                'sessionId': str(self.exam_session.id),
                'transcript': '   ',
                'history': [],
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_tts_requires_auth(self):
        self.client.logout()
        response = post_json(self.client, reverse('api_tts'), {'text': 'Hello'})
        self.assertEqual(response.status_code, 401)

    @patch('exams.views.services.open_tts_stream')
    def test_tts_streams_audio(self, mocked_stream):
        mocked_stream.return_value = iter([b'fake-mp3'])
        response = post_json(self.client, reverse('api_tts'), {'text': 'Hello'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'audio/mpeg')
        self.assertEqual(b''.join(response.streaming_content), b'fake-mp3')
        mocked_stream.assert_called_once_with('Hello', voice='onyx')

    @patch('exams.views.services.open_tts_stream')
    def test_tts_uses_french_voice(self, mocked_stream):
        mocked_stream.return_value = iter([b'fake-mp3'])
        response = post_json(
            self.client,
            reverse('api_tts'),
            {'text': 'Bonjour', 'language': 'fr'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'fake-mp3')
        mocked_stream.assert_called_once_with('Bonjour', voice='alloy')

    def test_tts_rejects_unknown_language(self):
        response = post_json(
            self.client,
            reverse('api_tts'),
            {'text': 'Hello', 'language': 'de'},
        )
        self.assertEqual(response.status_code, 400)

    @patch('exams.views.services.evaluate_transcript')
    def test_evaluate_saves_feedback_and_completes_session(self, mocked_evaluate):
        mocked_evaluate.return_value = {
            'overall_level': 'B2',
            'overall_verdict': 'Ready',
            'fluency_score': 7,
            'vocabulary_score': 6,
            'grammar_score': 7,
            'task_achievement_score': 8,
            'fluency_notes': ['Good pace.'],
            'vocabulary_notes': [],
            'grammar_notes': [],
            'task_achievement_notes': [],
            'pronunciation_flags': [],
            'recommendations': ['Keep practising.'],
        }

        response = post_json(
            self.client,
            reverse('api_session_evaluate'),
            {
                'sessionId': str(self.exam_session.id),
                'transcript': [
                    {'speaker': 'user', 'text': 'I enjoy reading.', 'timestamp': 1}
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.exam_session.refresh_from_db()
        self.assertEqual(self.exam_session.status, ExamSession.Status.COMPLETED)
        self.assertIsNotNone(self.exam_session.ended_at)
        self.assertEqual(len(self.exam_session.transcript), 1)

        feedback = Feedback.objects.get(session=self.exam_session)
        self.assertEqual(feedback.overall_level, 'B2')
        self.assertEqual(feedback.fluency_score, 7)

    def test_evaluate_requires_transcript(self):
        response = post_json(
            self.client,
            reverse('api_session_evaluate'),
            {'sessionId': str(self.exam_session.id), 'transcript': []},
        )
        self.assertEqual(response.status_code, 400)

    def test_feedback_page_shows_report(self):
        Feedback.objects.create(
            session=self.exam_session,
            user=self.user,
            overall_level='B2',
            overall_verdict='Ready',
            fluency_score=7,
            vocabulary_score=6,
            grammar_score=7,
            task_achievement_score=8,
            fluency_notes=['Good pace.'],
            recommendations=['Keep practising.'],
        )

        response = self.client.get(reverse('feedback', args=[self.exam_session.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'B2')
        self.assertContains(response, 'Prêt')
        self.assertContains(response, 'Good pace.')
        self.assertContains(response, 'Keep practising.')


class ExaminerPromptTests(TestCase):
    def test_english_prompt_and_opening(self):
        prompt = build_examiner_system_prompt('ielts', 'b2', 'topic_discussion', 1)
        self.assertIn('spoken English', prompt)
        self.assertNotIn('français', prompt)
        self.assertIn('Begin the speaking exam now', opening_instruction('en'))

    def test_french_prompt_and_opening(self):
        prompt = build_examiner_system_prompt(
            'ielts', 'b2', 'debate', 1, language='fr'
        )
        self.assertIn('français', prompt)
        self.assertIn('débat', prompt)
        self.assertIn('Commencez', opening_instruction('fr'))

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(
            opening_instruction('de'), opening_instruction('en')
        )


@override_settings(GROQ_API_KEY='test-key', GROQ_MODEL='test-model')
class EvaluationLanguageTests(TestCase):
    @patch('exams.services.requests.post')
    def test_french_evaluation_asks_for_french_notes(self, mocked_post):
        mocked_post.return_value.status_code = 200
        mocked_post.return_value.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': json.dumps(
                            {
                                'overall_level': 'B2',
                                'overall_verdict': 'Ready',
                                'scores': {
                                    'fluency': 7,
                                    'vocabulary': 6,
                                    'grammar': 7,
                                    'task_achievement': 8,
                                },
                                'notes': {'fluency': ['Bon débit.']},
                                'pronunciation_flags': [],
                                'recommendations': ['Continuez ainsi.'],
                            }
                        )
                    }
                }
            ]
        }
        session = ExamSession(
            exam_type='ielts',
            level='b2',
            exercise_type='debate',
            language='fr',
            duration_seconds=840,
        )

        result = services.evaluate_transcript(
            session, [{'speaker': 'user', 'text': 'Bonjour, je pense que…'}]
        )

        payload = mocked_post.call_args.kwargs['json']
        system_prompt = payload['messages'][0]['content']
        self.assertIn('in French', system_prompt)
        self.assertEqual(result['fluency_notes'], ['Bon débit.'])
        self.assertEqual(result['overall_verdict'], 'Ready')


class StripeWebhookTests(TestCase):
    def test_webhook_returns_503_when_unconfigured(self):
        response = self.client.post(
            reverse('api_stripe_webhook'),
            data='{}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 503)

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test', STRIPE_SECRET_KEY='sk_test')
    def test_webhook_rejects_invalid_signature(self):
        response = self.client.post(
            reverse('api_stripe_webhook'),
            data='{"type": "checkout.session.completed"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid',
        )
        self.assertEqual(response.status_code, 400)
