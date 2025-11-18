from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    date_of_birth = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_patient_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return self.email


class DonorProfile(models.Model):
    """Extended profile for donors"""
    # Relationship
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='donor_profile')
    
    # Profile Information
    photo = models.ImageField(upload_to='donor_photos/', null=True, blank=True, help_text="Profile photo")
    full_name = models.CharField(max_length=200, blank=True, help_text="Full name for display")
    short_bio = models.CharField(max_length=60, blank=True, help_text="Short bio (max 60 characters)")
    country = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    birthday = models.DateField(null=True, blank=True)
    workplace = models.CharField(max_length=200, blank=True)
    
    # Privacy
    is_profile_private = models.BooleanField(default=False, help_text="Make profile visible only to you")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name or self.user.email} - Donor Profile"
    
    @property
    def age(self):
        """Calculate age from birthday"""
        if self.birthday:
            from datetime import date
            today = date.today()
            return today.year - self.birthday.year - (
                (today.month, today.day) < (self.birthday.month, self.birthday.day)
            )
        return None


class PatientProfile(models.Model):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('SCHEDULED', 'Scheduled'),
        ('PUBLISHED', 'Published'),
        ('AWAITING_FUNDING', 'Awaiting Funding'),
        ('FULLY_FUNDED', 'Fully Funded'),
        ('TREATMENT_COMPLETE', 'Treatment Complete'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Relationship
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile')
    
    # Core Info (collected during registration)
    full_name = models.CharField(max_length=200)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    country = models.CharField(max_length=100)
    
    # Story (collected during registration)
    short_description = models.CharField(max_length=255, help_text="Brief summary for card display")
    long_story = models.TextField(help_text="Detailed patient story")
    
    # Medical Details (filled by admin during verification)
    medical_partner = models.CharField(max_length=200, blank=True, help_text="Hospital/Care center name")
    diagnosis = models.TextField(blank=True)
    treatment_needed = models.TextField(blank=True, help_text="e.g., Removal of Tumor")
    treatment_date = models.DateField(null=True, blank=True)
    
    # Funding Summary (set by admin during verification)
    funding_required = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Amount RHCI raises for patient")
    funding_received = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_treatment_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total average cost including other contributions")
    cost_breakdown_notes = models.TextField(blank=True, help_text="Additional notes about cost breakdown")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature this patient on homepage"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if applicable)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.status}"
    
    @property
    def age(self):
        """Calculate age from user's date of birth"""
        if self.user.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.user.date_of_birth.year - (
                (today.month, today.day) < (self.user.date_of_birth.month, self.user.date_of_birth.day)
            )
        return 0
    
    @property
    def funding_percentage(self):
        if self.funding_required > 0:
            return round((self.funding_received / self.funding_required) * 100, 1)
        return 0
    
    @property
    def funding_remaining(self):
        return self.funding_required - self.funding_received
    
    @property
    def funding_percentage_display(self):
        """Display funding percentage as '42% of funding raised'"""
        return f"{int(self.funding_percentage)}% of funding raised"
    
    @property
    def funding_raised_display(self):
        """Display as '$266 raised'"""
        return f"${self.funding_received:,.0f} raised"
    
    @property
    def funding_remaining_display(self):
        """Display as '$365 to go'"""
        return f"${self.funding_remaining:,.0f} to go"
    
    @property
    def funding_summary(self):
        """Complete funding summary: '42% of funding raised\n$266 raised, $365 to go'"""
        return {
            'percentage': int(self.funding_percentage),
            'percentage_display': self.funding_percentage_display,
            'raised': float(self.funding_received),
            'raised_display': self.funding_raised_display,
            'remaining': float(self.funding_remaining),
            'remaining_display': self.funding_remaining_display,
            'required': float(self.funding_required),
            'summary_text': f"{self.funding_raised_display}, {self.funding_remaining_display}"
        }
    
    @property
    def cost_breakdown_total(self):
        """Calculate total from all breakdown items"""
        from django.db.models import Sum
        total = self.cost_breakdowns.aggregate(Sum('amount'))['amount__sum']
        return total or 0
    
    @property
    def other_contributions(self):
        """Amount covered by other sources (not from donors)"""
        return self.total_treatment_cost - self.funding_required


class ExpenseTypeLookup(models.Model):
    """Lookup table for treatment expense types"""
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Hospital Fees, Medical Staff")
    slug = models.SlugField(max_length=100, unique=True, help_text="e.g., hospital-fees, medical-staff")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Order to display in breakdown")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Expense Type'
        verbose_name_plural = 'Expense Types'
    
    def __str__(self):
        return self.name


class TreatmentCostBreakdown(models.Model):
    """Dynamic cost breakdown items for patient treatment"""
    patient_profile = models.ForeignKey(
        PatientProfile, 
        on_delete=models.CASCADE, 
        related_name='cost_breakdowns'
    )
    expense_type = models.ForeignKey(
        ExpenseTypeLookup, 
        on_delete=models.PROTECT,
        help_text="Select expense type from lookup"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost for this expense")
    notes = models.TextField(blank=True, help_text="Additional details about this expense")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['expense_type__display_order', 'created_at']
        verbose_name = 'Treatment Cost Breakdown'
        verbose_name_plural = 'Treatment Cost Breakdowns'
    
    def __str__(self):
        return f"{self.patient_profile.full_name} - {self.expense_type.name}: ${self.amount}"


class PatientTimeline(models.Model):
    """
    Timeline events for patient journey from submission to treatment completion
    """
    EVENT_TYPES = [
        ('PROFILE_SUBMITTED', 'Profile Submitted'),
        ('TREATMENT_SCHEDULED', 'Treatment Scheduled'),
        ('PROFILE_PUBLISHED', 'Profile Published'),
        ('AWAITING_FUNDING', 'Awaiting Funding'),
        ('FUNDING_MILESTONE', 'Funding Milestone Reached'),
        ('FULLY_FUNDED', 'Fully Funded'),
        ('TREATMENT_STARTED', 'Treatment Started'),
        ('TREATMENT_COMPLETE', 'Treatment Complete'),
        ('UPDATE_POSTED', 'Update Posted'),
        ('STATUS_CHANGED', 'Status Changed'),
    ]
    
    patient_profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='timeline_events'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    title = models.CharField(max_length=200, help_text="Event title for display")
    description = models.TextField(help_text="Detailed description of the event")
    
    # Optional fields for additional context
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who triggered this event (admin, coordinator, etc.)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data like funding amount, location, etc."
    )
    
    is_milestone = models.BooleanField(
        default=False,
        help_text="Mark important events as milestones"
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Control visibility of this event"
    )
    is_current_state = models.BooleanField(
        default=False,
        help_text="Mark this event as the current state of the patient"
    )
    event_date = models.DateField(
        null=True,
        blank=True,
        help_text="Scheduled/actual date of event (can be future for TBD events)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']  # Chronological order (oldest first)
        verbose_name = 'Patient Timeline Event'
        verbose_name_plural = 'Patient Timeline Events'
        indexes = [
            models.Index(fields=['patient_profile', 'created_at']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.patient_profile.full_name} - {self.get_event_type_display()} ({self.created_at.strftime('%B %d, %Y')})"
    
    @property
    def formatted_date(self):
        """Return formatted date like 'October 30, 2025'"""
        return self.created_at.strftime('%B %d, %Y')
    
    @property
    def is_future(self):
        """Check if this is a future/pending event"""
        from django.utils import timezone
        return self.created_at > timezone.now()


# Auto-create profiles when users register
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create profile based on user type"""
    if created:
        if instance.user_type == 'DONOR':
            DonorProfile.objects.create(user=instance)
        elif instance.user_type == 'PATIENT':
            # PatientProfile will be created separately after registration with additional data
            # from the PatientRegisterSerializer
            pass


# Auto-create timeline events for patient profile changes
@receiver(post_save, sender=PatientProfile)
def create_patient_timeline_events(sender, instance, created, **kwargs):
    """
    Automatically create timeline events when patient profile is created or updated
    """
    if created:
        # Event 1: Profile Submitted (when account is created)
        PatientTimeline.objects.create(
            patient_profile=instance,
            event_type='PROFILE_SUBMITTED',
            title='PROFILE SUBMITTED',
            description=f"{instance.full_name} was submitted to RHCI Portal for medical treatment assistance.",
            is_milestone=True,
            is_visible=True
        )
        
        # Event 2: Initial status based on profile status
        if instance.status == 'SUBMITTED':
            # Profile awaiting admin review
            pass  # PROFILE_SUBMITTED already covers this
        
    else:
        # Track status changes
        try:
            # Get old instance from database to compare changes
            from django.core.exceptions import ObjectDoesNotExist
            try:
                old_instance = PatientProfile.objects.get(pk=instance.pk)
            except ObjectDoesNotExist:
                return
            
            # Check if treatment_date was set
            if old_instance.treatment_date is None and instance.treatment_date is not None:
                PatientTimeline.objects.create(
                    patient_profile=instance,
                    event_type='TREATMENT_SCHEDULED',
                    title='TREATMENT SCHEDULED',
                    description=f"{instance.full_name} was scheduled to receive treatment on {instance.treatment_date.strftime('%B %d, %Y')} at {instance.medical_partner or 'medical facility'}.",
                    event_date=instance.treatment_date,
                    is_milestone=True,
                    is_visible=True
                )
            
            # Check if status changed
            if old_instance.status != instance.status:
                status_events = {
                    'SCHEDULED': {
                        'type': 'TREATMENT_SCHEDULED',
                        'title': 'TREATMENT SCHEDULED',
                        'description': f"{instance.full_name} was scheduled to receive treatment at {instance.medical_partner or 'medical facility'}. Medical partners often provide care to patients before they are fully funded, operating under the guarantee that the cost of care will be paid for by donors.",
                        'is_milestone': True
                    },
                    'PUBLISHED': {
                        'type': 'PROFILE_PUBLISHED',
                        'title': 'PROFILE PUBLISHED',
                        'description': f"{instance.full_name}'s profile was published to start raising funds.",
                        'is_milestone': True
                    },
                    'AWAITING_FUNDING': {
                        'type': 'AWAITING_FUNDING',
                        'title': 'AWAITING FUNDING',
                        'description': f"{instance.full_name} is currently raising funds for treatment.",
                        'is_milestone': False
                    },
                    'FULLY_FUNDED': {
                        'type': 'FULLY_FUNDED',
                        'title': 'FULLY FUNDED',
                        'description': f"{instance.full_name}'s treatment has been fully funded! Thank you to all donors who made this possible.",
                        'is_milestone': True
                    },
                    'TREATMENT_COMPLETE': {
                        'type': 'TREATMENT_COMPLETE',
                        'title': 'TREATMENT COMPLETE',
                        'description': f"{instance.full_name} has successfully completed treatment. Thank you for your support!",
                        'is_milestone': True
                    }
                }
                
                if instance.status in status_events:
                    event_data = status_events[instance.status]
                    PatientTimeline.objects.create(
                        patient_profile=instance,
                        event_type=event_data['type'],
                        title=event_data['title'],
                        description=event_data['description'],
                        is_milestone=event_data['is_milestone'],
                        is_visible=True
                    )
            
            # Check if funding milestone reached (25%, 50%, 75%)
            if old_instance.funding_received != instance.funding_received:
                if instance.funding_required > 0:
                    percentage = (instance.funding_received / instance.funding_required) * 100
                    milestones = [25, 50, 75]
                    
                    for milestone in milestones:
                        old_percentage = (old_instance.funding_received / instance.funding_required) * 100 if instance.funding_required > 0 else 0
                        
                        if old_percentage < milestone <= percentage:
                            PatientTimeline.objects.create(
                                patient_profile=instance,
                                event_type='FUNDING_MILESTONE',
                                title=f'{milestone}% FUNDED',
                                description=f"{instance.full_name}'s treatment is now {milestone}% funded! ${instance.funding_received:,.2f} of ${instance.funding_required:,.2f} raised.",
                                is_milestone=True,
                                is_visible=True,
                                metadata={'percentage': milestone, 'amount': float(instance.funding_received)}
                            )
        except PatientProfile.DoesNotExist:
            pass
