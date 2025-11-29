from django.core.management.base import BaseCommand
from auth_app.lookups import CountryLookup
from patient.models import PatientProfile
from donor.models import DonorProfile


class Command(BaseCommand):
    help = 'Migrate country string values to CountryLookup ForeignKeys'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n🟠 Starting country data migration...\n'))
        
        # Migrate patient countries
        patients = PatientProfile.objects.all()
        patient_migrated = 0
        patient_not_found = []
        
        for patient in patients:
            if patient.country and not patient.country_fk:
                try:
                    country = CountryLookup.objects.get(name__iexact=patient.country)
                    patient.country_fk = country
                    patient.save(update_fields=['country_fk'])
                    patient_migrated += 1
                    self.stdout.write(f'✓ Patient {patient.id}: {patient.country} → {country.name}')
                except CountryLookup.DoesNotExist:
                    patient_not_found.append((patient.id, patient.country))
                    # Try to find "Other"
                    try:
                        other = CountryLookup.objects.get(code='OTH')
                        patient.country_fk = other
                        patient.save(update_fields=['country_fk'])
                        self.stdout.write(f'⚠ Patient {patient.id}: {patient.country} → Other (not found)')
                    except CountryLookup.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'✗ Patient {patient.id}: Country "{patient.country}" not found and no "Other" option'))
        
        # Migrate donor countries using raw SQL since the column is named country_id in DB
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('SELECT id, country_id FROM auth_app_donorprofile WHERE country_id IS NOT NULL AND country_id != ""')
        donor_rows = cursor.fetchall()
        donor_migrated = 0
        donor_not_found = []
        
        for donor_id, country_name in donor_rows:
            if country_name:
                try:
                    country = CountryLookup.objects.get(name__iexact=country_name)
                    cursor.execute('UPDATE auth_app_donorprofile SET country_fk_id = %s WHERE id = %s', [country.id, donor_id])
                    donor_migrated += 1
                    self.stdout.write(f'✓ Donor {donor_id}: {country_name} → {country.name}')
                except CountryLookup.DoesNotExist:
                    donor_not_found.append((donor_id, country_name))
                    # Try to find "Other"
                    try:
                        other = CountryLookup.objects.get(code='OTH')
                        cursor.execute('UPDATE auth_app_donorprofile SET country_fk_id = %s WHERE id = %s', [other.id, donor_id])
                        self.stdout.write(f'⚠ Donor {donor_id}: {country_name} → Other (not found)')
                    except CountryLookup.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'✗ Donor {donor_id}: Country "{country_name}" not found and no "Other" option'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n✅ Migration complete!'))
        self.stdout.write(f'   Patients migrated: {patient_migrated}')
        self.stdout.write(f'   Donors migrated: {donor_migrated}')
        
        if patient_not_found:
            self.stdout.write(self.style.WARNING(f'\n⚠ Patients with unmapped countries: {len(patient_not_found)}'))
            for pid, country in patient_not_found:
                self.stdout.write(f'   - Patient {pid}: {country}')
        
        if donor_not_found:
            self.stdout.write(self.style.WARNING(f'\n⚠ Donors with unmapped countries: {len(donor_not_found)}'))
            for did, country in donor_not_found:
                self.stdout.write(f'   - Donor {did}: {country}')
