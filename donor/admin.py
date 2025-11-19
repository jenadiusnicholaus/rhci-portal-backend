from django.contrib import admin
from .models import DonorProfile


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
