#!/usr/bin/env python
"""
Script to check user type and profile status
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from auth_app.models import CustomUser
from donor.models import DonorProfile

def check_user(email):
    """Check if user exists and has donor profile"""
    try:
        user = CustomUser.objects.get(email=email)
        print(f"\n✓ User found: {user.email}")
        print(f"  - ID: {user.id}")
        print(f"  - User Type: {user.user_type}")
        print(f"  - Is Active: {user.is_active}")
        print(f"  - Is Verified: {user.is_verified}")
        print(f"  - Name: {user.first_name} {user.last_name}")
        
        # Check for DonorProfile
        try:
            donor_profile = DonorProfile.objects.get(user=user)
            print(f"\n✓ DonorProfile exists:")
            print(f"  - ID: {donor_profile.id}")
            print(f"  - Full Name: {donor_profile.full_name}")
        except DonorProfile.DoesNotExist:
            print(f"\n✗ NO DonorProfile found!")
            print(f"  This user is registered as: {user.user_type}")
            if user.user_type == 'PATIENT':
                print(f"  → User needs to register as DONOR to access donor endpoints")
            elif user.user_type == 'DONOR':
                print(f"  → DonorProfile should have been created but is missing!")
                print(f"  → Creating DonorProfile now...")
                donor_profile = DonorProfile.objects.create(user=user)
                print(f"  ✓ DonorProfile created with ID: {donor_profile.id}")
        
    except CustomUser.DoesNotExist:
        print(f"\n✗ No user found with email: {email}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python check_user_type.py <email>")
        print("\nOr check all donors:")
        print("  python check_user_type.py --all-donors")
        sys.exit(1)
    
    if sys.argv[1] == '--all-donors':
        donors = CustomUser.objects.filter(user_type='DONOR')
        print(f"\nFound {donors.count()} DONOR users:")
        for user in donors:
            has_profile = DonorProfile.objects.filter(user=user).exists()
            status = "✓ Has profile" if has_profile else "✗ Missing profile"
            print(f"  {user.email} - {status}")
    else:
        email = sys.argv[1]
        check_user(email)
