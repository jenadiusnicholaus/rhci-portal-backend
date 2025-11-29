#!/usr/bin/env python
"""
Donor Account Seeding Script - DEVELOPMENT ONLY

Creates donor accounts with profile pictures for testing purposes.

Usage:
    python seed_donors.py              # Create donor accounts
    python seed_donors.py --clear      # Clear all donor accounts
"""

import os
import sys
import requests
import uuid
from io import BytesIO
from PIL import Image
import django
from django.conf import settings
from django.core.files.base import ContentFile

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from auth_app.models import CustomUser
from donor.models import DonorProfile


def download_image(url, timeout=10):
    """Download image from URL and return content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Verify it's an image
        img = Image.open(BytesIO(response.content))
        img.verify()
        
        # Re-open for saving (verify closes the file)
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        
        # Save to bytes
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        return output.read()
        
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return None


def get_donor_image_urls():
    """Get diverse profile images for donors"""
    donor_images = [
        # Professional diverse portraits for donors
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1494790108755-2616b9b9bbb8?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1488161628813-04466f872be2?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1552058544-f2b08422138a?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1504703395950-b89145a5425b?w=400&h=400&fit=crop&crop=face",
    ]
    return donor_images


def create_donor_account(email, password, first_name, last_name, photo_url=None):
    """Create a donor user account with profile"""
    try:
        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            print(f"  ⚠️  User {email} already exists, skipping...")
            return None
        
        # Create user
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type='DONOR',
            is_active=True,
            is_verified=True
        )
        
        print(f"  ✅ Created user: {email}")
        
        # Create donor profile
        donor_profile = DonorProfile.objects.create(
            user=user,
            full_name=f"{first_name} {last_name}",
            short_bio="Passionate healthcare supporter"
        )
        
        print(f"  ✅ Created donor profile for {first_name} {last_name}")
        
        # Download and assign photo if URL provided
        if photo_url:
            print(f"  🟠 Downloading profile photo...")
            image_content = download_image(photo_url)
            if image_content:
                filename = f"donor_{user.id}_{uuid.uuid4().hex[:8]}.jpg"
                donor_profile.photo.save(
                    filename,
                    ContentFile(image_content),
                    save=True
                )
                print(f"  ✅ Profile photo assigned: {donor_profile.photo.url}")
        
        return user
        
    except Exception as e:
        print(f"  ❌ Failed to create donor account: {e}")
        return None


def seed_donor_accounts():
    """Create multiple donor accounts for testing"""
    print("👥 SEEDING DONOR ACCOUNTS")
    print("=" * 50)
    
    # Donor accounts to create
    donors = [
        {
            "email": "donor1@gmail.com",
            "password": "donor123",
            "first_name": "Sarah",
            "last_name": "Johnson"
        },
        {
            "email": "donor2@gmail.com",
            "password": "donor123",
            "first_name": "Michael",
            "last_name": "Chen"
        },
        {
            "email": "donor3@gmail.com",
            "password": "donor123",
            "first_name": "Emily",
            "last_name": "Rodriguez"
        },
        {
            "email": "donor4@gmail.com",
            "password": "donor123",
            "first_name": "David",
            "last_name": "Omondi"
        },
        {
            "email": "donor5@gmail.com",
            "password": "donor123",
            "first_name": "Jessica",
            "last_name": "Kamau"
        },
        {
            "email": "testdonor@gmail.com",
            "password": "1234",
            "first_name": "Test",
            "last_name": "Donor"
        }
    ]
    
    image_urls = get_donor_image_urls()
    success_count = 0
    
    for i, donor_data in enumerate(donors):
        print(f"\n👤 [{i+1}/{len(donors)}] Creating {donor_data['first_name']} {donor_data['last_name']}")
        
        # Assign image URL (cycle through available images)
        photo_url = image_urls[i % len(image_urls)]
        
        user = create_donor_account(
            email=donor_data['email'],
            password=donor_data['password'],
            first_name=donor_data['first_name'],
            last_name=donor_data['last_name'],
            photo_url=photo_url
        )
        
        if user:
            success_count += 1
            print(f"  📧 Email: {donor_data['email']}")
            print(f"  🔑 Password: {donor_data['password']}")
    
    print("\n" + "=" * 50)
    print(f"✅ SEEDING COMPLETE!")
    print(f"✅ Successfully created: {success_count} donor accounts")
    print(f"\n📝 TEST CREDENTIALS:")
    print(f"   Email: testdonor@gmail.com")
    print(f"   Password: 1234")


def clear_donor_accounts():
    """Clear all donor accounts"""
    print("🗑️  CLEARING DONOR ACCOUNTS")
    print("=" * 50)
    
    # Get all donor users
    donor_users = CustomUser.objects.filter(user_type='DONOR')
    count = donor_users.count()
    
    if count == 0:
        print("✅ No donor accounts to clear!")
        return
    
    confirmation = input(f"❓ Are you sure you want to delete {count} donor accounts? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("❌ Operation cancelled")
        return
    
    # Delete donor profiles (will cascade delete photos)
    DonorProfile.objects.filter(user__user_type='DONOR').delete()
    
    # Delete donor users
    deleted_count = donor_users.delete()[0]
    
    print(f"\n✅ Deleted {deleted_count} donor accounts")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed donor accounts with images")
    parser.add_argument('--clear', action='store_true', help='Clear all donor accounts')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_donor_accounts()
    else:
        seed_donor_accounts()
    
    print("\n🎉 Done!")
