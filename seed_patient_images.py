#!/usr/bin/env python
"""
Patient Image Seeding Script - DEVELOPMENT ONLY

⚠️  IMPORTANT: This script is for DEVELOPMENT/TESTING purposes only!

Real healthcare platforms like Watsi.org use ACTUAL PATIENT PHOTOS:
- Real photos of patients who need medical help
- Images taken by medical partners/staff with proper consent
- Photos that show actual medical conditions when appropriate
- Professional photography that maintains patient dignity

For PRODUCTION use, you should:
1. Collect real patient photos through medical partners
2. Ensure proper patient consent and privacy compliance
3. Use professional photography that respects patient dignity
4. Store images securely with proper access controls

This script downloads placeholder portraits for development/demo purposes only.

Usage:
    python seed_patient_images.py              # Seed patients without photos
    python seed_patient_images.py --force      # Re-download images for all patients
    python seed_patient_images.py --clear      # Clear all patient images
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

from patient.models import PatientProfile

def download_image(url, timeout=10):
    """Download image from URL and return content"""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check if it's an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            print(f"  ❌ Not an image: {content_type}")
            return None
        
        # Load image content
        image_content = BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            image_content.write(chunk)
        image_content.seek(0)
        
        # Validate it's a valid image
        try:
            img = Image.open(image_content)
            img.verify()
            image_content.seek(0)
            return image_content.read()
        except Exception as e:
            print(f"  ❌ Invalid image: {e}")
            return None
            
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return None

def get_patient_image_urls():
    """Get images showing sick people seeking healthcare support - like real Watsi patient photos"""
    # IMPORTANT: This is for development/demo purposes only
    # Real healthcare platforms like Watsi.org use ACTUAL patient photos showing:
    # - Real patients with their medical conditions
    # - Authentic photos taken by medical partners
    # - Images that show the actual person who needs help
    # 
    # For production, you should:
    # 1. Use real patient photos (with proper consent)
    # 2. Photos taken by medical staff/partners
    # 3. Images that show the actual medical condition when appropriate
    # 4. Professional photos that maintain patient dignity
    
    # Images showing people in hospital/medical settings seeking healthcare support
    medical_support_urls = [
        # Patients in hospitals - sick people seeking medical help
        "https://images.unsplash.com/photo-1631815588090-d4bfec5b1ccb?w=400&h=400&fit=crop",  # Hospital patient
        "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=400&h=400&fit=crop",  # Patient in hospital
        "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=400&h=400&fit=crop",  # Sick person in clinic
        "https://images.unsplash.com/photo-1666214280557-f1b5022eb634?w=400&h=400&fit=crop",  # Medical patient
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=400&h=400&fit=crop",  # Patient needing care
        "https://images.unsplash.com/photo-1584362917165-526a968579e8?w=400&h=400&fit=crop",  # Hospital patient care
        
        # Medical consultations - people seeking healthcare support
        "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=400&h=400&fit=crop",  # Patient consultation
        "https://images.unsplash.com/photo-1638202993928-7267aad84c31?w=400&h=400&fit=crop",  # Medical examination
        "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&h=400&fit=crop",  # Patient checkup
        "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=400&h=400&fit=crop",  # Clinical visit
        
        # Sick children needing medical care
        "https://images.unsplash.com/photo-1631815589968-fdb09a223b1e?w=400&h=400&fit=crop",  # Sick child in hospital
        "https://images.unsplash.com/photo-1578496479914-7ef3b0193be3?w=400&h=400&fit=crop",  # Child patient
        "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&h=400&fit=crop",  # Pediatric patient
        "https://images.unsplash.com/photo-1581594693702-fbdc51b2763b?w=400&h=400&fit=crop",  # Child in medical care
        "https://images.unsplash.com/photo-1632053002940-e134d77f0b31?w=400&h=400&fit=crop",  # Young patient
        
        # Elderly patients in need of medical support
        "https://images.unsplash.com/photo-1581594549595-35f6edc7b762?w=400&h=400&fit=crop",  # Elderly patient
        "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&h=400&fit=crop",  # Senior in clinic
        "https://images.unsplash.com/photo-1581594693702-fbdc51b2763b?w=400&h=400&fit=crop",  # Elderly care
        
        # People with medical conditions seeking help
        "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=400&h=400&fit=crop",  # Patient with IV
        "https://images.unsplash.com/photo-1581594549595-35f6edc7b762?w=400&h=400&fit=crop",  # Medical treatment
        "https://images.unsplash.com/photo-1551076805-e1869033e561?w=400&h=400&fit=crop",  # Hospital care
        "https://images.unsplash.com/photo-1584362917165-526a968579e8?w=400&h=400&fit=crop",  # Patient recovery
        
        # African/Global patients in healthcare settings (matching your patient demographics)
        "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=400&h=400&fit=crop",  # International patient
        "https://images.unsplash.com/photo-1631815588090-d4bfec5b1ccb?w=400&h=400&fit=crop",  # Global healthcare
        "https://images.unsplash.com/photo-1666214280557-f1b5022eb634?w=400&h=400&fit=crop",  # Medical support
        
        # Medical conditions and healthcare needs
        "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=400&h=400&fit=crop",  # Clinical patient
        "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=400&h=400&fit=crop",  # Hospital setting
        "https://images.unsplash.com/photo-1638202993928-7267aad84c31?w=400&h=400&fit=crop",  # Medical examination
        "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=400&h=400&fit=crop",  # Healthcare seeker
        "https://images.unsplash.com/photo-1632053002940-e134d77f0b31?w=400&h=400&fit=crop",  # Patient in need
    ]
    
    return medical_support_urls

def assign_image_to_patient(patient, image_content, url):
    """Assign downloaded image to patient"""
    try:
        # Generate filename
        filename = f"patient_{patient.id}_{uuid.uuid4().hex[:8]}.jpg"
        
        # Save image to patient
        patient.photo.save(
            filename,
            ContentFile(image_content),
            save=True
        )
        
        print(f"  ✅ Image assigned: {patient.photo.url}")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to assign image: {e}")
        return False

def seed_patient_images():
    """Main function to seed patient images"""
    print("🖼️  SEEDING PATIENT IMAGES FROM INTERNET")
    print("=" * 50)
    
    # Get patients without photos
    patients_without_photos = PatientProfile.objects.filter(photo__isnull=True) | \
                             PatientProfile.objects.filter(photo='')
    
    if not patients_without_photos.exists():
        print("✅ All patients already have photos!")
        return
    
    print(f"📊 Found {patients_without_photos.count()} patients without photos")
    
    # Get image URLs
    image_urls = get_patient_image_urls()
    print(f"🔗 Using {len(image_urls)} image sources")
    
    success_count = 0
    fail_count = 0
    
    for i, patient in enumerate(patients_without_photos):
        print(f"\n👤 [{i+1}/{patients_without_photos.count()}] {patient.full_name} (ID: {patient.id})")
        
        # Try multiple URLs for this patient
        assigned = False
        for url_index in range(min(3, len(image_urls))):
            url = image_urls[(i + url_index) % len(image_urls)]
            print(f"  🟠 Trying: {url[:60]}...")
            
            # Download image
            image_content = download_image(url)
            if image_content:
                # Assign to patient
                if assign_image_to_patient(patient, image_content, url):
                    assigned = True
                    success_count += 1
                    break
        
        if not assigned:
            print(f"  ❌ Failed to assign any image to {patient.full_name}")
            fail_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ SEEDING COMPLETE!")
    print(f"✅ Successfully assigned: {success_count} images")
    print(f"❌ Failed assignments: {fail_count} patients")
    
    if success_count > 0:
        print(f"\n📷 Images saved to: {settings.MEDIA_ROOT}/patient_photos/")

def clear_patient_images():
    """Clear all patient images"""
    print("🗑️  CLEARING ALL PATIENT IMAGES")
    print("=" * 50)
    
    patients_with_photos = PatientProfile.objects.exclude(photo__isnull=True).exclude(photo='')
    count = patients_with_photos.count()
    
    if count == 0:
        print("✅ No patient images to clear!")
        return
    
    confirmation = input(f"❓ Are you sure you want to delete {count} patient images? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("❌ Operation cancelled")
        return
    
    cleared_count = 0
    for patient in patients_with_photos:
        try:
            if patient.photo:
                # Delete the file
                patient.photo.delete(save=False)
                patient.photo = None
                patient.save()
                cleared_count += 1
                print(f"  ✅ Cleared: {patient.full_name}")
        except Exception as e:
            print(f"  ❌ Failed to clear {patient.full_name}: {e}")
    
    print(f"\n✅ Cleared {cleared_count} patient images")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed patient images from internet")
    parser.add_argument('--clear', action='store_true', help='Clear all existing patient images')
    parser.add_argument('--force', action='store_true', help='Force re-download images for all patients')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_patient_images()
    else:
        if args.force:
            print("🟠 Force mode: Clearing existing images first...")
            # Clear images without confirmation in force mode
            patients_with_photos = PatientProfile.objects.exclude(photo__isnull=True).exclude(photo='')
            for patient in patients_with_photos:
                if patient.photo:
                    patient.photo.delete(save=False)
                    patient.photo = None
                    patient.save()
        
        seed_patient_images()
    
    print("\n🎉 Done!")