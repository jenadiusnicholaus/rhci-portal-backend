#!/usr/bin/env python
"""
Database Seeding Script for RHCI Portal
========================================

This script seeds the database with sample data including:
- Patients with complete profiles, timelines, and cost breakdowns
- Donors with profiles
- Countries (if not already populated)
- Expense types (if not already populated)

Usage:
    python seed_database.py [--patients=N] [--donors=N] [--clear]

Options:
    --patients=N    Number of patients to create (default: 5)
    --donors=N      Number of donors to create (default: 5)
    --clear         Clear existing test data before seeding
    --production    Run in production mode (careful!)

Example:
    python seed_database.py --patients=10 --donors=5
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from auth_app.lookups import CountryLookup
from patient.models import PatientProfile, ExpenseTypeLookup, TreatmentCostBreakdown, PatientTimeline, DonationAmountOption
from donor.models import DonorProfile

User = get_user_model()


# ============ SAMPLE DATA ============

COUNTRIES = [
    ('Kenya', 'KE'), ('Uganda', 'UG'), ('Tanzania', 'TZ'), ('Rwanda', 'RW'),
    ('Ethiopia', 'ET'), ('South Sudan', 'SS'), ('Somalia', 'SO'), ('Burundi', 'BI')
]

EXPENSE_TYPES = [
    ('Hospital Fees', 'hospital-fees', 'Basic hospital charges and room fees', 1),
    ('Medical Staff', 'medical-staff', 'Doctors, nurses, and medical professionals', 2),
    ('Surgery Costs', 'surgery-costs', 'Surgical procedure costs', 3),
    ('Medication', 'medication', 'Prescribed medicines and drugs', 4),
    ('Medical Supplies', 'medical-supplies', 'Medical equipment and supplies', 5),
]

PATIENT_DATA = [
    {
        'first_name': 'Peter', 'last_name': 'Kimani', 'email': 'peter.kimani@test.com',
        'gender': 'M', 'country': 'Kenya', 'dob': date(1990, 3, 15),
        'short_description': 'Young father needs life-saving brain tumor surgery',
        'long_story': '''Peter is a 34-year-old father of two from Nairobi, Kenya. He was diagnosed with a brain tumor 
that requires immediate surgical intervention. Peter works as a teacher and cannot afford the expensive surgery. 
His family is desperate for help to save his life and keep their family together.''',
        'diagnosis': 'Malignant brain tumor (Grade III glioma)',
        'treatment_needed': 'Neurosurgical tumor removal with post-operative care',
        'medical_partner': 'Kenyatta National Hospital',
        'funding_required': Decimal('15000.00'),
        'funding_received': Decimal('6300.00'),
        'is_featured': True,
        'status': 'AWAITING_FUNDING',
        'cost_breakdown': [
            ('Hospital Fees', 4000, 'ICU and ward fees'),
            ('Medical Staff', 5000, 'Neurosurgeon and medical team'),
            ('Surgery Costs', 4000, 'Operating room and equipment'),
            ('Medication', 1500, 'Post-surgery medications'),
            ('Medical Supplies', 500, 'Surgical supplies and dressings'),
        ]
    },
    {
        'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah.johnson@test.com',
        'gender': 'F', 'country': 'Uganda', 'dob': date(2010, 7, 22),
        'short_description': 'Young girl needs heart valve replacement surgery',
        'long_story': '''Sarah is a bright 14-year-old student from Kampala, Uganda, who was born with a congenital 
heart defect. She needs a heart valve replacement to live a normal life. Her single mother works as a market vendor 
and cannot afford the costly procedure. Sarah dreams of becoming a doctor to help others like herself.''',
        'diagnosis': 'Congenital heart valve defect',
        'treatment_needed': 'Heart valve replacement surgery',
        'medical_partner': 'Mulago National Referral Hospital',
        'funding_required': Decimal('12000.00'),
        'funding_received': Decimal('9000.00'),
        'is_featured': True,
        'status': 'AWAITING_FUNDING',
        'cost_breakdown': [
            ('Hospital Fees', 3000, 'Cardiac ward fees'),
            ('Medical Staff', 4500, 'Cardiac surgeon and team'),
            ('Surgery Costs', 3500, 'Heart valve and procedure'),
            ('Medication', 800, 'Anti-rejection and recovery meds'),
            ('Medical Supplies', 200, 'Cardiac monitoring equipment'),
        ]
    },
    {
        'first_name': 'Amina', 'last_name': 'Hassan', 'email': 'amina.hassan@test.com',
        'gender': 'F', 'country': 'Tanzania', 'dob': date(1985, 11, 8),
        'short_description': 'Mother of three needs urgent spinal surgery',
        'long_story': '''Amina is a 39-year-old mother from Dar es Salaam who suffered a spinal injury in an accident. 
She can no longer walk without surgery. Her husband works as a fisherman earning barely enough to feed their three children. 
Amina was once a seamstress and hopes to return to her work after recovery.''',
        'diagnosis': 'Spinal cord compression with paralysis',
        'treatment_needed': 'Spinal decompression and fusion surgery',
        'medical_partner': 'Muhimbili National Hospital',
        'funding_required': Decimal('18000.00'),
        'funding_received': Decimal('10800.00'),
        'is_featured': True,
        'status': 'AWAITING_FUNDING',
        'cost_breakdown': [
            ('Hospital Fees', 5000, 'Neurosurgical unit fees'),
            ('Medical Staff', 6000, 'Spinal surgeon and specialists'),
            ('Surgery Costs', 5000, 'Spinal implants and procedure'),
            ('Medication', 1500, 'Pain management and recovery'),
            ('Medical Supplies', 500, 'Surgical materials'),
        ]
    },
    {
        'first_name': 'John', 'last_name': 'Mwangi', 'email': 'john.mwangi@test.com',
        'gender': 'M', 'country': 'Kenya', 'dob': date(1978, 5, 30),
        'short_description': 'Farmer needs kidney transplant to survive',
        'long_story': '''John is a 46-year-old farmer from rural Kenya suffering from kidney failure. He needs a kidney 
transplant urgently. His brother has volunteered to be a donor, but the family cannot afford the surgery costs. 
John has six children depending on him and his farm is their only source of income.''',
        'diagnosis': 'End-stage renal disease (ESRD)',
        'treatment_needed': 'Kidney transplant surgery',
        'medical_partner': 'Nairobi Hospital',
        'funding_required': Decimal('25000.00'),
        'funding_received': Decimal('6250.00'),
        'is_featured': False,
        'status': 'AWAITING_FUNDING',
        'cost_breakdown': [
            ('Hospital Fees', 7000, 'Transplant unit extended stay'),
            ('Medical Staff', 8000, 'Transplant surgeon and team'),
            ('Surgery Costs', 7000, 'Kidney transplant procedure'),
            ('Medication', 2500, 'Immunosuppressants'),
            ('Medical Supplies', 500, 'Post-transplant supplies'),
        ]
    },
    {
        'first_name': 'Grace', 'last_name': 'Nakato', 'email': 'grace.nakato@test.com',
        'gender': 'F', 'country': 'Uganda', 'dob': date(2020, 1, 12),
        'short_description': 'Baby girl needs cleft palate repair surgery',
        'long_story': '''Grace is a 4-year-old girl born with a cleft palate. The condition makes it difficult for her 
to eat, speak, and breathe properly. Her parents are subsistence farmers who struggle to provide basic needs. 
This surgery will give Grace a chance at a normal childhood and prevent future complications.''',
        'diagnosis': 'Bilateral cleft lip and palate',
        'treatment_needed': 'Cleft palate repair surgery',
        'medical_partner': 'CoRSU Rehabilitation Hospital',
        'funding_required': Decimal('3500.00'),
        'funding_received': Decimal('2625.00'),
        'is_featured': False,
        'status': 'AWAITING_FUNDING',
        'cost_breakdown': [
            ('Hospital Fees', 800, 'Pediatric ward fees'),
            ('Medical Staff', 1200, 'Plastic surgeon and team'),
            ('Surgery Costs', 1000, 'Cleft repair procedure'),
            ('Medication', 300, 'Pediatric medications'),
            ('Medical Supplies', 200, 'Surgical materials'),
        ]
    },
]

DONOR_DATA = [
    {
        'first_name': 'Michael', 'last_name': 'Anderson', 'email': 'michael.anderson@donor.com',
        'country': 'Kenya', 'dob': date(1985, 4, 10),
        'short_bio': 'Tech entrepreneur passionate about healthcare access',
        'workplace': 'TechCare Solutions',
        'website': 'https://techcare.example.com',
    },
    {
        'first_name': 'Lisa', 'last_name': 'Thompson', 'email': 'lisa.thompson@donor.com',
        'country': 'Uganda', 'dob': date(1992, 8, 25),
        'short_bio': 'Nurse and healthcare advocate',
        'workplace': 'Kampala General Hospital',
        'website': '',
    },
    {
        'first_name': 'David', 'last_name': 'Ochieng', 'email': 'david.ochieng@donor.com',
        'country': 'Kenya', 'dob': date(1980, 12, 5),
        'short_bio': 'Business owner supporting community health',
        'workplace': 'Ochieng & Associates',
        'website': 'https://ochieng.example.com',
    },
    {
        'first_name': 'Emily', 'last_name': 'Musoke', 'email': 'emily.musoke@donor.com',
        'country': 'Tanzania', 'dob': date(1988, 6, 18),
        'short_bio': 'Educator and philanthropist',
        'workplace': 'Dar es Salaam International School',
        'website': '',
    },
    {
        'first_name': 'James', 'last_name': 'Kariuki', 'email': 'james.kariuki@donor.com',
        'country': 'Kenya', 'dob': date(1975, 3, 22),
        'short_bio': 'Retired doctor dedicated to helping patients',
        'workplace': 'RHCI Volunteer',
        'website': '',
    },
]


# ============ HELPER FUNCTIONS ============

def ensure_countries():
    """Ensure country lookup data exists"""
    print("📍 Checking countries...")
    created_count = 0
    for country_name, code in COUNTRIES:
        country, created = CountryLookup.objects.get_or_create(
            name=country_name,
            defaults={'code': code, 'is_active': True}
        )
        if created:
            created_count += 1
    
    if created_count > 0:
        print(f"   ✓ Created {created_count} countries")
    else:
        print(f"   ✓ All countries exist ({CountryLookup.objects.count()} total)")


def ensure_expense_types():
    """Ensure expense type lookup data exists"""
    print("💰 Checking expense types...")
    created_count = 0
    for name, slug, description, order in EXPENSE_TYPES:
        expense_type, created = ExpenseTypeLookup.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': description,
                'display_order': order,
                'is_active': True
            }
        )
        if created:
            created_count += 1
    
    if created_count > 0:
        print(f"   ✓ Created {created_count} expense types")
    else:
        print(f"   ✓ All expense types exist ({ExpenseTypeLookup.objects.count()} total)")


def create_patient(data, admin_user):
    """Create a patient with complete profile, cost breakdown, and timeline"""
    # Get country
    country = CountryLookup.objects.get(name=data['country'])
    
    # Create user
    user = User.objects.create_user(
        email=data['email'],
        password='Test123!@#',
        first_name=data['first_name'],
        last_name=data['last_name'],
        user_type='PATIENT',
        date_of_birth=data['dob'],
        is_verified=True,
        is_patient_verified=True,
    )
    
    # Create patient profile
    full_name = f"{data['first_name']} {data['last_name']}"
    profile = PatientProfile.objects.create(
        user=user,
        full_name=full_name,
        gender=data['gender'],
        country_fk=country,
        short_description=data['short_description'],
        long_story=data['long_story'],
        diagnosis=data['diagnosis'],
        treatment_needed=data['treatment_needed'],
        medical_partner=data['medical_partner'],
        treatment_date=date.today() + timedelta(days=random.randint(30, 90)),
        funding_required=data['funding_required'],
        funding_received=data['funding_received'],
        total_treatment_cost=data['funding_required'],
        status=data['status'],
        is_featured=data['is_featured'],
    )
    
    # Create cost breakdown
    for expense_name, amount, notes in data['cost_breakdown']:
        expense_slug = expense_name.lower().replace(' ', '-')
        expense_type = ExpenseTypeLookup.objects.get(slug=expense_slug)
        TreatmentCostBreakdown.objects.create(
            patient_profile=profile,
            expense_type=expense_type,
            amount=Decimal(str(amount)),
            notes=notes
        )
    
    # Create timeline events
    base_date = date.today() - timedelta(days=random.randint(30, 60))
    
    # Profile submitted
    PatientTimeline.objects.create(
        patient_profile=profile,
        event_type='PROFILE_SUBMITTED',
        title='Profile Submitted',
        description=f'{full_name} submitted their profile for review',
        event_date=base_date,
        created_by=user,
        is_milestone=True,
        is_visible=True,
    )
    
    # Treatment scheduled
    PatientTimeline.objects.create(
        patient_profile=profile,
        event_type='TREATMENT_SCHEDULED',
        title='Treatment Scheduled',
        description=f'Surgery scheduled at {data["medical_partner"]}',
        event_date=profile.treatment_date,
        created_by=admin_user,
        is_milestone=True,
        is_visible=True,
    )
    
    # Profile published
    PatientTimeline.objects.create(
        patient_profile=profile,
        event_type='PROFILE_PUBLISHED',
        title='Profile Published',
        description='Profile approved and published on RHCI platform',
        event_date=base_date + timedelta(days=2),
        created_by=admin_user,
        is_milestone=True,
        is_visible=True,
    )
    
    # Funding milestone
    funding_pct = (data['funding_received'] / data['funding_required']) * 100
    if funding_pct >= 25:
        PatientTimeline.objects.create(
            patient_profile=profile,
            event_type='FUNDING_MILESTONE',
            title=f'{int(funding_pct)}% Funded!',
            description=f'Reached {int(funding_pct)}% of funding goal. Thank you to all donors!',
            event_date=base_date + timedelta(days=random.randint(5, 15)),
            created_by=admin_user,
            is_milestone=True,
            is_visible=True,
            metadata={'percentage': int(funding_pct), 'amount': str(data['funding_received'])}
        )
    
    # Create donation amount options (quick select buttons)
    # Calculate smart amounts based on funding remaining
    remaining = data['funding_required'] - data['funding_received']
    
    # Create 4 suggested amounts similar to the image ($10, $28, $56, $150)
    amounts = [
        (remaining * Decimal('0.01'), 1, False),  # ~1% of remaining
        (remaining * Decimal('0.03'), 2, False),  # ~3% of remaining
        (remaining * Decimal('0.05'), 3, False),  # ~5% of remaining
        (remaining * Decimal('0.15'), 4, True),   # ~15% of remaining (recommended)
    ]
    
    for amount, order, is_recommended in amounts:
        # Round to nearest $5 or $10
        if amount < 50:
            rounded_amount = round(amount / 5) * 5
        else:
            rounded_amount = round(amount / 10) * 10
        
        if rounded_amount > 0:
            DonationAmountOption.objects.create(
                patient_profile=profile,
                amount=Decimal(str(rounded_amount)),
                display_order=order,
                is_active=True,
                is_recommended=is_recommended
            )
    
    return profile


def create_donor(data):
    """Create a donor with profile"""
    from django.db.models.signals import post_save
    from donor.signals import create_donor_profile
    
    # Temporarily disconnect the signal to avoid auto-creation issues
    post_save.disconnect(create_donor_profile, sender=User)
    
    try:
        # Get country
        country = CountryLookup.objects.get(name=data['country'])
        
        # Create user
        user = User.objects.create_user(
            email=data['email'],
            password='Test123!@#',
            first_name=data['first_name'],
            last_name=data['last_name'],
            user_type='DONOR',
            date_of_birth=data['dob'],
            is_verified=True,
        )
        
        # Manually create donor profile with all fields
        full_name = f"{data['first_name']} {data['last_name']}"
        profile = DonorProfile.objects.create(
            user=user,
            full_name=full_name,
            short_bio=data['short_bio'],
            country_fk=country,
            workplace=data['workplace'],
            website=data['website'],
            birthday=data['dob'],
            is_profile_private=False,
        )
    finally:
        # Re-connect the signal
        post_save.connect(create_donor_profile, sender=User)
    
    return profile


def clear_test_data():
    """Clear existing test data (users with @test.com or @donor.com emails)"""
    print("\n🗑️  Clearing existing test data...")
    
    test_emails = [p['email'] for p in PATIENT_DATA] + [d['email'] for d in DONOR_DATA]
    deleted_count = User.objects.filter(email__in=test_emails).delete()[0]
    
    if deleted_count > 0:
        print(f"   ✓ Deleted {deleted_count} test users and related data")
    else:
        print("   ✓ No test data to clear")


# ============ MAIN SEEDING FUNCTION ============

def seed_database(num_patients=None, num_donors=None, clear=False):
    """
    Seed the database with sample data
    
    Args:
        num_patients: Number of patients to create (defaults to all sample data)
        num_donors: Number of donors to create (defaults to all sample data)
        clear: Whether to clear existing test data first
    """
    print("\n" + "="*60)
    print("🌱 RHCI DATABASE SEEDING")
    print("="*60)
    
    # Clear test data if requested
    if clear:
        clear_test_data()
    
    # Ensure lookup data exists
    ensure_countries()
    ensure_expense_types()
    
    # Get or create admin user for timeline events
    admin_user, _ = User.objects.get_or_create(
        email='admin@rhci.org',
        defaults={
            'first_name': 'Admin',
            'last_name': 'User',
            'user_type': 'ADMIN',
            'is_staff': True,
            'is_superuser': True,
            'is_verified': True,
        }
    )
    if _:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"\n👤 Created admin user: admin@rhci.org (password: admin123)")
    
    # Determine how many to create
    patients_to_create = PATIENT_DATA[:num_patients] if num_patients else PATIENT_DATA
    donors_to_create = DONOR_DATA[:num_donors] if num_donors else DONOR_DATA
    
    # Create patients
    print(f"\n👥 Creating {len(patients_to_create)} patients...")
    for i, patient_data in enumerate(patients_to_create, 1):
        try:
            profile = create_patient(patient_data, admin_user)
            print(f"   {i}. ✓ {profile.full_name} ({profile.country_fk.name}) - ${profile.funding_received}/${profile.funding_required}")
        except Exception as e:
            print(f"   {i}. ✗ Failed to create {patient_data['email']}: {e}")
    
    # Create donors
    print(f"\n💝 Creating {len(donors_to_create)} donors...")
    for i, donor_data in enumerate(donors_to_create, 1):
        try:
            profile = create_donor(donor_data)
            print(f"   {i}. ✓ {profile.full_name} ({profile.country_fk.name})")
        except Exception as e:
            print(f"   {i}. ✗ Failed to create {donor_data['email']}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("✅ SEEDING COMPLETE!")
    print("="*60)
    print(f"📊 Database Summary:")
    print(f"   - Countries: {CountryLookup.objects.count()}")
    print(f"   - Expense Types: {ExpenseTypeLookup.objects.count()}")
    print(f"   - Patients: {PatientProfile.objects.count()}")
    print(f"   - Donors: {DonorProfile.objects.count()}")
    print(f"   - Timeline Events: {PatientTimeline.objects.count()}")
    print(f"   - Cost Breakdowns: {TreatmentCostBreakdown.objects.count()}")
    print(f"   - Donation Amount Options: {DonationAmountOption.objects.count()}")
    
    print("\n🔐 Test Credentials:")
    print("   Admin: admin@rhci.org / admin123")
    print(f"   Patient: {PATIENT_DATA[0]['email']} / Test123!@#")
    print(f"   Donor: {DONOR_DATA[0]['email']} / Test123!@#")
    print("\n" + "="*60 + "\n")


# ============ CLI INTERFACE ============

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed RHCI database with sample data')
    parser.add_argument('--patients', type=int, help='Number of patients to create')
    parser.add_argument('--donors', type=int, help='Number of donors to create')
    parser.add_argument('--clear', action='store_true', help='Clear existing test data first')
    parser.add_argument('--production', action='store_true', help='Allow running in production (use with caution!)')
    
    args = parser.parse_args()
    
    # Safety check for production
    if not args.production:
        from django.conf import settings
        if not settings.DEBUG:
            print("❌ ERROR: This appears to be a production environment (DEBUG=False)")
            print("   To run in production, use --production flag (use with extreme caution!)")
            sys.exit(1)
    
    seed_database(
        num_patients=args.patients,
        num_donors=args.donors,
        clear=args.clear
    )
