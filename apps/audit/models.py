import uuid
from django.db import models
from django.conf import settings

class AuditCategoryChoices(models.TextChoices):
    AUTH = 'AUTH', 'Authentication & Security'
    FOOD = 'FOOD', 'Food & Resource Management'
    REQUEST = 'REQUEST', 'Resource Requisitions'
    DELIVERY = 'DELIVERY', 'Volunteer & Courier Transport'
    DISASTER = 'DISASTER', 'Emergency Disaster Response'
    ADMIN = 'ADMIN', 'Coordinator Governance'

def generate_audit_id():
    return f"LOG-{uuid.uuid4().hex[:8].upper()}"

class ActivityLog(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_audit_id)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs'
    )
    user_name = models.CharField(max_length=255)
    user_role = models.CharField(max_length=50)
    action = models.CharField(max_length=100)
    details = models.TextField()
    category = models.CharField(
        max_length=30, choices=AuditCategoryChoices.choices, default=AuditCategoryChoices.ADMIN
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.category}] {self.user_name}: {self.action} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
