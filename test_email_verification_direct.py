#!/usr/bin/env python
"""
Direct test of email verification functionality
Run with: ./env/bin/python test_email_verification_direct.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from django.contrib.auth import get_user_model
from utils.email_verification import (
    generate_verification_token, 
    create_verification_token_hash,
    send_verification_email
)
from django.utils import timezone

User = get_user_model()

def test_email_sending():
    print("="*60)
    print("Testing Email Verification System")
    print("="*60)
    print()
    
    # 1. Create a test user
    test_email = f"test_direct_{int(timezone.now().timestamp())}@example.com"
    print(f"1. Creating test user: {test_email}")
    
    try:
        # Delete if exists
        User.objects.filter(email=test_email).delete()
        
        # Generate token
        token = generate_verification_token()
        token_hash = create_verification_token_hash(token)
        
        # Create user
        user = User.objects.create_user(
            email=test_email,
            password="TestPass123",
            first_name="Test",
            last_name="User",
            user_type='DONOR',
            is_active=False,
            is_verified=False,
            email_verification_token=token_hash,
            email_verification_sent_at=timezone.now()
        )
        
        print(f"   ✅ User created with ID: {user.id}")
        print(f"   - Email: {user.email}")
        print(f"   - is_active: {user.is_active}")
        print(f"   - is_verified: {user.is_verified}")
        print(f"   - Token hash stored: {token_hash[:20]}...")
        print()
        
        # 2. Test email sending
        print("2. Testing email sending...")
        verification_url = f"http://localhost:8000/api/v1.0/auth/donor/verify-email/?token={token}"
        
        try:
            send_verification_email(user, verification_url, user_type='donor')
            print(f"   ✅ Email sent successfully!")
            print(f"   - To: {user.email}")
            print(f"   - Verification URL: {verification_url[:60]}...")
            print()
            print("="*60)
            print("SUCCESS! Email verification system is working")
            print("="*60)
            print()
            print("Next steps:")
            print(f"1. Check email at: {test_email}")
            print("2. Click the verification link")
            print("3. Or test the URL manually:")
            print(f"   {verification_url}")
            
        except Exception as e:
            print(f"   ❌ Email sending failed!")
            print(f"   Error: {str(e)}")
            print()
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_email_sending()
