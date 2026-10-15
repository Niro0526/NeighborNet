import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier for auth."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('An email address is required.'))
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', 'active')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        user = self.create_user(email, password, **extra_fields)
        # Automatically assign approved COORDINATOR role to superusers
        UserRoleAssignment.objects.create(
            user=user,
            role=RoleChoices.COORDINATOR,
            is_approved=True
        )
        return user

class RoleChoices(models.TextChoices):
    FOOD_PROVIDER = 'FOOD_PROVIDER', _('Food Provider')
    RECIPIENT = 'RECIPIENT', _('Recipient NGO / Shelter')
    VOLUNTEER = 'VOLUNTEER', _('Volunteer Courier')
    COORDINATOR = 'COORDINATOR', _('Disaster Coordinator / Admin')

class UserStatusChoices(models.TextChoices):
    ACTIVE = 'active', _('Active')
    PENDING = 'pending_verification', _('Pending Verification')
    SUSPENDED = 'suspended', _('Suspended')

def generate_user_id():
    return f"USR-{uuid.uuid4().hex[:8].upper()}"

class User(AbstractUser):
    id = models.CharField(max_length=64, primary_key=True, default=generate_user_id)
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    default_workspace = models.CharField(
        max_length=20,
        choices=[('personal', 'Personal Dashboard'), ('admin', 'Administration Workspace')],
        default='personal'
    )
    status = models.CharField(max_length=30, choices=UserStatusChoices.choices, default=UserStatusChoices.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip() or self.email.split('@')[0]
        super().save(*args, **kwargs)

    @property
    def name(self):
        return self.full_name or f"{self.first_name} {self.last_name}".strip() or self.email.split('@')[0]

    def get_approved_roles(self):
        """Returns list of approved role strings."""
        return list(
            self.role_assignments.filter(is_approved=True).values_list('role', flat=True)
        )

    def has_role(self, role: str) -> bool:
        """Check if user has an approved role."""
        if self.is_superuser and role == RoleChoices.COORDINATOR:
            return True
        return self.role_assignments.filter(role=role, is_approved=True).exists()

    @property
    def is_coordinator(self) -> bool:
        return self.is_superuser or self.has_role(RoleChoices.COORDINATOR)

    @property
    def is_food_provider(self) -> bool:
        return self.has_role(RoleChoices.FOOD_PROVIDER)

    @property
    def is_recipient(self) -> bool:
        return self.has_role(RoleChoices.RECIPIENT)

    @property
    def is_volunteer(self) -> bool:
        return self.has_role(RoleChoices.VOLUNTEER)

    def __str__(self):
        return f"{self.name} ({self.email})"

class UserRoleAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.CharField(max_length=32, choices=RoleChoices.choices)
    is_approved = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_roles'
    )
    approved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'role')
        ordering = ['role']

    def __str__(self):
        status_str = "Approved" if self.is_approved else "Pending"
        return f"{self.user.email} - {self.role} ({status_str})"
