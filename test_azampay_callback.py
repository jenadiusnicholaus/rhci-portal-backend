#!/usr/bin/env python3
"""
Test AzamPay callback endpoint manually
"""
import requests
import json

# Your production callback URL
CALLBACK_URL = "https://rhci.co.tz/api/v1.0/donors/payment/azampay/callback/"

# Sample AzamPay callback payload (successful payment)
callback_payload = {
    "amount": "50000",
    "clientId": "your_client_id",
    "externalreference": "RHCI-DN-185-20250412134635",  # Use real donation ID
    "message": "Transaction successful",
    "mnoreference": "MPE123456789",
    "msisdn": "255789123456",
    "operator": "Mpesa",
    "password": "",  # Add webhook password if configured
    "reference": "AZM987654321",
    "transactionstatus": "success",  # This is the key field!
    "transid": "TXN123456789",
    "user": "user_id",
    "utilityref": "utility_reference",
    "additionalProperties": {
        "donation_id": "185"  # Fallback donation ID
    }
}

def test_callback():
    print("Testing AzamPay callback endpoint...")
    print(f"URL: {CALLBACK_URL}")
    print(f"Payload: {json.dumps(callback_payload, indent=2)}")
    
    try:
        response = requests.post(
            CALLBACK_URL,
            json=callback_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n\n")
            print("=" * 50)
            print("SUCCESS! Callback endpoint is working!")
            print("Check if donation status changed to COMPLETED")
            print("=" * 50)
        else:
            print("\n\n")
            print("=" * 50)
            print("ERROR! Callback endpoint failed!")
            print("Check the response above for details")
            print("=" * 50)
            
    except requests.exceptions.RequestException as e:
        print(f"\n\nERROR: Request failed: {e}")

if __name__ == "__main__":
    test_callback()
