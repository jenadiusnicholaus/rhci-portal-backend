from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from patient.models import PatientProfile, ExpenseTypeLookup, TreatmentCostBreakdown, PatientTimeline
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample patient data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample patients...')
        
        # Create expense types first
        expense_types = [
            {'name': 'Hospital Fees', 'slug': 'hospital-fees', 'display_order': 1},
            {'name': 'Medical Staff', 'slug': 'medical-staff', 'display_order': 2},
            {'name': 'Medication', 'slug': 'medication', 'display_order': 3},
            {'name': 'Medical Equipment', 'slug': 'medical-equipment', 'display_order': 4},
            {'name': 'Lab Tests', 'slug': 'lab-tests', 'display_order': 5},
        ]
        
        for et_data in expense_types:
            ExpenseTypeLookup.objects.get_or_create(
                slug=et_data['slug'],
                defaults=et_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(expense_types)} expense types'))
        
        # Sample patient data
        patients_data = [
            {
                'email': 'peter.kimani@example.com',
                'first_name': 'Peter',
                'last_name': 'Kimani',
                'date_of_birth': date(1985, 3, 15),
                'full_name': 'Peter Kimani',
                'gender': 'M',
                'country': 'Kenya',
                'short_description': 'Father of three needs urgent tumor removal surgery',
                'long_story': 'Peter is a 40-year-old father of three from Nairobi, Kenya. He was diagnosed with a brain tumor that requires immediate surgical intervention. As a small shop owner, he cannot afford the $15,000 surgery cost.',
                'medical_partner': 'Nairobi General Hospital',
                'diagnosis': 'Benign Brain Tumor',
                'treatment_needed': 'Tumor Removal Surgery',
                'treatment_date': date.today() + timedelta(days=30),
                'funding_required': 15000.00,
                'funding_received': 6300.00,
                'total_treatment_cost': 15000.00,
                'status': 'AWAITING_FUNDING',
                'is_featured': True,
            },
            {
                'email': 'sarah.johnson@example.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'date_of_birth': date(1992, 7, 22),
                'full_name': 'Sarah Johnson',
                'gender': 'F',
                'country': 'Uganda',
                'short_description': 'Young mother needs life-saving heart surgery',
                'long_story': 'Sarah is a 33-year-old mother from Kampala, Uganda. She suffers from a congenital heart defect that has worsened over the years. Without surgery, doctors give her only months to live.',
                'medical_partner': 'Uganda Heart Institute',
                'diagnosis': 'Congenital Heart Disease',
                'treatment_needed': 'Heart Valve Replacement',
                'treatment_date': date.today() + timedelta(days=45),
                'funding_required': 25000.00,
                'funding_received': 18750.00,
                'total_treatment_cost': 25000.00,
                'status': 'AWAITING_FUNDING',
                'is_featured': True,
            },
            {
                'email': 'amina.hassan@example.com',
                'first_name': 'Amina',
                'last_name': 'Hassan',
                'date_of_birth': date(2010, 11, 8),
                'full_name': 'Amina Hassan',
                'gender': 'F',
                'country': 'Tanzania',
                'short_description': '15-year-old needs surgery to walk again',
                'long_story': 'Amina is a bright 15-year-old from Dar es Salaam who dreams of becoming a doctor. A severe spinal condition has left her unable to walk, but surgery could change everything.',
                'medical_partner': 'Muhimbili National Hospital',
                'diagnosis': 'Severe Scoliosis',
                'treatment_needed': 'Spinal Correction Surgery',
                'treatment_date': date.today() + timedelta(days=60),
                'funding_required': 20000.00,
                'funding_received': 12000.00,
                'total_treatment_cost': 20000.00,
                'status': 'AWAITING_FUNDING',
                'is_featured': True,
            },
            {
                'email': 'john.mwangi@example.com',
                'first_name': 'John',
                'last_name': 'Mwangi',
                'date_of_birth': date(1978, 5, 30),
                'full_name': 'John Mwangi',
                'gender': 'M',
                'country': 'Kenya',
                'short_description': 'Farmer needs kidney transplant to survive',
                'long_story': 'John is a 47-year-old farmer from Kisumu who has supported his family through agriculture. Kidney failure has left him dependent on dialysis, and he urgently needs a transplant.',
                'medical_partner': 'Kenyatta National Hospital',
                'diagnosis': 'End-Stage Renal Disease',
                'treatment_needed': 'Kidney Transplant',
                'treatment_date': date.today() + timedelta(days=90),
                'funding_required': 35000.00,
                'funding_received': 8750.00,
                'total_treatment_cost': 35000.00,
                'status': 'AWAITING_FUNDING',
                'is_featured': False,
            },
            {
                'email': 'grace.nakato@example.com',
                'first_name': 'Grace',
                'last_name': 'Nakato',
                'date_of_birth': date(2015, 2, 14),
                'full_name': 'Grace Nakato',
                'gender': 'F',
                'country': 'Uganda',
                'short_description': '10-year-old needs surgery for cleft palate',
                'long_story': 'Grace is a 10-year-old from rural Uganda born with a cleft palate. The surgery will not only improve her appearance but also her ability to speak and eat properly.',
                'medical_partner': 'CoRSU Hospital',
                'diagnosis': 'Bilateral Cleft Palate',
                'treatment_needed': 'Cleft Palate Repair',
                'treatment_date': date.today() + timedelta(days=20),
                'funding_required': 5000.00,
                'funding_received': 3750.00,
                'total_treatment_cost': 5000.00,
                'status': 'AWAITING_FUNDING',
                'is_featured': False,
            },
        ]
        
        created_count = 0
        for patient_data in patients_data:
            # Create user
            user, user_created = User.objects.get_or_create(
                email=patient_data['email'],
                defaults={
                    'user_type': 'PATIENT',
                    'first_name': patient_data['first_name'],
                    'last_name': patient_data['last_name'],
                    'date_of_birth': patient_data['date_of_birth'],
                    'is_active': True,
                    'is_verified': True,
                    'is_patient_verified': True,
                }
            )
            
            if user_created:
                user.set_password('password123')
                user.save()
            
            # Create patient profile
            profile, profile_created = PatientProfile.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': patient_data['full_name'],
                    'gender': patient_data['gender'],
                    'country': patient_data['country'],
                    'short_description': patient_data['short_description'],
                    'long_story': patient_data['long_story'],
                    'medical_partner': patient_data['medical_partner'],
                    'diagnosis': patient_data['diagnosis'],
                    'treatment_needed': patient_data['treatment_needed'],
                    'treatment_date': patient_data['treatment_date'],
                    'funding_required': patient_data['funding_required'],
                    'funding_received': patient_data['funding_received'],
                    'total_treatment_cost': patient_data['total_treatment_cost'],
                    'status': patient_data['status'],
                    'is_featured': patient_data['is_featured'],
                }
            )
            
            if profile_created:
                created_count += 1
                self.stdout.write(f'Created patient: {patient_data["full_name"]}')
                
                # Create cost breakdown
                hospital_fees = ExpenseTypeLookup.objects.get(slug='hospital-fees')
                medical_staff = ExpenseTypeLookup.objects.get(slug='medical-staff')
                medication = ExpenseTypeLookup.objects.get(slug='medication')
                
                TreatmentCostBreakdown.objects.create(
                    patient_profile=profile,
                    expense_type=hospital_fees,
                    amount=patient_data['funding_required'] * 0.5
                )
                TreatmentCostBreakdown.objects.create(
                    patient_profile=profile,
                    expense_type=medical_staff,
                    amount=patient_data['funding_required'] * 0.3
                )
                TreatmentCostBreakdown.objects.create(
                    patient_profile=profile,
                    expense_type=medication,
                    amount=patient_data['funding_required'] * 0.2
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {created_count} patients'))
        self.stdout.write(self.style.SUCCESS(f'✓ Total patients in database: {PatientProfile.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Featured patients: {PatientProfile.objects.filter(is_featured=True).count()}'))
