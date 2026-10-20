from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'subscription_status',
        'subscription_tier',
        'sessions_used',
        'created_at',
    )
    list_filter = ('subscription_status', 'subscription_tier')
    search_fields = ('user__email', 'user__username', 'stripe_customer_id')
    readonly_fields = ('created_at',)
