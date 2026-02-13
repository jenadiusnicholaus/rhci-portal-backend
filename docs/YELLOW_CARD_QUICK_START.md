# Yellow Card Integration - Quick Start Guide

## 🎯 Overview

This is a quick reference guide for implementing Yellow Card payment integration. For detailed planning, see `YELLOW_CARD_INTEGRATION_PLAN.md`.

---

## 💱 Currency Strategy

```
┌─────────────────────────────────────────────────────────────┐
│              PAYMENT GATEWAY COMPARISON                      │
├─────────────────────────────────────────────────────────────┤
│  AzamPay          │  Yellow Card                            │
│  - TZS only       │  - TZS, KES, NGN, GHS, etc.            │
│  - Local payments │  - International + Multi-currency       │
│  - No conversion  │  - Auto-convert to USD/USDT             │
└─────────────────────────────────────────────────────────────┘

Database Storage:
- amount       = 50000      (local currency - TZS)
- currency     = "TZS"
- amount_usd   = 18.87      (converted USD) ← NEW FIELD
- exchange_rate = 2650.50   (rate used)     ← NEW FIELD
```

---

## ✅ Current Status

### Already Configured
- ✅ API credentials in `.env` (lines 98-103)
- ✅ Sandbox and Production URLs configured
- ✅ Donation model supports payment gateways

### Needs Implementation
- ⏳ Database migration (add `amount_usd`, `exchange_rate` fields)
- ⏳ Service layer (`yellowcard_service.py`)
- ⏳ View endpoints (donation views)
- ⏳ Webhook handlers
- ⏳ URL routing
- ⏳ Settings configuration
- ⏳ Testing

---

## 📋 Implementation Checklist

### Phase 1: Configuration (1-2 hours)
- [ ] Add `YELLOW_CARD_ENVIRONMENT=sandbox` to `.env`
- [ ] Add Yellow Card config section to `settings/settings.py`
- [ ] Test API credentials

### Phase 2: Service Layer (4-6 hours)
- [ ] Research Yellow Card API docs: https://docs.yellowcard.engineering/docs/authentication-api
- [ ] Create `donor/payments/yellowcard_service.py`
- [ ] Implement authentication/token management
- [ ] Implement payment initiation
- [ ] Implement status checking
- [ ] Implement callback processing

### Phase 3: Views (4-6 hours)
- [ ] Create Yellow Card donation views (8 views total)
- [ ] Follow pattern from `donation_type_views.py`
- [ ] Update Swagger documentation

### Phase 4: Routing (30 min)
- [ ] Add routes to `donor/urls.py`
- [ ] Test URL routing

### Phase 5: Callbacks (2-3 hours)
- [ ] Create webhook handler in `callback_views.py`
- [ ] Implement signature verification
- [ ] Test with webhook tool

### Phase 6: Testing (3-4 hours)
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Manual sandbox testing

### Phase 7: Documentation (2-3 hours)
- [ ] Write API docs
- [ ] Update code comments
- [ ] Create user guide

---

## 🔑 Key Files to Create/Modify

### New Files
```
donor/payments/yellowcard_service.py       # Service layer
donor/payments/tests/test_yellowcard_*.py  # Tests
docs/YELLOW_CARD_API.md                    # API documentation
```

### Files to Modify
```
.env                                        # Add YELLOW_CARD_ENVIRONMENT
settings/settings.py                        # Add Yellow Card config
donor/payments/donation_type_views.py       # Add Yellow Card views
donor/payments/callback_views.py           # Add webhook handler
donor/urls.py                              # Add routes
```

---

## 🔍 Yellow Card API Endpoints

**Full API Flow:** See `YELLOW_CARD_API_FLOW.md`

### Authentication (HMAC-SHA256)
```python
# Headers required for all API calls
headers = {
    "X-YC-Timestamp": unix_timestamp,
    "Authorization": f"YcHmacV1 {api_key}:{signature}",
    "Content-Type": "application/json"
}

# Signature = HMAC-SHA256(secret, timestamp + method + path + body)
```

### API Endpoints

| Step | Endpoint | Method | Purpose |
|------|----------|--------|---------|
| 1 | `/business/channels` | GET | Get payment methods |
| 2 | `/business/rates` | GET | Get exchange rates |
| 3 | `/business/rates/lock` | POST | Lock rate (30-60s) |
| 4 | `/business/payments` | POST | Create payment |
| 5 | `/business/payments/{id}/accept` | POST | Accept payment |
| 6 | `/business/payments/{id}` | GET | Check status |
| 7 | Webhook | POST | Receive updates |

### Payment Flow
```
Channels → Rates → Lock Rate → Create Payment → Accept → Webhook
```

### Webhook Events
- `payment.completed` - Success ✅
- `payment.failed` - Failed ❌
- `payment.expired` - Timeout
- `payment.processing` - In progress

**Documentation:** https://docs.yellowcard.engineering/reference/

---

## 📐 Code Pattern to Follow

### Reference Implementation
Use `azampay_service.py` as a template:

```python
# Service Structure
class YellowCardService:
    def __init__(self):
        # Load from settings
        pass
    
    def _get_access_token(self):
        # Token management with caching
        pass
    
    def initiate_payment(self, ...):
        # Payment initiation
        pass
    
    def check_transaction_status(self, ...):
        # Status checking
        pass
    
    def process_callback(self, ...):
        # Webhook processing
        pass
```

### View Structure
Follow `donation_type_views.py` pattern:
- Anonymous vs Authenticated
- One-time vs Monthly
- Patient vs Organization
- Total: 8 view classes

---

## 🔐 Security Checklist

- [ ] Credentials in `.env` (not committed)
- [ ] Webhook signature verification
- [ ] Token caching (secure)
- [ ] Error handling (no sensitive data exposed)
- [ ] HTTPS for webhooks
- [ ] Idempotency for callbacks

---

## 🧪 Testing Strategy

### Sandbox Testing
1. Test payment initiation
2. Test webhook callbacks
3. Test status checking
4. Test all donation types
5. Test error scenarios

### Production Testing
1. Small test payment ($1-5)
2. Verify webhook received
3. Verify donation status updated

---

## 📞 Resources

- **Full Plan:** `docs/YELLOW_CARD_INTEGRATION_PLAN.md`
- **API Docs:** https://docs.yellowcard.engineering/
- **Reference:** `donor/payments/azampay_service.py`

---

## ⚡ Quick Start Commands

```bash
# 1. Research API (first step!)
# Visit: https://docs.yellowcard.engineering/docs/authentication-api

# 2. Update .env
echo "YELLOW_CARD_ENVIRONMENT=sandbox" >> .env

# 3. Create service file
touch donor/payments/yellowcard_service.py

# 4. Start implementing following azampay_service.py pattern
```

---

**Next Step:** Research Yellow Card API documentation before coding!
