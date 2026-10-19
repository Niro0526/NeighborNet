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
