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


class PilotFeedbackCategoryChoices(models.TextChoices):
    FOOD_LISTING = 'food_listing', 'Ease of Listing Food'
    REQUESTING_RESOURCES = 'requesting_resources', 'Ease of Requesting Resources'
    ALLOCATION_EXPLANATIONS = 'allocation_explanations', 'Allocation Explanations'
    VOLUNTEER_ASSIGNMENT = 'volunteer_assignment', 'Volunteer Assignment Experience'
    DELIVERY_WORKFLOW = 'delivery_workflow', 'Delivery Workflow Usability'
    DISASTER_CLARITY = 'disaster_clarity', 'Disaster-Mode Clarity'
    GENERAL = 'general', 'General Platform Usability'


def generate_feedback_id():
    return f"FDB-{uuid.uuid4().hex[:8].upper()}"


class PilotFeedback(models.Model):
    """
    Pilot feedback mechanism for authenticated participants.
    Records ratings on key usability dimensions with participant consent.
    """
    id = models.CharField(max_length=64, primary_key=True, default=generate_feedback_id)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pilot_feedbacks'
    )
    user_name = models.CharField(max_length=255, blank=True)
    user_role = models.CharField(max_length=50)
    category = models.CharField(max_length=50, choices=PilotFeedbackCategoryChoices.choices)
    rating = models.IntegerField(help_text='Rating from 1 to 5')
    comments = models.TextField(blank=True)
    consent_to_share_internally = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.category}] {self.rating}/5 from {self.user_role} ({self.created_at.strftime('%Y-%m-%d')})"

