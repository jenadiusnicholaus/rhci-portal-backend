# Yellow Card API - Verification Checklist

## ⚠️ IMPORTANT: Verify Before Implementation

The Yellow Card documentation website (docs.yellowcard.engineering) is not accessible via automated tools. **You need to manually verify the following from the actual documentation before we implement.**

---

## ✅ What We Know (Confirmed)

| Item | Status | Source |
|------|--------|--------|
| Base URL (Sandbox) | `https://sandbox.api.yellowcard.io/business` | Yellow Card website |
| Base URL (Production) | `https://api.yellowcard.io/business` | Yellow Card website |
| API provides channels endpoint | `/business/channels` | Yellow Card widget docs |
| Supports Collection (On-Ramp) | Yes - receive local currency | FAQ |
| Supports Disbursement (Off-Ramp) | Yes - send local currency | FAQ |
| Settlement in USDT/USDC | Yes - stored in dashboard | FAQ |
| Supports 20+ African countries | Yes - including Tanzania | Website |
| Payment methods | Mobile Money, Bank Transfers | FAQ |
| Webhooks available | Yes - for real-time updates | Website |
| Code examples available | cURL, Python, Node, Ruby | Website |

---

## ❓ What Needs Verification (Check Yellow Card Docs)

### 1. Authentication Headers

**Please verify the exact authentication format:**

```
Questions:
- What headers are required? (X-YC-Timestamp? Authorization?)
- What is the signature algorithm? (HMAC-SHA256?)
- What is the signature message format?
- Example: timestamp + method + path + body ?
```

**Our assumption:**
```
X-YC-Timestamp: {unix_timestamp}
Authorization: YcHmacV1 {api_key}:{base64_hmac_signature}
Content-Type: application/json
```

### 2. Collection Endpoint (For Receiving Donations)

**Please verify the exact endpoint for COLLECTION (on-ramp):**

```
Questions:
- Is it POST /business/collections ?
- Or POST /business/payments with type="collection" ?
- Or something else entirely?
- What fields are required in the request body?
- Is there a separate "accept" step for collections?
```

**Our assumption:**
```
POST /business/collections
Body: {
  channelId, sequenceId, sender, amount, currency, rateLockId, ...
}
```

### 3. Rate Lock Endpoint

**Please verify:**

```
Questions:
- Endpoint: POST /business/rates/lock ?
- What is the request body format?
- How long is the rate valid? (30 seconds? 60 seconds?)
- What is returned? (id, rate, expiresAt?)
```

### 4. Get Channels Endpoint

**Please verify:**

```
Questions:
- Endpoint: GET /business/channels ?
- Are there query parameters for filtering? (country? type?)
- Does it distinguish between collection and disbursement channels?
```

### 5. Get Rates Endpoint

**Please verify:**

```
Questions:
- Endpoint: GET /business/rates ?
- What is the response format?
- Is there a "buy" vs "sell" rate?
```

### 6. Webhook Format

**Please verify:**

```
Questions:
- What events are sent? (collection.completed? payment.completed?)
- What is the payload format?
- Is there signature verification for webhooks?
- How to configure webhook URL?
```

### 7. Sender KYC Requirements

**Please verify:**

```
Questions:
- What sender fields are required?
- Is full KYC required for every transaction?
- Format: name, email, phone, address, dob, idType, idNumber?
```

---

## 📋 Verification Template

When you check the docs, please fill in:

```
AUTHENTICATION:
- Header 1: ________________
- Header 2: ________________
- Signature format: ________________

COLLECTION ENDPOINT:
- Method: ________________
- Path: ________________
- Required fields: ________________

RATE LOCK:
- Path: ________________
- Validity: ________________ seconds

CHANNELS:
- Path: ________________
- Filter params: ________________

RATES:
- Path: ________________
- Buy/Sell field names: ________________

WEBHOOKS:
- Collection event name: ________________
- Payload includes: ________________
```

---

## 🔗 Documentation Links to Check

1. **Main Docs:** https://docs.yellowcard.engineering/
2. **API Reference:** https://docs.yellowcard.engineering/reference/
3. **Authentication:** https://docs.yellowcard.engineering/docs/authentication-api
4. **Get Channels:** https://docs.yellowcard.engineering/reference/get-channels
5. **Get Rates:** https://docs.yellowcard.engineering/reference/get-rates

---

## ⏭️ Next Steps

1. **You:** Open Yellow Card docs in browser and verify the above
2. **You:** Fill in the verification template above
3. **We:** Update documentation with correct endpoints
4. **We:** Implement yellowcard_service.py with verified endpoints

---

## 💡 Alternative: Contact Yellow Card Support

If documentation is unclear, contact Yellow Card:
- Book a demo: https://yellowcard.io/api/
- Help center: https://help.yellowcard.io/
- They can provide exact API specifications

---

**DO NOT implement until these endpoints are verified from official docs!**
