from django.db import models
from django.conf import settings
from datetime import date
from auth_app.lookups import CountryLookup


class DonorProfile(models.Model):
    """Extended profile for donors"""
    # Relationship
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donor_profile')
    
    # Profile Information
    photo = models.ImageField(upload_to='donor_photos/', null=True, blank=True, help_text="Profile photo")
    full_name = models.CharField(max_length=200, blank=True, help_text="Full name for display")
    short_bio = models.CharField(max_length=60, blank=True, help_text="Short bio (max 60 characters)")
    country_fk = models.ForeignKey(CountryLookup, on_delete=models.PROTECT, null=True, blank=True, related_name='donors', db_column='country_id')  # References country_id column in DB
    website = models.URLField(max_length=200, blank=True)
    birthday = models.DateField(null=True, blank=True)
    workplace = models.CharField(max_length=200, blank=True)
    
    # Privacy
    is_profile_private = models.BooleanField(default=False, help_text="Make profile visible only to you")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_app_donorprofile'  # Keep existing table name
    
    def __str__(self):
        return f"{self.full_name or self.user.email} - Donor Profile"
    
    @property
    def age(self):
        """Calculate age from birthday"""
        if self.birthday:
            today = date.today()
            return today.year - self.birthday.year - (
                (today.month, today.day) < (self.birthday.month, self.birthday.day)
            )
        return None
