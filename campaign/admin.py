from django.contrib import admin
from .models import PaymentMethod, Campaign, CampaignPhoto, CampaignUpdate


class CampaignPhotoInline(admin.TabularInline):
    model = CampaignPhoto
    extra = 1
    fields = ['image', 'caption', 'display_order', 'is_primary']


class CampaignUpdateInline(admin.StackedInline):
    model = CampaignUpdate
    extra = 0
    fields = ['title', 'content', 'author', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'launcher_email', 'goal_amount', 
        'raised_amount', 'funding_progress', 'status', 'end_date', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'end_date']
    search_fields = ['title', 'description', 'launcher__email', 'launcher__first_name', 'launcher__last_name']
    readonly_fields = ['created_at', 'updated_at', 'funding_progress', 'remaining_amount', 'is_funded']
    filter_horizontal = ['payment_methods']
    inlines = [CampaignPhotoInline, CampaignUpdateInline]
    
    fieldsets = (
        ('Campaign Details', {
            'fields': ('launcher', 'title', 'description', 'goal_amount', 'raised_amount', 'end_date')
        }),
        ('Funding Progress', {
            'fields': ('funding_progress', 'remaining_amount', 'is_funded')
        }),
        ('Status', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('Payment Methods (Admin Only)', {
            'fields': ('payment_methods',),
            'description': 'Payment methods are controlled by RHCI admin. Campaign launchers cannot modify these.'
        }),
        ('Admin Notes', {
            'fields': ('admin_notes', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def launcher_email(self, obj):
        return obj.launcher.email
    launcher_email.short_description = 'Launcher'
    
    actions = ['approve_campaigns', 'reject_campaigns', 'activate_campaigns']
    
    def approve_campaigns(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status='PENDING_REVIEW').update(
            status='APPROVED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{count} campaign(s) approved.')
    approve_campaigns.short_description = 'Approve selected campaigns'
    
    def reject_campaigns(self, request, queryset):
        count = queryset.update(status='REJECTED')
        self.message_user(request, f'{count} campaign(s) rejected.')
    reject_campaigns.short_description = 'Reject selected campaigns'
    
    def activate_campaigns(self, request, queryset):
        count = queryset.filter(status='APPROVED').update(status='ACTIVE')
        self.message_user(request, f'{count} campaign(s) activated.')
    activate_campaigns.short_description = 'Activate approved campaigns'


@admin.register(CampaignPhoto)
class CampaignPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'campaign', 'caption', 'display_order', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['campaign__title', 'caption']


@admin.register(CampaignUpdate)
class CampaignUpdateAdmin(admin.ModelAdmin):
    list_display = ['id', 'campaign', 'title', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['campaign__title', 'title', 'content']
    readonly_fields = ['created_at']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'account_name', 'account_number', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'account_name', 'account_number', 'bank_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Payment Method Details', {
            'fields': ('name', 'account_name', 'account_number', 'bank_name', 'swift_code')
        }),
        ('Additional Information', {
            'fields': ('additional_info',)
        }),
        ('Status', {
            'fields': ('is_active', 'display_order')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
