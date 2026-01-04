from django.db import models
from django.conf import settings
from datetime import date
from decimal import Decimal
from auth_app.lookups import CountryLookup
from utils.constants import CURRENCY_CHOICES


class DonorProfile(models.Model):
    """Extended profile for donors"""
    # Relationship
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donor_profile')
    
    # Profile Information
    photo = models.ImageField(upload_to='donor_photos/', null=True, blank=True, help_text="Profile photo")
    full_name = models.CharField(max_length=200, blank=True, help_text="Full name for display")
    short_bio = models.CharField(max_length=60, blank=True, help_text="Short bio (max 60 characters)")
    country_fk = models.ForeignKey(CountryLookup, on_delete=models.PROTECT, null=True, blank=True, related_name='donors', db_column='country_fk_id')  # References country_id column in DB
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


class Donation(models.Model):
    """
    Core donation model supporting both anonymous and authenticated donations
    """
    DONATION_TYPE_CHOICES = [
        ('ONE_TIME', 'One-time Donation'),
        ('MONTHLY', 'Monthly Recurring'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    # Donor information
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations',
        help_text="Authenticated donor (null for anonymous donations)"
    )
    is_anonymous = models.BooleanField(
        default=False,
        help_text="Whether this donation is anonymous (hide donor identity)"
    )
    
    # Anonymous donor details (if not logged in)
    anonymous_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name for anonymous donations"
    )
    anonymous_email = models.EmailField(
        blank=True,
        help_text="Email for receipt/updates (anonymous donations)"
    )
    
    # Patient selection (optional - can be general donation)
    patient = models.ForeignKey(
        'patient.PatientProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations',
        help_text="Specific patient to donate to (null for general donation)"
    )
    
    # Donation details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total donation amount (patient_amount + rhci_support_amount)"
    )
    
    # Split donation amounts
    patient_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount allocated to patient funding"
    )
    rhci_support_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        null=True,
        blank=True,
        help_text="Optional amount to support RHCI operations"
    )
    
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text="Currency of the donation"
    )
    donation_type = models.CharField(
        max_length=20,
        choices=DONATION_TYPE_CHOICES,
        default='ONE_TIME'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Payment information
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Payment method used (e.g., card, mobile money)"
    )
    transaction_id = models.CharField(
        max_length=200,
        blank=True,
        unique=True,
        null=True,
        help_text="External payment gateway transaction ID"
    )
    payment_gateway = models.CharField(
        max_length=50,
        blank=True,
        help_text="Payment gateway used (e.g., Stripe, PayPal, M-Pesa)"
    )
    
    # Optional fields
    message = models.TextField(
        blank=True,
        help_text="Optional message from donor to patient"
    )
    dedication = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional dedication (e.g., 'In memory of...')"
    )
    
    # Recurring donation details
    recurring_frequency = models.IntegerField(
        default=1,
        help_text="Frequency in months (1=monthly, 3=quarterly, etc.)"
    )
    next_charge_date = models.DateField(
        null=True,
        blank=True,
        help_text="Next scheduled charge date for recurring donations"
    )
    is_recurring_active = models.BooleanField(
        default=False,
        help_text="Whether recurring donation is active"
    )
    parent_donation = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_payments',
        help_text="Parent donation for recurring payment children"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of donor"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser user agent"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When donation was successfully completed"
    )
    
    class Meta:
        db_table = 'donor_donation'
        ordering = ['-created_at']
        verbose_name = 'Donation'
        verbose_name_plural = 'Donations'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['donor', '-created_at']),
            models.Index(fields=['patient', '-created_at']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['rhci_support_amount', 'status']),  # For filtering RHCI donations
        ]
    
    def clean(self):
        """Validate donation amounts"""
        from django.core.exceptions import ValidationError
        
        # Calculate expected total
        patient_amt = self.patient_amount or Decimal('0.00')
        rhci_amt = self.rhci_support_amount or Decimal('0.00')
        calculated_total = patient_amt + rhci_amt
        
        # Validate total matches
        if self.amount != calculated_total:
            raise ValidationError({
                'amount': f'Total amount ({self.amount}) must equal patient_amount ({patient_amt}) + rhci_support_amount ({rhci_amt})'
            })
        
        # If patient is selected, patient_amount must be > 0
        if self.patient and patient_amt <= 0:
            raise ValidationError({
                'patient_amount': 'Patient amount must be greater than 0 when patient is selected'
            })
    
    def __str__(self):
        donor_name = self.get_donor_display_name()
        patient_name = self.patient.full_name if self.patient else "General Fund"
        return f"${self.amount} from {donor_name} to {patient_name}"
    
    def get_donor_display_name(self):
        """Get donor name for display"""
        if self.is_anonymous:
            return "Anonymous"
        if self.donor:
            return self.donor.get_full_name() or self.donor.email
        if self.anonymous_name:
            return self.anonymous_name
        return "Anonymous"
    
    @property
    def is_recurring(self):
        """Check if this is a recurring donation"""
        return self.donation_type == 'MONTHLY'
    
    @property
    def total_recurring_amount(self):
        """Total amount donated through this recurring donation"""
        if not self.is_recurring or not self.is_recurring_active:
            return self.amount
        
        total = Donation.objects.filter(
            parent_donation=self,
            status='COMPLETED'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        return total + self.amount


class DonationReceipt(models.Model):
    """
    Donation receipt/acknowledgment
    """
    donation = models.OneToOneField(
        Donation,
        on_delete=models.CASCADE,
        related_name='receipt'
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique receipt number for tax purposes"
    )
    receipt_url = models.URLField(
        blank=True,
        help_text="URL to downloadable PDF receipt"
    )
    email_sent = models.BooleanField(
        default=False,
        help_text="Whether receipt email was sent"
    )
    email_sent_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'donor_donationreceipt'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Receipt {self.receipt_number} - ${self.donation.amount}"


class DonationComment(models.Model):
    """
    Comments/updates from donors or admins on donations
    """
    donation = models.ForeignKey(
        Donation,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    comment = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal note (not visible to donor)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'donor_donationcomment'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on donation {self.donation.id}"
