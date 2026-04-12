#!/usr/bin/env python3
"""
Test Django URL resolver to check if callback URL is properly configured
"""
import os
import sys
import django

# Add project path
sys.path.append('/Users/mac/development/python_projects/rhci-portal-v1')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from django.urls import reverse
from django.test import Client

def test_callback_url():
    print("Testing Django URL configuration...")
    
    try:
        # Try to reverse the URL
        url = reverse('donor:azampay_callback')
        print(f"Reversed URL: {url}")
        
        # Test with Django test client
        client = Client()
        
        # Test POST request
        response = client.post('/api/v1.0/donors/payment/azampay/callback/', 
                             data={'test': 'data'},
                             content_type='application/json')
        
        print(f"Test Client Response Status: {response.status_code}")
        print(f"Test Client Response: {response.content.decode()}")
        
        # Test GET request (should fail with 405)
        response_get = client.get('/api/v1.0/donors/payment/azampay/callback/')
        print(f"GET Response Status: {response_get.status_code}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_callback_url()
