from django.conf import settings
from django.db import models


class Profile(models.Model):
    class SubscriptionStatus(models.TextChoices):
        FREE = 'free', 'Free'
        ACTIVE = 'active', 'Active'
        CANCELLED = 'cancelled', 'Cancelled'

    class SubscriptionTier(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        ANNUAL = 'annual', 'Annual'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, default='')
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.FREE,
    )
    subscription_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        blank=True,
        null=True,
    )
    sessions_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'profiles'

    def __str__(self):
        return f'Profile<{self.user.email or self.user.username}>'

    @property
    def is_subscribed(self):
        return self.subscription_status == self.SubscriptionStatus.ACTIVE

    @property
    def plan_label(self):
        if self.subscription_status == self.SubscriptionStatus.ACTIVE:
            if self.subscription_tier == self.SubscriptionTier.ANNUAL:
                return 'Annual'
            if self.subscription_tier == self.SubscriptionTier.MONTHLY:
                return 'Monthly'
            return 'Active'
        if self.subscription_status == self.SubscriptionStatus.CANCELLED:
            return 'Cancelled'
        return 'Free'
