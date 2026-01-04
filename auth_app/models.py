from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from .lookups import CountryLookup


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('user_type', 'ADMIN')
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('PATIENT', 'Patient'),
        ('DONOR', 'Donor'),
        ('ADMIN', 'Admin'),
    )
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, help_text="Phone number with country code")
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True, help_text="User profile picture")
    
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_patient_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    # Email verification fields
    email_verification_token = models.CharField(max_length=255, blank=True, null=True, help_text="Token for email verification")
    email_verification_sent_at = models.DateTimeField(blank=True, null=True, help_text="When verification email was sent")
    
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email
    
    def __str__(self):
        return self.email


class FinancialReport(models.Model):
    """
    Financial transparency reports that admin can upload.
    One report can be marked as public for community viewing.
    """
    title = models.CharField(max_length=255, help_text="Report title (e.g., 'Q1 2026 Financial Report')")
    description = models.TextField(blank=True, help_text="Brief description of the report")
    document = models.FileField(
        upload_to='financial_reports/',
        blank=True,
        null=True,
        help_text="Excel or PDF financial report document (optional if google_doc_url is provided)"
    )
    google_doc_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Google Doc/Drive link to financial report (optional if document file is uploaded)"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Mark as public for community transparency. Only one report can be public at a time."
    )
    
    uploaded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_reports',
        limit_choices_to={'user_type': 'ADMIN'}
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Financial Report'
        verbose_name_plural = 'Financial Reports'
    
    def __str__(self):
        public_label = " [PUBLIC]" if self.is_public else ""
        return f"{self.title}{public_label}"
    
    def save(self, *args, **kwargs):
        # If this report is being marked as public, unmark all other reports
        if self.is_public:
            FinancialReport.objects.filter(is_public=True).exclude(pk=self.pk).update(is_public=False)
        super().save(*args, **kwargs)
