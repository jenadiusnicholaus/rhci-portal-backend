# Azam Pay Integration - Quick Setup Guide

## ✅ What Was Implemented

Complete Azam Pay payment gateway integration for donation payments with:
- Mobile Money support (Airtel, Tigo, Halopesa, Azampesa)
- Bank transfer support
- Webhook callbacks for automatic status updates
- Payment status checking

## 📁 Files Created/Modified

### New Files
1. **`donor/azampay_service.py`** - Azam Pay API service class
2. **`donor/payment_views.py`** - Payment API endpoints
3. **`docs/AZAMPAY_INTEGRATION.md`** - Complete documentation

### Modified Files
1. **`donor/urls.py`** - Added 4 new payment endpoints
2. **`settings/settings.py`** - Added Azam Pay configuration
3. **`.env`** - Already has Azam Pay credentials

## 🚀 New API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1.0/donations/payment/azampay/mobile-money/` | POST | Initiate mobile money payment |
| `/api/v1.0/donations/payment/azampay/bank/` | POST | Initiate bank payment |
| `/api/v1.0/donations/payment/azampay/callback/` | POST | Webhook (automatic) |
| `/api/v1.0/donations/payment/status/` | GET | Check payment status |

## 🔧 Configuration

Your `.env` already has the credentials:

```env
AZAM_PAY_AUTH=https://authenticator-sandbox.azampay.co.tz
AZAM_PAY_CHECKOUT_URL=https://sandbox.azampay.co.tz
AZAM_PAY_APP_NAME=eshop
AZAM_PAY_CLIENT_ID=a6e6d2df-bd53-4fa4-a858-f0083b5e8ff0
AZAM_PAY_CLIENT_SECRET=<your_long_secret>
```

### Additional Setting Added
```env
USD_TO_TZS_RATE=2300
```

## 📝 Payment Flow

### 1. Create Donation
```bash
curl -X POST http://185.237.253.223:8082/api/v1.0/donations/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "amount": 50.00,
    "message": "Get well soon!"
  }'
```

**Response**:
```json
{
  "id": 123,
  "amount": "50.00",
  "status": "PENDING"
}
```

### 2. Pay with Mobile Money
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
  "transaction_id": "AZM123456"
}
```

### 3. User Confirms on Phone
- User receives USSD push
- Enters PIN
- Payment processed

### 4. Check Status
```bash
curl http://185.237.253.223:8082/api/v1.0/donations/payment/status/?donation_id=123
```

**Response**:
```json
{
  "donation_id": 123,
  "status": "COMPLETED",
  "transaction_id": "AZM123456",
  "amount": "50.00"
}
```

## 🎯 Testing Steps

### 1. Verify Server Running
```bash
curl http://185.237.253.223:8082/api/v1.0/donations/create/
```

### 2. Create Test Donation
Use Swagger UI: `http://185.237.253.223:8082/api/v1.0/swagger/`
- Navigate to "Donations" section
- Try "Create Donation" endpoint

### 3. Test Payment
- Use sandbox phone numbers (check Azam Pay docs)
- Provider: `Tigo` or `Airtel`
- Phone: `255XXXXXXXXX` format

### 4. Configure Webhook
In Azam Pay Dashboard:
```
Callback URL: http://185.237.253.223:8082/api/v1.0/donations/payment/azampay/callback/
```

## 🔐 Security Notes

### Current Setup (Development)
- ✅ Sandbox environment
- ✅ Test credentials
- ✅ No real money charged

### Production Checklist
- [ ] Change to production URLs
- [ ] Use production credentials
- [ ] Enable HTTPS/SSL
- [ ] Configure webhook URL
- [ ] Test with small amounts first
- [ ] Set up monitoring/alerts

## 📊 Supported Mobile Money Providers

1. **Tigo** - Tigo Pesa
2. **Airtel** - Airtel Money
3. **Halopesa** - Halotel
4. **Azampesa** - Azam Pesa

Phone format: `255XXXXXXXXX` (Tanzania country code)

## 💰 Currency Handling

- Donations stored in USD
- Converted to TZS for Azam Pay
- Rate: 1 USD = 2300 TZS (configurable)

**Update rate in `.env`**:
```env
USD_TO_TZS_RATE=2350
```

## 🔍 Donation Status Flow

```
PENDING → [User Pays] → COMPLETED
                      → FAILED
                      → CANCELLED
```

- **PENDING**: Created, awaiting payment
- **COMPLETED**: Payment successful, patient funded
- **FAILED**: Payment failed
- **CANCELLED**: User cancelled

## 🎨 Frontend Integration

### React Example
```jsx
const payDonation = async (donationId, phoneNumber) => {
  const response = await fetch(
    '/api/v1.0/donations/payment/azampay/mobile-money/',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        donation_id: donationId,
        provider: 'Tigo',
        phone_number: phoneNumber,
        currency: 'TZS'
      })
    }
  );
  
  const result = await response.json();
  
  if (result.success) {
    alert('Check your phone to confirm payment!');
  }
};
```

## 📱 User Experience

1. User selects patient to donate to
2. Enters amount and details
3. Clicks "Donate Now"
4. Selects payment method (Mobile Money)
5. Chooses provider (Tigo/Airtel/etc.)
6. Enters phone number
7. Receives USSD push on phone
8. Enters PIN to confirm
9. Payment completed automatically
10. Receives confirmation

## 🐛 Troubleshooting

### Payment Stuck in PENDING
**Check**: Webhook configured in Azam Pay dashboard?
**Fix**: Manually check status or wait for webhook retry

### Authentication Error
**Check**: CLIENT_ID and CLIENT_SECRET in .env correct?
**Fix**: Verify credentials with Azam Pay

### Phone Number Error
**Check**: Format is `255XXXXXXXXX`?
**Fix**: Add country code (255 for Tanzania)

## 📚 Documentation

Complete guide: `/docs/AZAMPAY_INTEGRATION.md`

Includes:
- Detailed API reference
- Frontend integration examples
- Error handling
- Security best practices
- Production deployment guide

## 🧪 Quick Test

```bash
# Start server
python manage.py runserver 0.0.0.0:8082

# In another terminal, test the endpoint
curl http://185.237.253.223:8082/api/v1.0/donations/payment/status/?donation_id=1
```

Expected: `{"detail": "Not found."}` (no donation yet) or actual donation status

## ✅ Status

- [x] Azam Pay service created
- [x] Payment endpoints implemented
- [x] Webhook handler ready
- [x] URL routing configured
- [x] Settings updated
- [x] Documentation complete
- [x] Syntax validation passed
- [x] Django check passed

**Ready for testing!** 🚀

## 🆘 Support

**Azam Pay**:
- Website: https://azampay.co.tz
- Docs: https://developers.azampay.co.tz
- Email: support@azampay.co.tz

**Code Issues**:
- Service: `donor/azampay_service.py`
- Views: `donor/payment_views.py`
- URLs: `donor/urls.py`

---

**Next Step**: Test with Swagger UI at `/api/v1.0/swagger/` → Look for "Donations - Payment" section
