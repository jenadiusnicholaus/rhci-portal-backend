# Payment Module

All payment-related code for RHCI Portal donation system.

## 📁 Structure

```
payments/
├── __init__.py                 # Package initialization
├── azampay_service.py          # AzamPay API integration
├── donation_type_views.py      # Donation APIs by type
└── callback_views.py           # Webhook & status check
```

## 📄 Files

### `azampay_service.py`
**AzamPay Payment Gateway Integration**
- Mobile money checkout (Mpesa, Airtel, Tigo, Halopesa, Azampesa)
- Bank transfer checkout (CRDB, NMB with OTP)
- Transaction status checking
- Webhook callback processing
- Phone number normalization
- Provider validation
- Token caching (30 min TTL)

### `donation_type_views.py`
**Donation API Endpoints (8 endpoints)**

**Patient Donations:**
1. `AnonymousOneTimePatientDonationView` - 🔓 One-time patient donation (no auth)
2. `AuthenticatedOneTimePatientDonationView` - 🔐 One-time patient donation (auth)
3. `AnonymousMonthlyPatientDonationView` - 🔓 Monthly patient donation (no auth)
4. `AuthenticatedMonthlyPatientDonationView` - 🔐 Monthly patient donation (auth)

**Organization Donations:**
5. `AnonymousOrganizationDonationView` - 🔓 One-time org donation (no auth)
6. `AuthenticatedOrganizationDonationView` - 🔐 One-time org donation (auth)
7. `AnonymousMonthlyOrganizationDonationView` - 🔓 Monthly org donation (no auth)
8. `AuthenticatedMonthlyOrganizationDonationView` - 🔐 Monthly org donation (auth)

### `callback_views.py`
**Webhook & Status Views**
- `AzamPayCallbackView` - Webhook endpoint for payment notifications
- `CheckPaymentStatusView` - Check donation payment status

## 🔗 URL Routes

All routes are defined in `donor/urls.py`:

```python
# Patient donations
/donate/azampay/patient/anonymous/          # One-time anonymous
/donate/azampay/patient/                    # One-time authenticated
/donate/azampay/patient/monthly/anonymous/  # Monthly anonymous
/donate/azampay/patient/monthly/            # Monthly authenticated

# Organization donations
/donate/azampay/organization/anonymous/          # One-time anonymous
/donate/azampay/organization/                    # One-time authenticated
/donate/azampay/organization/monthly/anonymous/  # Monthly anonymous
/donate/azampay/organization/monthly/            # Monthly authenticated

# Callback & status
/payment/azampay/callback/                  # Webhook
/payment/status/                            # Status check
```

## 🎯 Design Principles

1. **Separation by Type** - Each donation type has its own endpoint
2. **Clear Intent** - URL indicates donation type and auth requirement
3. **Shared Logic** - Common processing in base class `_process_donation()`
4. **Single Responsibility** - Each view class handles one specific use case
5. **Future Extensibility** - Easy to add PayPal, Stripe, etc.

## 🔄 Payment Flow

1. User submits donation via specific endpoint
2. Donation record created in database (PENDING status)
3. Payment initiated with AzamPay
4. Transaction ID saved to donation
5. User completes payment on their phone/bank
6. AzamPay sends webhook callback
7. Callback updates donation status (COMPLETED/FAILED)
8. Patient funding updated (if patient donation)

## 💳 Supported Providers

### Mobile Money:
- `mpesa` - M-Pesa (Vodacom)
- `airtel` - Airtel Money
- `tigo` - Tigo Pesa
- `halopesa` - Halo Pesa
- `azampesa` - Azam Pesa

### Bank Transfer:
- `crdb` - CRDB Bank (requires OTP)
- `nmb` - NMB Bank (requires OTP)

## 🔐 Authentication

- **Anonymous endpoints** - `AllowAny` permission, requires `anonymous_name` & `anonymous_email`
- **Authenticated endpoints** - `IsAuthenticated` permission, uses `request.user`

## 📊 Key Features

- ✅ One-time and monthly recurring donations
- ✅ Patient-specific and general organization donations
- ✅ Anonymous and authenticated donation flows
- ✅ Mobile money and bank transfer support
- ✅ Phone number auto-normalization (0XXX → 255XXX)
- ✅ Currency conversion (USD → TZS at 1:2300)
- ✅ Webhook callback processing
- ✅ Transaction status checking
- ✅ Patient funding tracking
- ✅ Automatic fully-funded status updates

## 🧪 Testing

See root-level documentation:
- `DONATION_BY_TYPE_TESTS.md` - Complete testing guide
- `TEST_DONATION_APIS.sh` - Automated test script

Quick test:
```bash
curl -X POST http://localhost:8000/api/v1.0/donors/donate/azampay/patient/anonymous/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "amount": 50,
    "anonymous_name": "Test",
    "anonymous_email": "test@example.com",
    "payment_method": "MOBILE_MONEY",
    "provider": "mpesa",
    "phone_number": "0789123456"
  }'
```

## 🚀 Future Enhancements

- [ ] Add PayPal integration
- [ ] Add Stripe integration
- [ ] Email receipt notifications
- [ ] Recurring charge automation
- [ ] Multi-currency support
- [ ] Payment retry logic
- [ ] Refund processing
