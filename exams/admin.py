from django.contrib import admin

from .models import ExamSession, Feedback


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'exam_type',
        'level',
        'exercise_type',
        'status',
        'started_at',
    )
    list_filter = ('exam_type', 'level', 'exercise_type', 'status')
    search_fields = ('id', 'user__email', 'user__username')
    readonly_fields = ('id', 'started_at')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('session', 'user', 'overall_level', 'overall_verdict', 'created_at')
    list_filter = ('overall_level', 'overall_verdict')
    search_fields = ('session__id', 'user__email')
    readonly_fields = ('id', 'created_at')
