import uuid
from django.db import models
from django.conf import settings

def generate_notification_id():
    return f"NOTIF-{uuid.uuid4().hex[:6].upper()}"

class Notification(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_notification_id)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True
    )
    role_target = models.CharField(max_length=50, blank=True, help_text='Target role category if broadcast')
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(
        max_length=20,
        choices=[('info', 'Info'), ('warning', 'Warning'), ('alert', 'Alert'), ('success', 'Success')],
        default='info'
    )
    read = models.BooleanField(default=False)
    action_url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        user_str = self.user.email if self.user else f"Role: {self.role_target}"
        return f"{self.title} -> {user_str} ({'Read' if self.read else 'Unread'})"
