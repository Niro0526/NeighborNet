import logging
from django.db import transaction
from .models import Notification

logger = logging.getLogger(__name__)

def send_notification(
    title: str,
    message: str,
    notif_type: str = 'info',
    user=None,
    organization=None,
    role_target: str = '',
    action_url: str = '',
    event_key: str = ''
):
    """
    Creates a database-backed notification with duplicate event protection and organization isolation.
    """
    # Persist individual inbox entries so reading a broadcast never marks it read for others.
    if user is None and (organization is not None or role_target):
        from apps.accounts.models import User
        recipients = User.objects.filter(is_active=True)
        if organization is not None:
            recipients = recipients.filter(organization_memberships__organization=organization, organization_memberships__is_active=True)
            from common.organization_scope import PROVIDER_TYPES, RECIPIENT_TYPES
            roles=['COORDINATOR']
            if organization.type in PROVIDER_TYPES:
                roles.append('FOOD_PROVIDER')
            if organization.type in RECIPIENT_TYPES:
                roles.append('RECIPIENT')
            recipients=recipients.filter(role_assignments__role__in=roles,role_assignments__is_approved=True)
        else:
            recipients = recipients.filter(role_assignments__role=role_target, role_assignments__is_approved=True)
        return [send_notification(title, message, notif_type, user=recipient, action_url=action_url,
                                  event_key=f'{event_key}:{recipient.pk}' if event_key else '')
                for recipient in recipients.distinct()]
    try:
        if event_key and Notification.objects.filter(event_key=event_key).exists():
            # Skip duplicate notification
            return None

        with transaction.atomic():
            notification = Notification.objects.create(
                user=user,
                organization=organization,
                role_target=role_target,
                title=title,
                message=message,
                type=notif_type,
                action_url=action_url,
                event_key=event_key
            )
            return notification
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        return None
