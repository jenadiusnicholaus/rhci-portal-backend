from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, FinancialReport
from .lookups import CountryLookup


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['email', 'user_type', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'user_type', 'date_of_birth', 'profile_picture')}),
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


@admin.register(CountryLookup)
class CountryLookupAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['display_order', 'name']
    list_editable = ['display_order', 'is_active']


@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_public', 'uploaded_by', 'uploaded_at']
    list_filter = ['is_public', 'uploaded_at']
    search_fields = ['title', 'description']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('title', 'description', 'document')}),
        ('Visibility', {'fields': ('is_public',)}),
        ('Metadata', {'fields': ('uploaded_by', 'uploaded_at', 'updated_at')}),
    )
