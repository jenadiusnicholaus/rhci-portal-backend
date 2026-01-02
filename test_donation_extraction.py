#!/usr/bin/env python3
"""
Test script to verify AzamPay callback donation ID extraction logic
"""

def test_extraction(external_id, additional_props):
    """Test the donation ID extraction logic"""
    donation_id = None
    
    # Method 1: Parse from external_id (utilityref)
    try:
        if external_id:
            parts = external_id.split('-')
            if len(parts) >= 3:
                donation_id = int(parts[2])
                print(f"✅ Method 1: Extracted donation_id {donation_id} from external_id: {external_id}")
    except (IndexError, ValueError) as e:
        print(f"⚠️ Method 1 failed: Could not parse donation_id from external_id '{external_id}': {e}")
    
    # Method 2: Fallback to additionalProperties
    if not donation_id:
        if additional_props and 'donation_id' in additional_props:
            try:
                donation_id = int(additional_props['donation_id'])
                print(f"✅ Method 2: Extracted donation_id {donation_id} from additionalProperties")
            except (ValueError, TypeError) as e:
                print(f"❌ Method 2 failed: Invalid donation_id in additionalProperties: {additional_props.get('donation_id')}")
    
    # Verify we have a donation_id
    if not donation_id:
        print(f"❌ FAILED: Could not extract donation_id from either method")
        return None
    
    print(f"✅ SUCCESS: Final donation_id = {donation_id}\n")
    return donation_id


if __name__ == "__main__":
    print("="*60)
    print("Testing AzamPay Callback Donation ID Extraction")
    print("="*60 + "\n")
    
    # Test Case 1: Production payload from AzamPay
    print("Test Case 1: Production payload")
    print("-" * 60)
    test_extraction(
        external_id="RHCI-DN-83-20260101114005",
        additional_props={
            "donation_id": "83",
            "patient_id": "12",
            "patient_name": "Jimmy Jacob",
            "is_anonymous": "true",
            "donation_type": "ONE_TIME"
        }
    )
    
    # Test Case 2: Only utilityref available
    print("Test Case 2: Only utilityref (no additionalProperties)")
    print("-" * 60)
    test_extraction(
        external_id="RHCI-DN-42-20251215123456",
        additional_props={}
    )
    
    # Test Case 3: Only additionalProperties available
    print("Test Case 3: Only additionalProperties (malformed utilityref)")
    print("-" * 60)
    test_extraction(
        external_id="INVALID-FORMAT",
        additional_props={
            "donation_id": "99"
        }
    )
    
    # Test Case 4: Both methods fail
    print("Test Case 4: Both methods fail")
    print("-" * 60)
    test_extraction(
        external_id="INVALID",
        additional_props={}
    )
    
    # Test Case 5: Different format but still valid
    print("Test Case 5: Short format")
    print("-" * 60)
    test_extraction(
        external_id="RHCI-DN-1",
        additional_props={}
    )
    
    print("="*60)
    print("Testing Complete")
    print("="*60)
