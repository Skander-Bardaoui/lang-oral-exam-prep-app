import uuid

from django.conf import settings
from django.db import models

from .config import EXAM_CHOICES, EXERCISE_CHOICES, LANGUAGE_CHOICES, LEVEL_CHOICES


class ExamSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'En cours'
        COMPLETED = 'completed', 'Terminée'
        ABANDONED = 'abandoned', 'Abandonnée'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_sessions',
    )
    exam_type = models.CharField(max_length=32, choices=EXAM_CHOICES)
    level = models.CharField(max_length=8, choices=LEVEL_CHOICES)
    exercise_type = models.CharField(max_length=32, choices=EXERCISE_CHOICES)
    language = models.CharField(max_length=8, choices=LANGUAGE_CHOICES, default='en')
    duration_seconds = models.PositiveIntegerField()
    transcript = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sessions'
        ordering = ('-started_at',)

    def __str__(self):
        return f'{self.get_exam_type_display()} {self.level} — {self.id}'


class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='feedback',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedback_reports',
    )
    overall_level = models.CharField(max_length=8, blank=True, default='')
    overall_verdict = models.CharField(max_length=32, blank=True, default='')
    fluency_score = models.PositiveSmallIntegerField(default=0)
    vocabulary_score = models.PositiveSmallIntegerField(default=0)
    grammar_score = models.PositiveSmallIntegerField(default=0)
    task_achievement_score = models.PositiveSmallIntegerField(default=0)
    fluency_notes = models.JSONField(default=list, blank=True)
    vocabulary_notes = models.JSONField(default=list, blank=True)
    grammar_notes = models.JSONField(default=list, blank=True)
    task_achievement_notes = models.JSONField(default=list, blank=True)
    pronunciation_flags = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedback'
        ordering = ('-created_at',)

    def __str__(self):
        return f'Feedback for {self.session_id}'
