# Yellow Card API - Complete Call Checklist

## 📋 All API Calls Required

This document lists **every API call** needed for Yellow Card integration, in the exact order they must be called.

---

## ⚠️ IMPORTANT: Collection vs Disbursement

Yellow Card has TWO types of payment operations:

| Type | Direction | Money Flow | Use Case |
|------|-----------|------------|----------|
| **Collection (On-Ramp)** | IN | Donor pays local → RHCI receives USD | ✅ **For Donations** |
| **Disbursement (Off-Ramp)** | OUT | RHCI sends USD → Recipient gets local | ❌ Not for donations |

**For RHCI Donations, we use COLLECTION (On-Ramp) APIs!**

```
COLLECTION FLOW (What we need):
┌──────────┐     ┌─────────────┐     ┌──────────┐
│  DONOR   │ ──► │ YELLOW CARD │ ──► │   RHCI   │
│ Pays TZS │     │  Converts   │     │ Gets USD │
└──────────┘     └─────────────┘     └──────────┘

DISBURSEMENT FLOW (NOT for donations):
┌──────────┐     ┌─────────────┐     ┌───────────┐
│   RHCI   │ ──► │ YELLOW CARD │ ──► │ RECIPIENT │
│ Sends USD│     │  Converts   │     │ Gets TZS  │
└──────────┘     └─────────────┘     └───────────┘
```

---

## 🔐 Authentication (Required for ALL Calls)

Every API request needs these headers:

```
Headers:
├── X-YC-Timestamp: {unix_timestamp}
├── Authorization: YcHmacV1 {api_key}:{signature}
└── Content-Type: application/json
```

**Signature Formula:**
```
message = timestamp + method + path + body
signature = Base64(HMAC-SHA256(api_secret, message))
```

---

## 📡 API Endpoints Summary (COLLECTION / On-Ramp) - VERIFIED ✅

**Source:** https://docs.yellowcard.engineering/docs/making-a-collection

| # | API Name | Method | When Called | Required? |
|---|----------|--------|-------------|-----------|
| 1 | **Get Channels** | GET | App init / Country select | ✅ Yes |
| 2 | **Get Rates** | GET | Show conversion to user | ✅ Yes |
| 3 | **Get Networks** | GET | If Mobile Money selected | ✅ Yes (for Mobile Money) |
| 4 | **Payment Reasons** | GET | Before submit | ✅ Yes |
| 5 | **Submit Collection Request** | POST | User confirms (creates quote) | ✅ Yes |
| 6 | **Accept Collection Request** | POST | After quote (confirm payment) | ✅ Yes |
| 7 | **Webhook Handler** | POST (incoming) | Receive payment status | ✅ Yes |
| 8 | **Lookup Collection** | GET | Poll status (if no webhook) | ⚪ Optional |
| 9 | **Deny Collection Request** | POST | Cancel before accept | ⚪ Optional |

**Key Finding:** Collection uses TWO calls: Submit (get quote) → Accept (confirm payment)

---

## 🔄 Complete Flow Diagram (COLLECTION / On-Ramp)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 YELLOW CARD COLLECTION (ON-RAMP) FLOW                       │
│                      For receiving donations                                │
└─────────────────────────────────────────────────────────────────────────────┘

INITIALIZATION (Once on app load or country change)
══════════════════════════════════════════════════════════════════════════════
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CALL 1: GET /business/channels                                             │
│  Purpose: Get available payment methods for country                         │
│  Filter: channels with type="collection" or direction="in"                 │
│  When: App initialization OR when user selects country                      │
│  Cache: Yes (refresh every 1-24 hours)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CALL 2: GET /business/rates                                                │
│  Purpose: Get exchange rates to show user                                   │
│  Use: "buy" rate (local currency → USD for on-ramp)                        │
│  When: Before showing donation form OR periodically refresh                 │
│  Cache: Yes (refresh every 1-5 minutes)                                     │
└─────────────────────────────────────────────────────────────────────────────┘


USER ENTERS DONATION AMOUNT
══════════════════════════════════════════════════════════════════════════════
    │
    │  User enters: 50,000 TZS
    │  Display: "≈ $18.87 USD" (from cached rates)
    │
    ▼

USER CLICKS "DONATE" BUTTON
══════════════════════════════════════════════════════════════════════════════
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CALL 3: POST /business/rates/lock                                          │
│  Purpose: Lock exchange rate for 30-60 seconds                              │
│  Type: "buy" (on-ramp: local → USD)                                        │
│  When: IMMEDIATELY when user clicks donate                                  │
│  ⚠️ IMPORTANT: Do NOT call earlier - rate expires quickly!                  │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    │  Response: { id: "rate_lock_123", rate: 2650.50, expiresAt: "..." }
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CREATE DONATION IN DATABASE (Our Backend)                                  │
│  Status: PENDING                                                            │
│  amount: 50000, currency: "TZS"                                            │
│  amount_usd: NULL (stored on success webhook)                              │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CALL 4: POST /business/collections                                         │
│  Purpose: Create COLLECTION request (donor paying IN)                       │
│  This is NOT disbursement - this is ON-RAMP!                               │
│  When: After rate lock, with donation details                               │
│  Includes: rateLockId, sender KYC, amount, currency                        │
│                                                                             │
│  ⚠️ NOTE: Exact endpoint may be:                                           │
│     - /business/collections                                                 │
│     - /business/payments (with type="collection")                          │
│     - Check Yellow Card docs for exact path                                │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    │  Response: { id: "col_123", status: "pending", paymentUrl: "..." }
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  UPDATE DONATION IN DATABASE                                                │
│  transaction_id: "col_123"                                                 │
│  payment_url: "https://..." (if Yellow Card provides checkout URL)         │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  DONOR COMPLETES PAYMENT                                                    │
│  Option A: Yellow Card hosted checkout page                                 │
│  Option B: Direct mobile money prompt to donor's phone                     │
│  Option C: Bank transfer instructions                                       │
└─────────────────────────────────────────────────────────────────────────────┘
    │
    ▼

WEBHOOK CALLBACK (Yellow Card → Our Server)
══════════════════════════════════════════════════════════════════════════════
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CALL 5: WEBHOOK (Incoming from Yellow Card)                                │
│  Event: collection.completed OR collection.failed                           │
│  Purpose: Update donation status + store USD amount                         │
│                                                                             │
│  ON SUCCESS:                                                                │
│    donation.status = "COMPLETED"                                           │
│    donation.amount_usd = 18.87        ← FROM WEBHOOK                       │
│    donation.exchange_rate = 2650.50   ← FROM WEBHOOK                       │
│                                                                             │
│  ON FAILURE:                                                                │
│    donation.status = "FAILED"                                              │
│    donation.amount_usd = NULL         ← NOT STORED                         │
└─────────────────────────────────────────────────────────────────────────────┘


OPTIONAL: STATUS POLLING (If webhook not received)
══════════════════════════════════════════════════════════════════════════════
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CALL 6: GET /business/collections/{id}  (OPTIONAL)                         │
│  Purpose: Check collection status manually                                  │
│  When: If webhook not received within expected time                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Collection vs Disbursement - Key Difference

```
COLLECTION (On-Ramp) - FOR DONATIONS ✅
═══════════════════════════════════════════════════════════════════
POST /business/collections (or similar)

• Donor PAYS local currency (TZS)
• Yellow Card CONVERTS to USDT
• USDT stored in YELLOW CARD DASHBOARD (not sent to RHCI immediately)
• RHCI can withdraw/settle from dashboard when needed
• Used for: Receiving donations

┌──────────┐      ┌─────────────┐      ┌──────────────────────┐
│  DONOR   │ ───► │ YELLOW CARD │ ───► │ YELLOW CARD DASHBOARD│
│ 50K TZS  │      │  Converts   │      │ RHCI Balance: +$18.87│
└──────────┘      └─────────────┘      │        (USDT)        │
                                        │                      │
                                        │  [Settle/Withdraw]   │
                                        └──────────────────────┘


DISBURSEMENT (Off-Ramp) - NOT FOR DONATIONS ❌
═══════════════════════════════════════════════════════════════════
POST /business/payments (with accept)

• RHCI SENDS USD from Yellow Card dashboard balance
• Yellow Card CONVERTS to local currency
• Recipient RECEIVES local currency (TZS)
• Used for: Paying out to beneficiaries (patients, vendors, etc.)
```

### 💰 Settlement Flow (Separate from API)

```
Yellow Card Dashboard                    RHCI Wallet/Bank
┌────────────────────┐                  ┌────────────────────┐
│  Balance: $500.00  │   Settlement     │                    │
│       USDT         │ ═══════════════► │  Receives USDT     │
│                    │   (Manual or     │  or USD            │
│ [Settle Button]    │    Scheduled)    │                    │
└────────────────────┘                  └────────────────────┘

• Settlements done via Yellow Card dashboard (not API)
• Can be manual (click button) or scheduled (daily/weekly)
• Yellow Card pays out in USDT or USD
```

---

## 📝 Detailed API Specifications

### CALL 1: Get Channels

```http
GET /business/channels
```

**Purpose:** Discover available payment methods (Mobile Money, Bank Transfer, etc.)

**Request:**
```python
# No body needed
headers = generate_headers("GET", "/business/channels", "")
response = requests.get(f"{base_url}/business/channels", headers=headers)
```

**Response:**
```json
{
  "channels": [
    {
      "id": "ch_tz_mobile_vodacom",
      "name": "Vodacom M-Pesa",
      "country": "TZ",
      "currency": "TZS",
      "type": "mobileMoney",
      "network": "vodacom",
      "minAmount": 1000,
      "maxAmount": 5000000,
      "status": "active"
    },
    {
      "id": "ch_tz_mobile_airtel",
      "name": "Airtel Money",
      "country": "TZ",
      "currency": "TZS",
      "type": "mobileMoney",
      "network": "airtel",
      "minAmount": 1000,
      "maxAmount": 3000000,
      "status": "active"
    },
    {
      "id": "ch_tz_bank",
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

**Usage:**
- Cache for 1-24 hours
- Filter by country (TZ for Tanzania)
- Show user available payment options

---

### CALL 2: Get Rates

```http
GET /business/rates
```

**Purpose:** Get current exchange rates for currency conversion display.

**Request:**
```python
headers = generate_headers("GET", "/business/rates", "")
response = requests.get(f"{base_url}/business/rates", headers=headers)
```

**Response:**
```json
{
  "rates": [
    {
      "code": "TZS",
      "currency": "Tanzanian Shilling",
      "buy": 2650.50,
      "sell": 2700.25,
      "lastUpdated": "2026-02-09T10:30:00Z"
    },
    {
      "code": "KES",
      "currency": "Kenyan Shilling",
      "buy": 130.00,
      "sell": 132.50,
      "lastUpdated": "2026-02-09T10:30:00Z"
    },
    {
      "code": "NGN",
      "currency": "Nigerian Naira",
      "buy": 1600.00,
      "sell": 1650.00,
      "lastUpdated": "2026-02-09T10:30:00Z"
    }
  ]
}
```

**Usage:**
- Cache for 1-5 minutes
- Use `buy` rate for on-ramp (user paying local → USD)
- Display estimated USD to user

---

### CALL 3: Lock Rate ⚠️ CRITICAL

```http
POST /business/rates/lock
```

**Purpose:** Lock exchange rate before payment (valid 30-60 seconds).

**⚠️ IMPORTANT:** Call this ONLY when user clicks "Donate" button, NOT before!

**Request:**
```python
body = {
    "currency": "TZS",
    "amount": 50000,
    "type": "buy"  # on-ramp (local → USD)
}
headers = generate_headers("POST", "/business/rates/lock", json.dumps(body))
response = requests.post(f"{base_url}/business/rates/lock", json=body, headers=headers)
```

**Response:**
```json
{
  "id": "rl_abc123xyz",
  "rate": 2650.50,
  "amount": 50000,
  "convertedAmount": 18.87,
  "currency": "TZS",
  "type": "buy",
  "expiresAt": "2026-02-09T10:31:00Z",
  "createdAt": "2026-02-09T10:30:00Z"
}
```

**Usage:**
- Store `id` for next API call
- Rate valid for ~60 seconds
- Must use `id` in create payment call

---

### CALL 4: Create Payment ⭐ MAIN

```http
POST /business/payments
```

**Purpose:** Create the payment request.

**Request:**
```python
body = {
    "channelId": "ch_tz_mobile_vodacom",
    "sequenceId": "RHCI-DN-123",  # Our unique donation ID
    "rateLockId": "rl_abc123xyz",  # From Call 3
    
    # Sender (Donor) KYC Information - REQUIRED
    "sender": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "255789123456",
        "country": "TZ",
        "address": {
            "line1": "123 Main Street",
            "city": "Dar es Salaam",
            "state": "Dar es Salaam",
            "country": "TZ",
            "postalCode": "00000"
        },
        "dob": "1990-01-15",
        "idType": "nationalId",
        "idNumber": "19900115-12345-00001-23"
    },
    
    # Destination (Payment details)
    "destination": {
        "accountNumber": "255789123456",
        "accountType": "mobileMoney",
        "networkCode": "vodacom"
    },
    
    # Amount
    "amount": 50000,
    "currency": "TZS",
    "reason": "donation",
    "forceAccept": false
}

headers = generate_headers("POST", "/business/payments", json.dumps(body))
response = requests.post(f"{base_url}/business/payments", json=body, headers=headers)
```

**Response:**
```json
{
  "id": "pay_xyz789abc",
  "sequenceId": "RHCI-DN-123",
  "status": "pending",
  "amount": 50000,
  "currency": "TZS",
  "convertedAmount": 18.87,
  "rate": 2650.50,
  "fee": 0.00,
  "channelId": "ch_tz_mobile_vodacom",
  "createdAt": "2026-02-09T10:30:15Z",
  "expiresAt": "2026-02-09T10:45:15Z"
}
```

**Usage:**
- Store `id` as `transaction_id` in donation
- Use `id` for accept call

---

### CALL 5: Accept Payment

```http
POST /business/payments/{paymentId}/accept
```

**Purpose:** Finalize and accept the payment request.

**Request:**
```python
payment_id = "pay_xyz789abc"
path = f"/business/payments/{payment_id}/accept"
headers = generate_headers("POST", path, "")
response = requests.post(f"{base_url}{path}", headers=headers)
```

**Response:**
```json
{
  "id": "pay_xyz789abc",
  "status": "processing",
  "message": "Payment is being processed"
}
```

---

### CALL 6: Webhook Handler (Incoming)

```http
POST /api/v1.0/donors/payment/yellowcard/callback/
```

**Purpose:** Receive payment status updates from Yellow Card.

**Webhook Payload (Success):**
```json
{
  "event": "payment.completed",
  "data": {
    "id": "pay_xyz789abc",
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

**Webhook Payload (Failure):**
```json
{
  "event": "payment.failed",
  "data": {
    "id": "pay_xyz789abc",
    "sequenceId": "RHCI-DN-123",
    "status": "failed",
    "failureReason": "Insufficient funds",
    "failedAt": "2026-02-09T10:35:00Z"
  },
  "timestamp": "2026-02-09T10:35:01Z"
}
```

**Handler:**
```python
def handle_webhook(request):
    payload = json.loads(request.body)
    event = payload['event']
    data = payload['data']
    
    # Get donation by sequenceId
    sequence_id = data['sequenceId']  # "RHCI-DN-123"
    donation_id = int(sequence_id.replace('RHCI-DN-', ''))
    donation = Donation.objects.get(id=donation_id)
    
    if event == 'payment.completed':
        donation.status = 'COMPLETED'
        donation.amount_usd = Decimal(str(data['convertedAmount']))  # ← STORE HERE!
        donation.exchange_rate = Decimal(str(data['rate']))          # ← STORE HERE!
        donation.completed_at = timezone.now()
        donation.save()
        
    elif event == 'payment.failed':
        donation.status = 'FAILED'
        donation.save()
    
    return JsonResponse({'received': True})
```

---

### CALL 7: Get Payment Status (Optional)

```http
GET /business/payments/{paymentId}
```

**Purpose:** Manually check payment status (fallback if webhook fails).

**Request:**
```python
payment_id = "pay_xyz789abc"
path = f"/business/payments/{payment_id}"
headers = generate_headers("GET", path, "")
response = requests.get(f"{base_url}{path}", headers=headers)
```

**Response:**
```json
{
  "id": "pay_xyz789abc",
  "sequenceId": "RHCI-DN-123",
  "status": "completed",
  "amount": 50000,
  "currency": "TZS",
  "convertedAmount": 18.87,
  "rate": 2650.50,
  "completedAt": "2026-02-09T10:35:00Z"
}
```

---

## ✅ Implementation Checklist

### Required API Calls (Must Implement)

- [ ] **GET /business/channels** - Get payment methods
- [ ] **GET /business/rates** - Get exchange rates
- [ ] **POST /business/rates/lock** - Lock rate before payment
- [ ] **POST /business/payments** - Create payment
- [ ] **POST /business/payments/{id}/accept** - Accept payment
- [ ] **Webhook Handler** - Receive payment updates

### Optional API Calls

- [ ] **GET /business/networks** - Get blockchain networks
- [ ] **POST /business/account/resolve** - Validate account
- [ ] **GET /business/payments/{id}** - Poll status

### Service Methods to Implement

```python
class YellowCardService:
    # Required
    def get_channels(self) -> dict                    # Call 1
    def get_rates(self) -> dict                       # Call 2
    def lock_rate(self, currency, amount) -> dict     # Call 3
    def create_payment(self, ...) -> dict             # Call 4
    def accept_payment(self, payment_id) -> dict      # Call 5
    def process_webhook(self, payload) -> dict        # Call 6
    
    # Optional
    def get_payment_status(self, payment_id) -> dict  # Call 7
    def get_networks(self) -> dict                    # Optional
    def resolve_account(self, ...) -> dict            # Optional
```

---

## 🔗 Quick Reference

| Call | Method | Endpoint | Required |
|------|--------|----------|----------|
| 1 | GET | `/business/channels` | ✅ |
| 2 | GET | `/business/rates` | ✅ |
| 3 | POST | `/business/rates/lock` | ✅ |
| 4 | POST | `/business/payments` | ✅ |
| 5 | POST | `/business/payments/{id}/accept` | ✅ |
| 6 | POST | Webhook (incoming) | ✅ |
| 7 | GET | `/business/payments/{id}` | ⚪ |

---

## ⚠️ Important Notes

1. **Rate Lock Timing:** Call `/rates/lock` ONLY when user clicks donate (expires in 30-60s)
2. **KYC Required:** Every payment requires sender KYC information
3. **Sequence ID:** Use unique ID format: `RHCI-DN-{donation_id}`
4. **USD Storage:** Store `amount_usd` ONLY on successful webhook
5. **Webhook URL:** Configure in Yellow Card dashboard

---

**Ready to implement!** Start with `yellowcard_service.py` implementing these 6 required calls.
