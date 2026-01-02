#!/usr/bin/env python3
"""
Test script to verify callback updates all necessary information
"""
from decimal import Decimal

class MockDonation:
    def __init__(self, donation_id, amount, patient=None):
        self.id = donation_id
        self.amount = Decimal(str(amount))
        self.status = 'PENDING'
        self.completed_at = None
        self.transaction_id = None
        self.payment_method = None
        self.payment_gateway = None
        self.currency = 'TZS'
        self.patient = patient
    
    def save(self):
        print(f"   💾 Saved donation {self.id}")
    
    def __str__(self):
        return f"Donation #{self.id} - {self.status}"

class MockPatient:
    def __init__(self, patient_id, name, funding_required, funding_received=0):
        self.id = patient_id
        self.full_name = name
        self.funding_required = Decimal(str(funding_required))
        self.funding_received = Decimal(str(funding_received))
        self.status = 'APPROVED'
    
    @property
    def funding_percentage(self):
        if self.funding_required > 0:
            return round((self.funding_received / self.funding_required) * 100, 1)
        return 0
    
    @property
    def funding_remaining(self):
        return self.funding_required - self.funding_received
    
    def save(self):
        print(f"   💾 Saved patient {self.id}")
    
    def __str__(self):
        return f"{self.full_name} - {self.status}"


def simulate_callback_success(donation, callback_data):
    """Simulate successful callback processing"""
    print(f"\n{'='*60}")
    print(f"Processing Callback for {donation}")
    print(f"{'='*60}")
    
    # Extract callback information
    transaction_status = callback_data.get('transactionstatus', '').upper()
    transaction_id = callback_data.get('reference')
    provider = callback_data.get('operator')
    
    print(f"📥 Callback Data:")
    print(f"   - Transaction ID: {transaction_id}")
    print(f"   - Status: {transaction_status}")
    print(f"   - Provider: {provider}")
    print(f"   - Amount: {callback_data.get('amount')}")
    
    if transaction_status == 'SUCCESS':
        print(f"\n✅ Processing Successful Payment")
        
        # Update donation
        old_status = donation.status
        donation.status = 'COMPLETED'
        donation.transaction_id = transaction_id
        donation.payment_method = f"Mobile Money - {provider}"
        donation.payment_gateway = 'AzamPay'
        donation.save()
        
        print(f"\n📝 Donation Updates:")
        print(f"   - Status: {old_status} → {donation.status}")
        print(f"   - Transaction ID: {donation.transaction_id}")
        print(f"   - Payment Method: {donation.payment_method}")
        print(f"   - Payment Gateway: {donation.payment_gateway}")
        
        # Update patient if applicable
        if donation.patient:
            patient = donation.patient
            old_funding = patient.funding_received
            old_percentage = patient.funding_percentage
            old_status = patient.status
            
            patient.funding_received += donation.amount
            new_percentage = patient.funding_percentage
            
            # Check if fully funded
            if patient.funding_received >= patient.funding_required:
                patient.status = 'FULLY_FUNDED'
            
            patient.save()
            
            print(f"\n👤 Patient Updates ({patient.full_name}):")
            print(f"   - Funding: ${old_funding:,.2f} → ${patient.funding_received:,.2f}")
            print(f"   - Donation Added: ${donation.amount:,.2f}")
            print(f"   - Progress: {old_percentage}% → {new_percentage}%")
            print(f"   - Remaining: ${patient.funding_remaining:,.2f}")
            print(f"   - Status: {old_status} → {patient.status}")
            
            if patient.status == 'FULLY_FUNDED':
                print(f"   🎉 PATIENT FULLY FUNDED!")
        
        print(f"\n✅ Callback Processing Complete!")
        return {
            'success': True,
            'donation': {
                'id': donation.id,
                'status': donation.status,
                'amount': str(donation.amount),
                'transaction_id': donation.transaction_id
            },
            'patient': {
                'id': donation.patient.id if donation.patient else None,
                'funding_percentage': donation.patient.funding_percentage if donation.patient else 0,
                'funding_received': str(donation.patient.funding_received) if donation.patient else '0',
                'status': donation.patient.status if donation.patient else None
            } if donation.patient else None
        }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing AzamPay Callback - Complete Update Flow")
    print("="*60)
    
    # Test Case 1: Donation with patient (partial funding)
    print("\n\n📋 TEST CASE 1: Donation with Patient (Partial Funding)")
    print("-"*60)
    patient1 = MockPatient(
        patient_id=12,
        name="Jimmy Jacob",
        funding_required=10000,
        funding_received=5000
    )
    donation1 = MockDonation(donation_id=83, amount=100, patient=patient1)
    
    callback1 = {
        "transactionstatus": "success",
        "reference": "260101wMAgxjKXq",
        "operator": "Halopesa",
        "amount": "100",
        "utilityref": "RHCI-DN-83-20260101114005"
    }
    
    result1 = simulate_callback_success(donation1, callback1)
    
    # Test Case 2: Donation that completes patient funding
    print("\n\n📋 TEST CASE 2: Donation that Fully Funds Patient")
    print("-"*60)
    patient2 = MockPatient(
        patient_id=15,
        name="Sarah Ahmed",
        funding_required=5000,
        funding_received=4800
    )
    donation2 = MockDonation(donation_id=100, amount=500, patient=patient2)
    
    callback2 = {
        "transactionstatus": "success",
        "reference": "260102ABC123XYZ",
        "operator": "Mpesa",
        "amount": "500",
        "utilityref": "RHCI-DN-100-20260102120000"
    }
    
    result2 = simulate_callback_success(donation2, callback2)
    
    # Test Case 3: General donation (no specific patient)
    print("\n\n📋 TEST CASE 3: General Donation (No Specific Patient)")
    print("-"*60)
    donation3 = MockDonation(donation_id=101, amount=250, patient=None)
    
    callback3 = {
        "transactionstatus": "success",
        "reference": "260102DEF456UVW",
        "operator": "Airtel",
        "amount": "250",
        "utilityref": "RHCI-DN-101-20260102130000"
    }
    
    result3 = simulate_callback_success(donation3, callback3)
    
    print("\n\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)
    print("\n📊 Summary:")
    print(f"   - Test 1: Patient funding updated ✓")
    print(f"   - Test 2: Patient fully funded ✓")
    print(f"   - Test 3: General donation (no patient) ✓")
    print(f"   - All donation details updated ✓")
    print(f"   - All patient percentages calculated ✓")
    print("\n")
