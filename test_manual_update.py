#!/usr/bin/env python3
"""
Test manual payment update endpoint with real donation data
"""
import requests
import json

# Manual update endpoint
MANUAL_UPDATE_URL = "https://rhci.co.tz/api/v1.0/donors/payment/azampay/manual-update/"

# Real donation data from your logs
manual_update_payload = {
    "donation_id": 185,
    "status": "COMPLETED"
}

def test_manual_update():
    print("Testing manual payment update endpoint...")
    print(f"URL: {MANUAL_UPDATE_URL}")
    print(f"Payload: {json.dumps(manual_update_payload, indent=2)}")
    
    try:
        response = requests.post(
            MANUAL_UPDATE_URL,
            json=manual_update_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n\n")
            print("=" * 50)
            print("SUCCESS! Manual update worked!")
            print("Check if donation status changed to COMPLETED")
            print("=" * 50)
        else:
            print("\n\n")
            print("=" * 50)
            print("ERROR! Manual update failed!")
            print("Check response above for details")
            print("=" * 50)
            
    except requests.exceptions.RequestException as e:
        print(f"\n\nERROR: Request failed: {e}")

if __name__ == "__main__":
    test_manual_update()
