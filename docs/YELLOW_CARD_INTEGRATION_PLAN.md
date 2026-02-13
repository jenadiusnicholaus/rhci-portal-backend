# Yellow Card API Integration Plan

## 📋 Overview

This document outlines the comprehensive plan for integrating Yellow Card payment gateway into the RHCI Portal donation system. The integration will follow the same architectural pattern as the existing AzamPay integration for consistency and maintainability.

**Status:** Planning Phase  
**Created:** February 9, 2026  
**Target Completion:** TBD

---

## 🎯 Objectives

1. **Enable Yellow Card payments** for donations (one-time and recurring)
2. **Support multiple currencies** (Yellow Card specializes in stablecoin/crypto payments)
3. **Maintain consistency** with existing AzamPay integration patterns
4. **Provide seamless user experience** with unified donation endpoints
5. **Ensure security** with proper authentication and webhook verification

---

## 📊 Current State Analysis

### ✅ Already Configured in `.env`

```env
# Yellow Card Configuration (Lines 98-103)
YELLOW_CARD_API_KEY=0392fa1c63d962a064b483013db4a52b
YELLOW_CARD_API_SECRET=41da10bae44592dd28da5577acf7507557a6834e656f372d6c2a9945234bc72b
YELLOW_CARD_SAND_BOX_URL=https://api-sandbox.yellowcard.co.tz
YELLOW_CARD_PROD_URL=https://api.yellowcard.io/business
```

### 📁 Existing Integration Pattern (AzamPay)

The project follows this structure:
```
donor/payments/
├── azampay_service.py          # Service layer (API client)
├── donation_type_views.py       # View endpoints
├── callback_views.py            # Webhook handlers
├── billpay_views.py            # Bill Pay API handlers
└── README.md                   # Documentation
```

### 🔍 Key Components to Replicate

1. **Service Layer** (`azampay_service.py`):
   - Token management with caching
   - API request handling
   - Error handling
   - Response parsing

2. **View Layer** (`donation_type_views.py`):
   - Anonymous/Authenticated donations
   - One-time/Monthly recurring
   - Patient/Organization donations

3. **Callback Handling** (`callback_views.py`):
   - Webhook verification
   - Payment status updates
   - Donation completion

---

## 🏗️ Implementation Plan

### Phase 1: Environment & Settings Configuration

#### 1.1 Update `.env` File
**Status:** ✅ Partially Complete

**Required Additions:**
```env
# Yellow Card Environment Selection
YELLOW_CARD_ENVIRONMENT=sandbox  # or 'production'

# Optional: Timeout Configuration
YELLOW_CARD_TIMEOUT_CONNECT=30
YELLOW_CARD_TIMEOUT_READ=60

# Optional: Webhook Security
YELLOW_CARD_WEBHOOK_SECRET=your-webhook-secret-here
```

**Action Items:**
- [ ] Add `YELLOW_CARD_ENVIRONMENT` variable
- [ ] Add timeout configuration (optional)
- [ ] Add webhook secret for production (optional)
- [ ] Verify API credentials are correct

#### 1.2 Update `settings/settings.py`
**Status:** ⏳ Pending

**Required Changes:**
```python
# Add Yellow Card configuration section (similar to AzamPay section)

# ============================================================================
# YELLOW CARD PAYMENT GATEWAY CONFIGURATION
# ============================================================================

# Environment: 'sandbox' or 'production'
YELLOW_CARD_ENVIRONMENT = config('YELLOW_CARD_ENVIRONMENT', default='sandbox')

# Dynamically load credentials based on environment
if YELLOW_CARD_ENVIRONMENT == 'production':
    YELLOW_CARD_BASE_URL = config('YELLOW_CARD_PROD_URL', default='https://api.yellowcard.io/business')
else:
    YELLOW_CARD_BASE_URL = config('YELLOW_CARD_SAND_BOX_URL', default='https://api-sandbox.yellowcard.co.tz')

YELLOW_CARD_API_KEY = config('YELLOW_CARD_API_KEY', default='')
YELLOW_CARD_API_SECRET = config('YELLOW_CARD_API_SECRET', default='')

# Timeout configuration (seconds)
YELLOW_CARD_TIMEOUT_CONNECT = config('YELLOW_CARD_TIMEOUT_CONNECT', default=30, cast=int)
YELLOW_CARD_TIMEOUT_READ = config('YELLOW_CARD_TIMEOUT_READ', default=60, cast=int)

# Webhook security (optional - for verifying callbacks)
YELLOW_CARD_WEBHOOK_SECRET = config('YELLOW_CARD_WEBHOOK_SECRET', default='')
```

**Action Items:**
- [ ] Add Yellow Card configuration section to `settings.py`
- [ ] Follow same pattern as AzamPay configuration
- [ ] Add environment-based URL selection
- [ ] Add timeout configuration
- [ ] Add webhook secret configuration

---

### Phase 2: Service Layer Implementation

#### 2.1 Create `yellowcard_service.py`
**Status:** ⏳ Pending  
**Location:** `donor/payments/yellowcard_service.py`

**Key Features:**
- Authentication token management (with caching)
- Payment initiation
- Transaction status checking
- Webhook callback processing
- Error handling and logging
- Currency support (USD, USDT, etc.)

**Class Structure:**
```python
class YellowCardError(Exception):
    """Custom exception for Yellow Card errors"""
    pass

class YellowCardService:
    """Yellow Card API service client"""
    
    def __init__(self):
        # Initialize from settings
        pass
    
    def _get_access_token(self) -> str:
        """Get or refresh access token with caching"""
        pass
    
    def initiate_payment(
        self,
        amount: Decimal,
        currency: str,
        external_id: str,
        customer_email: str,
        customer_name: str,
        additional_properties: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """Initiate payment with Yellow Card"""
        pass
    
    def check_transaction_status(self, reference_id: str) -> Tuple[bool, Dict]:
        """Check transaction status"""
        pass
    
    def process_callback(self, callback_data: Dict) -> Dict:
        """Process webhook callback from Yellow Card"""
        pass
```

**Action Items:**
- [ ] Research Yellow Card API authentication method (API key/secret vs OAuth)
- [ ] Implement token management (if required)
- [ ] Implement payment initiation endpoint
- [ ] Implement status check endpoint
- [ ] Implement callback processing
- [ ] Add comprehensive error handling
- [ ] Add logging (use existing logger pattern)
- [ ] Add token caching (if applicable)

**Dependencies:**
- Review Yellow Card API documentation: https://docs.yellowcard.engineering/docs/authentication-api
- Understand authentication flow
- Understand payment initiation flow
- Understand webhook/callback format

---

### Phase 3: View Layer Implementation

#### 3.1 Update `donation_type_views.py`
**Status:** ⏳ Pending

**Required Changes:**
Add Yellow Card payment option to existing donation views:

**New View Classes:**
```python
# Yellow Card Anonymous One-Time Patient Donation
class YellowCardAnonymousOneTimePatientDonationView(APIView):
    """🔓 Anonymous One-Time Patient Donation via Yellow Card"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Similar to AnonymousOneTimePatientDonationView
        # But uses yellowcard_service instead of azampay_service
        pass

# Yellow Card Authenticated One-Time Patient Donation
class YellowCardAuthenticatedOneTimePatientDonationView(APIView):
    """🔐 Authenticated One-Time Patient Donation via Yellow Card"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        pass

# ... (Similar for monthly, organization donations)
```

**Action Items:**
- [ ] Create Yellow Card versions of all 8 donation view classes
- [ ] Follow same pattern as AzamPay views
- [ ] Update Swagger documentation
- [ ] Handle Yellow Card specific requirements (email, name, etc.)
- [ ] Support Yellow Card supported currencies

**Alternative Approach (Unified Views):**
Instead of separate views, we could:
- Add `payment_gateway` parameter to existing views
- Route to appropriate service based on gateway selection
- **Pros:** Less code duplication, unified API
- **Cons:** More complex logic, harder to maintain gateway-specific features

**Recommendation:** Start with separate views for clarity, refactor later if needed.

---

### Phase 4: URL Routing

#### 4.1 Update `donor/urls.py`
**Status:** ⏳ Pending

**Required Changes:**
Add Yellow Card donation endpoints:

```python
# Yellow Card Patient Donations
path('donate/yellowcard/patient/anonymous/', YellowCardAnonymousOneTimePatientDonationView.as_view(), name='donate_yellowcard_patient_onetime_anonymous'),
path('donate/yellowcard/patient/', YellowCardAuthenticatedOneTimePatientDonationView.as_view(), name='donate_yellowcard_patient_onetime_authenticated'),
path('donate/yellowcard/patient/monthly/anonymous/', YellowCardAnonymousMonthlyPatientDonationView.as_view(), name='donate_yellowcard_patient_monthly_anonymous'),
path('donate/yellowcard/patient/monthly/', YellowCardAuthenticatedMonthlyPatientDonationView.as_view(), name='donate_yellowcard_patient_monthly_authenticated'),

# Yellow Card Organization Donations
path('donate/yellowcard/organization/anonymous/', YellowCardAnonymousOrganizationDonationView.as_view(), name='donate_yellowcard_organization_anonymous'),
path('donate/yellowcard/organization/', YellowCardAuthenticatedOrganizationDonationView.as_view(), name='donate_yellowcard_organization_authenticated'),
path('donate/yellowcard/organization/monthly/anonymous/', YellowCardAnonymousMonthlyOrganizationDonationView.as_view(), name='donate_yellowcard_organization_monthly_anonymous'),
path('donate/yellowcard/organization/monthly/', YellowCardAuthenticatedMonthlyOrganizationDonationView.as_view(), name='donate_yellowcard_organization_monthly_authenticated'),

# Yellow Card Payment Endpoints
path('payment/yellowcard/callback/', YellowCardCallbackView.as_view(), name='yellowcard_callback'),
path('payment/yellowcard/status/', YellowCardPaymentStatusView.as_view(), name='yellowcard_payment_status'),
```

**Action Items:**
- [ ] Add Yellow Card routes to `donor/urls.py`
- [ ] Follow same naming convention as AzamPay routes
- [ ] Ensure proper URL ordering (more specific routes first)

---

### Phase 5: Callback & Webhook Handling

#### 5.1 Create/Update `callback_views.py`
**Status:** ⏳ Pending

**Required Changes:**
Add Yellow Card callback handler:

```python
class YellowCardCallbackView(APIView):
    """Handle Yellow Card webhook callbacks"""
    permission_classes = [AllowAny]  # Webhooks don't use JWT
    
    def post(self, request):
        # Verify webhook signature (if Yellow Card provides)
        # Process callback data
        # Update donation status
        # Return success response
        pass

class YellowCardPaymentStatusView(APIView):
    """Check Yellow Card payment status"""
    permission_classes = [AllowAny]  # Or IsAuthenticated?
    
    def post(self, request):
        # Get transaction ID from request
        # Call yellowcard_service.check_transaction_status()
        # Return status
        pass
```

**Action Items:**
- [ ] Research Yellow Card webhook format
- [ ] Implement webhook signature verification (if available)
- [ ] Implement callback processing
- [ ] Update donation status based on callback
- [ ] Add error handling and logging
- [ ] Return proper HTTP responses

---

### Phase 6: Database & Model Updates

#### 6.1 Update `donor/models.py`
**Status:** ⏳ Migration Required

**Analysis:**
We need to add currency conversion fields to track:
- Original local currency amount (TZS, KES, NGN, etc.)
- Converted USD amount (for unified reporting)
- Exchange rate used (for audit trail)

**New Fields Required:**
```python
# Add to Donation model

# Currency conversion tracking (for Yellow Card multi-currency)
amount_usd = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    null=True,
    blank=True,
    help_text="Amount in USD (converted from local currency)"
)
exchange_rate = models.DecimalField(
    max_digits=12,
    decimal_places=6,
    null=True,
    blank=True,
    help_text="Exchange rate used (local currency to USD)"
)
rate_locked_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text="When exchange rate was locked"
)
```

**Currency Flow:**
```
┌─────────────────────────────────────────────────────────────┐
│  AzamPay (TZS Only)           Yellow Card (Multi-Currency)  │
├─────────────────────────────────────────────────────────────┤
│  Donor pays TZS               Donor pays TZS/KES/NGN/etc.   │
│  Store: amount=50000          Store: amount=50000           │
│         currency="TZS"               currency="TZS"         │
│         amount_usd=NULL              amount_usd=18.87       │
│                                      exchange_rate=2650.50  │
│  Settlement: TZS              Settlement: USD/USDT          │
└─────────────────────────────────────────────────────────────┘
```

**Action Items:**
- [ ] Add `amount_usd` field to Donation model
- [ ] Add `exchange_rate` field to Donation model
- [ ] Add `rate_locked_at` field to Donation model
- [ ] Create and run migration
- [ ] Update serializers to include new fields
- [ ] Update admin to show conversion info

---

### Phase 7: Testing Strategy

#### 7.1 Unit Tests
**Status:** ⏳ Pending

**Test Files to Create:**
- `donor/payments/tests/test_yellowcard_service.py`
- `donor/payments/tests/test_yellowcard_views.py`

**Test Coverage:**
- [ ] Token management and caching
- [ ] Payment initiation
- [ ] Status checking
- [ ] Callback processing
- [ ] Error handling
- [ ] Edge cases (invalid amounts, missing fields, etc.)

#### 7.2 Integration Tests
**Status:** ⏳ Pending

**Test Scenarios:**
- [ ] End-to-end donation flow (sandbox)
- [ ] Webhook callback processing
- [ ] Payment status updates
- [ ] Error scenarios

#### 7.3 Manual Testing Checklist
**Status:** ⏳ Pending

**Sandbox Testing:**
- [ ] Test payment initiation with valid data
- [ ] Test payment initiation with invalid data
- [ ] Test webhook callback (use webhook testing tool)
- [ ] Test status check endpoint
- [ ] Test all donation types (anonymous/auth, one-time/monthly, patient/org)
- [ ] Test error handling
- [ ] Test currency conversion (if applicable)

**Production Testing:**
- [ ] Small test payment ($1-5)
- [ ] Verify webhook received
- [ ] Verify donation status updated
- [ ] Verify email notifications (if applicable)

---

### Phase 8: Documentation

#### 8.1 API Documentation
**Status:** ⏳ Pending

**Files to Create/Update:**
- `docs/YELLOW_CARD_INTEGRATION.md` - Integration guide
- `docs/YELLOW_CARD_API.md` - API reference
- `donor/payments/YELLOW_CARD_README.md` - Service documentation

**Content:**
- [ ] Authentication setup
- [ ] API endpoints documentation
- [ ] Request/response examples
- [ ] Error handling guide
- [ ] Webhook setup instructions
- [ ] Testing guide
- [ ] Troubleshooting guide

#### 8.2 Code Documentation
**Status:** ⏳ Pending

**Action Items:**
- [ ] Add docstrings to all classes and methods
- [ ] Add inline comments for complex logic
- [ ] Update Swagger/OpenAPI documentation
- [ ] Add type hints (if not already present)

---

## 🔐 Security Considerations

### 1. API Credentials
- ✅ Store credentials in `.env` (not committed to git)
- ✅ Use environment variables in settings
- ⏳ Rotate credentials periodically
- ⏳ Use different credentials for sandbox/production

### 2. Webhook Security
- ⏳ Verify webhook signatures (if Yellow Card provides)
- ⏳ Use HTTPS for webhook endpoints
- ⏳ Validate webhook payloads
- ⏳ Implement idempotency (prevent duplicate processing)

### 3. Token Management
- ⏳ Cache tokens securely (use Django cache)
- ⏳ Handle token expiration gracefully
- ⏳ Implement token refresh logic

### 4. Error Handling
- ⏳ Don't expose sensitive information in error messages
- ⏳ Log errors securely (no credentials in logs)
- ⏳ Implement retry logic for transient failures

---

## 📝 Yellow Card API Reference

**Full API Flow Documentation:** See `YELLOW_CARD_API_FLOW.md` for detailed endpoint information.

### Base URLs
- **Sandbox:** `https://sandbox.api.yellowcard.io/business`
- **Production:** `https://api.yellowcard.io/business`

### Authentication Method
Yellow Card uses **HMAC-SHA256** signature authentication:

| Header | Description |
|--------|-------------|
| `X-YC-Timestamp` | Unix timestamp (seconds) |
| `Authorization` | `YcHmacV1 {api_key}:{signature}` |
| `Content-Type` | `application/json` |

**Signature Generation:**
```python
message = f"{timestamp}{method}{path}{body}"
signature = hmac.new(api_secret, message, sha256).digest()
signature = base64.b64encode(signature)
```

### API Endpoints to Implement

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 1 | `/business/channels` | GET | Get available payment methods |
| 2 | `/business/rates` | GET | Get exchange rates |
| 3 | `/business/rates/lock` | POST | Lock exchange rate |
| 4 | `/business/payments` | POST | Create payment request |
| 5 | `/business/payments/{id}/accept` | POST | Accept payment |
| 6 | `/business/payments/{id}` | GET | Check payment status |
| 7 | Webhook Handler | POST | Receive payment updates |

### Payment Flow Summary

```
1. GET /channels     → Get payment methods for country
2. GET /rates        → Get current exchange rates
3. POST /rates/lock  → Lock rate (30-60 sec validity)
4. POST /payments    → Create payment request
5. POST /payments/{id}/accept → Finalize payment
6. Webhook callback  → Receive completion notification
```

### Webhook Events
| Event | Description |
|-------|-------------|
| `payment.pending` | Payment awaiting processing |
| `payment.processing` | Payment being processed |
| `payment.completed` | Payment successful ✅ |
| `payment.failed` | Payment failed ❌ |
| `payment.expired` | Payment timed out |
| `payment.cancelled` | Payment cancelled |

### Important Notes
- **KYC Required:** Sender KYC data required for every transaction
- **Rate Lock:** Lock rate before creating payment (expires in 30-60 sec)
- **Sequence ID:** Use unique ID (donation reference) for idempotency
- **Currencies:** Local fiat (TZS, KES, NGN, etc.) → Stablecoin (USDT/USDC)

**Full Details:** See `docs/YELLOW_CARD_API_FLOW.md`

---

## 🚀 Implementation Order

### Recommended Sequence:

1. **Phase 1: Configuration** (1-2 hours)
   - Update `.env` and `settings.py`
   - Verify credentials work

2. **Phase 2: Service Layer** (4-6 hours)
   - Research API documentation
   - Implement `yellowcard_service.py`
   - Test service methods independently

3. **Phase 5: Callback Handling** (2-3 hours)
   - Implement webhook handler
   - Test with webhook testing tool

4. **Phase 3: View Layer** (4-6 hours)
   - Implement donation views
   - Test endpoints

5. **Phase 4: URL Routing** (30 minutes)
   - Add routes
   - Test routing

6. **Phase 7: Testing** (3-4 hours)
   - Write unit tests
   - Write integration tests
   - Manual testing

7. **Phase 8: Documentation** (2-3 hours)
   - Write API documentation
   - Update code comments
   - Create user guides

**Total Estimated Time:** 16-24 hours

---

## ✅ Pre-Implementation Checklist

Before starting implementation:

- [ ] Access Yellow Card API documentation
- [ ] Verify API credentials are valid
- [ ] Understand authentication flow
- [ ] Understand payment flow
- [ ] Understand webhook flow
- [ ] Review existing AzamPay code for patterns
- [ ] Set up sandbox environment
- [ ] Get test API credentials (if different from production)

---

## 📋 Post-Implementation Checklist

After implementation:

- [ ] All tests passing
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Sandbox testing complete
- [ ] Production credentials configured
- [ ] Webhook URL configured in Yellow Card dashboard
- [ ] Monitoring/logging in place
- [ ] Error handling tested
- [ ] Performance tested
- [ ] Security review completed

---

## 🔄 Future Enhancements

### Potential Improvements:
1. **Unified Payment Gateway Interface**
   - Abstract payment gateway logic
   - Allow switching between gateways easily
   - Support multiple gateways simultaneously

2. **Payment Gateway Selection**
   - Let users choose payment gateway
   - Show available gateways based on currency
   - Auto-select best gateway based on amount/currency

3. **Multi-Currency Support**
   - Yellow Card specializes in stablecoins
   - Support USDT, USDC, etc.
   - Handle currency conversion

4. **Payment Analytics**
   - Track payment gateway performance
   - Compare success rates
   - Monitor transaction fees

---

## 📞 Support & Resources

### Yellow Card Resources:
- **API Documentation:** https://docs.yellowcard.engineering/
- **Support:** Contact Yellow Card support team
- **Dashboard:** Yellow Card merchant dashboard (for webhook configuration)

### Internal Resources:
- **AzamPay Integration:** `donor/payments/azampay_service.py` (reference)
- **Payment Views:** `donor/payments/donation_type_views.py` (reference)
- **Callback Handling:** `donor/payments/callback_views.py` (reference)

---

## 📝 Notes

- This plan follows the same pattern as AzamPay integration for consistency
- Yellow Card may have different API structure - adapt as needed
- Focus on sandbox testing first before production deployment
- Keep security as top priority throughout implementation

---

**Last Updated:** February 9, 2026  
**Status:** Planning Complete - Ready for Implementation
