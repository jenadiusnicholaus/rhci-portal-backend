from django.core.management.base import BaseCommand
from patient.models import PatientProfile


class Command(BaseCommand):
    help = 'Generate bill identifiers for patients without one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without saving',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        patients = PatientProfile.objects.filter(bill_identifier__isnull=True)
        total_count = patients.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('All patients already have bill identifiers!'))
            return
        
        self.stdout.write(f'Found {total_count} patients without bill identifiers')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        count = 0
        for patient in patients:
            if dry_run:
                # Generate code without saving
                code = patient._generate_bill_identifier()
                self.stdout.write(f"Would generate: {code} for {patient.full_name}")
            else:
                # Save triggers auto-generation
                patient.save()
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Generated {patient.bill_identifier} for {patient.full_name}")
                )
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would generate {total_count} bill identifiers'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully generated {count} bill identifiers')
            )
