from django.core.management.base import BaseCommand
from auth_app.lookups import CountryLookup


class Command(BaseCommand):
    help = 'Populate country lookup table with common countries'

    def handle(self, *args, **options):
        countries = [
            {'name': 'Tanzania', 'code': 'TZA', 'display_order': 1},
            {'name': 'United States', 'code': 'USA', 'display_order': 2},
            {'name': 'United Kingdom', 'code': 'GBR', 'display_order': 3},
            {'name': 'Canada', 'code': 'CAN', 'display_order': 4},
            {'name': 'Australia', 'code': 'AUS', 'display_order': 5},
            {'name': 'Germany', 'code': 'DEU', 'display_order': 6},
            {'name': 'France', 'code': 'FRA', 'display_order': 7},
            {'name': 'Spain', 'code': 'ESP', 'display_order': 8},
            {'name': 'Italy', 'code': 'ITA', 'display_order': 9},
            {'name': 'Netherlands', 'code': 'NLD', 'display_order': 10},
            {'name': 'Belgium', 'code': 'BEL', 'display_order': 11},
            {'name': 'Switzerland', 'code': 'CHE', 'display_order': 12},
            {'name': 'Sweden', 'code': 'SWE', 'display_order': 13},
            {'name': 'Norway', 'code': 'NOR', 'display_order': 14},
            {'name': 'Denmark', 'code': 'DNK', 'display_order': 15},
            {'name': 'Finland', 'code': 'FIN', 'display_order': 16},
            {'name': 'Poland', 'code': 'POL', 'display_order': 17},
            {'name': 'Czech Republic', 'code': 'CZE', 'display_order': 18},
            {'name': 'Austria', 'code': 'AUT', 'display_order': 19},
            {'name': 'Ireland', 'code': 'IRL', 'display_order': 20},
            {'name': 'Portugal', 'code': 'PRT', 'display_order': 21},
            {'name': 'Greece', 'code': 'GRC', 'display_order': 22},
            {'name': 'New Zealand', 'code': 'NZL', 'display_order': 23},
            {'name': 'Singapore', 'code': 'SGP', 'display_order': 24},
            {'name': 'Japan', 'code': 'JPN', 'display_order': 25},
            {'name': 'South Korea', 'code': 'KOR', 'display_order': 26},
            {'name': 'China', 'code': 'CHN', 'display_order': 27},
            {'name': 'India', 'code': 'IND', 'display_order': 28},
            {'name': 'Brazil', 'code': 'BRA', 'display_order': 29},
            {'name': 'Mexico', 'code': 'MEX', 'display_order': 30},
            {'name': 'South Africa', 'code': 'ZAF', 'display_order': 31},
            {'name': 'Kenya', 'code': 'KEN', 'display_order': 32},
            {'name': 'Uganda', 'code': 'UGA', 'display_order': 33},
            {'name': 'Rwanda', 'code': 'RWA', 'display_order': 34},
            {'name': 'Nigeria', 'code': 'NGA', 'display_order': 35},
            {'name': 'Ghana', 'code': 'GHA', 'display_order': 36},
            {'name': 'Egypt', 'code': 'EGY', 'display_order': 37},
            {'name': 'Morocco', 'code': 'MAR', 'display_order': 38},
            {'name': 'Ethiopia', 'code': 'ETH', 'display_order': 39},
            {'name': 'Other', 'code': 'OTH', 'display_order': 999},
        ]

        created_count = 0
        updated_count = 0

        for country_data in countries:
            country, created = CountryLookup.objects.update_or_create(
                code=country_data['code'],
                defaults={
                    'name': country_data['name'],
                    'display_order': country_data['display_order'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {country.name} ({country.code})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {country.name} ({country.code})')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Created {created_count} countries, updated {updated_count}')
        )
