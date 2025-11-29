"""
Management command to seed donors and donations for testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from donor.models import DonorProfile, Donation
from patient.models import PatientProfile
from decimal import Decimal
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed donors and donations for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--donors',
            type=int,
            default=10,
            help='Number of donor accounts to create (default: 10)'
        )
        parser.add_argument(
            '--donations',
            type=int,
            default=20,
            help='Number of donations to create (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test donors and donations before seeding'
        )

    def handle(self, *args, **options):
        num_donors = options['donors']
        num_donations = options['donations']
        clear_existing = options['clear']

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("Seeding Donors and Donations"))
        self.stdout.write("="*60 + "\n")

        # Clear existing test data if requested
        if clear_existing:
            self.stdout.write("Clearing existing test data...")
            User.objects.filter(email__startswith='donor_test').delete()
            User.objects.filter(email__startswith='anonymous_donor').delete()
            self.stdout.write(self.style.SUCCESS("✓ Cleared existing test donors\n"))

        # Get published patients for donations
        published_patients = PatientProfile.objects.filter(
            status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED']
        )
        
        if not published_patients.exists():
            self.stdout.write(self.style.ERROR("✗ No published patients found. Please create patients first."))
            return

        self.stdout.write(f"Found {published_patients.count()} published patients\n")

        # Sample donor data
        donor_names = [
            ('John', 'Smith', 'Tech enthusiast helping those in need'),
            ('Sarah', 'Johnson', 'Healthcare advocate and philanthropist'),
            ('Michael', 'Williams', 'Passionate about medical equity'),
            ('Emily', 'Brown', 'Supporting life-saving treatments'),
            ('David', 'Jones', 'Making a difference one donation at a time'),
            ('Lisa', 'Garcia', 'Believer in accessible healthcare for all'),
            ('Robert', 'Miller', 'Helping patients achieve their dreams'),
            ('Jennifer', 'Davis', 'Committed to supporting medical needs'),
            ('William', 'Rodriguez', 'Advocate for patient care'),
            ('Maria', 'Martinez', 'Spreading hope through giving'),
            ('James', 'Hernandez', 'Supporting critical medical procedures'),
            ('Linda', 'Lopez', 'Making healthcare accessible'),
            ('Richard', 'Gonzalez', 'Passionate donor and advocate'),
            ('Patricia', 'Wilson', 'Helping patients in need'),
            ('Charles', 'Anderson', 'Medical philanthropy supporter'),
        ]

        workplaces = [
            'Microsoft', 'Google', 'Apple', 'Amazon', 'Meta',
            'Tesla', 'Healthcare Corp', 'Tech Innovations',
            'Medical Solutions', 'Global Health Foundation',
            'Community Hospital', 'Wellness Center', 'Self-employed',
            'Consultant', 'Entrepreneur'
        ]

        # Create donor accounts
        created_donors = []
        self.stdout.write(f"Creating {num_donors} donor accounts...\n")
        
        for i in range(num_donors):
            first_name, last_name, bio = random.choice(donor_names)
            email = f"donor_test{i+1}@example.com"
            
            # Check if donor already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"  Skipping {email} (already exists)")
                donor = User.objects.get(email=email)
                created_donors.append(donor)
                continue
            
            # Create donor user
            donor = User.objects.create_user(
                email=email,
                password='donor123',
                first_name=first_name,
                last_name=last_name,
                user_type='DONOR',
                is_active=True,
                is_verified=True
            )
            
            # Update donor profile (created by signal)
            profile = donor.donor_profile
            profile.full_name = f"{first_name} {last_name}"
            profile.short_bio = bio
            profile.workplace = random.choice(workplaces)
            profile.is_profile_private = random.choice([True, False])
            profile.save()
            
            created_donors.append(donor)
            self.stdout.write(f"  ✓ Created donor: {profile.full_name} ({email})")
        
        self.stdout.write(self.style.SUCCESS(f"\n✓ Created {len(created_donors)} donor accounts\n"))

        # Create donations
        self.stdout.write(f"Creating {num_donations} donations...\n")
        
        donation_amounts = [10, 20, 25, 50, 75, 100, 150, 200, 250, 500, 1000]
        messages = [
            "Wishing you a speedy recovery!",
            "You are in our prayers. Stay strong!",
            "Hope this helps with your treatment.",
            "Sending love and support your way.",
            "Praying for your healing and recovery.",
            "You've got this! Stay positive!",
            "Thinking of you and your family.",
            "May God bless you with good health.",
            "Supporting your journey to recovery.",
            "Get well soon! We're rooting for you!",
            "",  # Some donations without messages
            "",
        ]
        
        created_donations = 0
        failed_donations = 0
        
        for i in range(num_donations):
            # Randomly choose between authenticated and anonymous donation
            is_anonymous = random.choice([True, False, False, False])  # 25% anonymous
            
            # Select random patient
            patient = random.choice(published_patients)
            amount = Decimal(str(random.choice(donation_amounts)))
            message = random.choice(messages)
            
            try:
                if is_anonymous:
                    # Create anonymous donation
                    donation = Donation.objects.create(
                        donor=None,
                        is_anonymous=True,
                        anonymous_name=random.choice(['Anonymous Donor', 'A Friend', 'Well-wisher']),
                        anonymous_email=f"anonymous_donor{i}@example.com",
                        patient=patient,
                        amount=amount,
                        donation_type='ONE_TIME',
                        status='COMPLETED',
                        payment_method='Credit Card',
                        transaction_id=f"TXN-ANON-{i:05d}",
                        payment_gateway='Stripe',
                        message=message
                    )
                    self.stdout.write(f"  ✓ Anonymous donation: ${amount} to {patient.full_name}")
                else:
                    # Create authenticated donation
                    donor = random.choice(created_donors)
                    donation = Donation.objects.create(
                        donor=donor,
                        is_anonymous=False,
                        patient=patient,
                        amount=amount,
                        donation_type='ONE_TIME',
                        status='COMPLETED',
                        payment_method='Credit Card',
                        transaction_id=f"TXN-{i:05d}",
                        payment_gateway='Stripe',
                        message=message
                    )
                    donor_name = donor.donor_profile.full_name if hasattr(donor, 'donor_profile') else donor.email
                    self.stdout.write(f"  ✓ Donation: ${amount} from {donor_name} to {patient.full_name}")
                
                # Set random creation date (last 30 days)
                days_ago = random.randint(0, 30)
                donation.created_at = datetime.now() - timedelta(days=days_ago)
                donation.save()
                
                created_donations += 1
                
            except Exception as e:
                failed_donations += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Failed to create donation: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f"\n✓ Created {created_donations} donations"))
        if failed_donations > 0:
            self.stdout.write(self.style.WARNING(f"✗ Failed to create {failed_donations} donations"))
        
        # Summary
        self.stdout.write("\n" + "-"*60)
        self.stdout.write("Summary:")
        self.stdout.write("-"*60)
        
        total_amount = Donation.objects.filter(status='COMPLETED').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        self.stdout.write(f"Total Donors: {len(created_donors)}")
        self.stdout.write(f"Total Donations: {created_donations}")
        self.stdout.write(f"Total Amount Raised: ${total_amount:,.2f}")
        
        # Show donations per patient
        self.stdout.write("\nDonations per patient:")
        for patient in published_patients:
            patient_donations = Donation.objects.filter(
                patient=patient,
                status='COMPLETED'
            )
            count = patient_donations.count()
            total = patient_donations.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
            if count > 0:
                self.stdout.write(f"  {patient.full_name}: {count} donations, ${total:,.2f}")
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("✓ Seeding Complete!"))
        self.stdout.write("="*60 + "\n")
        
        self.stdout.write("Test the endpoint:")
        self.stdout.write(f"  GET http://localhost:8000/api/v1.0/patients/public/{published_patients.first().id}/donors/")
        self.stdout.write("\nDonor credentials:")
        self.stdout.write("  Email: donor_test1@example.com")
        self.stdout.write("  Password: donor123\n")


from django.db import models
