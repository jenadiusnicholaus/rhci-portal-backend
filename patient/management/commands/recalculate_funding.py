from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Recalculate and fix patient status based on actual completed donations'

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

        patient_id = options.get('patient_id')
        dry_run = options.get('dry_run')

        patients = PatientProfile.objects.all()
        if patient_id:
            patients = patients.filter(id=patient_id)

        updated = 0
        for patient in patients:
            # funding_received is now a computed property — always accurate
            actual_received = patient.funding_received
            should_be_funded = (
                patient.funding_required == 0 and actual_received > 0
            ) or (
                patient.funding_required > 0 and actual_received >= patient.funding_required
            )
            correct_status = 'FULLY_FUNDED' if should_be_funded else patient.status

            self.stdout.write(
                f"Patient {patient.id} ({patient.full_name}): "
                f"funding_received={actual_received}, "
                f"funding_required={patient.funding_required}, "
                f"status={patient.status}"
                + (f" → {correct_status}" if correct_status != patient.status else " ✓")
            )

            if correct_status != patient.status:
                if not dry_run:
                    patient.status = correct_status
                    patient.save()
                    updated += 1

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run — no changes saved.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated {updated} patient(s).'))
