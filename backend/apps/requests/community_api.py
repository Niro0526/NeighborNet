"""Authenticated personal claims, sharing locked inventory with NGO allocations."""
import math
import secrets
from datetime import timedelta
from decimal import Decimal
from django.db import transaction, connection
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .community_models import PersonalLocation, FoodClaim, FoodClaimEvent
from apps.resources.models import Resource
from apps.volunteers.models import Volunteer
from apps.notifications.services import send_notification
from apps.audit.models import ActivityLog
from apps.intelligence.services.distance import calculate_haversine_distance, MAX_SERVICE_RADIUS_KM


class ActiveAccount(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_active and request.user.status == 'active'


class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)

    class Meta:
        model = PersonalLocation
        fields = ['address', 'latitude', 'longitude']

    def validate(self, attrs):
        if any(not math.isfinite(attrs[k]) for k in ['latitude', 'longitude']):
            raise ValidationError('Coordinates must be finite.')
        return attrs


def provider_member(user, resource):
    return user.is_food_provider and resource.provider.memberships.filter(user=user, is_active=True).exists()


def geographic_distance(lat, lon, latitude, longitude):
    """Use PostGIS where enabled; retain the project's PostgreSQL-only deployment."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis')")
            if cursor.fetchone()[0]:
                cursor.execute('SELECT ST_DistanceSphere(ST_MakePoint(%s, %s), ST_MakePoint(%s, %s)) / 1000.0', [lon, lat, longitude, latitude])
                return float(cursor.fetchone()[0])
    return calculate_haversine_distance(lat, lon, latitude, longitude)


def check_food(resource, latitude, longitude, *, reserve=False, approval=False):
    now = timezone.now()
    if resource.is_disaster_relief or resource.disaster_event_id or not resource.is_food:
        raise ValidationError('Only normal community food offers can be claimed here.')
    if not resource.provider.verified or resource.status in ['EXPIRED', 'WITHDRAWN', 'DEPLETED', 'COLLECTED']:
        raise ValidationError('This verified food offer is no longer available.')
    if reserve and (resource.status != 'AVAILABLE' or resource.available_quantity <= 0):
        raise ValidationError('No food remains available.')
    margin = timedelta(hours=2) if reserve or approval else timedelta()
    if not resource.safe_until or resource.safe_until <= now + margin or resource.pickup_start >= resource.safe_until:
        raise ValidationError('Food must have a safe-use deadline with sufficient time remaining (two hours for claims and approval).')
    if resource.pickup_end <= now or not resource.storage_requirements:
        raise ValidationError('Pickup window has closed or storage instructions are missing.')
    lat = resource.pickup_latitude if resource.pickup_latitude is not None else resource.provider.latitude
    lon = resource.pickup_longitude if resource.pickup_longitude is not None else resource.provider.longitude
    distance = geographic_distance(lat, lon, latitude, longitude)
    if not math.isfinite(distance) or distance > MAX_SERVICE_RADIUS_KM:
        raise ValidationError(f'Location is outside the {MAX_SERVICE_RADIUS_KM} km service area.')
    return distance


class ClaimSerializer(serializers.ModelSerializer):
    resourceName = serializers.CharField(source='resource.name', read_only=True)
    providerName = serializers.CharField(source='resource.provider.name', read_only=True)
    unit = serializers.CharField(source='resource.unit', read_only=True)
    pickupAddress = serializers.SerializerMethodField()
    storageRequirements = serializers.CharField(source='resource.storage_requirements', read_only=True)
    safetyNotes = serializers.CharField(source='resource.safety_notes', read_only=True)
    safeUntil = serializers.DateTimeField(source='resource.safe_until', read_only=True)
    pickupStart = serializers.DateTimeField(source='resource.pickup_start', read_only=True)
    pickupEnd = serializers.DateTimeField(source='resource.pickup_end', read_only=True)
    events = serializers.SerializerMethodField()
    recipientName = serializers.SerializerMethodField()
    volunteerName = serializers.CharField(source='volunteer.full_name', read_only=True, default=None)
    volunteerUserId = serializers.CharField(source='volunteer.user_id', read_only=True, default=None)
    canHandover = serializers.SerializerMethodField()
    pickupCode = serializers.SerializerMethodField()

    class Meta:
        model = FoodClaim
        fields = ['id', 'resource', 'resourceName', 'providerName', 'recipient', 'recipientName', 'quantity', 'unit', 'method', 'status', 'address', 'latitude', 'longitude', 'volunteer', 'volunteerName', 'volunteerUserId', 'canHandover', 'pickupCode', 'approved_by', 'created_at', 'updated_at', 'pickupAddress', 'storageRequirements', 'safetyNotes', 'safeUntil', 'pickupStart', 'pickupEnd', 'events']
        read_only_fields = fields

    def get_pickupAddress(self, obj):
        return obj.resource.pickup_address or obj.resource.provider.address

    def get_canHandover(self, obj):
        user = self.context['request'].user
        return user.is_coordinator or provider_member(user, obj.resource) or bool(user.is_volunteer and obj.volunteer_id and obj.volunteer.user_id == user.pk)

    def get_pickupCode(self, obj):
        return obj.pickup_code if obj.recipient_id == self.context['request'].user.pk and obj.status == 'APPROVED' else None

    def get_recipientName(self, obj):
        user = self.context['request'].user
        return obj.recipient.name if user.is_coordinator or obj.recipient_id == user.pk or (obj.volunteer_id and obj.volunteer.user_id == user.pk) else 'Community recipient'

    def get_events(self, obj):
        return list(obj.events.values('status', 'created_at'))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context['request'].user
        if not (user.is_coordinator or instance.recipient_id == user.pk or (instance.volunteer_id and instance.volunteer.user_id == user.pk)):
            for key in ['recipient', 'address', 'latitude', 'longitude']:
                data.pop(key, None)
        return data


def record(claim, actor):
    FoodClaimEvent.objects.create(claim=claim, actor=actor, status=claim.status)
    ActivityLog.objects.create(user=actor, user_name=actor.name, user_role='USER', action=f'FOOD_CLAIM_{claim.status}', details=f'Food claim {claim.pk}: {claim.quantity} {claim.resource.unit} of {claim.resource.name}; {claim.status}.', category='FOOD')
    payload = dict(title='Food request update', message=f'{claim.resource.name}: {claim.quantity} {claim.resource.unit} — {claim.get_status_display()}.', action_url='/community-food')
    key = f'food-claim-{claim.pk}-{claim.status}'
    send_notification(**payload, user=claim.recipient, event_key=key+'-recipient')
    send_notification(**payload, organization=claim.resource.provider, event_key=key+'-provider')
    send_notification(**payload, role_target='COORDINATOR', event_key=key+'-coordinator')
    if claim.volunteer_id:
        send_notification(**payload, user=claim.volunteer.user, event_key=key+'-courier')
    elif claim.status == 'APPROVED' and claim.method == 'delivery':
        send_notification(**payload, role_target='VOLUNTEER', event_key=key+'-pool')


class CommunityFoodViewSet(viewsets.GenericViewSet):
    permission_classes = [ActiveAccount]
    serializer_class = ClaimSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        qs = FoodClaim.objects.select_related('resource__provider', 'recipient', 'volunteer__user').prefetch_related('events')
        if user.is_coordinator:
            return qs
        scope = Q(recipient=user)
        if user.is_food_provider:
            scope |= Q(resource__provider__memberships__user=user, resource__provider__memberships__is_active=True)
        if user.is_volunteer:
            scope |= Q(volunteer__user=user) | Q(status='APPROVED', method='delivery')
        return qs.filter(scope).distinct()

    def list(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=False, methods=['get', 'put'])
    def location(self, request):
        location = PersonalLocation.objects.filter(user=request.user).first()
        if request.method == 'GET':
            return Response(LocationSerializer(location).data if location else None)
        serializer = LocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        location, _ = PersonalLocation.objects.update_or_create(user=request.user, defaults=serializer.validated_data)
        return Response(LocationSerializer(location).data)

    @action(detail=False, methods=['get'])
    def offers(self, request):
        location = PersonalLocation.objects.filter(user=request.user).first()
        resources = Resource.objects.select_related('provider').filter(is_disaster_relief=False, disaster_event__isnull=True, provider__verified=True, status='AVAILABLE', quantity__gt=F('allocated_quantity'), safe_until__gt=timezone.now()+timedelta(hours=2), pickup_end__gt=timezone.now())
        results = []
        for resource in resources:
            if not resource.is_food:
                continue
            distance = None
            if location:
                try:
                    distance = check_food(resource, location.latitude, location.longitude, reserve=True)
                except ValidationError:
                    continue
            if provider_member(request.user, resource):
                continue
            results.append(dict(id=resource.pk, name=resource.name, providerName=resource.provider.name, availableQuantity=resource.available_quantity, unit=resource.unit, pickupAddress=resource.pickup_address or resource.provider.address, pickupStart=resource.pickup_start, pickupEnd=resource.pickup_end, safeUntil=resource.safe_until, storageRequirements=resource.storage_requirements, safetyNotes=resource.safety_notes, dietaryTags=resource.dietary_tags, distanceKm=distance))
        return Response(sorted(results, key=lambda row: row['distanceKm'] or 0))

    @transaction.atomic
    def create(self, request):
        location = PersonalLocation.objects.filter(user=request.user).first()
        if not location:
            raise ValidationError('Save your location before requesting food.')
        resource = get_object_or_404(Resource.objects.select_for_update(), pk=request.data.get('resource'))
        if provider_member(request.user, resource) or resource.created_by_id == request.user.pk:
            raise ValidationError('You cannot claim your own donation.')
        if FoodClaim.objects.filter(resource=resource, recipient=request.user).exclude(status__in=['REJECTED', 'CANCELLED']).exists():
            return Response({'detail': 'You already requested this offer.'}, status=409)
        check_food(resource, location.latitude, location.longitude, reserve=True)
        class Input(serializers.Serializer):
            quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'), default=Decimal('1'))
            method = serializers.ChoiceField(choices=['delivery', 'pickup'], default='delivery')
            safetyAcknowledged = serializers.BooleanField()
        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        if not data.validated_data['safetyAcknowledged']:
            raise ValidationError('Confirm that you can follow the food safety and storage instructions.')
        quantity = data.validated_data['quantity']
        if quantity > Decimal(str(resource.available_quantity)):
            raise ValidationError('Requested quantity exceeds available food.')
        if data.validated_data['method'] == 'delivery' and resource.unit != 'kg':
            raise ValidationError('Volunteer capacity is measured in kg. Please select authorized pickup for this offer.')
        claim = FoodClaim.objects.create(resource=resource, recipient=request.user, quantity=quantity, method=data.validated_data['method'], address=location.address, latitude=location.latitude, longitude=location.longitude)
        resource.allocated_quantity = round(resource.allocated_quantity + float(quantity), 2)
        resource.save()
        record(claim, request.user)
        return Response(self.get_serializer(claim).data, status=201)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def transition(self, request, pk=None):
        # Always lock inventory before claim, including competing requests and cancellations.
        visible = self.get_object()
        resource = Resource.objects.select_for_update().get(pk=visible.resource_id)
        claim = FoodClaim.objects.select_for_update(of=('self',)).select_related('recipient', 'volunteer__user').get(pk=visible.pk)
        claim.resource = resource
        user = request.user
        target = request.data.get('status')
        owner = claim.recipient_id == user.pk
        provider = provider_member(user, resource)
        courier = bool(claim.volunteer_id and claim.volunteer.user_id == user.pk and user.is_volunteer)
        coordinator = user.is_coordinator
        allowed = False
        if target in ['APPROVED', 'REJECTED']:
            allowed = coordinator and claim.status == 'PENDING'
            if allowed and target == 'APPROVED':
                if not claim.recipient.is_active or claim.recipient.status != 'active':
                    raise ValidationError('Recipient account is no longer eligible.')
                check_food(resource, claim.latitude, claim.longitude, approval=True)
                claim.approved_by = user
                if claim.method == 'pickup':
                    claim.pickup_code = secrets.token_hex(6)
        elif target == 'CANCELLED':
            allowed = (owner or coordinator) and claim.status in ['PENDING', 'APPROVED', 'ASSIGNED']
        elif target == 'ASSIGNED':
            allowed = user.is_volunteer and not owner and not provider and claim.status == 'APPROVED' and claim.method == 'delivery'
            if allowed:
                volunteer = Volunteer.objects.select_for_update().filter(user=user, verified=True, status='available').first()
                if not volunteer:
                    raise ValidationError('A verified, available volunteer profile is required.')
                # Capacity is measured in kg; other units require coordinator dispatch policy.
                if resource.unit != 'kg' or float(claim.quantity) > volunteer.vehicle_capacity_kg:
                    raise ValidationError('Mission exceeds vehicle capacity or uses an unsupported weight unit; choose authorized pickup.')
                check_food(resource, claim.latitude, claim.longitude)
                claim.volunteer = volunteer
                volunteer.status = 'busy'
                volunteer.save(update_fields=['status'])
        elif target == 'PICKED_UP':
            allowed = (claim.status == 'ASSIGNED' and (provider or courier or coordinator)) or (claim.status == 'APPROVED' and claim.method == 'pickup' and (provider or coordinator))
            if allowed:
                check_food(resource, claim.latitude, claim.longitude)
                if timezone.now() < resource.pickup_start:
                    raise ValidationError('The pickup window has not opened yet.')
                if request.data.get('safetyAcknowledged') is not True:
                    raise ValidationError('Confirm safe handling before handover.')
                if claim.method == 'pickup' and not secrets.compare_digest(str(request.data.get('pickupCode', '')), claim.pickup_code):
                    raise ValidationError('Enter the pickup code shown to the approved recipient.')
        elif target == 'DELIVERED':
            allowed = claim.method == 'delivery' and claim.status == 'PICKED_UP' and (courier or coordinator)
            if allowed and (not resource.safe_until or resource.safe_until <= timezone.now()):
                raise ValidationError('Food has expired; contact the coordinator for safe disposal.')
        elif target == 'RECEIVED':
            allowed = owner and (claim.status == 'DELIVERED' or (claim.method == 'pickup' and claim.status == 'PICKED_UP'))
        if not allowed:
            raise PermissionDenied('This action is not permitted for your account or the current request status.')
        if target in ['REJECTED', 'CANCELLED']:
            resource.allocated_quantity = round(max(0, resource.allocated_quantity-float(claim.quantity)), 2)
            if resource.status == 'RESERVED' and resource.available_quantity > 0:
                resource.status = 'AVAILABLE'
            resource.save()
        if target in ['CANCELLED', 'DELIVERED'] and claim.volunteer_id:
            volunteer = Volunteer.objects.select_for_update().get(pk=claim.volunteer_id)
            volunteer.status = 'available'
            if target == 'DELIVERED':
                volunteer.completed_deliveries_count += 1
            volunteer.save()
        claim.status = target
        claim.save()
        record(claim, user)
        return Response(self.get_serializer(claim).data)
