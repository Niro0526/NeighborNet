from rest_framework.exceptions import ValidationError, PermissionDenied
from apps.organizations.models import Organization

PROVIDER_TYPES = ['RESTAURANT', 'BAKERY', 'SUPERMARKET', 'HOTEL', 'COMMUNITY_KITCHEN']
RECIPIENT_TYPES = ['FOOD_BANK', 'NGO', 'SHELTER', 'COMMUNITY_KITCHEN', 'RELIEF_CENTER']

def resolve_organization(user, organization_id, provider=False):
    qs = Organization.objects.filter(type__in=PROVIDER_TYPES if provider else RECIPIENT_TYPES)
    if not user.is_coordinator:
        qs = qs.filter(memberships__user=user, memberships__is_active=True)
    if organization_id:
        org = qs.filter(pk=organization_id).first()
    else:
        org = qs.first()
    if not org:
        raise PermissionDenied('An active membership in the correct organization is required.')
    if not org.verified:
        raise ValidationError('The organization must be verified before participating.')
    return org
