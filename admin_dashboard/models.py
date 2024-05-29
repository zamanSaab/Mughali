
from django.db import models
from django.utils import timezone

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order', 'Order'),
        ('booking', 'Booking'),
    ]

    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    redirect_url = models.URLField(blank=True, null=True)
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')

    def __str__(self):
        return self.message

