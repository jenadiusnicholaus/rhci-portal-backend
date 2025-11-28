# Azam Pay Integration for Donations

Complete guide for processing donation payments using Azam Pay mobile money and bank transfers.

## Overview

The RHCI Portal integrates with Azam Pay to accept donations via:
- **Mobile Money**: Airtel, Tigo, Halopesa, Azampesa
- **Bank Transfers**: Direct bank payments

## Configuration

### Environment Variables (.env)

```env
# Azam Pay Configuration
AZAM_PAY_AUTH=https://authenticator-sandbox.azampay.co.tz
AZAM_PAY_CHECKOUT_URL=https://sandbox.azampay.co.tz
AZAM_PAY_APP_NAME=eshop
AZAM_PAY_CLIENT_ID=your_client_id_here
AZAM_PAY_CLIENT_SECRET=your_client_secret_here

# Currency Exchange Rate
USD_TO_TZS_RATE=2300
```

### Production URLs
```env
AZAM_PAY_AUTH=https://authenticator.azampay.co.tz
AZAM_PAY_CHECKOUT_URL=https://checkout.azampay.co.tz
```

## API Endpoints

### 1. Mobile Money Payment

**Endpoint**: `POST /api/v1.0/donations/payment/azampay/mobile-money/`

**Description**: Initiate mobile money payment for a donation

**Request Body**:
```json
{
  "donation_id": 123,
  "provider": "Tigo",
  "phone_number": "255712345678",
  "currency": "TZS"
}
```

**Supported Providers**:
- `Airtel`
- `Tigo`
- `Halopesa`
- `Azampesa`

**Phone Number Format**:
- Tanzania: `255XXXXXXXXX`
- Example: `255712345678`

**Response Success (200)**:
```json
{
  "success": true,
  "message": "Payment initiated. Please check your phone to confirm.",
  "donation_id": 123,
  "transaction_id": "TXN123456",
  "amount": "50000.00",
  "currency": "TZS",
  "provider": "Tigo"
}
```

**Response Error (400)**:
```json
{
  "error": "Payment initiation failed",
  "details": "Insufficient balance"
}
```

### 2. Bank Payment

**Endpoint**: `POST /api/v1.0/donations/payment/azampay/bank/`

**Description**: Initiate bank transfer payment

**Request Body**:
```json
{
  "donation_id": 123,
  "provider": "CRDB",
  "merchant_account_number": "0123456789",
  "merchant_mobile_number": "255712345678",
  "otp": "123456",
  "currency": "TZS"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Bank payment initiated successfully",
  "donation_id": 123,
  "transaction_id": "TXN123456"
}
```

### 3. Payment Status Check

**Endpoint**: `GET /api/v1.0/donations/payment/status/?donation_id=123`

**Description**: Check current payment status

**Response**:
```json
{
  "donation_id": 123,
  "status": "COMPLETED",
  "transaction_id": "TXN123456",
  "amount": "50.00",
  "payment_method": "Mobile Money - Tigo",
  "payment_gateway": "Azam Pay",
  "created_at": "2025-11-28T10:30:00Z",
  "completed_at": "2025-11-28T10:31:45Z"
}
```

**Donation Statuses**:
- `PENDING`: Payment initiated, awaiting confirmation
- `COMPLETED`: Payment successful
- `FAILED`: Payment failed
- `CANCELLED`: Payment cancelled by user
- `REFUNDED`: Payment refunded

### 4. Webhook Callback (Internal)

**Endpoint**: `POST /api/v1.0/donations/payment/azampay/callback/`

**Description**: Receives payment notifications from Azam Pay (automatic)

**Configure in Azam Pay Dashboard**:
```
Callback URL: https://185.237.253.223:8082/api/v1.0/donations/payment/azampay/callback/
```

## Complete Payment Flow

### Step-by-Step Process

#### Step 1: Create Donation

```bash
curl -X POST http://185.237.253.223:8082/api/v1.0/donations/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 5,
    "amount": 50.00,
    "message": "Get well soon!",
    "is_anonymous": false
  }'
```

**Response**:
```json
{
  "id": 123,
  "amount": "50.00",
  "status": "PENDING",
  "patient": {
    "id": 5,
    "full_name": "John Kamau"
  }
}
```

#### Step 2: Initiate Payment

```bash
curl -X POST http://185.237.253.223:8082/api/v1.0/donations/payment/azampay/mobile-money/ \
  -H "Content-Type: application/json" \
  -d '{
    "donation_id": 123,
    "provider": "Tigo",
    "phone_number": "255712345678",
    "currency": "TZS"
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Payment initiated. Please check your phone to confirm.",
  "donation_id": 123,
  "transaction_id": "AZM123456789"
}
```

#### Step 3: User Confirms on Phone

- User receives USSD push notification
- User enters PIN to confirm payment
- Payment processed by mobile money provider

#### Step 4: Webhook Updates Status

- Azam Pay sends callback to your server
- Donation status automatically updated to `COMPLETED`
- Patient funding amount increased
- Email receipt sent (if configured)

#### Step 5: Check Status (Optional)

```bash
curl http://185.237.253.223:8082/api/v1.0/donations/payment/status/?donation_id=123
```

## Frontend Integration Examples

### React/JavaScript

```javascript
// Create donation and initiate payment
const processDonation = async (patientId, amount, phoneNumber, provider) => {
  try {
    // Step 1: Create donation
    const donationResponse = await fetch(
      'http://185.237.253.223:8082/api/v1.0/donations/create/',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}` // If authenticated
        },
        body: JSON.stringify({
          patient_id: patientId,
          amount: amount,
          message: 'Get well soon!'
        })
      }
    );
    
    const donation = await donationResponse.json();
    
    // Step 2: Initiate payment
    const paymentResponse = await fetch(
      'http://185.237.253.223:8082/api/v1.0/donations/payment/azampay/mobile-money/',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          donation_id: donation.id,
          provider: provider,
          phone_number: phoneNumber,
          currency: 'TZS'
        })
      }
    );
    
    const paymentResult = await paymentResponse.json();
    
    if (paymentResult.success) {
      // Show success message
      alert('Payment initiated! Please check your phone to confirm.');
      
      // Start polling for status
      pollPaymentStatus(donation.id);
    } else {
      alert('Payment failed: ' + paymentResult.details);
    }
    
  } catch (error) {
    console.error('Error processing donation:', error);
    alert('An error occurred. Please try again.');
  }
};

// Poll payment status
const pollPaymentStatus = (donationId) => {
  const interval = setInterval(async () => {
    const response = await fetch(
      `http://185.237.253.223:8082/api/v1.0/donations/payment/status/?donation_id=${donationId}`
    );
    
    const status = await response.json();
    
    if (status.status === 'COMPLETED') {
      clearInterval(interval);
      alert('Payment successful! Thank you for your donation.');
      window.location.href = '/donation-success';
    } else if (status.status === 'FAILED') {
      clearInterval(interval);
      alert('Payment failed. Please try again.');
    }
  }, 3000); // Check every 3 seconds
  
  // Stop polling after 5 minutes
  setTimeout(() => clearInterval(interval), 300000);
};
```

### React Component Example

```jsx
import React, { useState } from 'react';

const DonationPaymentForm = ({ patientId, donationAmount }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [provider, setProvider] = useState('Tigo');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      // Create donation
      const donationRes = await fetch('/api/v1.0/donations/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          amount: donationAmount,
          is_anonymous: false
        })
      });
      
      const donation = await donationRes.json();

      // Initiate payment
      const paymentRes = await fetch(
        '/api/v1.0/donations/payment/azampay/mobile-money/',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            donation_id: donation.id,
            provider: provider,
            phone_number: phoneNumber,
            currency: 'TZS'
          })
        }
      );

      const result = await paymentRes.json();

      if (result.success) {
        setMessage('Payment initiated! Check your phone to confirm.');
        // Poll for status or redirect
      } else {
        setMessage('Payment failed: ' + result.details);
      }

    } catch (error) {
      setMessage('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Complete Your Donation</h3>
      <p>Amount: ${donationAmount}</p>
      
      <div>
        <label>Mobile Money Provider:</label>
        <select value={provider} onChange={(e) => setProvider(e.target.value)}>
          <option value="Tigo">Tigo</option>
          <option value="Airtel">Airtel</option>
          <option value="Halopesa">Halopesa</option>
          <option value="Azampesa">Azampesa</option>
        </select>
      </div>

      <div>
        <label>Phone Number:</label>
        <input
          type="tel"
          placeholder="255712345678"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
          required
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Pay Now'}
      </button>

      {message && <p className="message">{message}</p>}
    </form>
  );
};

export default DonationPaymentForm;
```

## Testing

### Test Credentials (Sandbox)

Use the sandbox credentials from your `.env` file.

### Test Phone Numbers

Azam Pay provides test phone numbers for sandbox testing:
- Check Azam Pay documentation for current test numbers
- Test transactions won't charge real money

### Test Flow

```bash
# 1. Create test donation
curl -X POST http://localhost:8000/api/v1.0/donations/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "amount": 100.00,
    "is_anonymous": false
  }'

# 2. Initiate test payment
curl -X POST http://localhost:8000/api/v1.0/donations/payment/azampay/mobile-money/ \
  -H "Content-Type: application/json" \
  -d '{
    "donation_id": 1,
    "provider": "Tigo",
    "phone_number": "255TEST123456",
    "currency": "TZS"
  }'

# 3. Check status
curl http://localhost:8000/api/v1.0/donations/payment/status/?donation_id=1
```

## Database Changes

The existing `Donation` model already supports payment processing:

```python
class Donation(models.Model):
    # Payment fields
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=200, unique=True, null=True)
    payment_gateway = models.CharField(max_length=50, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
```

No migrations needed!

## Security Considerations

### 1. Webhook Authentication
- Verify webhook requests are from Azam Pay
- Check IP whitelist
- Validate signature (if provided)

### 2. Idempotency
- Use unique `external_id` for each transaction
- Prevent duplicate payments
- Handle webhook retries gracefully

### 3. Error Handling
- Log all payment attempts
- Store failed payment details
- Implement retry mechanism

### 4. Production Checklist

- [ ] Update `.env` with production Azam Pay credentials
- [ ] Change to production URLs (remove `-sandbox`)
- [ ] Configure webhook URL in Azam Pay dashboard
- [ ] Set up SSL/HTTPS for webhook endpoint
- [ ] Implement proper logging and monitoring
- [ ] Test with real (small) amounts
- [ ] Set up email notifications for donations
- [ ] Configure proper exchange rate updates

## Troubleshooting

### Payment Stuck in PENDING

**Check**:
1. Webhook URL configured correctly?
2. Server accessible from Azam Pay?
3. Check Azam Pay dashboard for transaction status

**Manual Fix**:
```python
# In Django shell
from donor.models import Donation
donation = Donation.objects.get(id=123)
donation.status = 'COMPLETED'
donation.completed_at = timezone.now()
donation.save()
```

### Webhook Not Receiving Callbacks

**Debug**:
```bash
# Check webhook endpoint is accessible
curl -X POST https://185.237.253.223:8082/api/v1.0/donations/payment/azampay/callback/ \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

**Solutions**:
- Ensure server has public IP
- Check firewall rules
- Verify SSL certificate valid
- Check Azam Pay dashboard logs

### Authentication Errors

**Check**:
- CLIENT_ID and CLIENT_SECRET correct
- Not expired
- Correct environment (sandbox vs production)

## Support

### Azam Pay Documentation
- Website: https://azampay.co.tz
- Developer Docs: https://developers.azampay.co.tz
- Support: support@azampay.co.tz

### Code Files
- Service: `donor/azampay_service.py`
- Views: `donor/payment_views.py`
- URLs: `donor/urls.py`
- Settings: `settings/settings.py`

## Currency Conversion

The system converts USD donations to TZS automatically:

```python
# USD to TZS conversion
amount_tzs = amount_usd * 2300  # Rate from settings
```

**Update Exchange Rate**:
Edit `.env`:
```env
USD_TO_TZS_RATE=2350
```

Or implement dynamic rate API (recommended for production).

## Next Steps

1. **Test Integration**: Use sandbox credentials
2. **Configure Webhook**: Set URL in Azam Pay dashboard
3. **Test Payments**: Make test donations
4. **Go Live**: Switch to production credentials
5. **Monitor**: Watch logs and Azam Pay dashboard

---

**Status**: ✅ Ready for testing

**Last Updated**: November 28, 2025
