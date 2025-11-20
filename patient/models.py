from django.db import models
from django.conf import settings
from datetime import date
from auth_app.lookups import CountryLookup


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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    
    # Core Info (collected during registration)
    photo = models.ImageField(upload_to='patient_photos/', null=True, blank=True, help_text="Patient profile photo")
    full_name = models.CharField(max_length=200)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    country_fk = models.ForeignKey(CountryLookup, on_delete=models.PROTECT, null=True, blank=True, related_name='patients', db_column='country_fk_id')  # References country_fk_id column in DB
    
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
    
    class Meta:
        db_table = 'auth_app_patientprofile'  # Keep existing table name
        
    def __str__(self):
        return f"{self.full_name} - {self.status}"
    
    @property
    def age(self):
        """Calculate age from user's date of birth"""
        if self.user.date_of_birth:
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
        """Complete funding summary"""
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
        db_table = 'auth_app_expensetypelookup'  # Keep existing table name
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
        db_table = 'auth_app_treatmentcostbreakdown'  # Keep existing table name
        ordering = ['expense_type__display_order']
        verbose_name = 'Treatment Cost Breakdown'
        verbose_name_plural = 'Treatment Cost Breakdowns'
    
    def __str__(self):
        return f"{self.patient_profile.full_name} - {self.expense_type.name}: ${self.amount}"


class DonationAmountOption(models.Model):
    """
    Suggested donation amounts for quick selection (e.g., $10, $28, $56, $150)
    Allows admins to configure donation amount buttons for each patient
    """
    patient_profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='donation_amount_options'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Suggested donation amount"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Order to display (lower numbers first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Show this option to donors"
    )
    is_recommended = models.BooleanField(
        default=False,
        help_text="Highlight this amount as recommended"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patient_donationamountoption'
        ordering = ['patient_profile', 'display_order', 'amount']
        verbose_name = 'Donation Amount Option'
        verbose_name_plural = 'Donation Amount Options'
        unique_together = ['patient_profile', 'amount']
    
    def __str__(self):
        recommended = " (Recommended)" if self.is_recommended else ""
        return f"{self.patient_profile.full_name} - ${self.amount}{recommended}"


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
        settings.AUTH_USER_MODEL,
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
        db_table = 'auth_app_patienttimeline'  # Keep existing table name
        ordering = ['created_at']  # Chronological order (oldest first)
        verbose_name = 'Patient Timeline Event'
        verbose_name_plural = 'Patient Timeline Events'
        indexes = [
            models.Index(fields=['patient_profile', 'created_at']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.patient_profile.full_name} - {self.get_event_type_display()}"
    
    @property
    def formatted_date(self):
        """Return a formatted date string"""
        return self.created_at.strftime("%B %d, %Y")
    
    @property
    def is_future(self):
        """Check if event_date is in the future"""
        if self.event_date:
            return self.event_date > date.today()
        return False


# Import donation models
# Donation models are now in the donor app
# from donor.models import Donation, DonationReceipt, DonationComment
