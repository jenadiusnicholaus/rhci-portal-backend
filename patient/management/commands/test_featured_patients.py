"""
Test script for Featured Patients API
Run this script to test the featured patient functionality.
"""

from django.core.management.base import BaseCommand
from patient.models import PatientProfile
from auth_app.models import CustomUser
from datetime import date


class Command(BaseCommand):
    help = 'Test featured patients functionality'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("Testing Featured Patients API"))
        self.stdout.write("="*60 + "\n")

        # Get published patients
        published_patients = PatientProfile.objects.filter(
            status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED']
        )
        
        self.stdout.write(f"✓ Found {published_patients.count()} published patients")
        
        # Check current featured patients
        featured_patients = PatientProfile.objects.filter(is_featured=True)
        self.stdout.write(f"✓ Currently {featured_patients.count()} patients are featured\n")
        
        if featured_patients.exists():
            self.stdout.write("Featured Patients:")
            for patient in featured_patients:
                self.stdout.write(f"  - {patient.full_name} (ID: {patient.id}, Status: {patient.status})")
        else:
            self.stdout.write(self.style.WARNING("  No patients are currently featured"))
        
        self.stdout.write("\n" + "-"*60)
        self.stdout.write("Testing: Feature Patient Toggle")
        self.stdout.write("-"*60 + "\n")
        
        if published_patients.exists():
            # Get first published patient
            test_patient = published_patients.first()
            original_featured_status = test_patient.is_featured
            
            self.stdout.write(f"Testing with patient: {test_patient.full_name} (ID: {test_patient.id})")
            self.stdout.write(f"  Current featured status: {original_featured_status}")
            
            # Toggle to featured
            test_patient.is_featured = True
            test_patient.save()
            test_patient.refresh_from_db()
            
            self.stdout.write(f"  After setting to featured: {test_patient.is_featured}")
            
            if test_patient.is_featured:
                self.stdout.write(self.style.SUCCESS("  ✓ Successfully featured patient"))
            else:
                self.stdout.write(self.style.ERROR("  ✗ Failed to feature patient"))
            
            # Check if patient appears in featured queryset
            featured_query = PatientProfile.objects.filter(
                user__is_patient_verified=True,
                status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED'],
                is_featured=True
            )
            
            if test_patient in featured_query:
                self.stdout.write(self.style.SUCCESS("  ✓ Patient appears in featured query"))
            else:
                self.stdout.write(self.style.ERROR("  ✗ Patient does not appear in featured query"))
                self.stdout.write(f"    User verified: {test_patient.user.is_patient_verified}")
                self.stdout.write(f"    Status: {test_patient.status}")
                self.stdout.write(f"    Is featured: {test_patient.is_featured}")
            
            # Restore original status
            test_patient.is_featured = original_featured_status
            test_patient.save()
            self.stdout.write(f"\n  Restored original featured status: {original_featured_status}")
        else:
            self.stdout.write(self.style.WARNING("  No published patients available for testing"))
        
        self.stdout.write("\n" + "-"*60)
        self.stdout.write("Testing: Validation Rules")
        self.stdout.write("-"*60 + "\n")
        
        # Check unpublished patients
        unpublished_patients = PatientProfile.objects.filter(
            status='SUBMITTED'
        )
        
        if unpublished_patients.exists():
            test_unpublished = unpublished_patients.first()
            self.stdout.write(f"✓ Found unpublished patient: {test_unpublished.full_name} (ID: {test_unpublished.id})")
            self.stdout.write(f"  Status: {test_unpublished.status}")
            self.stdout.write("  Note: API endpoint should reject featuring unpublished patients")
        else:
            self.stdout.write("  No unpublished patients found")
        
        self.stdout.write("\n" + "-"*60)
        self.stdout.write("API Endpoints to Test:")
        self.stdout.write("-"*60 + "\n")
        
        self.stdout.write("1. Feature a patient (Admin only):")
        if published_patients.exists():
            patient_id = published_patients.first().id
            self.stdout.write(f"   PATCH http://localhost:8000/api/v1.0/patients/admin/{patient_id}/featured/")
            self.stdout.write('   Body: {"is_featured": true}')
            self.stdout.write('   Headers: Authorization: Bearer <admin_token>')
        
        self.stdout.write("\n2. Get featured patients (Public):")
        self.stdout.write("   GET http://localhost:8000/api/v1.0/patients/public/featured/")
        
        self.stdout.write("\n3. Get patient stats (Admin only):")
        self.stdout.write("   GET http://localhost:8000/api/v1.0/patients/admin/stats/")
        self.stdout.write("   (Includes featured_patients count)")
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("Test Complete!"))
        self.stdout.write("="*60 + "\n")
