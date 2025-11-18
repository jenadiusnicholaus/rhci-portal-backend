"""
Test script for Admin Management API

This script demonstrates the admin workflow:
1. Admin logs in
2. Admin views pending patient submissions
3. Admin edits patient details
4. Admin approves patient
5. Admin publishes patient
6. Admin adds manual timeline events
7. View public patient profile

Run this script after starting the server:
    python manage.py runserver 0.0.0.0:8091

Then in another terminal:
    python auth_app/test_admin_api.py
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8091/api/auth"


def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)


def main():
    print("\n" + "="*70)
    print("  RHCI Portal - Admin Management API Test")
    print("="*70)
    
    # Step 1: Admin Login
    print("\n[1] Admin Login")
    admin_email = input("Enter admin email (default: admin@rhci.org): ").strip() or "admin@rhci.org"
    admin_password = input("Enter admin password: ").strip()
    
    login_response = requests.post(f"{BASE_URL}/login/", json={
        "email": admin_email,
        "password": admin_password
    })
    
    if login_response.status_code != 200:
        print_response("Login Failed", login_response)
        return
    
    admin_token = login_response.json()['tokens']['access']
    headers = {"Authorization": f"Bearer {admin_token}"}
    print("✅ Admin login successful!")
    
    # Step 2: View Pending Patient Submissions
    print("\n[2] Fetching pending patient submissions...")
    patients_response = requests.get(
        f"{BASE_URL}/admin/patients/",
        headers=headers,
        params={"status": "SUBMITTED", "ordering": "-created_at"}
    )
    print_response("Pending Patient Submissions", patients_response)
    
    if patients_response.status_code != 200 or not patients_response.json().get('results'):
        print("\n⚠️  No pending submissions found. Create a patient account first.")
        return
    
    # Select first patient
    patient = patients_response.json()['results'][0]
    patient_id = patient['id']
    print(f"\n📋 Working with patient: {patient['full_name']} (ID: {patient_id})")
    
    # Step 3: Edit Patient Details
    print("\n[3] Updating patient medical details...")
    edit_response = requests.patch(
        f"{BASE_URL}/admin/patients/{patient_id}/",
        headers=headers,
        json={
            "diagnosis": "Severe heart condition requiring urgent surgery",
            "treatment_needed": "Open-heart surgery with valve replacement",
            "medical_partner": "Kenyatta National Hospital",
            "treatment_date": (date.today() + timedelta(days=30)).isoformat(),
            "funding_required": "15000.00",
            "total_treatment_cost": "20000.00"
        }
    )
    print_response("Patient Details Updated", edit_response)
    
    # Step 4: Approve Patient
    print("\n[4] Approving patient profile...")
    approve_response = requests.post(
        f"{BASE_URL}/admin/patients/{patient_id}/approve/",
        headers=headers,
        json={"action": "approve"}
    )
    print_response("Patient Approved", approve_response)
    
    # Step 5: Publish Patient
    print("\n[5] Publishing patient profile...")
    publish_response = requests.post(
        f"{BASE_URL}/admin/patients/{patient_id}/publish/",
        headers=headers,
        json={
            "publish": True,
            "featured": True
        }
    )
    print_response("Patient Published", publish_response)
    
    # Step 6: Add Manual Timeline Event
    print("\n[6] Adding manual timeline event...")
    timeline_response = requests.post(
        f"{BASE_URL}/admin/timeline/create/",
        headers=headers,
        json={
            "patient_profile": patient_id,
            "event_type": "UPDATE_POSTED",
            "title": "Pre-Surgery Consultation Completed",
            "description": f"Patient {patient['full_name']} completed pre-surgery consultation. All tests came back positive. Surgery scheduled for next month.",
            "is_milestone": False,
            "is_visible": True,
            "is_current_state": True,
            "metadata": {
                "consultation_type": "Pre-surgery",
                "doctor": "Dr. Sarah Johnson"
            }
        }
    )
    print_response("Timeline Event Added", timeline_response)
    
    # Step 7: View Timeline
    print("\n[7] Viewing patient timeline...")
    timeline_list_response = requests.get(
        f"{BASE_URL}/admin/patients/{patient_id}/timeline/",
        headers=headers
    )
    print_response("Patient Timeline", timeline_list_response)
    
    # Step 8: View Public Profile
    print("\n[8] Viewing public patient profile (no auth)...")
    public_response = requests.get(f"{BASE_URL}/public/patients/{patient_id}/")
    print_response("Public Patient Profile", public_response)
    
    # Step 9: View Featured Patients
    print("\n[9] Viewing featured patients for homepage...")
    featured_response = requests.get(f"{BASE_URL}/public/patients/featured/")
    print_response("Featured Patients", featured_response)
    
    # Summary
    print("\n" + "="*70)
    print("  ✅ Admin Workflow Complete!")
    print("="*70)
    print(f"\n  Patient '{patient['full_name']}' is now:")
    print(f"  • Verified and Approved")
    print(f"  • Published and Featured")
    print(f"  • Visible on public API")
    print(f"  • Has complete timeline with {len(timeline_list_response.json()) if timeline_list_response.status_code == 200 else '?'} events")
    print("\n  Next steps:")
    print("  • View Swagger docs at http://localhost:8091/swagger/")
    print("  • Test funding updates to trigger milestone events")
    print("  • Add more timeline events as treatment progresses")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
