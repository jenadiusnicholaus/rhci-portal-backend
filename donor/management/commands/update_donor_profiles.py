from django.core.management.base import BaseCommand
from donor.models import DonorProfile
from datetime import date


class Command(BaseCommand):
    help = 'Update donor profiles with sample data'

    def handle(self, *args, **options):
        donors_data = [
            {
                'id': 1,
                'full_name': 'John Nicholaus',
                'short_bio': 'Software engineer passionate about healthcare tech',
                'country': 'Tanzania',
                'website': 'https://jnicholaus.dev',
                'birthday': date(1990, 5, 15),
                'workplace': 'Tech Solutions Inc.',
            },
            {
                'id': 2,
                'full_name': 'Sarah Johnson',
                'short_bio': 'Healthcare professional helping patients in need',
                'country': 'United States',
                'website': 'https://sarahjohnson.com',
                'birthday': date(1985, 8, 22),
                'workplace': 'Memorial Hospital',
            },
            {
                'id': 3,
                'full_name': 'Michael Chen',
                'short_bio': 'Entrepreneur supporting medical causes worldwide',
                'country': 'Singapore',
                'website': '',
                'birthday': date(1988, 12, 10),
                'workplace': 'Chen Enterprises',
            },
            {
                'id': 4,
                'full_name': 'Emma Williams',
                'short_bio': 'Philanthropist improving healthcare access',
                'country': 'United Kingdom',
                'website': 'https://emmawilliams.org',
                'birthday': date(1992, 3, 18),
                'workplace': 'Williams Foundation',
            },
            {
                'id': 5,
                'full_name': 'David Martinez',
                'short_bio': 'Medical researcher supporting patient care',
                'country': 'Spain',
                'website': '',
                'birthday': date(1987, 7, 25),
                'workplace': 'Barcelona Research Institute',
            },
        ]

        updated_count = 0
        for data in donors_data:
            try:
                donor = DonorProfile.objects.get(id=data['id'])
                donor.full_name = data['full_name']
                donor.short_bio = data['short_bio']
                donor.country = data['country']
                donor.website = data['website']
                donor.birthday = data['birthday']
                donor.workplace = data['workplace']
                donor.is_profile_private = False  # Make profiles public
                donor.save()
                
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Updated donor profile: {donor.full_name} (ID: {donor.id})')
                )
            except DonorProfile.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Donor profile with ID {data["id"]} not found')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Updated {updated_count} donor profiles')
        )
