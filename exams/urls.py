from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('setup/', views.setup, name='setup'),
    path('session/', views.session_room, name='session'),
    path('feedback/<uuid:session_id>/', views.feedback_view, name='feedback'),
    path('api/session/start/', views.start_session, name='api_session_start'),
    path('api/session/evaluate/', views.evaluate_session, name='api_session_evaluate'),
    path('api/stt/token/', views.stt_token, name='api_stt_token'),
    path('api/llm/', views.llm_reply, name='api_llm'),
    path('api/tts/', views.tts, name='api_tts'),
    path('api/stripe/webhook/', views.stripe_webhook, name='api_stripe_webhook'),
    path('health/', views.health, name='health'),
]
