# Yellow Card Integration - Executive Summary

## 📊 Current State

### ✅ Completed
- ✅ API credentials configured in `.env`
- ✅ Environment variable added (`YELLOW_CARD_ENVIRONMENT`)
- ✅ Integration plan created
- ✅ Project structure analyzed
- ✅ API flow documented with currency conversion

### ⏳ Pending Implementation
- ⏳ Database migration (add currency conversion fields)
- ⏳ Service layer (`yellowcard_service.py`)
- ⏳ View endpoints (8 donation views)
- ⏳ Webhook handlers
- ⏳ Settings configuration
- ⏳ URL routing
- ⏳ Testing

---

## 💱 Currency Strategy

### Payment Gateway Comparison

| Feature | AzamPay | Yellow Card |
|---------|---------|-------------|
| **Currencies** | TZS only | TZS, KES, NGN, GHS, etc. |
| **Settlement** | TZS | USD/USDT (stablecoin) |
| **Use Case** | Tanzania local | International + Multi-currency |
| **Conversion** | None | Auto-convert to USD |

### What We Store

```
Database Fields:
├── amount          → Local currency amount (50,000 TZS) - What donor paid
├── currency        → Currency code ("TZS")
├── amount_usd      → USD value ($18.87) ← NEW - For RHCI reports
├── exchange_rate   → Rate used (2650.50) ← NEW - Audit trail
└── rate_locked_at  → Timestamp           ← NEW - Audit trail

Note: amount_usd stores USD value for RHCI reporting
      Yellow Card holds the actual funds as USDT (1 USDT ≈ $1 USD)
```

### Conversion Flow (Stored on Success!)

```
DONOR PAYS (Local)         →  YELLOW CARD  →  YELLOW CARD DASHBOARD
─────────────────────────────────────────────────────────────────────
50,000 TZS (Tanzania)      →  Converts     →  +$18.87 USDT (to balance)
5,000 KES (Kenya)          →  Converts     →  +$38.46 USDT (to balance)
50,000 NGN (Nigeria)       →  Converts     →  +$31.25 USDT (to balance)
─────────────────────────────────────────────────────────────────────
                              Dashboard Balance: $88.58 USDT
                              ↓
                              RHCI can withdraw/settle when needed
```

### 💰 Yellow Card Dashboard vs RHCI Database

```
┌─────────────────────────────┐     ┌─────────────────────────────┐
│   YELLOW CARD DASHBOARD     │     │      RHCI DATABASE          │
├─────────────────────────────┤     ├─────────────────────────────┤
│  Stores: USDT (stablecoin)  │     │  Stores: USD (real value)   │
│  Balance: $88.58 USDT       │     │  amount_usd: 88.58          │
│                             │     │                             │
│  For: Settlement/Withdrawal │     │  For: Reports & Dashboards  │
│  Access: YC Portal          │     │  Access: RHCI System        │
└─────────────────────────────┘     └─────────────────────────────┘
        │                                      │
        │  1 USDT ≈ $1 USD                    │
        └──────────────────────────────────────┘
```

**Why store USD in RHCI database?**
- ✅ Patient funding: "Patient X received $500 USD"
- ✅ Dashboard stats: "Total donations: $10,000 USD"
- ✅ Financial reports: "Q1 revenue: $25,000 USD"
- ✅ Donor receipts: "Thank you for $50 USD"
- ✅ Multi-currency totals (TZS + KES + NGN → all in USD)

### ⭐ When USD Amount is Stored

```
1. CREATE PAYMENT (status=PENDING)
   └── amount_usd = NULL     ⏳ Not yet stored

2. WEBHOOK: payment.completed ✅
   └── amount_usd = 18.87    ✅ NOW STORED (from webhook)

3. WEBHOOK: payment.failed ❌
   └── amount_usd = NULL     ❌ Not stored (payment failed)
```

**Why on success only?** Yellow Card confirms the actual rate used in the webhook, ensuring accurate audit trail.

---

## 🎯 Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend/Client                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Django REST Framework Views                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  YellowCardAnonymousOneTimePatientDonationView   │  │
│  │  YellowCardAuthenticatedOneTimePatientDonation  │  │
│  │  YellowCardAnonymousMonthlyPatientDonationView  │  │
│  │  ... (8 total views)                             │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Yellow Card Service Layer                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  yellowcard_service.py                          │  │
│  │  - Authentication/Token Management              │  │
│  │  - Payment Initiation                           │  │
│  │  - Status Checking                              │  │
│  │  - Callback Processing                          │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Yellow Card API                             │
│  https://api-sandbox.yellowcard.co.tz (sandbox)         │
│  https://api.yellowcard.io/business (production)        │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ (Webhook Callback)
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Webhook Handler                             │
│  YellowCardCallbackView                                 │
│  - Verify signature                                     │
│  - Update donation status                               │
│  - Process payment                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
rhci-portal-v1/
├── .env                                    ✅ Updated
├── settings/
│   └── settings.py                         ⏳ Add Yellow Card config
├── donor/
│   ├── models.py                           ⏳ Add amount_usd, exchange_rate fields
│   ├── serializers.py                      ⏳ Update serializers
│   ├── migrations/
│   │   └── XXXX_add_currency_conversion.py ⏳ NEW - Migration
│   ├── payments/
│   │   ├── yellowcard_service.py          ⏳ NEW - Service layer
│   │   ├── donation_type_views.py         ⏳ Add Yellow Card views
│   │   ├── callback_views.py              ⏳ Add webhook handler
│   │   └── tests/
│   │       └── test_yellowcard_*.py        ⏳ NEW - Tests
│   └── urls.py                             ⏳ Add routes
└── docs/
    ├── YELLOW_CARD_INTEGRATION_PLAN.md     ✅ Created
    ├── YELLOW_CARD_QUICK_START.md          ✅ Created
    └── YELLOW_CARD_API.md                  ⏳ Create after research
```

---

## 🔄 Implementation Phases

### Phase 1: Configuration ✅ (Partially Done)
- ✅ `.env` updated with `YELLOW_CARD_ENVIRONMENT`
- ⏳ Add Yellow Card config to `settings.py`

### Phase 2: Service Layer ⏳ (Next Step)
- ⏳ Research Yellow Card API documentation
- ⏳ Create `yellowcard_service.py`
- ⏳ Implement authentication
- ⏳ Implement payment methods

### Phase 3: Views ⏳
- ⏳ Create 8 donation view classes
- ⏳ Follow AzamPay pattern
- ⏳ Update Swagger docs

### Phase 4: Routing ⏳
- ⏳ Add URL routes
- ⏳ Test routing

### Phase 5: Callbacks ⏳
- ⏳ Implement webhook handler
- ⏳ Add signature verification
- ⏳ Test callbacks

### Phase 6: Testing ⏳
- ⏳ Unit tests
- ⏳ Integration tests
- ⏳ Manual testing

### Phase 7: Documentation ⏳
- ⏳ API documentation
- ⏳ Code comments
- ⏳ User guides

---

## 🔑 Key Implementation Details

### Service Layer Pattern
```python
# Follow azampay_service.py structure:
class YellowCardService:
    def __init__(self):
        self.base_url = settings.YELLOW_CARD_BASE_URL
        self.api_key = settings.YELLOW_CARD_API_KEY
        self.api_secret = settings.YELLOW_CARD_API_SECRET
    
    def _get_access_token(self):
        # Token management with caching
        pass
    
    def initiate_payment(self, amount, currency, ...):
        # Payment initiation
        pass
```

### View Pattern
```python
# Follow donation_type_views.py structure:
class YellowCardAnonymousOneTimePatientDonationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Create donation
        # Call yellowcard_service.initiate_payment()
        # Return response
        pass
```

### URL Pattern
```python
# Add to donor/urls.py:
path('donate/yellowcard/patient/anonymous/', 
     YellowCardAnonymousOneTimePatientDonationView.as_view(), 
     name='donate_yellowcard_patient_onetime_anonymous'),
# ... (8 routes total)
```

---

## 📡 Yellow Card API Endpoints

**Full Details:** See `YELLOW_CARD_API_FLOW.md`

### Base URLs
- **Sandbox:** `https://sandbox.api.yellowcard.io/business`
- **Production:** `https://api.yellowcard.io/business`

### Authentication (HMAC-SHA256)
```
Headers:
- X-YC-Timestamp: {unix_timestamp}
- Authorization: YcHmacV1 {api_key}:{signature}
- Content-Type: application/json

Signature = HMAC-SHA256(secret, timestamp + method + path + body)
```

### API Call Sequence

```
Step 1: GET /channels         → Get payment methods (Mobile Money, Bank)
Step 2: GET /rates            → Get exchange rates (TZS → USD/USDT)
Step 3: POST /rates/lock      → Lock rate for 30-60 seconds
Step 4: POST /payments        → Create payment request
Step 5: POST /payments/{id}/accept → Accept/finalize payment
Step 6: Webhook callback      → Receive payment.completed event
Step 7: GET /payments/{id}    → (Optional) Poll status
```

### Webhook Events
| Event | Action |
|-------|--------|
| `payment.completed` | Mark donation COMPLETED |
| `payment.failed` | Mark donation FAILED |
| `payment.expired` | Mark donation EXPIRED |

**Documentation:** https://docs.yellowcard.engineering/reference/

---

## ⏱️ Time Estimates

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Configuration | 1-2 hours |
| 2 | Service Layer | 4-6 hours |
| 3 | Views | 4-6 hours |
| 4 | Routing | 30 minutes |
| 5 | Callbacks | 2-3 hours |
| 6 | Testing | 3-4 hours |
| 7 | Documentation | 2-3 hours |
| **Total** | | **16-24 hours** |

---

## ✅ Pre-Implementation Checklist

- [x] Review existing AzamPay integration
- [x] Analyze project structure
- [x] Create integration plan
- [x] Update `.env` file
- [ ] Research Yellow Card API documentation
- [ ] Verify API credentials
- [ ] Set up sandbox environment

---

## 🚀 Next Steps

1. **Research Phase** (Critical!)
   - Access Yellow Card API documentation
   - Understand authentication flow
   - Understand payment flow
   - Understand webhook flow

2. **Configuration Phase**
   - Add Yellow Card config to `settings.py`
   - Test API credentials

3. **Implementation Phase**
   - Start with service layer
   - Then views
   - Then callbacks
   - Finally testing

---

## 📚 Documentation

- **Full Plan:** `docs/YELLOW_CARD_INTEGRATION_PLAN.md`
- **Quick Start:** `docs/YELLOW_CARD_QUICK_START.md`
- **API Docs:** https://docs.yellowcard.engineering/
- **Reference:** `donor/payments/azampay_service.py`

---

## 🔐 Security Notes

- ✅ Credentials stored in `.env` (not committed)
- ⏳ Webhook signature verification needed
- ⏳ Token caching security
- ⏳ Error handling (no sensitive data)
- ⏳ HTTPS for webhooks

---

**Status:** Planning Complete ✅ | Ready for Implementation ⏳  
**Last Updated:** February 9, 2026
