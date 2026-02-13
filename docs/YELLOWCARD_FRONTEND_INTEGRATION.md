# Yellow Card Payment Integration - Frontend Guide

## Overview

Yellow Card enables **Mobile Money** and **Bank Transfer** donations across Africa. This guide explains how to integrate Yellow Card payments in the frontend.

---

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1.0/donors/yellowcard/countries/` | GET | No | **Get all supported countries** |
| `/api/v1.0/donors/yellowcard/channels/` | GET | No | Get available payment channels |
| `/api/v1.0/donors/yellowcard/networks/` | GET | No | Get networks for a channel |
| `/api/v1.0/donors/yellowcard/donate/anonymous/` | POST | No | Anonymous donation |
| `/api/v1.0/donors/yellowcard/donate/` | POST | JWT | Authenticated donation |
| `/api/v1.0/donors/yellowcard/status/` | GET | No | Check payment status |

---

## Step-by-Step Integration

### Step 0: Get Supported Countries (First!)

**Always call this first** to get the list of countries that support Yellow Card payments.

```javascript
// GET /api/v1.0/donors/yellowcard/countries/
const response = await fetch(`${API_URL}/donors/yellowcard/countries/`);
const data = await response.json();
```

**Response:**
```json
{
  "success": true,
  "countries": [
    {
      "code": "TZ",
      "name": "Tanzania",
      "currency": "TZS",
      "momo": true,
      "bank": true,
      "has_rate": true
    },
    {
      "code": "UG",
      "name": "Uganda",
      "currency": "UGX",
      "momo": true,
      "bank": true,
      "has_rate": true
    },
    {
      "code": "RW",
      "name": "Rwanda",
      "currency": "RWF",
      "momo": true,
      "bank": true,
      "has_rate": true
    },
    {
      "code": "CM",
      "name": "Cameroon",
      "currency": "XAF",
      "momo": false,
      "bank": true,
      "has_rate": true
    }
  ],
  "all_countries": [...],  // All countries (some may not have rates in sandbox)
  "count": 6,
  "total_count": 20
}
```

**Frontend Usage:**
```javascript
// Filter countries for dropdown
const countryDropdown = data.countries.map(c => ({
  value: c.code,
  label: c.name,
  currency: c.currency,
  hasMomo: c.momo,
  hasBank: c.bank
}));

// Show in country selector
<select>
  {countryDropdown.map(country => (
    <option key={country.value} value={country.value}>
      {country.label} ({country.currency})
    </option>
  ))}
</select>
```

**Important:**
- `countries` array: Only countries with active channels AND buy rates (fully supported)
- `all_countries` array: All countries (some may not work in sandbox)
- Use `momo` and `bank` flags to show/hide payment method options

---

### Step 1: Get Available Channels

Fetch payment channels for the user's country.

```javascript
// GET /api/v1.0/donors/yellowcard/channels/?country=TZ
const response = await fetch(`${API_URL}/donors/yellowcard/channels/?country=TZ`);
const data = await response.json();
```

**Response:**
```json
{
  "success": true,
  "channels": [
    {
      "id": "fc7a5bc2-9100-473e-8c01-df563494ee73",
      "channelType": "bank",
      "name": "Bank Transfer",
      "min": 2500,
      "currency": "TZS",
      "status": "active"
    },
    {
      "id": "656d4e72-7849-4fd6-b0a0-8631c8adf704",
      "channelType": "momo",
      "name": "Mobile Money",
      "min": 2500,
      "currency": "TZS",
      "status": "active"
    }
  ]
}
```

**Display to User:**
- 📱 Mobile Money
- 🏦 Bank Transfer

---

### Step 2: Get Networks for Selected Channel

When user selects a channel, fetch available networks.

```javascript
// GET /api/v1.0/donors/yellowcard/networks/?channel_id=656d4e72-7849-4fd6-b0a0-8631c8adf704
const response = await fetch(`${API_URL}/donors/yellowcard/networks/?channel_id=${channelId}`);
const data = await response.json();
```

**Response (Mobile Money):**
```json
{
  "success": true,
  "networks": [
    {
      "id": "0dae3b0d-4074-406b-aede-790c0be061cc",
      "name": "AIRTELMONEYTZ",
      "code": "AIRTELMONEYTZ",
      "accountNumberType": "phone",
      "status": "active"
    },
    {
      "id": "7692c976-15ee-41fc-a8d2-0d74afc4a16a",
      "name": "Mobile Wallet",
      "code": "Mobile Wallet",
      "accountNumberType": "phone",
      "status": "active"
    }
  ]
}
```

**Display to User:**
- Airtel Money
- Vodacom M-Pesa
- Tigo Pesa
- etc.

---

### Step 3: Submit Donation

#### Mobile Money Donation (Anonymous)

```javascript
// POST /api/v1.0/donors/yellowcard/donate/anonymous/
const response = await fetch(`${API_URL}/donors/yellowcard/donate/anonymous/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    // Patient info (optional - omit for organization-only donation)
    patient_id: 1,
    
    // Amounts
    patient_amount: 45000,        // Amount for patient (required if patient_id provided)
    rhci_support_amount: 5000,    // Amount for RHCI (always optional)
    
    // Currency & Country
    currency: "TZS",
    country: "TZ",
    
    // Sender info
    sender_name: "John Doe",
    sender_email: "john@example.com",
    
    // Mobile Money specific
    account_type: "phone",                    // "phone" for mobile money
    sender_phone: "+255712345678",            // Required for mobile money
    
    // Payment channel (from Step 1 & 2)
    channel_id: "656d4e72-7849-4fd6-b0a0-8631c8adf704",  // Mobile money channel
    network_id: "0dae3b0d-4074-406b-aede-790c0be061cc",
    network_name: "AIRTELMONEYTZ",
    
    // Optional
    message: "Get well soon!"
  })
});
```

#### Bank Transfer Donation (Anonymous)

```javascript
// POST /api/v1.0/donors/yellowcard/donate/anonymous/
const response = await fetch(`${API_URL}/donors/yellowcard/donate/anonymous/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    // Patient info (optional)
    patient_id: 1,
    
    // Amounts
    patient_amount: 50000,
    
    // Currency & Country
    currency: "TZS",
    country: "TZ",
    
    // Sender info
    sender_name: "John Doe",
    sender_email: "john@example.com",
    
    // Bank Transfer specific
    account_type: "bank",                     // "bank" for bank transfer
    bank_account_number: "1234567890",        // Required for bank transfer
    bank_account_name: "John Doe",            // Account holder name (optional)
    
    // Payment channel (from Step 1 & 2)
    channel_id: "fc7a5bc2-9100-473e-8c01-df563494ee73",  // Bank channel
    network_id: "xxx-bank-network-id",
    network_name: "KCB BANK",
    
    // Optional
    message: "Get well soon!"
  })
});
```

#### Authenticated Donation

```javascript
// POST /api/v1.0/donors/yellowcard/donate/
const response = await fetch(`${API_URL}/donors/yellowcard/donate/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    // Patient info (optional)
    patient_id: 1,
    
    // Amounts
    patient_amount: 45000,
    rhci_support_amount: 5000,
    
    // Currency & Country
    currency: "TZS",
    country: "TZ",
    
    // Sender phone (required if not in user profile)
    sender_phone: "+255712345678",
    
    // Payment channel
    channel_id: "656d4e72-7849-4fd6-b0a0-8631c8adf704",
    network_id: "0dae3b0d-4074-406b-aede-790c0be061cc",
    network_name: "AIRTELMONEYTZ",
    
    // Optional
    message: "Get well soon!"
  })
});
```

> **Note:** For authenticated users, `sender_name` and `sender_email` are auto-filled from their profile. Only `sender_phone` is needed if not in their profile.

---

### Step 4: Handle Response

**Success Response:**
```json
{
  "success": true,
  "message": "Donation initiated. Please confirm payment on your phone.",
  "donation_id": 54,
  "transaction_id": "YC-1C68A4A09409",
  "collection_id": "10b203a8-4569-4cd8-9222-3bb5bac0f592",
  "amount": "50000",
  "patient_amount": "45000",
  "rhci_support_amount": "5000",
  "currency": "TZS",
  "usd_amount": "19.35",
  "rate": "2583.6",
  "status": "PROCESSING",
  "patient_id": 1,
  "patient_name": "Peter Kimani",
  "environment": "sandbox"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "sender_phone is required"
}
```

---

### Step 5: Check Payment Status (Optional)

Poll for payment status updates.

```javascript
// GET /api/v1.0/donors/yellowcard/status/?collection_id=xxx
const response = await fetch(
  `${API_URL}/donors/yellowcard/status/?collection_id=${collectionId}`
);
const data = await response.json();
```

**Response:**
```json
{
  "success": true,
  "donation_id": 54,
  "transaction_id": "YC-1C68A4A09409",
  "collection_id": "10b203a8-4569-4cd8-9222-3bb5bac0f592",
  "status": "COMPLETED",
  "yellowcard_status": "complete",
  "amount": "50000.00",
  "currency": "TZS",
  "amount_usd": "19.35"
}
```

---

## Donation Types

### 1. Patient Donation Only
```json
{
  "patient_id": 1,
  "patient_amount": 50000,
  // ... other fields
}
```
**Total charged: 50,000 TZS**

### 2. Patient + RHCI Support
```json
{
  "patient_id": 1,
  "patient_amount": 45000,
  "rhci_support_amount": 5000,
  // ... other fields
}
```
**Total charged: 50,000 TZS** (45K to patient, 5K to RHCI)

### 3. RHCI Organization Only (no patient)
```json
{
  "rhci_support_amount": 50000,
  // ... other fields (no patient_id)
}
```
**Total charged: 50,000 TZS** (all to RHCI)

---

## Request Fields Reference

### Common Fields (All Donations)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `patient_id` | integer | No | Patient ID (omit for org-only donation) |
| `patient_amount` | number | If patient_id | Amount for patient in local currency |
| `rhci_support_amount` | number | No | Amount for RHCI support (always optional) |
| `currency` | string | No | Currency code (default: TZS) |
| `country` | string | No | Country code (default: TZ) |
| `sender_name` | string | Anonymous only | Donor's full name |
| `sender_email` | string | Anonymous only | Donor's email |
| `channel_id` | string | Yes | Channel ID from `/channels/` endpoint |
| `network_id` | string | Yes | Network ID from `/networks/` endpoint |
| `network_name` | string | No | Network name (e.g., "AIRTELMONEYTZ", "KCB") |
| `account_type` | string | No | `"phone"` for mobile money, `"bank"` for bank (default: phone) |
| `message` | string | No | Optional message to patient |

### Mobile Money Fields (`account_type: "phone"`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sender_phone` | string | Yes | Donor's phone number with country code (e.g., `+255712345678`) |

### Bank Transfer Fields (`account_type: "bank"`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bank_account_number` | string | Yes | Donor's bank account number |
| `bank_account_name` | string | No | Account holder name (optional) |

> For authenticated users, `sender_phone` is auto-filled from profile if available.

---

## Payment Status Values

| Status | Description |
|--------|-------------|
| `PROCESSING` | Payment initiated, waiting for user confirmation |
| `COMPLETED` | Payment successful |
| `FAILED` | Payment failed or rejected |
| `EXPIRED` | Payment request expired |
| `CANCELLED` | Payment cancelled by user |

---

## Supported Countries & Currencies

> **Note:** Check Yellow Card API for the latest supported countries. Some currencies may not have buy rates available in sandbox.

| Country | Code | Currency | Mobile Money | Bank | Notes |
|---------|------|----------|--------------|------|-------|
| Tanzania | TZ | TZS | ✅ | ✅ | Full support |
| Kenya | KE | KES | ✅ | ✅ | Full support |
| Nigeria | NG | NGN | ✅ | ✅ | Full support |
| Uganda | UG | UGX | ✅ | ✅ | Full support |
| South Africa | ZA | ZAR | ✅ | ✅ | Full support |
| Rwanda | RW | RWF | ✅ | ✅ | Full support |
| Cameroon | CM | XAF | ✅ | ✅ | CFA Franc |
| Ivory Coast | CI | XOF | ✅ | ✅ | West African Franc |
| Zambia | ZM | ZMW | ✅ | ✅ | Kwacha |
| ~~Ghana~~ | ~~GH~~ | ~~GHS~~ | ❌ | ❌ | **Not currently available** |

> ⚠️ **Ghana (GHS) is NOT currently supported** by Yellow Card. No buy rate available.

---

## Example React Implementation

```jsx
import React, { useState, useEffect } from 'react';

const YellowCardDonation = ({ patientId, isAuthenticated, accessToken }) => {
  const [channels, setChannels] = useState([]);
  const [networks, setNetworks] = useState([]);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [selectedNetwork, setSelectedNetwork] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    patient_amount: '',
    rhci_support_amount: '',
    sender_name: '',
    sender_phone: '',
    sender_email: '',
    message: ''
  });

  // Step 1: Load channels on mount
  useEffect(() => {
    fetch(`${API_URL}/donors/yellowcard/channels/?country=TZ`)
      .then(res => res.json())
      .then(data => setChannels(data.channels));
  }, []);

  // Step 2: Load networks when channel selected
  useEffect(() => {
    if (selectedChannel) {
      fetch(`${API_URL}/donors/yellowcard/networks/?channel_id=${selectedChannel.id}`)
        .then(res => res.json())
        .then(data => setNetworks(data.networks));
    }
  }, [selectedChannel]);

  // Step 3: Submit donation
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const endpoint = isAuthenticated 
      ? '/donors/yellowcard/donate/'
      : '/donors/yellowcard/donate/anonymous/';

    const headers = {
      'Content-Type': 'application/json',
      ...(isAuthenticated && { 'Authorization': `Bearer ${accessToken}` })
    };

    const body = {
      patient_id: patientId,
      patient_amount: parseFloat(formData.patient_amount),
      rhci_support_amount: parseFloat(formData.rhci_support_amount) || 0,
      currency: 'TZS',
      country: 'TZ',
      channel_id: selectedChannel.id,
      network_id: selectedNetwork.id,
      network_name: selectedNetwork.name,
      message: formData.message,
      // Only include sender info for anonymous
      ...(!isAuthenticated && {
        sender_name: formData.sender_name,
        sender_email: formData.sender_email,
      }),
      // Phone always needed if not in profile
      sender_phone: formData.sender_phone
    };

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Show success - user will receive USSD prompt
        alert(`Donation initiated! Please confirm on your phone.\n\nTransaction: ${data.transaction_id}`);
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Channel Selection */}
      <div>
        <label>Payment Method</label>
        <select onChange={(e) => setSelectedChannel(channels.find(c => c.id === e.target.value))}>
          <option value="">Select payment method</option>
          {channels.map(channel => (
            <option key={channel.id} value={channel.id}>
              {channel.channelType === 'momo' ? '📱 Mobile Money' : '🏦 Bank Transfer'}
            </option>
          ))}
        </select>
      </div>

      {/* Network Selection */}
      {selectedChannel && (
        <div>
          <label>Provider</label>
          <select onChange={(e) => setSelectedNetwork(networks.find(n => n.id === e.target.value))}>
            <option value="">Select provider</option>
            {networks.map(network => (
              <option key={network.id} value={network.id}>
                {network.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Amount Fields */}
      <div>
        <label>Donation Amount (TZS)</label>
        <input
          type="number"
          value={formData.patient_amount}
          onChange={(e) => setFormData({...formData, patient_amount: e.target.value})}
          placeholder="e.g., 50000"
          required
        />
      </div>

      <div>
        <label>Support RHCI (Optional)</label>
        <input
          type="number"
          value={formData.rhci_support_amount}
          onChange={(e) => setFormData({...formData, rhci_support_amount: e.target.value})}
          placeholder="e.g., 5000"
        />
      </div>

      {/* Sender Info (Anonymous only) */}
      {!isAuthenticated && (
        <>
          <div>
            <label>Your Name</label>
            <input
              type="text"
              value={formData.sender_name}
              onChange={(e) => setFormData({...formData, sender_name: e.target.value})}
              required
            />
          </div>
          <div>
            <label>Your Email</label>
            <input
              type="email"
              value={formData.sender_email}
              onChange={(e) => setFormData({...formData, sender_email: e.target.value})}
              required
            />
          </div>
        </>
      )}

      {/* Phone (always needed) */}
      <div>
        <label>Phone Number</label>
        <input
          type="tel"
          value={formData.sender_phone}
          onChange={(e) => setFormData({...formData, sender_phone: e.target.value})}
          placeholder="+255712345678"
          required
        />
      </div>

      {/* Message */}
      <div>
        <label>Message (Optional)</label>
        <textarea
          value={formData.message}
          onChange={(e) => setFormData({...formData, message: e.target.value})}
          placeholder="Get well soon!"
        />
      </div>

      {/* Total Display */}
      <div>
        <strong>Total: {(parseFloat(formData.patient_amount) || 0) + (parseFloat(formData.rhci_support_amount) || 0)} TZS</strong>
      </div>

      <button type="submit" disabled={loading || !selectedChannel || !selectedNetwork}>
        {loading ? 'Processing...' : 'Donate Now'}
      </button>
    </form>
  );
};

export default YellowCardDonation;
```

---

## Testing

### Sandbox Test Account Numbers (IMPORTANT!)

Yellow Card sandbox uses **special test account numbers** to simulate success/failure. **Yellow Card automatically completes/fails transactions based on these test numbers.**

---

### Frontend `.env` Configuration for Sandbox Testing

Add these to your **frontend `.env`** file for sandbox testing:

```env
# ============ YELLOW CARD SANDBOX TEST DATA ============
# Use these ONLY in sandbox/development mode

# Environment flag
REACT_APP_YELLOW_CARD_ENV=sandbox

# Test Account Numbers (Yellow Card auto-completes based on these)
REACT_APP_YC_TEST_MOBILE_SUCCESS=+2551111111111
REACT_APP_YC_TEST_MOBILE_FAILURE=+2550000000000
REACT_APP_YC_TEST_BANK_SUCCESS=1111111111
REACT_APP_YC_TEST_BANK_FAILURE=0000000000

# Tanzania Channel & Network IDs (Sandbox)
REACT_APP_YC_TZ_MOBILE_CHANNEL=656d4e72-7849-4fd6-b0a0-8631c8adf704
REACT_APP_YC_TZ_BANK_CHANNEL=fc7a5bc2-9100-473e-8c01-df563494ee73
REACT_APP_YC_TZ_AIRTEL_NETWORK=0dae3b0d-4074-406b-aede-790c0be061cc
```

---

### Frontend Code Example - Auto-fill Test Data in Sandbox

```javascript
// In your donation form component
const isSandbox = process.env.REACT_APP_YELLOW_CARD_ENV === 'sandbox';

// Auto-fill test account numbers in sandbox mode
const getTestAccountNumber = (paymentType, testType = 'success') => {
  if (!isSandbox) return ''; // Don't auto-fill in production
  
  if (paymentType === 'phone') {
    return testType === 'success' 
      ? process.env.REACT_APP_YC_TEST_MOBILE_SUCCESS 
      : process.env.REACT_APP_YC_TEST_MOBILE_FAILURE;
  } else if (paymentType === 'bank') {
    return testType === 'success'
      ? process.env.REACT_APP_YC_TEST_BANK_SUCCESS
      : process.env.REACT_APP_YC_TEST_BANK_FAILURE;
  }
  return '';
};

// Usage in form
const [senderPhone, setSenderPhone] = useState(
  isSandbox ? process.env.REACT_APP_YC_TEST_MOBILE_SUCCESS : ''
);
const [bankAccountNumber, setBankAccountNumber] = useState(
  isSandbox ? process.env.REACT_APP_YC_TEST_BANK_SUCCESS : ''
);
```

---

### Test Account Numbers Reference

#### Mobile Money Test Numbers

| Test Type | Account Number Format | Tanzania Example |
|-----------|----------------------|------------------|
| ✅ **SUCCESS** | `+{countryCode}1111111111` | `+2551111111111` |
| ❌ **FAILURE** | `+{countryCode}0000000000` | `+2550000000000` |

**Country Codes:**
- Tanzania: `255`
- Kenya: `254`
- Nigeria: `234`
- Uganda: `256`
- Ghana: `233`

#### Bank Transfer Test Numbers

| Test Type | Account Number |
|-----------|----------------|
| ✅ **SUCCESS** | `1111111111` |
| ❌ **FAILURE** | `0000000000` |

---

### Test IDs for Tanzania (Sandbox)

| Item | Value |
|------|-------|
| **Mobile Money Channel** | `656d4e72-7849-4fd6-b0a0-8631c8adf704` |
| **Bank Channel** | `fc7a5bc2-9100-473e-8c01-df563494ee73` |
| **Airtel Money Network** | `0dae3b0d-4074-406b-aede-790c0be061cc` |
| **Success Mobile Phone** | `+2551111111111` |
| **Failure Mobile Phone** | `+2550000000000` |
| **Success Bank Account** | `1111111111` |
| **Failure Bank Account** | `0000000000` |

---

### Test cURL - Mobile Money (Success)

```bash
curl -X POST "http://localhost:8090/api/v1.0/donors/yellowcard/donate/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "patient_amount": 45000,
    "rhci_support_amount": 5000,
    "currency": "TZS",
    "country": "TZ",
    "sender_name": "John Doe",
    "sender_email": "john@example.com",
    "account_type": "phone",
    "sender_phone": "+2551111111111",
    "channel_id": "656d4e72-7849-4fd6-b0a0-8631c8adf704",
    "network_id": "0dae3b0d-4074-406b-aede-790c0be061cc",
    "network_name": "AIRTELMONEYTZ"
  }'
```

### Test cURL - Bank Transfer (Success)

```bash
curl -X POST "http://localhost:8090/api/v1.0/donors/yellowcard/donate/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "patient_amount": 45000,
    "currency": "TZS",
    "country": "TZ",
    "sender_name": "John Doe",
    "sender_email": "john@example.com",
    "account_type": "bank",
    "bank_account_number": "1111111111",
    "bank_account_name": "John Doe",
    "channel_id": "fc7a5bc2-9100-473e-8c01-df563494ee73",
    "network_id": "0dae3b0d-4074-406b-aede-790c0be061cc"
  }'
```

### Test cURL - Mobile Money (Failure)

```bash
curl -X POST "http://localhost:8090/api/v1.0/donors/yellowcard/donate/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "patient_amount": 45000,
    "currency": "TZS",
    "country": "TZ",
    "sender_name": "Jane Doe",
    "sender_email": "jane@example.com",
    "account_type": "phone",
    "sender_phone": "+2550000000000",
    "channel_id": "656d4e72-7849-4fd6-b0a0-8631c8adf704",
    "network_id": "0dae3b0d-4074-406b-aede-790c0be061cc"
  }'
```

### Test cURL - Bank Transfer (Failure)

```bash
curl -X POST "http://localhost:8090/api/v1.0/donors/yellowcard/donate/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "patient_amount": 45000,
    "currency": "TZS",
    "country": "TZ",
    "sender_name": "Jane Doe",
    "sender_email": "jane@example.com",
    "account_type": "bank",
    "bank_account_number": "0000000000",
    "channel_id": "fc7a5bc2-9100-473e-8c01-df563494ee73",
    "network_id": "0dae3b0d-4074-406b-aede-790c0be061cc"
  }'
```

---

### How Sandbox Testing Works

1. **Submit donation** with test phone number (`+2551111111111` for success)
2. **Yellow Card auto-completes** the transaction within ~15-30 seconds
3. **Check status** via `/yellowcard/status/?collection_id=xxx`
4. **Webhook received** (if configured) with final status

> **Note:** In sandbox, Yellow Card automatically simulates the payment based on the test account number. No manual simulation required!

---

## User Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. User selects patient to donate to                       │
├─────────────────────────────────────────────────────────────┤
│  2. User enters donation amounts:                           │
│     • Patient amount (required)                             │
│     • RHCI support amount (optional)                        │
├─────────────────────────────────────────────────────────────┤
│  3. User selects payment method:                            │
│     • 📱 Mobile Money                                       │
│     • 🏦 Bank Transfer                                      │
├─────────────────────────────────────────────────────────────┤
│  4. User selects provider:                                  │
│     • Airtel Money                                          │
│     • Vodacom M-Pesa                                        │
│     • etc.                                                  │
├─────────────────────────────────────────────────────────────┤
│  5. User enters phone number & personal info (if anonymous) │
├─────────────────────────────────────────────────────────────┤
│  6. User clicks "Donate Now"                                │
├─────────────────────────────────────────────────────────────┤
│  7. API returns success → Show "Check your phone"           │
├─────────────────────────────────────────────────────────────┤
│  8. User receives USSD prompt on phone                      │
├─────────────────────────────────────────────────────────────┤
│  9. User confirms payment with PIN                          │
├─────────────────────────────────────────────────────────────┤
│  10. Webhook updates donation status → Show success         │
└─────────────────────────────────────────────────────────────┘
```

---

## Questions?

Contact the backend team for support.
