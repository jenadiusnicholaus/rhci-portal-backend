from django.db import models
from django.conf import settings
from decimal import Decimal


class PaymentMethod(models.Model):
    """
    Payment methods configured by RHCI admin for receiving campaign donations
    Campaign launchers CANNOT modify these - only RHCI admin can set them up
    """
    name = models.CharField(
        max_length=100,
        help_text="Payment method name (e.g., M-Pesa, Bank Transfer, PayPal)"
    )
    account_name = models.CharField(
        max_length=200,
        help_text="Account holder name"
    )
    account_number = models.CharField(
        max_length=200,
        help_text="Account/phone number"
    )
    bank_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Bank name (if applicable)"
    )
    swift_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="SWIFT/BIC code for international transfers"
    )
    additional_info = models.TextField(
        blank=True,
        help_text="Additional payment instructions"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this payment method is currently active"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payment_methods'
    )
    
    class Meta:
        db_table = 'campaign_paymentmethod'
        ordering = ['display_order', 'name']
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def __str__(self):
        return f"{self.name} - {self.account_number}"


class Campaign(models.Model):
    """
    Campaign model for fundraising
    Launched by users, payment methods controlled by RHCI admin
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    ]
    
    # Campaign Owner
    launcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='campaigns',
        help_text="User who launched this campaign"
    )
    
    # Campaign Details
    title = models.CharField(
        max_length=200,
        help_text="Campaign title"
    )
    description = models.TextField(
        help_text="Campaign story/description"
    )
    
    # Funding
    goal_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Fundraising goal amount"
    )
    raised_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount raised so far"
    )
    
    # Timeline
    end_date = models.DateField(
        help_text="Campaign end date"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Payment Methods (READ-ONLY for campaign launchers)
    # These are set by RHCI admin only
    payment_methods = models.ManyToManyField(
        PaymentMethod,
        related_name='campaigns',
        blank=True,
        help_text="Payment methods for this campaign (Set by RHCI admin only)"
    )
    
    # Admin fields
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal admin notes"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if rejected)"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_campaigns'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaign_campaign'
        ordering = ['-created_at']
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['launcher', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.launcher.email}"
    
    @property
    def funding_progress(self):
        """Calculate funding progress percentage"""
        if self.goal_amount > 0:
            # Convert to float for percentage calculation
            return float((self.raised_amount / self.goal_amount) * Decimal('100'))
        return 0.0
    
    @property
    def is_funded(self):
        """Check if campaign has reached goal"""
        return self.raised_amount >= self.goal_amount
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return max(self.goal_amount - self.raised_amount, Decimal('0.00'))


class CampaignPhoto(models.Model):
    """
    Photos for campaigns
    """
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    image = models.ImageField(
        upload_to='campaign_photos/',
        help_text="Campaign photo"
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text="Photo caption"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary photo for campaign card"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'campaign_campaignphoto'
        ordering = ['display_order', 'created_at']
        verbose_name = 'Campaign Photo'
        verbose_name_plural = 'Campaign Photos'
    
    def __str__(self):
        return f"Photo for {self.campaign.title}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary photos
        if self.is_primary:
            CampaignPhoto.objects.filter(
                campaign=self.campaign,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class CampaignUpdate(models.Model):
    """
    Updates posted by campaign launcher
    """
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='updates'
    )
    title = models.CharField(
        max_length=200,
        help_text="Update title"
    )
    content = models.TextField(
        help_text="Update content"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'campaign_campaignupdate'
        ordering = ['-created_at']
        verbose_name = 'Campaign Update'
        verbose_name_plural = 'Campaign Updates'
    
    def __str__(self):
        return f"Update: {self.title}"
