#!/usr/bin/env python
"""Seed images for existing donor profiles"""
import os, sys, django, requests, uuid
from io import BytesIO
from PIL import Image

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from donor.models import DonorProfile
from django.core.files.base import ContentFile

def download_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        img.verify()
        img = Image.open(BytesIO(response.content))
        
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)
        return output.read()
    except Exception as e:
        print(f"  ❌ {e}")
        return None

images = [
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop",
    "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop",
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop",
    "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=400&h=400&fit=crop",
    "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=400&h=400&fit=crop",
]

profiles = DonorProfile.objects.filter(photo__isnull=True) | DonorProfile.objects.filter(photo='')
print(f"🖼️  Seeding images for {profiles.count()} donor profiles")

for i, profile in enumerate(profiles):
    url = images[i % len(images)]
    print(f"\n👤 {profile.user.email}")
    content = download_image(url)
    if content:
        filename = f"donor_{profile.user.id}_{uuid.uuid4().hex[:8]}.jpg"
        profile.photo.save(filename, ContentFile(content), save=True)
        print(f"  ✅ Photo assigned")

print("\n✅ Done!")
