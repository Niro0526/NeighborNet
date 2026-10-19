from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User, UserRoleAssignment, RoleChoices
from apps.organizations.models import Organization, OrganizationMembership, OrganizationTypeChoices, MembershipRoleChoices
from apps.resources.models import Resource, ResourceCategoryChoices, ResourceStatusChoices, StorageRequirementChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices, VehicleTypeChoices
from apps.deliveries.models import Allocation, AllocationStatusChoices, DeliveryTask, DeliveryTaskStatusChoices
from apps.disasters.models import DisasterEvent, DisasterStatusChoices, DisasterTypeChoices, DisasterSeverityChoices
from apps.notifications.models import Notification
from apps.audit.models import ActivityLog, AuditCategoryChoices

class Command(BaseCommand):
    help = 'Idempotently seeds fictional Sri Lankan demo entities matching frontend personas (ModelX 2.0).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force seeding even if DEBUG=False',
        )

    def handle(self, *args, **options):
        from django.conf import settings
        if not settings.DEBUG and not options.get('force'):
            self.stderr.write(self.style.ERROR(
                'Safety check: seed_demo command is disabled in production environments (DEBUG=False).'
            ))
            return

        self.stdout.write(self.style.NOTICE('Starting NeighborNet AI development database seeding...'))

        now = timezone.now()

        # 1. Seed Users (7 Scenarios)
        users_data = [
            {
                'id': 'USR-001',
                'email': 'ravi.mendis@greenbites.lk',
                'full_name': 'Ravi Mendis',
                'first_name': 'Ravi',
                'last_name': 'Mendis',
                'phone': '+94 77 123 4567',
                'roles': [RoleChoices.FOOD_PROVIDER, RoleChoices.VOLUNTEER],
                'default_workspace': 'personal',
                'avatar_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
            },
            {
                'id': 'USR-002',
                'email': 'fathima@pererahotels.lk',
                'full_name': 'Fathima Rizwan',
                'first_name': 'Fathima',
                'last_name': 'Rizwan',
                'phone': '+94 71 456 7890',
                'roles': [RoleChoices.FOOD_PROVIDER],
                'default_workspace': 'personal',
                'avatar_url': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150',
            },
            {
                'id': 'USR-003',
                'email': 'sister.mary@graceeldercare.org',
                'full_name': 'Sister Mary Teresa',
                'first_name': 'Mary',
                'last_name': 'Teresa',
                'phone': '+94 11 264 5589',
                'roles': [RoleChoices.RECIPIENT],
                'default_workspace': 'personal',
                'avatar_url': 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150',
            },
            {
                'id': 'USR-004',
                'email': 'dinesh.mendis@gmail.com',
                'full_name': 'Dinesh Mendis',
                'first_name': 'Dinesh',
                'last_name': 'Mendis',
                'phone': '+94 76 987 6543',
                'roles': [RoleChoices.VOLUNTEER],
                'default_workspace': 'personal',
                'avatar_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
            },
            {
                'id': 'USR-005',
                'email': 'anuki.b@suwasetha.org',
                'full_name': 'Anuki Bandara',
                'first_name': 'Anuki',
                'last_name': 'Bandara',
                'phone': '+94 70 334 5566',
                'roles': [RoleChoices.RECIPIENT, RoleChoices.VOLUNTEER],
                'default_workspace': 'personal',
                'avatar_url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150',
            },
            {
                'id': 'USR-006',
                'email': 'kaveen.j@dmc.gov.lk',
                'full_name': 'Dr. Kaveen Jayawardena',
                'first_name': 'Kaveen',
                'last_name': 'Jayawardena',
                'phone': '+94 11 288 9900',
                'roles': [RoleChoices.COORDINATOR],
                'default_workspace': 'admin',
                'avatar_url': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150',
            },
            {
                'id': 'USR-007',
                'email': 'malik.farook@redcross.lk',
                'full_name': 'Malik Farook',
                'first_name': 'Malik',
                'last_name': 'Farook',
                'phone': '+94 77 889 9001',
                'roles': [RoleChoices.COORDINATOR, RoleChoices.VOLUNTEER],
                'default_workspace': 'personal',
                'avatar_url': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
            },
        ]

        users_map = {}
        for u_data in users_data:
            roles = u_data.pop('roles')
            user, created = User.objects.get_or_create(
                id=u_data['id'],
                defaults={
                    'email': u_data['email'],
                    'username': u_data['email'],
                    'full_name': u_data['full_name'],
                    'first_name': u_data['first_name'],
                    'last_name': u_data['last_name'],
                    'phone': u_data['phone'],
                    'default_workspace': u_data['default_workspace'],
                    'avatar_url': u_data['avatar_url'],
                    'status': 'active'
                }
            )
            # Default development password
            user.set_password('password123')
            user.save()
            users_map[user.id] = user

            # Assign roles
            for role in roles:
                UserRoleAssignment.objects.get_or_create(
                    user=user,
                    role=role,
                    defaults={'is_approved': True}
                )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(users_map)} users across 7 role scenarios."))

        # 2. Seed Disaster Event
        disaster, _ = DisasterEvent.objects.get_or_create(
            id='DIS-001',
            defaults={
                'title': 'Monsoon Flash Floods — Colombo South & Moratuwa Basin',
                'description': 'Severe rainfall over the Kelani/Bolgoda catchments triggered localized inundation in Moratuwa lowlands. Rapid distribution of drinking water, ready-to-eat meals, and dry rations prioritized.',
                'disaster_type': DisasterTypeChoices.FLOOD,
                'severity': DisasterSeverityChoices.CRITICAL,
                'status': DisasterStatusChoices.ACTIVE,
                'affected_location': 'Moratuwa & Colombo South Lowlands (Bolgoda Lake Basin)',
                'affected_population': 4800,
                'declared_at': now - timedelta(hours=6),
                'declared_by': users_map['USR-006']
            }
        )

        # 3. Seed Organizations
        orgs_data = [
            {
                'id': 'ORG-001',
                'name': 'GreenBites Bakery & Cafe',
                'type': OrganizationTypeChoices.BAKERY,
                'registration_number': 'PV-109283-LK',
                'verified': True,
                'contact_email': 'hello@greenbites.lk',
                'contact_phone': '+94 11 265 0101',
                'address': '248 Galle Road, Katubedda, Moratuwa',
                'city': 'Moratuwa',
                'postal_code': '10400',
                'latitude': 6.7972,
                'longitude': 79.8884,
                'operating_hours': '06:30 - 21:00',
                'description': 'Artisan bakery producing freshly baked sourdough, rotis, and wholesome snack boxes.',
                'owner': users_map['USR-001'],
            },
            {
                'id': 'ORG-002',
                'name': 'Perera Grand Catering & Hotel',
                'type': OrganizationTypeChoices.HOTEL,
                'registration_number': 'PV-894721-LK',
                'verified': True,
                'contact_email': 'operations@pererahotels.lk',
                'contact_phone': '+94 11 243 8900',
                'address': '12 Marine Drive, Colombo 03',
                'city': 'Colombo',
                'postal_code': '00300',
                'latitude': 6.9012,
                'longitude': 79.8529,
                'operating_hours': '24 Hours',
                'description': 'Leading hotel and buffet kitchen with regular daily banquet surpluses.',
                'owner': users_map['USR-002'],
            },
            {
                'id': 'ORG-003',
                'name': 'Grace Home for the Elderly',
                'type': OrganizationTypeChoices.SHELTER,
                'registration_number': 'NGO-44321-SL',
                'verified': True,
                'contact_email': 'admin@graceeldercare.org',
                'contact_phone': '+94 11 264 5589',
                'address': '84 Lunawa Station Road, Moratuwa',
                'city': 'Moratuwa',
                'postal_code': '10400',
                'latitude': 6.7824,
                'longitude': 79.8841,
                'capacity': 85,
                'operating_hours': '07:00 - 19:00',
                'description': 'Residential elderly community shelter housing 65 permanent senior residents.',
                'owner': users_map['USR-003'],
            },
            {
                'id': 'ORG-004',
                'name': 'Suwasetha Child Development Center',
                'type': OrganizationTypeChoices.NGO,
                'registration_number': 'NGO-99812-SL',
                'verified': True,
                'contact_email': 'shelter@suwasetha.org',
                'contact_phone': '+94 11 271 3344',
                'address': '15 Ferry Road, Ratmalana',
                'city': 'Ratmalana',
                'postal_code': '10390',
                'latitude': 6.8189,
                'longitude': 79.8821,
                'capacity': 120,
                'operating_hours': '08:00 - 18:00',
                'description': 'Community children center and temporary flood evacuation outpost.',
                'owner': users_map['USR-005'],
            },
            {
                'id': 'ORG-005',
                'name': 'Disaster Management Center (DMC) Moratuwa Unit',
                'type': OrganizationTypeChoices.GOVERNMENT_DISASTER_DESK,
                'registration_number': 'GOV-DMC-04',
                'verified': True,
                'contact_email': 'moratuwa@dmc.gov.lk',
                'contact_phone': '+94 11 288 9900',
                'address': 'Divisional Secretariat, Moratuwa',
                'city': 'Moratuwa',
                'postal_code': '10400',
                'latitude': 6.7730,
                'longitude': 79.8816,
                'capacity': 5000,
                'description': 'Government regional command post coordinating multi-agency flood response.',
                'owner': users_map['USR-006'],
            },
        ]

        orgs_map = {}
        for o_data in orgs_data:
            owner = o_data.pop('owner')
            org, _ = Organization.objects.get_or_create(
                id=o_data['id'],
                defaults=o_data
            )
            orgs_map[org.id] = org
            OrganizationMembership.objects.get_or_create(
                organization=org,
                user=owner,
                defaults={'role': MembershipRoleChoices.OWNER, 'is_active': True}
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(orgs_map)} organizations."))

        # 4. Seed Resources (Surplus Food & Emergency Supplies)
        resources_data = [
            {
                'id': 'RES-001',
                'provider': orgs_map['ORG-001'],
                'name': 'Artisan Sourdough & Sandwich Bread',
                'category': ResourceCategoryChoices.BAKERY,
                'quantity': 35.0,
                'unit': 'kg',
                'pickup_start': now + timedelta(hours=1),
                'pickup_end': now + timedelta(hours=5),
                'safe_until': now + timedelta(hours=24),
                'storage_requirements': StorageRequirementChoices.AMBIENT,
                'status': ResourceStatusChoices.AVAILABLE,
                'dietary_tags': ['Vegetarian', 'Vegan'],
                'safety_notes': 'Baked fresh today. Store in dry ambient conditions.',
                'created_by': users_map['USR-001']
            },
            {
                'id': 'RES-002',
                'provider': orgs_map['ORG-001'],
                'name': 'Vegetable Roti & Curry Puffs Batch',
                'category': ResourceCategoryChoices.COOKED_MEALS,
                'quantity': 60.0,
                'unit': 'meals',
                'pickup_start': now + timedelta(minutes=30),
                'pickup_end': now + timedelta(hours=3),
                'safe_until': now + timedelta(hours=8),
                'storage_requirements': StorageRequirementChoices.KEEP_WARM,
                'status': ResourceStatusChoices.AVAILABLE,
                'dietary_tags': ['Vegetarian', 'Halal'],
                'safety_notes': 'Hot holding container ready for courier insulated bag.',
                'created_by': users_map['USR-001']
            },
            {
                'id': 'RES-003',
                'provider': orgs_map['ORG-002'],
                'name': 'Steamed Rice & Dhal Banquet Packs',
                'category': ResourceCategoryChoices.COOKED_MEALS,
                'quantity': 80.0,
                'unit': 'meals',
                'pickup_start': now + timedelta(hours=2),
                'pickup_end': now + timedelta(hours=6),
                'safe_until': now + timedelta(hours=10),
                'storage_requirements': StorageRequirementChoices.KEEP_WARM,
                'status': ResourceStatusChoices.AVAILABLE,
                'dietary_tags': ['Vegetarian', 'Halal'],
                'safety_notes': 'Prepared in commercial HACCP certified banquet kitchen.',
                'created_by': users_map['USR-002']
            },
            {
                'id': 'RES-004',
                'provider': orgs_map['ORG-001'],
                'name': 'Potable Drinking Water Cans (5L Units)',
                'category': ResourceCategoryChoices.DRINKING_WATER,
                'quantity': 150.0,
                'unit': 'liters',
                'pickup_start': now,
                'pickup_end': now + timedelta(hours=12),
                'safe_until': now + timedelta(days=30),
                'storage_requirements': StorageRequirementChoices.AMBIENT,
                'status': ResourceStatusChoices.AVAILABLE,
                'is_disaster_relief': True,
                'disaster_event': disaster,
                'safety_notes': 'Factory sealed potable water cans for emergency relief.',
                'created_by': users_map['USR-001']
            },
        ]

        resources_map = {}
        for r_data in resources_data:
            res, _ = Resource.objects.get_or_create(
                id=r_data['id'],
                defaults=r_data
            )
            resources_map[res.id] = res

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(resources_map)} resources."))

        # 5. Seed Resource Requests
        requests_data = [
            {
                'id': 'REQ-001',
                'recipient': orgs_map['ORG-003'],
                'item_name': 'Hot Prepared Lunch Rations',
                'category': ResourceCategoryChoices.COOKED_MEALS,
                'requested_quantity': 65.0,
                'unit': 'meals',
                'priority': RequestPriorityChoices.HIGH,
                'status': RequestStatusChoices.OPEN,
                'people_impacted': 65,
                'urgency_deadline': now + timedelta(hours=4),
                'special_instructions': 'Senior residents require soft diet options. Gate open at Lunawa Road.',
                'created_by': users_map['USR-003']
            },
            {
                'id': 'REQ-002',
                'recipient': orgs_map['ORG-004'],
                'item_name': 'Emergency Drinking Water & Biscuits',
                'category': ResourceCategoryChoices.DRINKING_WATER,
                'requested_quantity': 100.0,
                'unit': 'liters',
                'priority': RequestPriorityChoices.URGENT,
                'status': RequestStatusChoices.OPEN,
                'people_impacted': 120,
                'urgency_deadline': now + timedelta(hours=2),
                'is_disaster_relief': True,
                'disaster_event': disaster,
                'special_instructions': 'Mains water line temporarily contaminated due to low-lying canal overflow.',
                'created_by': users_map['USR-005']
            },
        ]

        requests_map = {}
        for req_data in requests_data:
            req, _ = ResourceRequest.objects.get_or_create(
                id=req_data['id'],
                defaults=req_data
            )
            requests_map[req.id] = req

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(requests_map)} resource requests."))

        # 6. Seed Volunteers
        volunteers_data = [
            {
                'id': 'VOL-001',
                'user': users_map['USR-004'],
                'vehicle_type': VehicleTypeChoices.MOTORCYCLE,
                'vehicle_capacity_kg': 25.0,
                'status': VolunteerAvailabilityChoices.AVAILABLE,
                'verified': True,
                'completed_deliveries_count': 34,
                'rating': 4.9,
                'badge': 'Top Responder'
            },
            {
                'id': 'VOL-002',
                'user': users_map['USR-001'],
                'vehicle_type': VehicleTypeChoices.VAN,
                'vehicle_capacity_kg': 150.0,
                'status': VolunteerAvailabilityChoices.AVAILABLE,
                'verified': True,
                'completed_deliveries_count': 18,
                'rating': 4.8,
                'badge': 'Heavy Courier'
            },
            {
                'id': 'VOL-003',
                'user': users_map['USR-005'],
                'vehicle_type': VehicleTypeChoices.CAR,
                'vehicle_capacity_kg': 50.0,
                'status': VolunteerAvailabilityChoices.AVAILABLE,
                'verified': True,
                'completed_deliveries_count': 12,
                'rating': 4.9,
                'badge': 'Community Hero'
            },
            {
                'id': 'VOL-004',
                'user': users_map['USR-007'],
                'vehicle_type': VehicleTypeChoices.VAN,
                'vehicle_capacity_kg': 120.0,
                'status': VolunteerAvailabilityChoices.AVAILABLE,
                'verified': True,
                'completed_deliveries_count': 42,
                'rating': 5.0,
                'badge': 'Disaster Lead'
            },
        ]

        vols_map = {}
        for v_data in volunteers_data:
            vol, _ = Volunteer.objects.get_or_create(
                id=v_data['id'],
                defaults=v_data
            )
            vols_map[vol.id] = vol

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(vols_map)} volunteer courier profiles."))

        # 7. Seed Allocation & Delivery Tasks
        # Allocation 1: RES-001 (bread) -> REQ-001 (Grace home)
        alc, _ = Allocation.objects.get_or_create(
            id='ALC-001',
            defaults={
                'resource': resources_map['RES-001'],
                'request': requests_map['REQ-001'],
                'allocated_quantity': 20.0,
                'status': AllocationStatusChoices.APPROVED,
                'created_by': users_map['USR-006'],
                'approved_by': users_map['USR-006']
            }
        )
        resources_map['RES-001'].allocated_quantity = 20.0
        resources_map['RES-001'].save()

        # Delivery Task 1 (Active for Ravi VOL-002)
        DeliveryTask.objects.get_or_create(
            id='TSK-001',
            defaults={
                'allocation': alc,
                'resource': resources_map['RES-001'],
                'request': requests_map['REQ-001'],
                'volunteer': vols_map['VOL-002'],
                'title': 'Bakery Bread Transfer to Grace Home',
                'cargo_description': 'Artisan Sourdough & Sandwich Bread (20 kg)',
                'quantity': 20.0,
                'unit': 'kg',
                'status': DeliveryTaskStatusChoices.ACCEPTED,
                'priority': RequestPriorityChoices.HIGH,
                'pickup_address': orgs_map['ORG-001'].address,
                'delivery_address': orgs_map['ORG-003'].address,
                'pickup_contact_phone': orgs_map['ORG-001'].contact_phone,
                'delivery_contact_phone': orgs_map['ORG-003'].contact_phone,
                'pickup_time_window': '12:00 - 15:00',
                'delivery_deadline': now + timedelta(hours=3),
                'estimated_duration_min': 20,
                'is_disaster_mode': False,
                'accepted_at': now - timedelta(minutes=15)
            }
        )

        # Delivery Task 2 (Emergency Water - Available for Volunteers)
        DeliveryTask.objects.get_or_create(
            id='TSK-002',
            defaults={
                'resource': resources_map['RES-004'],
                'request': requests_map['REQ-002'],
                'title': 'Emergency Water Dispatch to Suwasetha Center',
                'cargo_description': 'Potable Drinking Water Cans (60 Liters)',
                'quantity': 60.0,
                'unit': 'liters',
                'status': DeliveryTaskStatusChoices.AVAILABLE,
                'priority': RequestPriorityChoices.URGENT,
                'pickup_address': orgs_map['ORG-001'].address,
                'delivery_address': orgs_map['ORG-004'].address,
                'pickup_contact_phone': orgs_map['ORG-001'].contact_phone,
                'delivery_contact_phone': orgs_map['ORG-004'].contact_phone,
                'pickup_time_window': 'Immediate Dispatch',
                'delivery_deadline': now + timedelta(hours=2),
                'estimated_duration_min': 25,
                'is_disaster_mode': True,
                'disaster_event': disaster
            }
        )

        # 8. Seed Initial Activity Logs
        ActivityLog.objects.get_or_create(
            id='LOG-0001',
            defaults={
                'user': users_map['USR-006'],
                'user_name': 'Dr. Kaveen Jayawardena',
                'user_role': 'COORDINATOR',
                'action': 'DISASTER_ACTIVATED',
                'details': 'Incident Commander activated emergency protocol for Bolgoda flash flood basin.',
                'category': AuditCategoryChoices.DISASTER
            }
        )
        ActivityLog.objects.get_or_create(
            id='LOG-0002',
            defaults={
                'user': users_map['USR-001'],
                'user_name': 'Ravi Mendis',
                'user_role': 'FOOD_PROVIDER',
                'action': 'FOOD_LISTED',
                'details': 'GreenBites Bakery listed 35 kg of surplus artisan sandwich bread.',
                'category': AuditCategoryChoices.FOOD
            }
        )

        self.stdout.write(self.style.SUCCESS(
            '[OK] Successfully completed idempotent seed_demo! All 7 demo personas and workflows ready.'
        ))
