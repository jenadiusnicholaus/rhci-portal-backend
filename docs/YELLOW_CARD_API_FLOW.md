# Yellow Card API - Step-by-Step Integration Flow

## 📋 Overview

This document outlines the specific Yellow Card API endpoints we need to call and the order of operations for payment integration.

**API Documentation:** https://docs.yellowcard.engineering/reference/

**Base URLs:**
- **Sandbox:** `https://sandbox.api.yellowcard.io/business`
- **Production:** `https://api.yellowcard.io/business`

---

## 💱 Currency Conversion Strategy

### Payment Gateway Comparison

| Gateway | Local Currency | Settlement | Use Case |
|---------|---------------|------------|----------|
| **AzamPay** | TZS only | TZS | Tanzania local payments (Mobile Money) |
| **Yellow Card** | TZS, KES, NGN, etc. | USD/USDT | International + Multi-currency |

### Currency Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CURRENCY CONVERSION FLOW                        │
└─────────────────────────────────────────────────────────────────────┘

DONOR PAYS (Local Currency)          RHCI RECEIVES (Settlement)
─────────────────────────────────────────────────────────────────────
Tanzania Donor pays 50,000 TZS  →  Yellow Card converts → $18.87 USD
Kenya Donor pays 5,000 KES      →  Yellow Card converts → $38.46 USD
Nigeria Donor pays 50,000 NGN   →  Yellow Card converts → $31.25 USD
─────────────────────────────────────────────────────────────────────

DATABASE RECORDS:
- amount: 50000              (local currency amount)
- currency: "TZS"            (local currency code)
- amount_usd: 18.87          (converted USD amount) ← NEW FIELD
- exchange_rate: 2650.50     (rate at time of payment) ← NEW FIELD
```

### What We Store in Database

| Field | Description | Example | Purpose |
|-------|-------------|---------|---------|
| `amount` | Original amount in local currency | 50000.00 | What donor paid |
| `currency` | Local currency code | TZS | Donor's currency |
| `amount_usd` | **USD equivalent value** | 18.87 | For RHCI reports & dashboards |
| `exchange_rate` | Rate used for conversion | 2650.50 | Audit trail |
| `rate_locked_at` | When rate was locked | 2026-02-09T10:30:00Z | Audit trail |

### 💡 Why Store USD in Database?

```
┌─────────────────────────────────────────────────────────────────────────┐
│  YELLOW CARD DASHBOARD          vs          RHCI DATABASE              │
├─────────────────────────────────────────────────────────────────────────┤
│  Stores: USDT (stablecoin)                  Stores: USD (real value)   │
│  Purpose: Settlement/Withdrawal             Purpose: Reporting         │
│  Access: Yellow Card portal                 Access: RHCI system        │
│                                                                         │
│  Note: 1 USDT ≈ $1 USD (stablecoin pegged to dollar)                   │
└─────────────────────────────────────────────────────────────────────────┘

RHCI needs USD in database for:
✅ Patient funding progress ("Patient X has received $500 USD")
✅ Dashboard statistics ("Total donations: $10,000 USD")  
✅ Financial reports ("Q1 donations: $25,000 USD")
✅ Donor receipts ("Thank you for your $50 USD donation")
✅ Multi-currency comparison (TZS + KES + NGN all in USD)
```

### Model Update Required

```python
# donor/models.py - Add these fields to Donation model

# Currency conversion tracking (for Yellow Card)
# Stores USD value for RHCI reporting (Yellow Card holds as USDT)
amount_usd = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    null=True,
    blank=True,
    help_text="USD equivalent value for RHCI reporting (Yellow Card holds as USDT, 1 USDT ≈ $1 USD)"
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

### 📊 Database Usage Examples

```python
# Patient funding progress
patient = PatientProfile.objects.get(id=123)
total_funding_usd = patient.donations.filter(
    status='COMPLETED'
).aggregate(Sum('amount_usd'))['amount_usd__sum'] or 0
# Display: "Patient has received $1,234.56 USD in donations"

# Dashboard total donations
total_donations_usd = Donation.objects.filter(
    status='COMPLETED',
    payment_gateway='Yellow Card'
).aggregate(Sum('amount_usd'))['amount_usd__sum'] or 0
# Display: "Total Yellow Card donations: $10,500.00 USD"

# Donor receipt
donation = Donation.objects.get(id=456)
# Display: "Thank you! You donated 50,000 TZS ($18.87 USD)"
print(f"Local: {donation.amount} {donation.currency}")
print(f"USD Value: ${donation.amount_usd}")
```

---

## 🔐 Step 1: Authentication

Yellow Card uses HMAC-based authentication with API Key and Secret.

### Required Headers for ALL API Calls

| Header | Description |
|--------|-------------|
| `X-YC-Timestamp` | Unix timestamp (seconds since epoch) |
| `Authorization` | `YcHmacV1 {api_key}:{signature}` |
| `Content-Type` | `application/json` |

### Signature Generation

```python
import hmac
import hashlib
import time

def generate_signature(api_secret: str, timestamp: str, method: str, path: str, body: str = "") -> str:
    """
    Generate HMAC-SHA256 signature for Yellow Card API
    
    Args:
        api_secret: Your Yellow Card API secret
        timestamp: Unix timestamp as string
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path (e.g., /business/channels)
        body: Request body JSON string (empty for GET requests)
    
    Returns:
        Base64-encoded HMAC-SHA256 signature
    """
    # Construct message to sign
    message = f"{timestamp}{method}{path}{body}"
    
    # Create HMAC-SHA256 signature
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # Return base64 encoded signature
    import base64
    return base64.b64encode(signature).decode('utf-8')
```

### Example Headers Construction

```python
import time

api_key = "your-api-key"
api_secret = "your-api-secret"
timestamp = str(int(time.time()))
method = "GET"
path = "/business/channels"
body = ""  # Empty for GET

signature = generate_signature(api_secret, timestamp, method, path, body)

headers = {
    "X-YC-Timestamp": timestamp,
    "Authorization": f"YcHmacV1 {api_key}:{signature}",
    "Content-Type": "application/json"
}
```

---

## ⚠️ IMPORTANT: Collection vs Disbursement

Yellow Card has TWO types of operations:

| Type | Direction | Use Case | For RHCI |
|------|-----------|----------|----------|
| **Collection (On-Ramp)** | Donor → Yellow Card → RHCI Dashboard | Receive payments | ✅ **For Donations** |
| **Disbursement (Off-Ramp)** | RHCI Dashboard → Yellow Card → Recipient | Send payments | ❌ Not for donations |

**For donations, we need COLLECTION (On-Ramp) APIs!**

```
COLLECTION FLOW (What we need for donations):
┌──────────┐         ┌─────────────┐         ┌─────────────────────┐
│  DONOR   │  ────►  │ YELLOW CARD │  ────►  │  YELLOW CARD        │
│ Pays TZS │         │  Converts   │         │  DASHBOARD (USDT)   │
└──────────┘         └─────────────┘         │                     │
     │                                        │  RHCI Balance: $500 │
     │                                        │  ┌───────────────┐  │
     │  50,000 TZS                           │  │ Settle/Withdraw│  │
     │                                        │  └───────────────┘  │
     └────────────────────────────────────►  └─────────────────────┘
                                                       │
                                                       │ (When RHCI wants)
                                                       ▼
                                              ┌─────────────────────┐
                                              │   RHCI WALLET/BANK  │
                                              │   Receives USDT     │
                                              └─────────────────────┘
```

### 💰 Yellow Card Dashboard Balance

Yellow Card **holds USDT in your dashboard** after each successful collection:

- Donor pays 50,000 TZS → Yellow Card converts → **$18.87 USDT added to dashboard**
- Funds accumulate in Yellow Card dashboard
- RHCI can **withdraw/settle** whenever needed (daily, weekly, etc.)
- Settlement options: USDT to crypto wallet, USD to bank account

---

## 🔄 Collection Flow - Step by Step (For Donations)

### Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                YELLOW CARD COLLECTION (ON-RAMP) FLOW                │
│                       For Receiving Donations                       │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Get Channels       →  Get available payment methods (collection)
           ↓
Step 2: Get Rates          →  Get exchange rates ("buy" for on-ramp)
           ↓
Step 3: Lock Rate          →  Lock rate for 30-60 seconds
           ↓
Step 4: Create Collection  →  Create collection request (donor pays in)
           ↓
Step 5: Donor Pays         →  Donor completes payment (mobile money/bank)
           ↓
Step 6: Webhook Callback   →  Receive payment status + USD amount
           ↓
Step 7: Get Status         →  (Optional) Poll for status
```

### ⚠️ Note on API Endpoints

The exact endpoint names may vary. Check Yellow Card documentation for:
- `/business/collections` - For on-ramp (receiving payments)
- `/business/payments` - May be for off-ramp (disbursements) only

The `/business/payments` with `accept` that you mentioned is likely for **disbursements** (paying OUT), not collections (receiving IN).

---

## 📡 API Endpoints - Detailed

### Step 1: Get Channels

**Purpose:** Discover available payment channels (mobile money, bank transfer, etc.) for each country.

```http
GET /business/channels
```

**When to Call:** On app initialization or when user selects country.

**Response Example:**
```json
{
  "channels": [
    {
      "id": "channel_id",
      "name": "Mobile Money",
      "country": "TZ",
      "currency": "TZS",
      "type": "mobileMoney",
      "minAmount": 1000,
      "maxAmount": 5000000,
      "status": "active"
    },
    {
      "id": "channel_id_2",
      "name": "Bank Transfer",
      "country": "TZ",
      "currency": "TZS",
      "type": "bank",
      "minAmount": 10000,
      "maxAmount": 50000000,
      "status": "active"
    }
  ]
}
```

**Implementation:**
```python
def get_channels(self):
    """Get available payment channels"""
    path = "/business/channels"
    return self._make_request("GET", path)
```

---

### Step 2: Get Rates

**Purpose:** Get current exchange rates for currency conversion.

```http
GET /business/rates
```

**When to Call:** Before showing prices to user, or when calculating payment amount.

**Response Example:**
```json
{
  "rates": [
    {
      "code": "TZS",
      "currency": "Tanzanian Shilling",
      "buy": 2650.50,
      "sell": 2700.25,
      "lastUpdated": "2026-02-09T10:30:00Z"
    }
  ]
}
```

**Implementation:**
```python
def get_rates(self):
    """Get current exchange rates"""
    path = "/business/rates"
    return self._make_request("GET", path)
```

---

### Step 3: Get Networks (Optional)

**Purpose:** Get supported blockchain networks for crypto settlements.

```http
GET /business/networks
```

**When to Call:** If you need to specify settlement network.

**Response Example:**
```json
{
  "networks": [
    {
      "code": "ethereum",
      "name": "Ethereum",
      "assets": ["USDT", "USDC"]
    },
    {
      "code": "tron",
      "name": "Tron",
      "assets": ["USDT"]
    }
  ]
}
```

---

### Step 4: Lock Rate ⚠️ IMPORTANT

**Purpose:** Lock in exchange rate for a specific duration (usually 30-60 seconds).

```http
POST /business/rates/lock
```

**When to Call:** Just before creating payment request.

**Request Body:**
```json
{
  "currency": "TZS",
  "amount": 50000,
  "type": "buy"
}
```

**Response Example:**
```json
{
  "id": "rate_lock_id",
  "rate": 2650.50,
  "expiresAt": "2026-02-09T10:31:00Z",
  "amount": 50000,
  "convertedAmount": 18.87
}
```

**Implementation:**
```python
def lock_rate(self, currency: str, amount: Decimal, rate_type: str = "buy"):
    """Lock in exchange rate"""
    path = "/business/rates/lock"
    body = {
        "currency": currency,
        "amount": str(amount),
        "type": rate_type
    }
    return self._make_request("POST", path, body)
```

---

### Step 5: Resolve Account

**Purpose:** Validate recipient account details before payment.

```http
POST /business/account/resolve
```

**When to Call:** Before creating payment to validate account.

**Request Body:**
```json
{
  "channelId": "channel_id",
  "accountNumber": "255789123456",
  "accountType": "mobileMoney"
}
```

**Response Example:**
```json
{
  "accountName": "John Doe",
  "accountNumber": "255789123456",
  "valid": true
}
```

---

### Step 6: Create Payment Request ⭐ MAIN ENDPOINT

**Purpose:** Initiate a payment request.

```http
POST /business/payments
```

**When to Call:** When user confirms donation.

**Request Body:**
```json
{
  "channelId": "channel_id",
  "sequenceId": "RHCI-DN-123",
  "sender": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "255789123456",
    "country": "TZ",
    "address": {
      "line1": "123 Main St",
      "city": "Dar es Salaam",
      "country": "TZ"
    },
    "dob": "1990-01-01",
    "idType": "passport",
    "idNumber": "AB123456"
  },
  "destination": {
    "accountNumber": "255789123456",
    "accountType": "mobileMoney",
    "accountName": "Jane Doe",
    "networkCode": "vodacom"
  },
  "amount": 50000,
  "currency": "TZS",
  "reason": "donation",
  "forceAccept": false,
  "rateLockId": "rate_lock_id"
}
```

**Response Example:**
```json
{
  "id": "payment_id",
  "sequenceId": "RHCI-DN-123",
  "status": "pending",
  "amount": 50000,
  "currency": "TZS",
  "convertedAmount": 18.87,
  "rate": 2650.50,
  "createdAt": "2026-02-09T10:30:00Z",
  "expiresAt": "2026-02-09T10:45:00Z"
}
```

**Implementation:**
```python
def create_payment(
    self,
    channel_id: str,
    sequence_id: str,
    sender: dict,
    destination: dict,
    amount: Decimal,
    currency: str,
    reason: str = "donation",
    rate_lock_id: str = None
):
    """Create a payment request"""
    path = "/business/payments"
    body = {
        "channelId": channel_id,
        "sequenceId": sequence_id,
        "sender": sender,
        "destination": destination,
        "amount": str(amount),
        "currency": currency,
        "reason": reason,
        "forceAccept": False
    }
    
    if rate_lock_id:
        body["rateLockId"] = rate_lock_id
    
    return self._make_request("POST", path, body)
```

---

### Step 7: Accept Payment Request

**Purpose:** Finalize and accept the payment.

```http
POST /business/payments/{paymentId}/accept
```

**When to Call:** After payment is created and user confirms.

**Response Example:**
```json
{
  "id": "payment_id",
  "status": "processing",
  "message": "Payment is being processed"
}
```

---

### Step 8: Webhook Callback 🔔 (Currency Conversion Stored Here!)

**Purpose:** Receive real-time payment status updates and **store final converted amounts**.

**Webhook URL:** Configure in Yellow Card dashboard (e.g., `https://yoursite.com/api/v1.0/donors/payment/yellowcard/callback/`)

**Webhook Payload Example:**
```json
{
  "event": "payment.completed",
  "data": {
    "id": "payment_id",
    "sequenceId": "RHCI-DN-123",
    "status": "completed",
    "amount": 50000,
    "currency": "TZS",
    "convertedAmount": 18.87,
    "rate": 2650.50,
    "fee": 0.50,
    "completedAt": "2026-02-09T10:35:00Z"
  },
  "timestamp": "2026-02-09T10:35:01Z"
}
```

**Webhook Events:**
| Event | Description |
|-------|-------------|
| `payment.pending` | Payment created, awaiting processing |
| `payment.processing` | Payment is being processed |
| `payment.completed` | Payment successful ✅ **Store USD amount here!** |
| `payment.failed` | Payment failed |
| `payment.expired` | Payment expired (timeout) |
| `payment.cancelled` | Payment cancelled |

**Implementation (Store USD on Success):**
```python
from django.utils import timezone
from decimal import Decimal

def handle_webhook(self, request):
    """
    Process Yellow Card webhook callback
    
    ⭐ IMPORTANT: We store the converted USD amount ONLY on successful payment!
    This ensures we have the actual conversion rate used by Yellow Card.
    """
    # Verify webhook signature (if applicable)
    payload = json.loads(request.body)
    event = payload.get('event')
    data = payload.get('data')
    
    sequence_id = data.get('sequenceId')  # Our donation ID (e.g., "RHCI-DN-123")
    status = data.get('status')
    
    # Extract donation ID from sequence_id
    donation_id = sequence_id.replace('RHCI-DN-', '')
    
    try:
        donation = Donation.objects.get(id=donation_id)
    except Donation.DoesNotExist:
        return JsonResponse({'error': 'Donation not found'}, status=404)
    
    if status == 'completed':
        # ✅ SUCCESS - Store the converted USD amount!
        donation.status = 'COMPLETED'
        donation.completed_at = timezone.now()
        
        # Store currency conversion from Yellow Card response
        donation.amount_usd = Decimal(str(data.get('convertedAmount', 0)))
        donation.exchange_rate = Decimal(str(data.get('rate', 0)))
        donation.rate_locked_at = timezone.now()
        
        # Store Yellow Card transaction reference
        donation.transaction_id = data.get('id')
        
        donation.save()
        
        logger.info(
            f"✅ Donation {donation_id} COMPLETED: "
            f"{donation.amount} {donation.currency} = ${donation.amount_usd} USD "
            f"(rate: {donation.exchange_rate})"
        )
        
    elif status == 'failed':
        donation.status = 'FAILED'
        donation.save()
        logger.error(f"❌ Donation {donation_id} FAILED")
        
    elif status == 'expired':
        donation.status = 'CANCELLED'
        donation.save()
        logger.warning(f"⏰ Donation {donation_id} EXPIRED")
    
    return JsonResponse({'received': True})
```

### ⭐ When Currency Conversion is Stored

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CURRENCY STORAGE TIMELINE                          │
└─────────────────────────────────────────────────────────────────────┘

1. CREATE PAYMENT (Initial)
   ├── amount = 50000        ✅ Stored (local amount)
   ├── currency = "TZS"      ✅ Stored (local currency)
   ├── amount_usd = NULL     ⏳ Not yet (waiting for confirmation)
   ├── exchange_rate = NULL  ⏳ Not yet
   └── status = "PENDING"

2. WEBHOOK: payment.completed (On Success!)
   ├── amount = 50000        ✅ Already stored
   ├── currency = "TZS"      ✅ Already stored
   ├── amount_usd = 18.87    ✅ NOW STORED (from webhook data)
   ├── exchange_rate = 2650.50 ✅ NOW STORED (actual rate used)
   └── status = "COMPLETED"  ✅ Updated

3. WEBHOOK: payment.failed (On Failure)
   ├── amount_usd = NULL     ❌ Not stored (payment failed)
   ├── exchange_rate = NULL  ❌ Not stored
   └── status = "FAILED"     ✅ Updated
```

**Why store on success only?**
- Yellow Card confirms the actual conversion rate used
- Prevents storing estimated rates that might differ
- Ensures audit trail matches actual transaction

---

### Step 9: Get Payment Status

**Purpose:** Check payment status (alternative to webhook).

```http
GET /business/payments/{paymentId}
```

**When to Call:** For status polling or verification.

**Response Example:**
```json
{
  "id": "payment_id",
  "sequenceId": "RHCI-DN-123",
  "status": "completed",
  "amount": 50000,
  "currency": "TZS",
  "completedAt": "2026-02-09T10:35:00Z"
}
```

---

## 🎯 Implementation Summary

### Database Migration Required

Add these fields to `Donation` model:

```python
# donor/models.py - Add to Donation class

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

**Migration Command:**
```bash
python manage.py makemigrations donor --name add_currency_conversion_fields
python manage.py migrate
```

### APIs We Need to Implement

| Priority | Endpoint | Purpose | Required |
|----------|----------|---------|----------|
| 1️⃣ | `GET /business/channels` | Get payment methods | ✅ Yes |
| 2️⃣ | `GET /business/rates` | Get exchange rates | ✅ Yes |
| 3️⃣ | `POST /business/rates/lock` | Lock rate | ✅ Yes |
| 4️⃣ | `POST /business/payments` | Create payment | ✅ Yes |
| 5️⃣ | `POST /business/payments/{id}/accept` | Accept payment | ✅ Yes |
| 6️⃣ | Webhook Handler | Receive updates | ✅ Yes |
| 7️⃣ | `GET /business/payments/{id}` | Check status | Optional |
| 8️⃣ | `GET /business/networks` | Get networks | Optional |
| 9️⃣ | `POST /business/account/resolve` | Validate account | Optional |

---

## 📝 Service Class Structure

```python
class YellowCardService:
    """Yellow Card API service"""
    
    def __init__(self):
        self.base_url = settings.YELLOW_CARD_BASE_URL
        self.api_key = settings.YELLOW_CARD_API_KEY
        self.api_secret = settings.YELLOW_CARD_API_SECRET
    
    # Authentication
    def _generate_signature(self, timestamp, method, path, body=""):
        pass
    
    def _get_headers(self, method, path, body=""):
        pass
    
    def _make_request(self, method, path, body=None):
        pass
    
    # Core APIs
    def get_channels(self):
        """Step 1: Get available payment channels"""
        pass
    
    def get_rates(self):
        """Step 2: Get exchange rates"""
        pass
    
    def lock_rate(self, currency, amount):
        """Step 4: Lock exchange rate"""
        pass
    
    def create_payment(self, channel_id, sequence_id, sender, destination, amount, currency):
        """Step 6: Create payment request"""
        pass
    
    def accept_payment(self, payment_id):
        """Step 7: Accept payment"""
        pass
    
    def get_payment_status(self, payment_id):
        """Step 9: Get payment status"""
        pass
    
    def process_webhook(self, payload):
        """Step 8: Process webhook callback"""
        pass
```

---

## 🔄 Complete Payment Flow Example

```python
from decimal import Decimal
from django.utils import timezone

# ============================================
# STEP 1-3: USER INTERFACE (Show rates to user)
# ============================================

# 1. User selects payment method
channels = yellowcard_service.get_channels()
selected_channel = channels['channels'][0]  # User picks one

# 2. Get current rates (to show user the estimated conversion)
rates = yellowcard_service.get_rates()
tzs_rate = next(r for r in rates['rates'] if r['code'] == 'TZS')
# Example: tzs_rate = {"code": "TZS", "buy": 2650.50, "sell": 2700.25}

# 3. User enters amount (e.g., 50000 TZS)
local_amount = Decimal('50000')
local_currency = 'TZS'

# Show estimated USD to user (for display only!)
estimated_usd = local_amount / Decimal(str(tzs_rate['buy']))
# Display: "You will donate approximately $18.87 USD"

# ============================================
# STEP 4-5: INITIATE PAYMENT
# ============================================

# 4. Lock the rate (just before payment - valid for 30-60 seconds)
rate_lock = yellowcard_service.lock_rate(local_currency, local_amount)
rate_lock_id = rate_lock['id']

# 5. Create donation record - LOCAL AMOUNT ONLY (USD stored on success!)
donation = Donation.objects.create(
    # Local currency (what donor will pay)
    amount=local_amount,              # 50000.00
    currency=local_currency,          # "TZS"
    
    # ⚠️ USD fields are NULL initially - stored on webhook success!
    amount_usd=None,                  # Will be set on payment.completed
    exchange_rate=None,               # Will be set on payment.completed
    rate_locked_at=None,              # Will be set on payment.completed
    
    # Payment info
    status='PENDING',
    payment_gateway='Yellow Card',
    # ... other fields
)

# ============================================
# STEP 6-8: PROCESS PAYMENT
# ============================================

# 6. Create payment with Yellow Card
payment = yellowcard_service.create_payment(
    channel_id=selected_channel['id'],
    sequence_id=f"RHCI-DN-{donation.id}",
    sender={
        "name": "John Doe",
        "email": "john@example.com",
        # ... KYC data
    },
    destination={
        "accountNumber": "255789123456",
        # ... account details
    },
    amount=local_amount,
    currency=local_currency,
    rate_lock_id=rate_lock_id
)

# 7. Update donation with Yellow Card payment ID
donation.transaction_id = payment['id']
donation.save()

# 8. Accept payment (finalize)
yellowcard_service.accept_payment(payment['id'])

# ============================================
# STEP 9: WEBHOOK CALLBACK (Async - USD stored here!)
# ============================================

# 9. Yellow Card sends webhook when payment completes
# See handle_webhook() - THIS IS WHERE amount_usd IS STORED!
#
# On payment.completed webhook:
#   donation.status = 'COMPLETED'
#   donation.amount_usd = 18.87        ← Stored from webhook!
#   donation.exchange_rate = 2650.50   ← Stored from webhook!
#   donation.rate_locked_at = now()
#   donation.save()
```

### 📊 Database State at Each Step

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: After creating donation (PENDING)                          │
├─────────────────────────────────────────────────────────────────────┤
│  amount = 50000.00          ✅                                      │
│  currency = "TZS"           ✅                                      │
│  amount_usd = NULL          ⏳ (waiting for success)                │
│  exchange_rate = NULL       ⏳ (waiting for success)                │
│  status = "PENDING"         ✅                                      │
│  payment_gateway = "Yellow Card"  ✅                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 9: After webhook payment.completed (SUCCESS!)                  │
├─────────────────────────────────────────────────────────────────────┤
│  amount = 50000.00          ✅ (unchanged)                          │
│  currency = "TZS"           ✅ (unchanged)                          │
│  amount_usd = 18.87         ✅ NOW STORED!                          │
│  exchange_rate = 2650.50    ✅ NOW STORED!                          │
│  status = "COMPLETED"       ✅ UPDATED!                             │
│  completed_at = 2026-02-09  ✅ UPDATED!                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 9: After webhook payment.failed (FAILURE)                      │
├─────────────────────────────────────────────────────────────────────┤
│  amount = 50000.00          ✅ (unchanged)                          │
│  currency = "TZS"           ✅ (unchanged)                          │
│  amount_usd = NULL          ❌ NOT STORED (payment failed)          │
│  exchange_rate = NULL       ❌ NOT STORED                           │
│  status = "FAILED"          ✅ UPDATED!                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 💱 Currency Conversion Examples

### Tanzania (TZS → USD)
```python
# Donor pays 50,000 TZS
local_amount = 50000
local_currency = "TZS"
exchange_rate = 2650.50  # From Yellow Card rates API
amount_usd = 50000 / 2650.50  # = $18.87

# Store in database:
donation.amount = 50000          # Local amount (TZS)
donation.currency = "TZS"
donation.amount_usd = 18.87      # USD equivalent
donation.exchange_rate = 2650.50
```

### Kenya (KES → USD)
```python
# Donor pays 5,000 KES
local_amount = 5000
local_currency = "KES"
exchange_rate = 130.00  # From Yellow Card rates API
amount_usd = 5000 / 130.00  # = $38.46

# Store in database:
donation.amount = 5000
donation.currency = "KES"
donation.amount_usd = 38.46
donation.exchange_rate = 130.00
```

### Nigeria (NGN → USD)
```python
# Donor pays 50,000 NGN
local_amount = 50000
local_currency = "NGN"
exchange_rate = 1600.00  # From Yellow Card rates API
amount_usd = 50000 / 1600.00  # = $31.25

# Store in database:
donation.amount = 50000
donation.currency = "NGN"
donation.amount_usd = 31.25
donation.exchange_rate = 1600.00
```

---

## 📊 Reporting with Dual Currency

### Dashboard Stats Query
```python
from django.db.models import Sum, F
from donor.models import Donation

# Total donations by local currency
donations_by_currency = Donation.objects.filter(
    status='COMPLETED'
).values('currency').annotate(
    total_local=Sum('amount'),
    total_usd=Sum('amount_usd')
)

# Result:
# [
#     {"currency": "TZS", "total_local": 5000000, "total_usd": 1886.79},
#     {"currency": "KES", "total_local": 250000, "total_usd": 1923.08},
#     {"currency": "NGN", "total_local": 1000000, "total_usd": 625.00},
# ]

# Grand total in USD
total_usd = Donation.objects.filter(
    status='COMPLETED'
).aggregate(total=Sum('amount_usd'))['total']
# Result: $4434.87 USD
```

### Patient Funding Progress
```python
# Patient funding in local currency (TZS for Tanzania patients)
patient = PatientProfile.objects.get(id=123)

# Get donations in TZS
tzs_donations = patient.donations.filter(
    status='COMPLETED',
    currency='TZS'
).aggregate(total=Sum('amount'))['total'] or 0

# Get all donations converted to USD for unified reporting
all_donations_usd = patient.donations.filter(
    status='COMPLETED'
).aggregate(total=Sum('amount_usd'))['total'] or 0

# Display to user:
# "This patient has received TSh 500,000 ($188.68 USD)"
```

---

## ⚠️ Important Notes

1. **KYC Data Required:** Yellow Card requires sender KYC information for every transaction
2. **Rate Lock Expiry:** Lock rate before creating payment (usually 30-60 sec validity)
3. **Sequence ID:** Use unique sequence IDs (your donation reference)
4. **Webhooks:** Configure webhook URL in Yellow Card dashboard
5. **Idempotency:** Use `sequenceId` to prevent duplicate payments
6. **Error Handling:** Handle rate lock expiry, payment failures gracefully

---

## 🔗 References

- **API Reference:** https://docs.yellowcard.engineering/reference/
- **Get Channels:** https://docs.yellowcard.engineering/reference/get-channels
- **Create Payment:** https://docs.yellowcard.engineering/reference/create-payment-request
- **Accept Payment:** https://docs.yellowcard.engineering/reference/accept-payment-request

---

**Next Step:** Implement `yellowcard_service.py` following this flow!
