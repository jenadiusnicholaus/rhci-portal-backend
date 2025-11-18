from django.db import models


class CountryLookup(models.Model):
    """
    Country lookup table for consistent country selection across the platform.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Country name")
    code = models.CharField(max_length=3, unique=True, help_text="ISO 3166-1 alpha-3 country code")
    display_order = models.IntegerField(default=0, help_text="Order in which to display countries")
    is_active = models.BooleanField(default=True, help_text="Whether this country is available for selection")
    
    class Meta:
        db_table = 'country_lookup'
        ordering = ['display_order', 'name']
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
    
    def __str__(self):
        return self.name
