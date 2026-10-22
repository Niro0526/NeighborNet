import os
import sys
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from apps.accounts.models import User, UserRoleAssignment, RoleChoices, UserStatusChoices
from apps.organizations.models import Organization, OrganizationTypeChoices, OrganizationMembership, MembershipRoleChoices
from apps.resources.models import Resource, ResourceCategoryChoices, ResourceStatusChoices, StorageRequirementChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices, VehicleTypeChoices
from apps.deliveries.models import (
    Allocation, AllocationStatusChoices,
    DeliveryTask, DeliveryTaskStatusChoices,
    DeliveryStatusEvent
)
from apps.audit.models import ActivityLog, AuditCategoryChoices, PilotFeedback, PilotFeedbackCategoryChoices
from apps.notifications.services import send_notification

class Command(BaseCommand):
    help = "Seeds isolated synthetic pilot demonstration data with safety guards against production execution."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-demo',
            action='store_true',
            help='Override production safeguard to run demo setup.',
        )

    def handle(self, *args, **options):
        from common.synthetic_data import require_synthetic_database
        require_synthetic_database()
        # 1. Production Safeguard
        is_production = not getattr(settings, 'DEBUG', True)
        if is_production and not options['force_demo']:
            self.stderr.write(
                self.style.ERROR(
                    "SAFETY RESTRICTION: Automatic synthetic demo seeding is disabled in production environments.\n"
                    "Use --force-demo only in isolated staging or testing instances."
                )
            )
            sys.exit(1)

        self.stdout.write(self.style.NOTICE("Initializing Isolated Pilot Demonstration Dataset..."))
        now = timezone.now()

        with transaction.atomic():
            # 2. Coordinator Account
            coord_user, _ = User.objects.get_or_create(
                email="coordinator.demo@neighbornet.lk",
                defaults={
                    'full_name': "Dr. Kaveen Silva",
                    'phone': "+94 77 123 4567",
                    'status': UserStatusChoices.ACTIVE,
                    'default_workspace': 'admin'
                }
            )
            coord_user.set_password("DemoCoordPass123!")
            coord_user.save()
            UserRoleAssignment.objects.get_or_create(
                user=coord_user,
                role=RoleChoices.COORDINATOR,
                defaults={'is_approved': True}
            )

            # 3. Verified Food Provider
            provider_user, _ = User.objects.get_or_create(
                email="provider.demo@neighbornet.lk",
                defaults={
                    'full_name': "Ravi Mendis (GreenBites)",
                    'phone': "+94 71 234 5678",
                    'status': UserStatusChoices.ACTIVE,
                }
            )
            provider_user.set_password("DemoProvider123!")
            provider_user.save()
            UserRoleAssignment.objects.get_or_create(
                user=provider_user,
                role=RoleChoices.FOOD_PROVIDER,
                defaults={'is_approved': True}
            )

            provider_org, _ = Organization.objects.get_or_create(
                name="[DEMO] GreenBites Bakery & Kitchen",
                defaults={
                    'type': OrganizationTypeChoices.BAKERY,
                    'registration_number': "PV-DEMO-99120",
                    'verified': True,
                    'verified_by': coord_user,
                    'verified_at': now - timedelta(days=5),
                    'contact_email': "provider.demo@neighbornet.lk",
                    'contact_phone': "+94 11 264 5500",
                    'address': "No. 42, Galle Road, Rawathawatte",
                    'city': "Moratuwa",
                    'postal_code': "10400",
                    'latitude': 6.7820,
                    'longitude': 79.8825,
                    'capacity': 120,
                    'operating_hours': "07:00 - 20:00",
                    'service_area': "Moratuwa & Mount Lavinia",
                    'description': "Artisanal bakery and hot community food donor."
                }
            )
            OrganizationMembership.objects.get_or_create(
                organization=provider_org,
                user=provider_user,
                defaults={'role': MembershipRoleChoices.OWNER}
            )

            # 4. Verified Recipient NGO
            recipient_user, _ = User.objects.get_or_create(
                email="recipient.demo@neighbornet.lk",
                defaults={
                    'full_name': "Sister Anoma (Hope Center)",
                    'phone': "+94 76 345 6789",
                    'status': UserStatusChoices.ACTIVE,
                }
            )
            recipient_user.set_password("DemoRecipient123!")
            recipient_user.save()
            UserRoleAssignment.objects.get_or_create(
                user=recipient_user,
                role=RoleChoices.RECIPIENT,
                defaults={'is_approved': True}
            )

            recipient_org, _ = Organization.objects.get_or_create(
                name="[DEMO] Hope Community Center",
                defaults={
                    'type': OrganizationTypeChoices.SHELTER,
                    'registration_number': "NGO-DEMO-44321",
                    'verified': True,
                    'verified_by': coord_user,
                    'verified_at': now - timedelta(days=4),
                    'contact_email': "recipient.demo@neighbornet.lk",
                    'contact_phone': "+94 11 265 1122",
                    'address': "No. 18, Dehiwala Canal Road",
                    'city': "Dehiwala-Mount Lavinia",
                    'postal_code': "10350",
                    'latitude': 6.8410,
                    'longitude': 79.8730,
                    'capacity': 250,
                    'operating_hours': "24 Hours Emergency Intake",
                    'service_area': "Dehiwala & Ratmalana Municipal Area",
                    'description': "Children's evening nutrition program and emergency shelter."
                }
            )
            OrganizationMembership.objects.get_or_create(
                organization=recipient_org,
                user=recipient_user,
                defaults={'role': MembershipRoleChoices.OWNER}
            )

            # 5. Verified Volunteer Courier
            volunteer_user, _ = User.objects.get_or_create(
                email="courier.demo@neighbornet.lk",
                defaults={
                    'full_name': "Kasun Perera",
                    'phone': "+94 72 456 7890",
                    'status': UserStatusChoices.ACTIVE,
                }
            )
            volunteer_user.set_password("DemoCourier123!")
            volunteer_user.save()
            UserRoleAssignment.objects.get_or_create(
                user=volunteer_user,
                role=RoleChoices.VOLUNTEER,
                defaults={'is_approved': True}
            )
            vol_profile, _ = Volunteer.objects.get_or_create(
                user=volunteer_user,
                defaults={
                    'status': VolunteerAvailabilityChoices.AVAILABLE,
                    'vehicle_type': VehicleTypeChoices.MOTORCYCLE,
                    'vehicle_capacity_kg': 25.0,
                    'completed_deliveries_count': 18,
                    'rating': 4.9,
                    'verified': True,
                    'verified_by': coord_user,
                    'verified_at': now - timedelta(days=7),
                    'service_area': "Moratuwa & Colombo South Corridors",
                    'badge': "Top Responder"
                }
            )

            # 6. Sample Food Resource Listing
            bread_lot, _ = Resource.objects.get_or_create(
                name="[DEMO] Surplus Whole-Wheat Bread & Buns",
                provider=provider_org,
                defaults={
                    'created_by': provider_user,
                    'category': ResourceCategoryChoices.BAKERY,
                    'quantity': 35.0,
                    'allocated_quantity': 20.0,
                    'unit': 'kg',
                    'pickup_start': now,
                    'pickup_end': now + timedelta(hours=6),
                    'safe_until': now + timedelta(hours=14),
                    'storage_requirements': StorageRequirementChoices.AMBIENT,
                    'status': ResourceStatusChoices.AVAILABLE,
                    'dietary_tags': ['Vegetarian', 'Halal'],
                    'safety_notes': "Freshly packaged at noon. Safe consumption window verified."
                }

            )

            # 7. Sample Requisition Request
            shelter_req, _ = ResourceRequest.objects.get_or_create(
                item_name="[DEMO] Evening Community Dinner Bakery Rations",
                recipient=recipient_org,
                defaults={
                    'created_by': recipient_user,
                    'category': ResourceCategoryChoices.BAKERY,
                    'requested_quantity': 20.0,
                    'fulfilled_quantity': 20.0,
                    'unit': 'kg',
                    'priority': RequestPriorityChoices.HIGH,
                    'status': RequestStatusChoices.ALLOCATED,
                    'people_impacted': 45,
                    'urgency_deadline': now + timedelta(hours=4),
                    'delivery_address': recipient_org.address,
                    'special_instructions': "Please deliver to back kitchen intake dock."
                }
            )

            # 8. Sample Allocation & Delivery Task with Event History
            allocation, _ = Allocation.objects.get_or_create(
                resource=bread_lot,
                request=shelter_req,
                defaults={
                    'allocated_quantity': 20.0,
                    'status': AllocationStatusChoices.APPROVED,
                    'created_by': coord_user,
                    'approved_by': coord_user
                }
            )

            task, _ = DeliveryTask.objects.get_or_create(
                allocation=allocation,
                resource=bread_lot,
                request=shelter_req,
                defaults={
                    'title': "[DEMO] Bakery Surplus Distribution -> Hope Center",
                    'cargo_description': "Surplus Whole-Wheat Bread (20.0 kg)",
                    'quantity': 20.0,
                    'unit': 'kg',
                    'status': DeliveryTaskStatusChoices.DELIVERED,
                    'priority': RequestPriorityChoices.HIGH,
                    'volunteer': vol_profile,
                    'pickup_address': provider_org.address,
                    'delivery_address': recipient_org.address,
                    'delivery_deadline': now + timedelta(hours=4),
                    'accepted_at': now - timedelta(minutes=90),
                    'arrived_pickup_at': now - timedelta(minutes=70),
                    'picked_up_at': now - timedelta(minutes=55),
                    'arrived_delivery_at': now - timedelta(minutes=25),
                    'delivered_at': now - timedelta(minutes=15),
                }
            )

            # 9. Append-only Status History Events
            if not task.status_events.exists():
                DeliveryStatusEvent.objects.create(
                    delivery_task=task,
                    from_status='INITIAL',
                    to_status=DeliveryTaskStatusChoices.AVAILABLE,
                    changed_by=coord_user,
                    notes="Task dispatched to courier fleet.",
                    created_at=now - timedelta(minutes=100)
                )
                DeliveryStatusEvent.objects.create(
                    delivery_task=task,
                    from_status=DeliveryTaskStatusChoices.AVAILABLE,
                    to_status=DeliveryTaskStatusChoices.ACCEPTED,
                    changed_by=volunteer_user,
                    notes="Mission accepted by courier Kasun Perera.",
                    created_at=now - timedelta(minutes=90)
                )
                DeliveryStatusEvent.objects.create(
                    delivery_task=task,
                    from_status=DeliveryTaskStatusChoices.ACCEPTED,
                    to_status=DeliveryTaskStatusChoices.ARRIVED_PICKUP,
                    changed_by=volunteer_user,
                    notes="Courier arrived at GreenBites bakery.",
                    created_at=now - timedelta(minutes=70)
                )
                DeliveryStatusEvent.objects.create(
                    delivery_task=task,
                    from_status=DeliveryTaskStatusChoices.ARRIVED_PICKUP,
                    to_status=DeliveryTaskStatusChoices.PICKED_UP,
                    changed_by=volunteer_user,
                    notes="Cargo inspected and securely loaded on courier carrier.",
                    created_at=now - timedelta(minutes=55)
                )
                DeliveryStatusEvent.objects.create(
                    delivery_task=task,
                    from_status=DeliveryTaskStatusChoices.PICKED_UP,
                    to_status=DeliveryTaskStatusChoices.ARRIVED_DELIVERY,
                    changed_by=volunteer_user,
                    notes="Courier arrived at Hope Community Center.",
                    created_at=now - timedelta(minutes=25)
                )
                DeliveryStatusEvent.objects.create(
                    delivery_task=task,
                    from_status=DeliveryTaskStatusChoices.ARRIVED_DELIVERY,
                    to_status=DeliveryTaskStatusChoices.DELIVERED,
                    changed_by=volunteer_user,
                    notes="Shelter staff verified 20.0 kg rations intact. Safe delivery confirmed.",
                    created_at=now - timedelta(minutes=15)
                )

            # 10. Sample Pilot Feedback Records
            PilotFeedback.objects.get_or_create(
                user=provider_user,
                category=PilotFeedbackCategoryChoices.FOOD_LISTING,
                defaults={
                    'user_name': provider_user.name,
                    'user_role': 'FOOD_PROVIDER',
                    'rating': 5,
                    'comments': "Listing excess bakery stock takes under 60 seconds. Expiry countdown is very clear.",
                    'consent_to_share_internally': True
                }
            )
            PilotFeedback.objects.get_or_create(
                user=recipient_user,
                category=PilotFeedbackCategoryChoices.REQUESTING_RESOURCES,
                defaults={
                    'user_name': recipient_user.name,
                    'user_role': 'RECIPIENT',
                    'rating': 5,
                    'comments': "The request category selection and urgency deadline matching work reliably.",
                    'consent_to_share_internally': True
                }
            )
            PilotFeedback.objects.get_or_create(
                user=volunteer_user,
                category=PilotFeedbackCategoryChoices.DELIVERY_WORKFLOW,
                defaults={
                    'user_name': volunteer_user.name,
                    'user_role': 'VOLUNTEER',
                    'rating': 4,
                    'comments': "Step-by-step state machine with arrived pickup and delivery timestamps is clean and unambiguous.",
                    'consent_to_share_internally': True
                }
            )

        self.stdout.write(self.style.SUCCESS("[OK] Isolated Pilot Demonstration Dataset successfully initialized!"))

