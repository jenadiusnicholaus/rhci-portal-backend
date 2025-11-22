# Admin Dashboard Statistics API

## Overview

The Admin Dashboard Statistics API provides a comprehensive overview of all platform metrics in a single endpoint. This is designed specifically for admin dashboard views that need real-time platform insights.

**Endpoint**: `GET /api/v1.0/patients/admin/dashboard/stats/`

**Authentication**: Required - Admin users only

**Swagger Tag**: `Admin - Dashboard & Analytics`

---

## Response Structure

### User Overview Statistics
```json
{
  "total_users": 150,
  "total_patients": 45,
  "total_donors": 100,
  "total_admins": 5,
  "active_users": 142,
  "verified_users": 138
}
```

### Patient Statistics
```json
{
  "patients_submitted": 12,
  "patients_published": 28,
  "patients_fully_funded": 5,
  "patients_featured": 8,
  "patients_pending_review": 12
}
```

### Donor Statistics
```json
{
  "active_donors": 95,
  "total_donations_count": 324,
  "unique_donors_count": 87
}
```

### Campaign Statistics
```json
{
  "total_campaigns": 15,
  "active_campaigns": 8,
  "completed_campaigns": 7
}
```

### Financial Statistics
```json
{
  "total_funding_goal": "450000.00",
  "total_funding_raised": "287500.50",
  "total_donations_amount": "287500.50",
  "average_donation_amount": "887.97",
  "overall_funding_percentage": 63.89
}
```

### Recent Activity (This Month - Last 30 Days)
```json
{
  "new_patients_this_month": 8,
  "new_donors_this_month": 15,
  "donations_this_month": 89,
  "donations_amount_this_month": "78450.00"
}
```

### Recent Activity (This Week - Last 7 Days)
```json
{
  "new_patients_this_week": 3,
  "new_donors_this_week": 5,
  "donations_this_week": 24,
  "donations_amount_this_week": "21300.00"
}
```

### Recent Activity (Today)
```json
{
  "new_patients_today": 1,
  "new_donors_today": 2,
  "donations_today": 7,
  "donations_amount_today": "6250.00"
}
```

### Geographic Breakdown
```json
{
  "patients_by_country": {
    "Kenya": 15,
    "Uganda": 12,
    "Tanzania": 10,
    "Rwanda": 8
  },
  "donors_by_country": {
    "United States": 45,
    "United Kingdom": 22,
    "Canada": 18,
    "Australia": 10
  }
}
```

### Status & Gender Breakdown
```json
{
  "patients_by_status": {
    "SUBMITTED": 12,
    "PUBLISHED": 28,
    "FULLY_FUNDED": 5
  },
  "patients_by_gender": {
    "MALE": 22,
    "FEMALE": 23
  }
}
```

### Top Performers
```json
{
  "top_funded_patients": [
    {
      "id": 123,
      "full_name": "John Kamau",
      "funding_received": "25000.00",
      "funding_required": "30000.00",
      "funding_percentage": 83.33,
      "country": "Kenya"
    }
  ],
  "top_donors": [
    {
      "name": "Sarah Johnson",
      "email": "sarah@example.com",
      "total_donated": "15000.00",
      "donation_count": 25
    }
  ],
  "recent_donations": [
    {
      "id": 456,
      "amount": "500.00",
      "created_at": "2024-01-15T14:30:00Z",
      "donor_name": "Michael Brown",
      "patient_name": "Jane Wanjiru",
      "payment_method": "MPESA"
    }
  ]
}
```

### Trends (Last 30 Days)
```json
{
  "daily_donations_trend": [
    {
      "date": "2024-01-01",
      "count": 12,
      "amount": 10500.00
    },
    {
      "date": "2024-01-02",
      "count": 15,
      "amount": 13200.00
    }
  ],
  "daily_registrations_trend": [
    {
      "date": "2024-01-01",
      "patients": 2,
      "donors": 5
    },
    {
      "date": "2024-01-02",
      "patients": 1,
      "donors": 3
    }
  ]
}
```

---

## Complete Response Example

```json
{
  "total_users": 150,
  "total_patients": 45,
  "total_donors": 100,
  "total_admins": 5,
  "active_users": 142,
  "verified_users": 138,
  
  "patients_submitted": 12,
  "patients_published": 28,
  "patients_fully_funded": 5,
  "patients_featured": 8,
  "patients_pending_review": 12,
  
  "active_donors": 95,
  "total_donations_count": 324,
  "unique_donors_count": 87,
  
  "total_campaigns": 15,
  "active_campaigns": 8,
  "completed_campaigns": 7,
  
  "total_funding_goal": "450000.00",
  "total_funding_raised": "287500.50",
  "total_donations_amount": "287500.50",
  "average_donation_amount": "887.97",
  "overall_funding_percentage": 63.89,
  
  "new_patients_this_month": 8,
  "new_donors_this_month": 15,
  "donations_this_month": 89,
  "donations_amount_this_month": "78450.00",
  
  "new_patients_this_week": 3,
  "new_donors_this_week": 5,
  "donations_this_week": 24,
  "donations_amount_this_week": "21300.00",
  
  "new_patients_today": 1,
  "new_donors_today": 2,
  "donations_today": 7,
  "donations_amount_today": "6250.00",
  
  "patients_by_country": {
    "Kenya": 15,
    "Uganda": 12,
    "Tanzania": 10
  },
  "donors_by_country": {
    "United States": 45,
    "United Kingdom": 22
  },
  "patients_by_status": {
    "SUBMITTED": 12,
    "PUBLISHED": 28
  },
  "patients_by_gender": {
    "MALE": 22,
    "FEMALE": 23
  },
  
  "top_funded_patients": [
    {
      "id": 123,
      "full_name": "John Kamau",
      "funding_received": "25000.00",
      "funding_required": "30000.00",
      "funding_percentage": 83.33,
      "country": "Kenya"
    }
  ],
  "top_donors": [
    {
      "name": "Sarah Johnson",
      "email": "sarah@example.com",
      "total_donated": "15000.00",
      "donation_count": 25
    }
  ],
  "recent_donations": [
    {
      "id": 456,
      "amount": "500.00",
      "created_at": "2024-01-15T14:30:00Z",
      "donor_name": "Michael Brown",
      "patient_name": "Jane Wanjiru",
      "payment_method": "MPESA"
    }
  ],
  
  "daily_donations_trend": [
    {
      "date": "2024-01-01",
      "count": 12,
      "amount": 10500.00
    }
  ],
  "daily_registrations_trend": [
    {
      "date": "2024-01-01",
      "patients": 2,
      "donors": 5
    }
  ]
}
```

---

## Usage Examples

### cURL Example
```bash
curl -X GET \
  'http://185.237.253.223:8082/api/v1.0/patients/admin/dashboard/stats/' \
  -H 'Authorization: Bearer YOUR_ADMIN_TOKEN'
```

### JavaScript/Fetch Example
```javascript
const fetchDashboardStats = async () => {
  const response = await fetch(
    'http://185.237.253.223:8082/api/v1.0/patients/admin/dashboard/stats/',
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${adminToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const stats = await response.json();
  return stats;
};
```

### Python/Requests Example
```python
import requests

url = "http://185.237.253.223:8082/api/v1.0/patients/admin/dashboard/stats/"
headers = {
    "Authorization": f"Bearer {admin_token}"
}

response = requests.get(url, headers=headers)
stats = response.json()
```

---

## Dashboard Widget Mapping

### KPI Cards (Top Row)
```javascript
// Total Users Card
{
  title: "Total Users",
  value: stats.total_users,
  subtitle: `${stats.active_users} active`,
  icon: "users"
}

// Total Donations Card
{
  title: "Total Donations",
  value: `$${stats.total_donations_amount}`,
  subtitle: `${stats.total_donations_count} donations`,
  icon: "dollar-sign"
}

// Funding Progress Card
{
  title: "Funding Progress",
  value: `${stats.overall_funding_percentage}%`,
  subtitle: `$${stats.total_funding_raised} / $${stats.total_funding_goal}`,
  icon: "trending-up"
}

// Active Campaigns Card
{
  title: "Active Campaigns",
  value: stats.active_campaigns,
  subtitle: `${stats.total_campaigns} total`,
  icon: "activity"
}
```

### Activity Metrics (Second Row)
```javascript
// Today's Activity
{
  patients: stats.new_patients_today,
  donors: stats.new_donors_today,
  donations: stats.donations_today,
  amount: stats.donations_amount_today
}

// This Week
{
  patients: stats.new_patients_this_week,
  donors: stats.new_donors_this_week,
  donations: stats.donations_this_week,
  amount: stats.donations_amount_this_week
}

// This Month
{
  patients: stats.new_patients_this_month,
  donors: stats.new_donors_this_month,
  donations: stats.donations_this_month,
  amount: stats.donations_amount_this_month
}
```

### Charts
```javascript
// Donation Trend Line Chart
const donationChartData = {
  labels: stats.daily_donations_trend.map(d => d.date),
  datasets: [{
    label: 'Donations',
    data: stats.daily_donations_trend.map(d => d.amount)
  }]
};

// Registration Trend Area Chart
const registrationChartData = {
  labels: stats.daily_registrations_trend.map(d => d.date),
  datasets: [
    {
      label: 'Patients',
      data: stats.daily_registrations_trend.map(d => d.patients)
    },
    {
      label: 'Donors',
      data: stats.daily_registrations_trend.map(d => d.donors)
    }
  ]
};

// Patient Status Pie Chart
const statusChartData = {
  labels: Object.keys(stats.patients_by_status),
  data: Object.values(stats.patients_by_status)
};

// Geographic Distribution Map
const geoData = {
  patients: stats.patients_by_country,
  donors: stats.donors_by_country
};
```

### Tables
```javascript
// Top Funded Patients Table
const topPatientsTable = stats.top_funded_patients.map(patient => ({
  name: patient.full_name,
  country: patient.country,
  progress: `${patient.funding_percentage.toFixed(1)}%`,
  raised: `$${patient.funding_received}`,
  goal: `$${patient.funding_required}`
}));

// Top Donors Table
const topDonorsTable = stats.top_donors.map(donor => ({
  name: donor.name,
  email: donor.email,
  totalDonated: `$${donor.total_donated}`,
  donationCount: donor.donation_count
}));

// Recent Donations Table
const recentDonationsTable = stats.recent_donations.map(donation => ({
  donor: donation.donor_name,
  patient: donation.patient_name,
  amount: `$${donation.amount}`,
  date: new Date(donation.created_at).toLocaleDateString(),
  method: donation.payment_method
}));
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## Performance Considerations

### Caching Strategy
```python
# Recommended caching for production
from django.core.cache import cache

def get_dashboard_stats():
    cache_key = 'admin_dashboard_stats'
    cached_stats = cache.get(cache_key)
    
    if cached_stats:
        return cached_stats
    
    # Fetch stats from API
    stats = fetch_from_api()
    
    # Cache for 5 minutes
    cache.set(cache_key, stats, 300)
    return stats
```

### Database Optimization
- All queries use database indexes
- Aggregation functions for efficient counting
- SELECT RELATED for foreign key optimization
- Limited result sets (top 5, recent 10)

### Frontend Optimization
- Cache dashboard stats for 5 minutes
- Use loading states while fetching
- Implement progressive loading for charts
- Consider WebSocket for real-time updates

---

## Comparison with Patient-Only Stats

| Feature | Dashboard Stats (`/admin/dashboard/stats/`) | Patient Stats (`/admin/stats/`) |
|---------|-------------------------------------------|--------------------------------|
| **Scope** | Platform-wide (all entities) | Patient-focused only |
| **Users** | ✅ All user types | ❌ Not included |
| **Patients** | ✅ Comprehensive | ✅ Comprehensive |
| **Donors** | ✅ Activity & engagement | ❌ Not included |
| **Campaigns** | ✅ Status overview | ❌ Not included |
| **Donations** | ✅ Complete metrics | ❌ Not included |
| **Financial** | ✅ Platform-wide | ✅ Patient funding only |
| **Time Periods** | ✅ Today, Week, Month | ✅ Month only |
| **Trends** | ✅ Daily charts (30 days) | ❌ Not included |
| **Top Performers** | ✅ Patients & Donors | ❌ Not included |
| **Recent Activity** | ✅ Last 10 donations | ❌ Not included |
| **Use Case** | Executive dashboard | Patient management panel |

---

## Best Practices

### 1. Implement Client-Side Caching
```javascript
class DashboardStatsService {
  constructor() {
    this.cache = null;
    this.cacheTime = null;
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }
  
  async getStats(forceRefresh = false) {
    const now = Date.now();
    
    if (!forceRefresh && this.cache && 
        (now - this.cacheTime < this.cacheTimeout)) {
      return this.cache;
    }
    
    const stats = await this.fetchFromAPI();
    this.cache = stats;
    this.cacheTime = now;
    
    return stats;
  }
}
```

### 2. Handle Loading States
```javascript
function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetchDashboardStats()
      .then(setStats)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);
  
  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorMessage error={error} />;
  
  return <Dashboard stats={stats} />;
}
```

### 3. Progressive Chart Rendering
```javascript
// Load KPIs first, then charts
async function loadDashboard() {
  const stats = await fetchDashboardStats();
  
  // Render KPIs immediately
  renderKPIs(stats);
  
  // Render charts after a short delay
  setTimeout(() => {
    renderCharts(stats);
  }, 100);
  
  // Render tables last
  setTimeout(() => {
    renderTables(stats);
  }, 200);
}
```

### 4. Real-Time Updates (Optional)
```javascript
// Poll for updates every 5 minutes
setInterval(async () => {
  const stats = await fetchDashboardStats();
  updateDashboard(stats);
}, 5 * 60 * 1000);
```

---

## Security Notes

- **Admin Only**: Endpoint requires admin authentication
- **Rate Limiting**: Recommended 60 requests/minute
- **Sensitive Data**: Contains financial and user information
- **HTTPS**: Always use encrypted connections in production
- **Token Security**: Store admin tokens securely

---

## Related Endpoints

- **Patient Stats**: `GET /api/v1.0/patients/admin/stats/` - Patient-focused statistics
- **Patient Management**: `GET /api/v1.0/patients/admin/manage/` - Patient list with filters
- **Donation History**: `GET /api/v1.0/donations/admin/history/` - Complete donation records

---

## Support

For questions or issues with the Dashboard Statistics API:
- Check Swagger documentation at `/api/v1.0/swagger/`
- Review patient management docs in `docs/API_ADMIN_PATIENT_MANAGEMENT.md`
- Contact backend development team
