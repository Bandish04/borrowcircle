import uuid
import secrets
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier for authentication."""
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        MEMBER = 'member', 'Member'
        MODERATOR = 'moderator', 'Moderator'
        ADMIN = 'admin', 'Admin'

    class AccountStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'
        BANNED = 'banned', 'Banned'
        DEACTIVATED = 'deactivated', 'Deactivated'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True)

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    account_status = models.CharField(max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE)

    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"


class OTPVerification(models.Model):
    """Stores OTP codes for email verification and password reset."""

    class OTPType(models.TextChoices):
        EMAIL_VERIFY = 'email_verify', 'Email Verification'
        PASSWORD_RESET = 'password_reset', 'Password Reset'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_type = models.CharField(max_length=20, choices=OTPType.choices)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_otp():
        """Generate a cryptographically secure 6-digit OTP code."""
        return str(secrets.randbelow(900000) + 100000)

    @classmethod
    def create_for_user(cls, user, otp_type):
        """Create a new OTP for a user, invalidating any previous ones."""
        # Invalidate all previous OTPs of same type for this user
        cls.objects.filter(user=user, otp_type=otp_type, is_used=False).update(is_used=True)

        return cls.objects.create(
            user=user,
            otp_type=otp_type,
            code=cls.generate_otp(),
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def is_valid(self):
        """Check if OTP is still valid (not used and not expired)."""
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP {self.code} for {self.user.email} ({self.otp_type})"


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, max_length=500)
    city = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.email}"


class ReliabilitySummary(models.Model):
    """Transparent trust summary instead of a hidden star rating."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reliability')
    completed_loans = models.PositiveIntegerField(default=0)
    on_time_returns = models.PositiveIntegerField(default=0)
    late_returns = models.PositiveIntegerField(default=0)
    cancellations = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reliability for {self.user.email}: {self.completed_loans} completed"