# AzamPay Bill Pay API Integration Guide

## Overview

This document explains the AzamPay **Bill Pay API** - an alternative payment method that allows donors to pay directly from their mobile money apps or USSD without visiting your website.

---

## What is Bill Pay API?

### Current Setup (Checkout API)
- **You** initiate payment from your website
- Donor provides phone number on your platform
- AzamPay sends push notification to donor's phone
- Donor approves payment on mobile device
- **Flow: Website → AzamPay → Donor**

### Bill Pay API (New Method)
- **Donor** initiates payment from their mobile money app or USSD
- Donor selects RHCI as the biller
- Donor enters Patient ID (Bill Identifier)
- Payment comes directly to your system
- **Flow: Donor → AzamPay → Your Server**

---

## Why Bill Pay API is Perfect for RHCI Donations

### 🇹🇿 Tanzania Context

**USSD is King in Tanzania:**
- Most Tanzanians use `*150*00#` daily for payments
- Works on basic phones (no smartphone needed)
- No internet connection required
- Already familiar interface (same as paying electricity/water bills)

**Mobile Money Penetration:**
- 70%+ of Tanzanians use mobile money
- M-Pesa, Airtel Money, Tigo Pesa widely used
- People trust bill payment channels
- Faster than bank transfers

---

## Key Advantages

### ✅ **1. Donors Don't Need Your Website**
```
Traditional: Donor → Google → Your Website → Donation Form → Payment
Bill Pay:   Donor → M-Pesa App → RHCI → Patient ID → Done ✨
```

### ✅ **2. Offline Fundraising Campaigns**

**Print Patient Cards:**
```
┌──────────────────────────────────┐
│  🏥 HELP JIMMY JACOB             │
│  Age: 5 | Condition: Heart       │
│  Surgery Cost: TSh 1,000,000     │
│                                  │
│  📱 DONATE VIA MOBILE MONEY:     │
│  ─────────────────────────────   │
│  M-Pesa: *150*00# → RHCI         │
│  Patient ID: 12                  │
│                                  │
│  🌐 Online: rhci.org/patient/12  │
└──────────────────────────────────┘
```

**At Events/Churches:**
- Display patient ID on screens
- Attendees donate immediately via USSD
- No website navigation needed
- Real-time fundraising updates

### ✅ **3. Viral Social Media Campaigns**

**Facebook/Instagram Posts:**
```
🆘 URGENT: 5-year-old needs life-saving surgery

💰 Help us raise TSh 1,000,000
📱 Donate in 30 seconds via M-Pesa:
   
   *150*00# → Select RHCI → Enter: 12
   
✅ 100% goes directly to treatment
🙏 Share this post to save a life
🏥 Patient: Jimmy Jacob

#SaveJimmy #RHCI #Donation
```

**WhatsApp Sharing:**
```
🏥 *Jimmy Jacob needs your help*

Quick donate via M-Pesa:
*150*00# → RHCI → ID: 12

Any amount helps! 🙏
Share with your contacts ➡️
```

**Twitter/X Campaign:**
```
🚨 Help save Jimmy Jacob!
📱 *150*00# → RHCI → 12
💵 TSh 100+ helps
RT to spread ↻
```

### ✅ **4. Recurring Donors**
Once a donor pays via Bill Pay:
- Biller code is saved in their M-Pesa favorites
- Can donate again: `*150*00# → RHCI → 12` (2 taps!)
- No need to remember website URL
- Instant donation anytime

### ✅ **5. Trust & Security**
- Payment through official M-Pesa/Airtel channels
- Donor sees verified "RHCI" name in app
- Same secure system as utility bills
- Government-regulated payment rails

### ✅ **6. Maximum Reach**
**Online Donors:**
- Use website (Checkout API)
- See patient photos/story
- Interactive experience

**Offline Donors:**
- Use USSD/Mobile App (Bill Pay API)
- Quick and convenient
- No internet needed

---

## How It Works

### 🔄 Flow Overview

```
1. Donor opens M-Pesa/Airtel/Bank app
2. Donor selects "Pay Bills" option
3. Donor selects your organization (RHCI) from list
4. Donor enters BillIdentifier (e.g., patient ID "12")
5. Your Name Lookup API receives request
   → You return patient name and donation amount
6. Donor confirms payment
7. Your Payment API receives payment confirmation
   → You mark donation as completed
8. Donor receives payment receipt
```

### Step-by-Step Example

**Donor's Perspective:**
1. Opens M-Pesa app
2. Taps "Pay Bills"
3. Selects "RHCI" from biller list
4. Enters Patient ID: **12**
5. Sees: "Donate to **Jimmy Jacob** - TSh 1,000,000 needed"
6. Enters donation amount: **50,000**
7. Enters M-Pesa PIN
8. Receives: "Thank you! TSh 50,000 donated to Jimmy Jacob"

**Your System's Role:**
- **Step 5:** Name Lookup API returns patient details
- **Step 7:** Payment API records donation and updates funding
- **Step 8:** System can send additional email receipt/thank you

---

## Technical Implementation

### Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Donor     │         │   AzamPay    │         │  Your API   │
│  (M-Pesa)   │────────▶│  (Gateway)   │────────▶│  (Django)   │
└─────────────┘         └──────────────┘         └─────────────┘
     │                         │                         │
     │ 1. Enter Patient ID     │                         │
     │────────────────────────▶│                         │
     │                         │ 2. Name Lookup          │
     │                         │────────────────────────▶│
     │                         │ 3. Return Patient Info  │
     │                         │◀────────────────────────│
     │ 4. Show Patient Name    │                         │
     │◀────────────────────────│                         │
     │ 5. Enter Amount & PIN   │                         │
     │────────────────────────▶│                         │
     │                         │ 6. Process Payment      │
     │                         │────────────────────────▶│
     │                         │ 7. Confirm Receipt      │
     │                         │◀────────────────────────│
     │ 8. Payment Successful   │                         │
     │◀────────────────────────│                         │
```

### Required Endpoints (You Must Provide)

#### 1. Name Lookup API

**Endpoint:** `POST /api/merchant/name-lookup`  
**Called by:** AzamPay when donor enters Patient ID

**Request from AzamPay:**
```json
{
  "Data": {
    "BillIdentifier": "12",
    "Currency": "TZS",
    "Language": "en",
    "Country": "Tanzania",
    "TimeStamp": "2026-01-02T10:20:30Z",
    "BillType": "Donation",
    "AdditionalProperties": {}
  },
  "Hash": "711bd3c3e54488523683182aa01c8a83544e45b7ba2c45652e039bf830e5daf2"
}
```

**Your Response:**
```json
{
  "Name": "Jimmy Jacob",
  "BillAmount": 1000000,
  "BillIdentifier": "12",
  "Status": "Success",
  "Message": "Patient found. Donation for heart surgery.",
  "StatusCode": 0
}
```

#### 2. Payment API

**Endpoint:** `POST /api/merchant/payment`  
**Called by:** AzamPay when donor completes payment

**Request from AzamPay:**
```json
{
  "Data": {
    "FspReferenceId": "MPE20260102123456",
    "PgReferenceId": "AZM20260102789012",
    "Amount": 50000,
    "BillIdentifier": "12",
    "PaymentDesc": "Donation to Jimmy Jacob",
    "FspCode": "Mpesa",
    "Country": "Tanzania",
    "TimeStamp": "2026-01-02T10:25:30Z",
    "BillType": "Donation",
    "AdditionalProperties": {
      "DonorPhone": "255789123456",
      "DonorName": "John Doe"
    }
  },
  "Hash": "ca3f49b2ee7740bf68062445ee7027d33baa4dbb0e456cdc7534ddd34bf19fb1"
}
```

**Your Response:**
```json
{
  "MerchantReferenceId": "RHCI-DN-125",
  "Status": "Success",
  "StatusCode": 0,
  "Message": "Thank you! TSh 50,000 donation received for Jimmy Jacob."
}
```

**What Your System Does:**
1. Verify JWT token and hash signature
2. Find patient with ID 12
3. Create donation record
4. Update patient funding: `funding_received += 50000`
5. Calculate new percentage: `(50000 / 1000000) * 100 = 5%`
6. Return confirmation with donation reference

#### 3. Status Check API

**Endpoint:** `POST /api/merchant/status-check`  
**Called by:** Donor or AzamPay to verify payment

**Request:**
```json
{
  "MerchantReferenceId": "RHCI-DN-125"
}
```

**Your Response:**
```json
{
  "MerchantReferenceId": "RHCI-DN-125",
  "Status": "Success",
  "StatusCode": 0,
  "Message": "Payment successful. TSh 50,000 donated to Jimmy Jacob."
}
```

---

## Security Implementation

### 1. JWT Token Authentication

**Every request includes JWT in Authorization header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token contains:**
- `userId`: Your merchant ID
- `exp`: Expiration time (120 seconds validity)
- `iat`: Issued at time

**You must verify:**
```python
import jwt
from django.conf import settings

def verify_jwt_token(token):
    try:
        payload = jwt.decode(
            token, 
            settings.AZAMPAY_BILLPAY_SECRET,
            algorithms=['HS256']
        )
        
        # Check expiration
        if payload['exp'] < time.time():
            return False, "Token expired"
            
        return True, payload
        
    except jwt.InvalidTokenError as e:
        return False, str(e)
```

### 2. HMAC-SHA256 Hash Verification

**Every request includes Hash field calculated by AzamPay:**

**Verification Steps:**
```python
import hashlib
import hmac
import json

def verify_request_hash(data_dict, received_hash):
    # 1. Convert data to minified JSON (no spaces)
    json_string = json.dumps(data_dict, separators=(',', ':'))
    
    # 2. Calculate SHA256 hash
    sha256_hash = hashlib.sha256(json_string.encode()).hexdigest()
    
    # 3. Sign with HMAC using shared secret
    signature = hmac.new(
        settings.AZAMPAY_BILLPAY_SECRET.encode(),
        sha256_hash.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # 4. Compare with received hash
    return hmac.compare_digest(signature, received_hash)
```

**Example:**
```python
# Data received
data = {
    "BillIdentifier": "12",
    "Currency": "TZS",
    "Language": "en",
    "Country": "Tanzania",
    "TimeStamp": "2026-01-02T10:20:30Z"
}

# JSON: {"BillIdentifier":"12","Currency":"TZS",...}
# SHA256: fe6173685ce463cc966f6fce41fd59a92f181d1d7e63b8a17a3e42e41e381cbd
# HMAC: 711bd3c3e54488523683182aa01c8a83544e45b7ba2c45652e039bf830e5daf2
```

---

## Patient ID as Bill Identifier

### Simple Approach
Use existing Patient ID directly:
- Patient ID `12` → Bill Identifier: `12`
- Patient ID `45` → Bill Identifier: `45`

**Advantages:**
- ✅ No new system needed
- ✅ Easy to remember
- ✅ Already in database
- ✅ Can print on patient cards

### Alternative: Friendly Codes
Generate memorable codes:
- Patient ID `12` → Code: `JIMMY-001`
- Patient ID `45` → Code: `SARAH-045`

**Implementation:**
```python
@property
def bill_identifier(self):
    # Option 1: Simple ID
    return str(self.id)
    
    # Option 2: Friendly code
    first_name = self.full_name.split()[0].upper()
    return f"{first_name}-{self.id:03d}"
```

---

## Marketing & Promotion

### Website Integration

**Patient Detail Page:**
```html
<div class="donation-methods">
  <h3>💳 Choose How to Donate</h3>
  
  <!-- Method 1: Website -->
  <div class="method online">
    <h4>🌐 Donate Online (Instant)</h4>
    <form>
      <input type="number" placeholder="Amount (TSh)">
      <input type="tel" placeholder="Phone Number">
      <button>Donate Now</button>
    </form>
  </div>
  
  <!-- Method 2: USSD/App -->
  <div class="method ussd">
    <h4>📱 Donate via Mobile Money (Anytime)</h4>
    <div class="ussd-instructions">
      <p><strong>M-Pesa / Airtel Money:</strong></p>
      <ol>
        <li>Dial <code>*150*00#</code></li>
        <li>Select "RHCI"</li>
        <li>Enter Patient ID: <strong>12</strong></li>
        <li>Enter amount and PIN</li>
      </ol>
      
      <div class="share-code">
        <p>📤 Share this code:</p>
        <code class="patient-code">RHCI → 12</code>
        <button onclick="copyCode()">Copy</button>
        <button onclick="shareWhatsApp()">Share WhatsApp</button>
      </div>
    </div>
  </div>
</div>
```

### Social Media Templates

**Template 1: Urgent Case**
```
🆘 URGENT: [Patient Name] needs life-saving surgery

💰 Goal: TSh [Amount]
⏰ Raised: TSh [Current] ([Percentage]%)
📅 Surgery Date: [Date]

📱 DONATE NOW via M-Pesa:
   *150*00# → RHCI → ID: [PatientID]

✅ 100% goes to medical treatment
🏥 RHCI - Registered Charity #[Number]
🙏 Every donation counts

➡️ Share to save a life

#[PatientName] #RHCI #Tanzania #Donation
```

**Template 2: Success Story**
```
✨ UPDATE: We raised TSh [Amount] for [Patient]!

Thanks to [Number] generous donors who donated via:
📱 M-Pesa: *150*00# → RHCI → [ID]
🌐 Online: rhci.org/patient/[ID]

👨‍⚕️ Surgery scheduled for [Date]
📸 Updates coming soon

🙏 Still need help? Share this post!
```

### Printable Materials

**Flyer Template:**
```
┌─────────────────────────────────────────┐
│     🏥 RHCI - Raising Hope Care Int'l   │
├─────────────────────────────────────────┤
│                                         │
│  📸 [Patient Photo]                     │
│                                         │
│  HELP [PATIENT NAME]                    │
│  Age: [Age] | Condition: [Condition]    │
│                                         │
│  💰 FUNDING GOAL                        │
│  ─────────────────────────              │
│  Needed:    TSh [Required]              │
│  Raised:    TSh [Received]              │
│  Remaining: TSh [Remaining]             │
│                                         │
│  📱 DONATE VIA MOBILE MONEY             │
│  ─────────────────────────              │
│  1. Dial *150*00#                       │
│  2. Select "RHCI"                       │
│  3. Enter Patient ID: [ID]              │
│  4. Enter amount & PIN                  │
│                                         │
│  🌐 OR DONATE ONLINE                    │
│  rhci.org/patient/[ID]                  │
│                                         │
│  ✅ 100% goes to medical treatment      │
│  📞 Contact: +255 XXX XXX XXX           │
│  📧 info@rhci.org                       │
└─────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Backend Development (Week 1-2)
- [ ] Create Name Lookup API endpoint
- [ ] Create Payment Processing API endpoint
- [ ] Create Status Check API endpoint
- [ ] Implement JWT token verification
- [ ] Implement HMAC hash verification
- [ ] Add comprehensive logging
- [ ] Write unit tests
- [ ] Test with AzamPay sandbox

### Phase 2: Integration Testing (Week 3)
- [ ] Get shared secret from AzamPay
- [ ] Configure JWT validation
- [ ] Test Name Lookup flow
- [ ] Test Payment flow
- [ ] Test Status Check flow
- [ ] Handle error scenarios
- [ ] Performance testing
- [ ] Security audit

### Phase 3: Frontend Updates (Week 4)
- [ ] Add "Donate via Mobile Money" section
- [ ] Create patient donation cards
- [ ] Add share buttons (WhatsApp, Twitter, Facebook)
- [ ] Show patient Bill Identifier prominently
- [ ] Create printable flyer generator
- [ ] Mobile-responsive design

### Phase 4: Marketing Materials (Week 5)
- [ ] Design social media templates
- [ ] Create patient card designs
- [ ] Prepare event materials
- [ ] Write donor instructions
- [ ] Train staff on new system
- [ ] Create FAQ document

### Phase 5: Launch (Week 6)
- [ ] Submit to AzamPay for approval
- [ ] Get added to biller list
- [ ] Test with real payments
- [ ] Monitor first donations
- [ ] Gather feedback
- [ ] Iterate improvements

---

## Best Practices

### For Donors
**Clear Instructions:**
- Use simple language
- Step-by-step guides
- Visual aids (screenshots)
- Multiple language support (Swahili/English)

**Example Good Instructions:**
```
📱 How to donate via M-Pesa:

1️⃣ Dial *150*00# on your phone
2️⃣ Select "Lipa Kwa Bili" (Pay Bill)
3️⃣ Choose "RHCI"
4️⃣ Enter patient code: 12
5️⃣ You'll see: "Donate to Jimmy Jacob"
6️⃣ Enter donation amount
7️⃣ Enter your M-Pesa PIN
8️⃣ Done! You'll receive confirmation

💡 Minimum: TSh 1,000
✅ Instant receipt
🙏 100% goes to treatment
```

### For Patients
**Easy-to-Share Codes:**
- Make codes memorable
- Provide multiple formats
- Create shareable graphics
- Print on materials

### For Staff
**Monitoring Dashboard:**
- Real-time donation tracking
- Alert on large donations
- Donor contact information
- Payment verification tools

---

## Comparison: Checkout API vs Bill Pay API

| Feature | Checkout API | Bill Pay API |
|---------|-------------|--------------|
| **Initiation** | Website (you) | Donor |
| **Platform** | Web only | USSD/App/Web |
| **Internet Required** | Yes | No |
| **Phone Needed** | Smartphone preferred | Any phone |
| **User Experience** | Rich (photos, stories) | Quick & simple |
| **Sharing** | Share URL | Share Patient ID |
| **Recurring** | Need to visit site | Saved in favorites |
| **Offline Fundraising** | ❌ Limited | ✅ Excellent |
| **Social Viral Potential** | ⚠️ Medium | ✅ High |
| **Setup Complexity** | ⚠️ Medium | ⚠️ High |
| **Security** | Bearer Token | JWT + HMAC |
| **Best For** | First-time web donors | Repeat & offline donors |

---

## Recommendation: Use BOTH! 🎯

**Implement Dual Payment Strategy:**

### Website Donations (Checkout API)
✅ Keep current implementation  
✅ Best for first-time donors  
✅ Rich storytelling experience  
✅ Immediate website feedback  

### Mobile Money Donations (Bill Pay API)
✅ Add new implementation  
✅ Best for sharing & recurring  
✅ Offline fundraising  
✅ Viral social campaigns  

**Result:** Maximum donation reach across all channels!

---

## Technical Requirements

### Environment Variables
```bash
# .env
AZAMPAY_BILLPAY_SECRET=your_shared_secret_key
AZAMPAY_BILLPAY_TOKEN_EXPIRY=120  # seconds
AZAMPAY_BILLPAY_ENABLED=True
```

### Dependencies
```txt
PyJWT==2.8.0  # JWT token validation
cryptography==41.0.7  # Hash verification
```

### Settings Configuration
```python
# settings.py

AZAMPAY_BILLPAY_CONFIG = {
    'SECRET': env('AZAMPAY_BILLPAY_SECRET'),
    'TOKEN_EXPIRY': 120,
    'HASH_ALGORITHM': 'HS256',
    'ENABLED': env.bool('AZAMPAY_BILLPAY_ENABLED', False),
}
```

---

## Support & Resources

### AzamPay Documentation
- API Docs: https://developerdocs.azampay.co.tz/redoc#tag/Bill-Pay-API
- Support Email: support@azampay.com
- Developer Portal: https://developers.azampay.co.tz/

### RHCI Implementation
- Backend Endpoints: `/api/v1/billpay/`
- Admin Dashboard: `/admin/billpay/`
- Testing Guide: See `TESTING_BILLPAY.md`
- API Documentation: See `API_BILLPAY.md`

---

## FAQ

**Q: Can donors use any mobile money provider?**  
A: Yes - M-Pesa, Airtel Money, Tigo Pesa, Halopesa all work.

**Q: Is there a minimum donation amount?**  
A: Typically TSh 1,000 minimum (set by mobile money providers).

**Q: How fast is payment processing?**  
A: Instant - donation recorded within seconds.

**Q: Can donors get receipts?**  
A: Yes - SMS receipt sent immediately + email receipt from your system.

**Q: What if payment fails?**  
A: Donor's money is returned automatically by mobile money provider.

**Q: Can we track which channel donations came from?**  
A: Yes - we log whether donation was via Checkout API or Bill Pay API.

**Q: Can patients have multiple active fundraising campaigns?**  
A: Yes - each patient has one Bill Identifier but can have multiple donation records.

---

## Next Steps

1. **Contact AzamPay:**
   - Request Bill Pay API access
   - Get shared secret key
   - Request to be added to biller list

2. **Development:**
   - Implement 3 secure endpoints
   - Add JWT + HMAC verification
   - Test in sandbox environment

3. **Launch:**
   - Go live with production
   - Train staff on new system
   - Start marketing campaigns

4. **Monitor:**
   - Track donation sources
   - Gather donor feedback
   - Optimize user experience

---

**Ready to 10x your donation reach in Tanzania? Let's implement Bill Pay API! 🚀**
