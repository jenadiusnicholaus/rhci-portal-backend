# 💰 Frontend Currency Implementation Guide

**Date:** January 1, 2026  
**Backend Changes:** Multi-currency support with TZS validation for AzamPay

---

## 📋 Overview

The backend now supports **multi-currency** for donations and patient funding, with the following key requirement:
- **All payments through AzamPay MUST use TZS (Tanzanian Shilling)**
- Other currencies can be stored but cannot be processed for payment
- Amounts are stored as entered (no currency conversion)

---

## 🔄 What Changed

### 1. **New Currency Fields Added:**

| Model | Field | Type | Default | Required |
|-------|-------|------|---------|----------|
| `Donation` | `currency` | String (enum) | `TZS` | No |
| `PatientProfile` | `funding_currency` | String (enum) | `USD` | No |
| `DonationAmountOption` | `currency` | String (enum) | `USD` | No |

### 2. **Available Currencies:**
```javascript
const CURRENCIES = [
  { code: 'USD', name: 'US Dollar', symbol: '$' },
  { code: 'EUR', name: 'Euro', symbol: '€' },
  { code: 'GBP', name: 'British Pound', symbol: '£' },
  { code: 'TZS', name: 'Tanzanian Shilling', symbol: 'TSh' }, // ✅ REQUIRED for AzamPay
  { code: 'KES', name: 'Kenyan Shilling', symbol: 'KSh' },
  { code: 'UGX', name: 'Ugandan Shilling', symbol: 'USh' },
  { code: 'ZAR', name: 'South African Rand', symbol: 'R' },
  { code: 'NGN', name: 'Nigerian Naira', symbol: '₦' },
  { code: 'GHS', name: 'Ghanaian Cedi', symbol: 'GH₵' },
  { code: 'CAD', name: 'Canadian Dollar', symbol: 'C$' },
  { code: 'AUD', name: 'Australian Dollar', symbol: 'A$' },
];
```

---

## 🎯 Implementation Tasks

### **TASK 1: Update Admin Patient Forms** ⚡ HIGH PRIORITY

When creating or editing patients, add currency selection.

#### API Changes:
```typescript
// OLD Request Body
POST /api/v1.0/patients/admin/
{
  "full_name": "John Doe",
  "funding_required": 5000,
  "total_treatment_cost": 5000
}

// NEW Request Body
POST /api/v1.0/patients/admin/
{
  "full_name": "John Doe",
  "funding_required": 5000000,           // Amount in TZS
  "funding_currency": "TZS",              // ✅ NEW FIELD
  "total_treatment_cost": 5000000
}
```

#### UI Changes Needed:
1. **Add Currency Dropdown** in patient create/edit forms:
   ```jsx
   <FormSelect
     label="Funding Currency"
     name="funding_currency"
     defaultValue="TZS"
     required
   >
     <option value="USD">USD - US Dollar ($)</option>
     <option value="EUR">EUR - Euro (€)</option>
     <option value="TZS">TZS - Tanzanian Shilling (TSh)</option>
     {/* ... other currencies */}
   </FormSelect>
   ```

2. **Update Amount Input Labels:**
   ```jsx
   <FormInput
     label={`Funding Required (${formData.funding_currency || 'TZS'})`}
     name="funding_required"
     type="number"
     placeholder={formData.funding_currency === 'TZS' ? '5000000' : '5000'}
   />
   ```

3. **Show Warning for Non-TZS:**
   ```jsx
   {formData.funding_currency !== 'TZS' && (
     <Alert type="warning">
       ⚠️ Note: Only TZS can be processed through AzamPay payment gateway.
       Donations in other currencies will be stored but cannot be paid online.
     </Alert>
   )}
   ```

#### Endpoints Affected:
- `POST /api/v1.0/patients/admin/` - Create patient
- `PATCH /api/v1.0/patients/admin/{id}/` - Update patient
- `PUT /api/v1.0/patients/admin/{id}/` - Full update
- `GET /api/v1.0/patients/admin/review/{id}/` - Response includes `funding_currency`

---

### **TASK 2: Update Donation Amount Options (Admin)** ⚡ HIGH PRIORITY

Admins create suggested donation amounts for each patient.

#### API Changes:
```typescript
// OLD Request Body
POST /api/v1.0/patients/admin/{patient_id}/donation-amounts/
{
  "amount": 50,
  "display_order": 1,
  "is_recommended": true
}

// NEW Request Body
POST /api/v1.0/patients/admin/{patient_id}/donation-amounts/
{
  "amount": 50000,                        // Amount in patient's currency
  "currency": "TZS",                      // ✅ NEW FIELD (should match patient's funding_currency)
  "display_order": 1,
  "is_recommended": true
}
```

#### UI Changes Needed:
1. **Auto-populate currency from patient:**
   ```jsx
   const handleCreateDonationAmount = () => {
     const defaultCurrency = patient.funding_currency || 'TZS';
     
     setFormData({
       amount: '',
       currency: defaultCurrency,  // Auto-set from patient
       display_order: 1,
       is_recommended: false
     });
   };
   ```

2. **Show currency in amount list:**
   ```jsx
   <div className="donation-amount-card">
     <h4>{amount.currency} {amount.amount.toLocaleString()}</h4>
     <span className="currency-badge">{amount.currency_symbol}</span>
   </div>
   ```

#### API Response Changes:
```json
{
  "id": 1,
  "amount": 50000,
  "currency": "TZS",               // ✅ NEW
  "currency_symbol": "TSh",        // ✅ NEW
  "display_order": 1,
  "is_active": true,
  "is_recommended": true
}
```

---

### **TASK 3: Update Donation Flow (Donor Side)** 🔥 CRITICAL

Most important change - actual donation submission.

#### API Changes:
```typescript
// OLD Request Body
POST /api/v1.0/donations/patient/anonymous/one-time/
{
  "patient_id": 1,
  "amount": 50,
  "anonymous_name": "John Doe",
  "anonymous_email": "john@example.com",
  "payment_method": "MOBILE_MONEY",
  "provider": "mpesa",
  "phone_number": "0789123456"
}

// NEW Request Body
POST /api/v1.0/donations/patient/anonymous/one-time/
{
  "patient_id": 1,
  "amount": 50000,                        // Amount in TZS
  "currency": "TZS",                      // ✅ NEW FIELD (MUST be TZS for payment)
  "anonymous_name": "John Doe",
  "anonymous_email": "john@example.com",
  "payment_method": "MOBILE_MONEY",
  "provider": "mpesa",
  "phone_number": "0789123456"
}
```

#### UI Changes Needed:

1. **Currency Validation Before Payment:**
   ```jsx
   const handleDonateClick = async () => {
     // Validate currency is TZS
     if (donationData.currency !== 'TZS') {
       showError('AzamPay only accepts TZS currency. Please adjust amount to Tanzanian Shillings.');
       return;
     }
     
     // Proceed with payment
     await submitDonation();
   };
   ```

2. **Display Patient Funding in Correct Currency:**
   ```jsx
   const PatientFundingCard = ({ patient }) => {
     const symbol = getCurrencySymbol(patient.funding_currency || 'USD');
     
     return (
       <div>
         <h3>Funding Progress</h3>
         <p className="funding-amount">
           {symbol}{patient.funding_received.toLocaleString()} 
           <span className="currency-code">({patient.funding_currency})</span>
         </p>
         <p className="funding-goal">
           of {symbol}{patient.funding_required.toLocaleString()} goal
         </p>
       </div>
     );
   };
   ```

3. **Quick-Select Amount Buttons:**
   ```jsx
   {donationAmounts.map((option) => (
     <button
       key={option.id}
       onClick={() => setAmount(option.amount)}
       className={option.is_recommended ? 'recommended' : ''}
     >
       {option.currency_symbol} {option.amount.toLocaleString()}
       {option.is_recommended && ' ⭐'}
     </button>
   ))}
   ```

4. **Error Handling:**
   ```typescript
   try {
     const response = await createDonation(donationData);
     // Success
   } catch (error) {
     if (error.response?.data?.error?.includes('TZS')) {
       // Currency mismatch error
       showError('Payment gateway only accepts TZS. Please select a TZS amount.');
     }
   }
   ```

---

### **TASK 4: Update Patient Profile Display (Public)** 🎨 MEDIUM PRIORITY

Show currency information to donors viewing patient profiles.

#### API Response Changes:
```json
GET /api/v1.0/auth/patients/discover/
{
  "id": 1,
  "full_name": "John Doe",
  "funding_required": 5000000,
  "funding_received": 1000000,
  "funding_currency": "TZS",         // ✅ NEW
  "funding_percentage": 20.0
}
```

#### UI Changes:
```jsx
const PatientCard = ({ patient }) => {
  const currencySymbol = patient.funding_currency === 'TZS' ? 'TSh' : '$';
  
  return (
    <div className="patient-card">
      <h3>{patient.full_name}</h3>
      <div className="funding-info">
        <div className="raised">
          <strong>{currencySymbol}{patient.funding_received.toLocaleString()}</strong>
          <span> raised of {currencySymbol}{patient.funding_required.toLocaleString()}</span>
        </div>
        <ProgressBar value={patient.funding_percentage} />
      </div>
    </div>
  );
};
```

---

### **TASK 5: Update Donation History/Receipts** 📊 LOW PRIORITY

Show currency information in donor dashboard and receipts.

#### API Response Changes:
```json
GET /api/v1.0/donations/donor/my-donations/
{
  "id": 123,
  "amount": 50000,
  "currency": "TZS",                    // ✅ NEW
  "currency_display": "Tanzanian Shilling", // ✅ NEW
  "patient_name": "John Doe",
  "status": "COMPLETED",
  "created_at": "2026-01-01T10:00:00Z"
}
```

#### UI Changes:
```jsx
const DonationHistoryRow = ({ donation }) => (
  <tr>
    <td>{donation.patient_name}</td>
    <td>
      {donation.currency} {donation.amount.toLocaleString()}
      <span className="currency-full">({donation.currency_display})</span>
    </td>
    <td>{donation.status}</td>
    <td>{formatDate(donation.created_at)}</td>
  </tr>
);
```

---

## 🛠️ Helper Functions

### Currency Symbol Helper
```typescript
// utils/currency.ts
export const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  TZS: 'TSh',
  KES: 'KSh',
  UGX: 'USh',
  ZAR: 'R',
  NGN: '₦',
  GHS: 'GH₵',
  CAD: 'C$',
  AUD: 'A$',
};

export const getCurrencySymbol = (currencyCode: string): string => {
  return CURRENCY_SYMBOLS[currencyCode] || currencyCode;
};

export const formatCurrency = (amount: number, currency: string): string => {
  const symbol = getCurrencySymbol(currency);
  return `${symbol}${amount.toLocaleString()}`;
};
```

### Currency Validation
```typescript
// utils/validation.ts
export const validateDonationCurrency = (currency: string): boolean => {
  if (currency !== 'TZS') {
    return false;
  }
  return true;
};

export const getCurrencyWarning = (currency: string): string | null => {
  if (currency !== 'TZS') {
    return 'Only TZS currency can be processed through AzamPay payment gateway.';
  }
  return null;
};
```

---

## ⚠️ Important Notes

### 1. **No Currency Conversion**
- The system does NOT convert currencies
- Amounts are stored exactly as entered
- Example: 50000 TZS stays 50000 TZS, not converted to USD

### 2. **AzamPay TZS Requirement**
- **All payments MUST be in TZS**
- Backend validates this before processing
- Show clear error if user tries non-TZS payment

### 3. **Amount Scale Differences**
```javascript
// TZS amounts are much larger than USD
USD: $50 = reasonable donation
TZS: 50000 TSh = roughly equivalent

// Update example amounts accordingly
const exampleAmounts = {
  USD: [10, 25, 50, 100, 250],
  TZS: [10000, 25000, 50000, 100000, 250000]
};
```

### 4. **Backward Compatibility**
- Existing donations without currency field will default to `USD`
- Existing patients without `funding_currency` will default to `USD`
- New donations default to `TZS`

---

## 🧪 Testing Checklist

### Admin Side:
- [ ] Create patient with TZS currency
- [ ] Create patient with USD currency (should show warning)
- [ ] Update patient currency field
- [ ] Create donation amount options with TZS
- [ ] View patient list showing currency

### Donor Side:
- [ ] View patient profile with TZS funding
- [ ] Click quick-select TZS amount button
- [ ] Submit donation with TZS currency (should succeed)
- [ ] Try to submit donation with USD currency (should fail with clear error)
- [ ] View donation history showing currency

### Edge Cases:
- [ ] Patient with USD funding (cannot donate via AzamPay - show message)
- [ ] Mixed currency donation amounts (should filter/warn)
- [ ] Large TZS numbers display correctly (commas, formatting)

---

## 📞 Backend API Endpoints Reference

### Patient Management (Admin)
```
POST   /api/v1.0/patients/admin/                          # Create patient (add funding_currency)
GET    /api/v1.0/patients/admin/                          # List patients (returns funding_currency)
PATCH  /api/v1.0/patients/admin/{id}/                     # Update patient (can update funding_currency)
GET    /api/v1.0/patients/admin/review/{id}/              # Get patient details (includes funding_currency)
```

### Donation Amount Options (Admin)
```
GET    /api/v1.0/patients/admin/{patient_id}/donation-amounts/           # List amounts (returns currency)
POST   /api/v1.0/patients/admin/{patient_id}/donation-amounts/           # Create amount (add currency)
PATCH  /api/v1.0/patients/admin/{patient_id}/donation-amounts/{id}/      # Update amount (can update currency)
```

### Donations (Donor)
```
POST   /api/v1.0/donations/patient/anonymous/one-time/    # Anonymous donation (add currency)
POST   /api/v1.0/donations/patient/authenticated/one-time/ # Authenticated donation (add currency)
GET    /api/v1.0/donations/donor/my-donations/            # Donation history (returns currency)
```

### Public Patient Discovery
```
GET    /api/v1.0/auth/patients/discover/                  # List patients (returns funding_currency)
GET    /api/v1.0/auth/patients/public/{id}/               # Patient details (returns funding_currency)
GET    /api/v1.0/patients/public/{patient_id}/donation-amounts/ # Get amounts (returns currency)
```

---

## 🚀 Migration Steps

### Phase 1: Admin Panel (Week 1)
1. Add currency dropdown to patient forms
2. Update patient list to show currency
3. Add currency to donation amount forms
4. Test admin workflows

### Phase 2: Donor UI (Week 2)
1. Update patient card displays
2. Add currency to donation flow
3. Implement TZS validation
4. Update quick-select buttons
5. Test donation process end-to-end

### Phase 3: Polish (Week 3)
1. Update donation history
2. Add currency to receipts
3. Update all amount displays
4. Final testing

---

## 📝 Questions or Issues?

If you encounter any issues or need clarification:
1. Check Swagger documentation: `http://your-api/swagger/`
2. Review error responses from API
3. Contact backend team with specific error messages

---

**Document Version:** 1.0  
**Last Updated:** January 1, 2026  
**Backend Version:** v1.0 (Currency Support)
