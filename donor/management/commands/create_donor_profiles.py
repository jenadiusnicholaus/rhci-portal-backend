from django.core.management.base import BaseCommand
from auth_app.models import CustomUser
from donor.models import DonorProfile


class Command(BaseCommand):
    help = 'Creates DonorProfile for all DONOR users who don\'t have one'

    def handle(self, *args, **options):
        donors = CustomUser.objects.filter(user_type='DONOR')
        created_count = 0
        
        for donor in donors:
            if not hasattr(donor, 'donor_profile'):
                DonorProfile.objects.create(user=donor)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created DonorProfile for {donor.email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ DonorProfile already exists for {donor.email}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Created {created_count} donor profiles')
        )
