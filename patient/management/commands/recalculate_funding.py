from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal


class Command(BaseCommand):
    help = 'Recalculate funding_received for all patients from completed donations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patient-id',
            type=int,
            help='Recalculate only for a specific patient ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving',
        )

    def handle(self, *args, **options):
        from patient.models import PatientProfile
        from donor.models import Donation

        patient_id = options.get('patient_id')
        dry_run = options.get('dry_run')

        patients = PatientProfile.objects.all()
        if patient_id:
            patients = patients.filter(id=patient_id)

        updated = 0
        for patient in patients:
            actual_received = Donation.objects.filter(
                patient=patient,
                status='COMPLETED'
            ).aggregate(total=Sum('patient_amount'))['total'] or Decimal('0.00')

            if patient.funding_received != actual_received:
                self.stdout.write(
                    f"Patient {patient.id} ({patient.full_name}): "
                    f"funding_received {patient.funding_received} → {actual_received}"
                )
                if not dry_run:
                    patient.funding_received = actual_received
                    if patient.funding_required == 0 and actual_received > 0:
                        patient.status = 'FULLY_FUNDED'
                    elif actual_received >= patient.funding_required > 0:
                        patient.status = 'FULLY_FUNDED'
                    patient.save()
                    updated += 1

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run — no changes saved.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated {updated} patient(s).'))
