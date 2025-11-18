from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, DonorProfile, PatientProfile, ExpenseTypeLookup, TreatmentCostBreakdown, PatientTimeline


class TreatmentCostBreakdownInline(admin.TabularInline):
    """Inline for adding cost breakdown items"""
    model = TreatmentCostBreakdown
    extra = 1
    fields = ['expense_type', 'amount', 'notes']
    autocomplete_fields = ['expense_type']


class PatientTimelineInline(admin.TabularInline):
    """Inline for viewing and adding timeline events"""
    model = PatientTimeline
    extra = 0
    fields = ['event_type', 'title', 'description', 'event_date', 'created_by', 'is_milestone', 'is_visible', 'is_current_state', 'created_at']
    readonly_fields = ['created_at']
    ordering = ['created_at']  # Chronological order (oldest first)


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    inlines = [TreatmentCostBreakdownInline, PatientTimelineInline]
    list_display = [
        'full_name', 'status', 'funding_required', 'funding_received', 
        'cost_breakdown_total', 'created_at'
    ]
    list_filter = ['status', 'gender', 'created_at']
    search_fields = ['full_name', 'user__email', 'diagnosis']
    readonly_fields = [
        'cost_breakdown_total', 'funding_percentage', 
        'funding_remaining', 'other_contributions', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'full_name', 'age', 'gender', 'country')
        }),
        ('Medical Details', {
            'fields': ('medical_partner', 'diagnosis', 'treatment_needed', 'treatment_date')
        }),
        ('Story', {
            'fields': ('short_description', 'long_story')
        }),
        ('Funding Summary', {
            'fields': (
                'funding_required', 'funding_received', 'total_treatment_cost',
                'funding_percentage', 'funding_remaining', 'other_contributions',
                'cost_breakdown_notes'
            )
        }),
        ('Calculated Totals', {
            'fields': ('cost_breakdown_total',),
            'description': 'Auto-calculated from breakdown items below'
        }),
        ('Status & Publication', {
            'fields': ('status', 'is_featured', 'rejection_reason', 'created_at', 'updated_at')
        }),
    )


@admin.register(ExpenseTypeLookup)
class ExpenseTypeLookupAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'country', 'is_profile_private', 'created_at']
    list_filter = ['is_profile_private', 'country', 'created_at']
    search_fields = ['full_name', 'user__email', 'short_bio', 'workplace']
    readonly_fields = ['age', 'created_at', 'updated_at']
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'photo', 'full_name', 'short_bio')
        }),
        ('Personal Details', {
            'fields': ('birthday', 'age', 'country', 'workplace', 'website')
        }),
        ('Privacy', {
            'fields': ('is_profile_private',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['email', 'user_type', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'user_type')}),
        ('Permissions', {
            'fields': ('is_active', 'is_verified', 'is_patient_verified', 
                      'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_type', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )


@admin.register(TreatmentCostBreakdown)
class TreatmentCostBreakdownAdmin(admin.ModelAdmin):
    list_display = ['patient_profile', 'expense_type', 'amount', 'created_at']
    list_filter = ['expense_type', 'created_at']
    search_fields = ['patient_profile__full_name', 'expense_type__name']
    autocomplete_fields = ['patient_profile', 'expense_type']


@admin.register(PatientTimeline)
class PatientTimelineAdmin(admin.ModelAdmin):
    list_display = ['patient_profile', 'event_type', 'title', 'event_date', 'is_milestone', 'is_visible', 'is_current_state', 'created_at']
    list_filter = ['event_type', 'is_milestone', 'is_visible', 'is_current_state', 'created_at']
    search_fields = ['patient_profile__full_name', 'title', 'description']
    readonly_fields = ['formatted_date', 'is_future', 'created_at', 'updated_at']
    autocomplete_fields = ['patient_profile', 'created_by']
    fieldsets = (
        ('Event Details', {
            'fields': ('patient_profile', 'event_type', 'title', 'description', 'event_date')
        }),
        ('Event Metadata', {
            'fields': ('created_by', 'metadata', 'is_milestone', 'is_visible', 'is_current_state')
        }),
        ('Timestamps', {
            'fields': ('formatted_date', 'created_at', 'updated_at', 'is_future')
        }),
    )
