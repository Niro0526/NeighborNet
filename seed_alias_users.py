import os
import sys
import django

sys.path.insert(0, os.path.abspath('backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User, RoleAssignment, RoleChoices, RoleStatusChoices
from apps.volunteers.models import Volunteer, VehicleTypeChoices, VolunteerAvailabilityChoices

users_to_add = [
    {
        'email': 'admin@neighbornet.org',
        'full_name': 'Administrator (Coordinator + Volunteer)',
        'first_name': 'System',
        'last_name': 'Admin',
        'phone': '+94 11 200 0001',
        'roles': [RoleChoices.COORDINATOR, RoleChoices.VOLUNTEER],
        'default_workspace': 'admin',
    },
    {
        'email': 'coordinator@neighbornet.org',
        'full_name': 'Sarah Chen (Disaster Coordinator)',
        'first_name': 'Sarah',
        'last_name': 'Chen',
        'phone': '+94 11 200 0002',
        'roles': [RoleChoices.COORDINATOR, RoleChoices.VOLUNTEER],
        'default_workspace': 'admin',
    },
    {
        'email': 'volunteer@neighbornet.org',
        'full_name': 'David Kim (Volunteer Courier)',
        'first_name': 'David',
        'last_name': 'Kim',
        'phone': '+94 77 000 0003',
        'roles': [RoleChoices.VOLUNTEER],
        'default_workspace': 'personal',
    },
    {
        'email': 'provider@neighbornet.org',
        'full_name': 'Marcus Vance (Food Provider)',
        'first_name': 'Marcus',
        'last_name': 'Vance',
        'phone': '+94 77 000 0004',
        'roles': [RoleChoices.FOOD_PROVIDER],
        'default_workspace': 'personal',
    },
    {
        'email': 'recipient@neighbornet.org',
        'full_name': 'Elena Rostova (Recipient NGO)',
        'first_name': 'Elena',
        'last_name': 'Rostova',
        'phone': '+94 77 000 0005',
        'roles': [RoleChoices.RECIPIENT],
        'default_workspace': 'personal',
    },
    {
        'email': 'multirole@neighbornet.org',
        'full_name': 'Amina Patel (Multi-Role)',
        'first_name': 'Amina',
        'last_name': 'Patel',
        'phone': '+94 77 000 0006',
        'roles': [RoleChoices.COORDINATOR, RoleChoices.VOLUNTEER, RoleChoices.FOOD_PROVIDER],
        'default_workspace': 'personal',
    },
]

for data in users_to_add:
    roles = data.pop('roles')
    user, created = User.objects.get_or_create(
        email=data['email'],
        defaults={
            'username': data['email'],
            'full_name': data['full_name'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'phone': data['phone'],
            'default_workspace': data['default_workspace'],
            'status': 'active',
            'is_staff': True,
        }
    )
    user.set_password('password123')
    user.is_active = True
    user.is_staff = True
    user.save()

    for role in roles:
        RoleAssignment.objects.get_or_create(
            user=user,
            role=role,
            defaults={
                'status': RoleStatusChoices.APPROVED,
                'reviewed_by': user,
            }
        )

    if RoleChoices.VOLUNTEER in roles:
        Volunteer.objects.get_or_create(
            user=user,
            defaults={
                'vehicle_type': VehicleTypeChoices.MOTORCYCLE,
                'max_capacity_kg': 35.0,
                'has_thermal_box': True,
                'has_refrigeration': False,
                'latitude': 6.795,
                'longitude': 79.885,
                'operating_radius_km': 15.0,
                'status': VolunteerAvailabilityChoices.AVAILABLE,
                'verified': True,
            }
        )

    print(f"User {user.email} verified with roles: {roles}")
