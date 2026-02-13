# Yellow Card Collection API - VERIFIED Flow

## ✅ Verified from Official Documentation

Source: https://docs.yellowcard.engineering/docs/making-a-collection

---

## 📡 Collection API Endpoints (CONFIRMED)

| # | Step | API Endpoint | Method | Purpose |
|---|------|--------------|--------|---------|
| 1 | Get Channels | `Get Channels` | GET | Get available payment methods |
| 2 | Get Rates | `Get Rates` | GET | Get exchange rates (local fiat/USD) |
| 3 | Get Networks | `Get Networks` | GET | Get mobile money networks (if Mobile Money selected) |
| 4 | Get Payment Reasons | `Payment Reasons` | GET | Get list of reasons for transaction |
| 5 | Submit Collection | `Submit Collection Request` | POST | Create collection request (returns quote) |
| 6 | Accept Collection | `Accept Collection Request` | POST | Accept/confirm the collection |
| 7 | Webhooks | Webhook (incoming) | POST | Receive payment status updates |
| 8 | Lookup Collection | `Lookup Collection` | GET | Get transaction details |

---

## 🔄 Complete Collection Flow (7 Steps)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    YELLOW CARD COLLECTION FLOW (VERIFIED)                   │
│                         For Receiving Donations                             │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 1: Payment Screen (Show amount & options)
══════════════════════════════════════════════════════════════════════════════
    │
    ├── API: GET /channels         → Get available payment methods
    │                                 Returns: Limits for payment channel
    │
    └── API: GET /rates            → Get exchange rates
                                     Returns: Rate of local fiat/USD
    │
    ▼

STEP 2: Choose Payment Channel
══════════════════════════════════════════════════════════════════════════════
    │
    ├── API: GET /channels         → Get list of payment options
    │                                 (Mobile Money, Bank Transfer, EFT)
    │
    │   IF Mobile Money selected:
    │   └── API: GET /networks     → Get mobile money networks
    │                                 (Vodacom, Airtel, etc.)
    │
    │   Collect from user:
    │   ├── First name
    │   ├── Last name
    │   ├── Mobile number (with country code)
    │   └── Select provider/network
    │
    ▼

STEP 3: Enter Reason for Sending
══════════════════════════════════════════════════════════════════════════════
    │
    └── API: GET /payment-reasons  → Get pre-defined list of reasons
                                     User selects: "donation", etc.
    │
    ▼

STEP 4: Review Payment Details (User Confirms)
══════════════════════════════════════════════════════════════════════════════
    │
    │   Show transaction details:
    │   ├── Payment Option
    │   ├── Payment Channel
    │   ├── Payment Network
    │   ├── Account number
    │   ├── Mobile number
    │   ├── Total amount
    │   └── Rate (if required)
    │
    └── API: POST Submit Collection Request
             → Returns: A QUOTE to make the collection
             → Contains: Collection ID, rate, amounts
    │
    ▼

STEP 5: Initiate Payment (Accept the Quote)
══════════════════════════════════════════════════════════════════════════════
    │
    ├── API: POST Accept Collection Request
    │        → Confirms the collection
    │        → Payment processing starts
    │
    │   OR
    │
    └── API: POST Deny Collection Request
             → Cancels the collection
    │
    ▼

STEP 6: Payment Successful (Webhook)
══════════════════════════════════════════════════════════════════════════════
    │
    └── WEBHOOK: Yellow Card sends notification
                 → Event: collection completed/failed
                 → Contains: status, amounts, USD conversion
    │
    │   ON SUCCESS:
    │   └── Store amount_usd in database
    │
    ▼

STEP 7: Retrieve Information (Optional)
══════════════════════════════════════════════════════════════════════════════
    │
    └── API: GET Lookup Collection
             → Get full transaction details
             → Use for verification or status polling
```

---

## 📋 API Calls Summary (For RHCI Implementation)

### Required Calls

| # | API | When | Purpose |
|---|-----|------|---------|
| 1 | **Get Channels** | App init | Get Mobile Money, Bank options |
| 2 | **Get Rates** | Before form | Get TZS/USD rate |
| 3 | **Get Networks** | If Mobile Money | Get Vodacom, Airtel, etc. |
| 4 | **Payment Reasons** | Before submit | Get "donation" reason ID |
| 5 | **Submit Collection Request** | User confirms | Create collection (get quote) |
| 6 | **Accept Collection Request** | After quote | Confirm & initiate payment |
| 7 | **Webhook Handler** | Async | Receive success/failure |

### Optional Calls

| # | API | When | Purpose |
|---|-----|------|---------|
| 8 | **Lookup Collection** | If needed | Poll status or verify |
| 9 | **Deny Collection Request** | If user cancels | Cancel before accept |

---

## 🔑 Key Differences from Our Previous Assumptions

| Aspect | Our Assumption | Actual (Verified) |
|--------|----------------|-------------------|
| Rate Lock | Separate `/rates/lock` endpoint | Part of `Submit Collection Request` |
| Create + Accept | Single call | **Two calls**: Submit (quote) → Accept (confirm) |
| Networks | Part of channels | **Separate endpoint**: `Get Networks` |
| Payment Reasons | Not required | **Required**: Must provide reason |

---

## 📝 Data to Collect from User (For Mobile Money)

```
Required Fields:
├── First name
├── Last name
├── Mobile number
├── Country code (e.g., +255 for Tanzania)
├── Provider/Network (from Get Networks)
├── Payment reason (from Payment Reasons)
└── Amount
```

---

## 🏗️ Service Methods to Implement

```python
class YellowCardService:
    # Step 1: Initialization
    def get_channels(self) -> dict
    def get_rates(self) -> dict
    def get_networks(self) -> dict
    def get_payment_reasons(self) -> dict
    
    # Step 2: Create Collection
    def submit_collection_request(
        self,
        channel_id: str,
        network: str,
        amount: Decimal,
        currency: str,
        sender: dict,        # name, phone, etc.
        reason: str,
        sequence_id: str     # our donation ID
    ) -> dict  # Returns quote
    
    # Step 3: Confirm Collection
    def accept_collection_request(self, collection_id: str) -> dict
    def deny_collection_request(self, collection_id: str) -> dict
    
    # Step 4: Status
    def lookup_collection(self, collection_id: str) -> dict
    def process_webhook(self, payload: dict) -> dict
```

---

## ✅ Verified API Flow for RHCI Donations

```
1. GET Channels        → Show payment options (Mobile Money, Bank)
2. GET Rates           → Show "50,000 TZS ≈ $18.87 USD"
3. GET Networks        → Show Vodacom, Airtel, Tigo options
4. GET Payment Reasons → Get "donation" reason ID
5. POST Submit Collection → Create quote (lock rate)
6. POST Accept Collection → Confirm payment
7. WEBHOOK             → Receive success, store amount_usd
```

---

## ⏭️ Next Steps

1. ✅ Collection flow verified
2. ⏳ Need to verify exact endpoint URLs (e.g., `/business/channels` or `/channels`)
3. ⏳ Need to verify authentication headers
4. ⏳ Need to verify request/response body formats
5. ⏳ Implement `yellowcard_service.py`

---

**Documentation Source:** https://docs.yellowcard.engineering/docs/making-a-collection
