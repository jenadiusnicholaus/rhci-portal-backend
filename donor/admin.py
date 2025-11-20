from django.contrib import admin
from .models import DonorProfile, Donation, DonationReceipt, DonationComment


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'country_fk', 'is_profile_private', 'created_at']
    list_filter = ['is_profile_private', 'country_fk', 'created_at']
    search_fields = ['full_name', 'user__email', 'short_bio', 'workplace']
    readonly_fields = ['age', 'created_at', 'updated_at']
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'photo', 'full_name', 'short_bio')
        }),
        ('Personal Details', {
            'fields': ('birthday', 'age', 'country_fk', 'workplace', 'website')
        }),
        ('Privacy', {
            'fields': ('is_profile_private',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class DonationReceiptInline(admin.StackedInline):
    model = DonationReceipt
    extra = 0
    readonly_fields = ['created_at']


class DonationCommentInline(admin.TabularInline):
    model = DonationComment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_donor_name', 'get_patient_name', 'amount', 
        'donation_type', 'status', 'is_anonymous', 'created_at'
    ]
    list_filter = [
        'status', 'donation_type', 'is_anonymous', 
        'payment_gateway', 'created_at'
    ]
    search_fields = [
        'donor__email', 'donor__first_name', 'donor__last_name',
        'anonymous_name', 'anonymous_email', 
        'patient__full_name', 'transaction_id'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'is_recurring', 
        'total_recurring_amount', 'ip_address', 'user_agent'
    ]
    inlines = [DonationReceiptInline, DonationCommentInline]
    
    fieldsets = (
        ('Donor Information', {
            'fields': ('donor', 'is_anonymous', 'anonymous_name', 'anonymous_email')
        }),
        ('Donation Details', {
            'fields': ('patient', 'amount', 'donation_type', 'status', 'message', 'dedication')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_gateway', 'transaction_id')
        }),
        ('Recurring Details', {
            'fields': (
                'is_recurring', 'recurring_frequency', 'next_charge_date', 
                'is_recurring_active', 'parent_donation', 'total_recurring_amount'
            )
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
    
    def get_donor_name(self, obj):
        return obj.get_donor_display_name()
    get_donor_name.short_description = 'Donor'
    
    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else "General Fund"
    get_patient_name.short_description = 'Patient'
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(status='COMPLETED', completed_at=timezone.now())
        self.message_user(request, f'{count} donation(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected donations as completed'
    
    def mark_as_failed(self, request, queryset):
        count = queryset.update(status='FAILED')
        self.message_user(request, f'{count} donation(s) marked as failed.')
    mark_as_failed.short_description = 'Mark selected donations as failed'


@admin.register(DonationReceipt)
class DonationReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'donation', 'email_sent', 'email_sent_at', 'created_at']
    list_filter = ['email_sent', 'created_at']
    search_fields = ['receipt_number', 'donation__id', 'donation__anonymous_email']
    readonly_fields = ['created_at']


@admin.register(DonationComment)
class DonationCommentAdmin(admin.ModelAdmin):
    list_display = ['donation', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['comment', 'donation__id']
    readonly_fields = ['created_at']
