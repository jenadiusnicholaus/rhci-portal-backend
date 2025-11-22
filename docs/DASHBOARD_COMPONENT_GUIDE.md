# Admin Dashboard Layout - Component Mapping

This document shows how to map the dashboard stats API response to actual dashboard components.

## Dashboard Layout (Recommended)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ADMIN DASHBOARD                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Total   │  │  Total   │  │ Funding  │  │  Active  │           │
│  │  Users   │  │Donations │  │ Progress │  │Campaigns │           │
│  │   150    │  │ $287.5K  │  │  63.89%  │  │    8     │           │
│  │ 142 active│ │ 324 done │  │$287K/$450K│ │ 15 total │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    RECENT ACTIVITY                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │   │
│  │  │  TODAY   │  │THIS WEEK │  │THIS MONTH│                 │   │
│  │  │  1 👤    │  │  3 👤    │  │  8 👤    │  New Patients  │   │
│  │  │  2 💝    │  │  5 💝    │  │ 15 💝    │  New Donors    │   │
│  │  │  7 💰    │  │ 24 💰    │  │ 89 💰    │  Donations     │   │
│  │  │ $6.2K    │  │ $21.3K   │  │ $78.4K   │  Amount        │   │
│  │  └──────────┘  └──────────┘  └──────────┘                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────┐  ┌─────────────────────────────┐    │
│  │  DONATION TRENDS (30d)   │  │  REGISTRATIONS TREND (30d)  │    │
│  │                          │  │                             │    │
│  │  $                       │  │  #                          │    │
│  │  │     ╱╲    ╱╲         │  │  │   ╱╲                     │    │
│  │  │   ╱╲  ╲  ╱  ╲  ╱╲    │  │  │ ╱╲  ╲   ╱╲              │    │
│  │  │ ╱╲  ╲  ╲╱    ╲╱  ╲   │  │  │╱  ╲  ╲ ╱  ╲  ╱╲         │    │
│  │  └────────────────────── │  │  └─────────────────────────  │    │
│  │   Jan 1 ─────────→ 30   │  │  Patients ▬  Donors ▬      │    │
│  └──────────────────────────┘  └─────────────────────────────┘    │
│                                                                       │
│  ┌──────────────────────────┐  ┌─────────────────────────────┐    │
│  │   PATIENT STATUS         │  │   GEOGRAPHIC DISTRIBUTION   │    │
│  │                          │  │                             │    │
│  │    ┌───┐                 │  │   🌍 Patients:             │    │
│  │    │   │ PUBLISHED  28   │  │   Kenya      ████████  15  │    │
│  │    │ █ │ SUBMITTED  12   │  │   Uganda     ███████   12  │    │
│  │    │█ █│ FUNDED      5   │  │   Tanzania   ██████    10  │    │
│  │    └───┘                 │  │                             │    │
│  │                          │  │   💝 Donors:               │    │
│  └──────────────────────────┘  │   USA        ██████████ 45  │    │
│                                 │   UK         ██████     22  │    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │            TOP FUNDED PATIENTS                            │     │
│  │  Name         Country   Progress  Raised      Goal        │     │
│  │  John Kamau   Kenya     ████ 83%  $25,000     $30,000     │     │
│  │  Jane Wanjiru Uganda    ███  70%  $21,000     $30,000     │     │
│  │  ...                                                       │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │            TOP DONORS                                     │     │
│  │  Name           Email            Total      Donations     │     │
│  │  Sarah Johnson  sarah@ex...      $15,000    25           │     │
│  │  Mike Chen      mike@exa...      $12,500    18           │     │
│  │  ...                                                      │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │            RECENT DONATIONS                               │     │
│  │  Donor          Patient       Amount   Date      Method   │     │
│  │  Michael Brown  Jane Wanjiru  $500     Jan 15   MPESA    │     │
│  │  Lisa Anderson  John Kamau    $250     Jan 15   CARD     │     │
│  │  ...                                                      │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Implementation

### 1. KPI Cards (Row 1)

```javascript
const KPICard = ({ title, value, subtitle, icon, trend }) => (
  <div className="kpi-card">
    <div className="kpi-icon">{icon}</div>
    <div className="kpi-content">
      <h3>{title}</h3>
      <div className="kpi-value">{value}</div>
      <div className="kpi-subtitle">{subtitle}</div>
      {trend && <div className="kpi-trend">{trend}</div>}
    </div>
  </div>
);

// Usage
const DashboardKPIs = ({ stats }) => (
  <div className="kpi-row">
    <KPICard
      title="Total Users"
      value={stats.total_users}
      subtitle={`${stats.active_users} active`}
      icon="👥"
      trend={`+${stats.new_users_this_month} this month`}
    />
    
    <KPICard
      title="Total Donations"
      value={`$${formatNumber(stats.total_donations_amount)}`}
      subtitle={`${stats.total_donations_count} donations`}
      icon="💰"
      trend={`+$${formatNumber(stats.donations_amount_this_month)} this month`}
    />
    
    <KPICard
      title="Funding Progress"
      value={`${stats.overall_funding_percentage.toFixed(1)}%`}
      subtitle={`$${formatNumber(stats.total_funding_raised)} / $${formatNumber(stats.total_funding_goal)}`}
      icon="📈"
    />
    
    <KPICard
      title="Active Campaigns"
      value={stats.active_campaigns}
      subtitle={`${stats.total_campaigns} total`}
      icon="🎯"
    />
  </div>
);
```

### 2. Recent Activity Panel

```javascript
const ActivityPeriod = ({ period, label, stats }) => (
  <div className="activity-period">
    <h4>{label}</h4>
    <div className="activity-metric">
      <span className="icon">👤</span>
      <span className="value">{period.patients}</span>
      <span className="label">New Patients</span>
    </div>
    <div className="activity-metric">
      <span className="icon">💝</span>
      <span className="value">{period.donors}</span>
      <span className="label">New Donors</span>
    </div>
    <div className="activity-metric">
      <span className="icon">💰</span>
      <span className="value">{period.donations}</span>
      <span className="label">Donations</span>
    </div>
    <div className="activity-metric">
      <span className="icon">💵</span>
      <span className="value">${formatNumber(period.amount)}</span>
      <span className="label">Amount</span>
    </div>
  </div>
);

const RecentActivityPanel = ({ stats }) => (
  <div className="recent-activity-panel">
    <h3>Recent Activity</h3>
    <div className="activity-periods">
      <ActivityPeriod
        label="Today"
        period={{
          patients: stats.new_patients_today,
          donors: stats.new_donors_today,
          donations: stats.donations_today,
          amount: stats.donations_amount_today
        }}
      />
      
      <ActivityPeriod
        label="This Week"
        period={{
          patients: stats.new_patients_this_week,
          donors: stats.new_donors_this_week,
          donations: stats.donations_this_week,
          amount: stats.donations_amount_this_week
        }}
      />
      
      <ActivityPeriod
        label="This Month"
        period={{
          patients: stats.new_patients_this_month,
          donors: stats.new_donors_this_month,
          donations: stats.donations_this_month,
          amount: stats.donations_amount_this_month
        }}
      />
    </div>
  </div>
);
```

### 3. Donation Trend Chart

```javascript
import { Line } from 'react-chartjs-2';

const DonationTrendChart = ({ stats }) => {
  const data = {
    labels: stats.daily_donations_trend.map(d => 
      new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    ),
    datasets: [
      {
        label: 'Donation Amount',
        data: stats.daily_donations_trend.map(d => d.amount),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      },
      {
        label: 'Donation Count',
        data: stats.daily_donations_trend.map(d => d.count),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4,
        fill: true,
        yAxisID: 'y1'
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: { display: true, text: 'Amount ($)' }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: { display: true, text: 'Count' },
        grid: { drawOnChartArea: false }
      }
    }
  };

  return (
    <div className="chart-container">
      <h3>Donation Trends (Last 30 Days)</h3>
      <Line data={data} options={options} height={300} />
    </div>
  );
};
```

### 4. Registration Trend Chart

```javascript
import { Area } from 'recharts';

const RegistrationTrendChart = ({ stats }) => {
  const data = stats.daily_registrations_trend.map(d => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    patients: d.patients,
    donors: d.donors
  }));

  return (
    <div className="chart-container">
      <h3>User Registrations (Last 30 Days)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Area
            type="monotone"
            dataKey="patients"
            stackId="1"
            stroke="#8b5cf6"
            fill="#8b5cf6"
            name="Patients"
          />
          <Area
            type="monotone"
            dataKey="donors"
            stackId="1"
            stroke="#ec4899"
            fill="#ec4899"
            name="Donors"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### 5. Patient Status Pie Chart

```javascript
import { Pie } from 'react-chartjs-2';

const PatientStatusChart = ({ stats }) => {
  const data = {
    labels: Object.keys(stats.patients_by_status),
    datasets: [{
      data: Object.values(stats.patients_by_status),
      backgroundColor: [
        'rgb(59, 130, 246)',   // SUBMITTED - Blue
        'rgb(34, 197, 94)',    // PUBLISHED - Green
        'rgb(234, 179, 8)',    // FULLY_FUNDED - Yellow
        'rgb(239, 68, 68)',    // REJECTED - Red
      ]
    }]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom'
      }
    }
  };

  return (
    <div className="chart-container">
      <h3>Patient Status Distribution</h3>
      <Pie data={data} options={options} height={300} />
    </div>
  );
};
```

### 6. Geographic Distribution

```javascript
const GeographicDistribution = ({ stats }) => {
  const maxPatients = Math.max(...Object.values(stats.patients_by_country));
  const maxDonors = Math.max(...Object.values(stats.donors_by_country));

  return (
    <div className="geo-distribution">
      <h3>Geographic Distribution</h3>
      
      <div className="geo-section">
        <h4>🌍 Patients</h4>
        {Object.entries(stats.patients_by_country)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 5)
          .map(([country, count]) => (
            <div key={country} className="geo-bar">
              <span className="country-name">{country}</span>
              <div className="bar-container">
                <div 
                  className="bar" 
                  style={{ width: `${(count / maxPatients) * 100}%` }}
                />
              </div>
              <span className="count">{count}</span>
            </div>
          ))
        }
      </div>
      
      <div className="geo-section">
        <h4>💝 Donors</h4>
        {Object.entries(stats.donors_by_country)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 5)
          .map(([country, count]) => (
            <div key={country} className="geo-bar">
              <span className="country-name">{country}</span>
              <div className="bar-container">
                <div 
                  className="bar" 
                  style={{ width: `${(count / maxDonors) * 100}%` }}
                />
              </div>
              <span className="count">{count}</span>
            </div>
          ))
        }
      </div>
    </div>
  );
};
```

### 7. Top Funded Patients Table

```javascript
const TopFundedPatientsTable = ({ stats }) => (
  <div className="data-table">
    <h3>Top Funded Patients</h3>
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Country</th>
          <th>Progress</th>
          <th>Raised</th>
          <th>Goal</th>
        </tr>
      </thead>
      <tbody>
        {stats.top_funded_patients.map(patient => (
          <tr key={patient.id}>
            <td>
              <a href={`/admin/patients/${patient.id}`}>
                {patient.full_name}
              </a>
            </td>
            <td>{patient.country}</td>
            <td>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${patient.funding_percentage}%` }}
                />
                <span>{patient.funding_percentage.toFixed(1)}%</span>
              </div>
            </td>
            <td>${formatNumber(patient.funding_received)}</td>
            <td>${formatNumber(patient.funding_required)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
```

### 8. Top Donors Table

```javascript
const TopDonorsTable = ({ stats }) => (
  <div className="data-table">
    <h3>Top Donors</h3>
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th>Total Donated</th>
          <th>Donations</th>
          <th>Avg. Donation</th>
        </tr>
      </thead>
      <tbody>
        {stats.top_donors.map((donor, index) => (
          <tr key={index}>
            <td>
              <div className="donor-info">
                <span className="donor-avatar">
                  {donor.name.charAt(0)}
                </span>
                {donor.name}
              </div>
            </td>
            <td>{donor.email}</td>
            <td className="amount-cell">
              ${formatNumber(donor.total_donated)}
            </td>
            <td>{donor.donation_count}</td>
            <td className="amount-cell">
              ${formatNumber(donor.total_donated / donor.donation_count)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
```

### 9. Recent Donations Table

```javascript
const RecentDonationsTable = ({ stats }) => (
  <div className="data-table">
    <h3>Recent Donations</h3>
    <table>
      <thead>
        <tr>
          <th>Donor</th>
          <th>Patient</th>
          <th>Amount</th>
          <th>Date</th>
          <th>Method</th>
        </tr>
      </thead>
      <tbody>
        {stats.recent_donations.map(donation => (
          <tr key={donation.id}>
            <td>{donation.donor_name}</td>
            <td>
              <a href={`/patients/${donation.patient_id}`}>
                {donation.patient_name}
              </a>
            </td>
            <td className="amount-cell">
              ${formatNumber(donation.amount)}
            </td>
            <td>
              {new Date(donation.created_at).toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </td>
            <td>
              <span className={`payment-badge ${donation.payment_method.toLowerCase()}`}>
                {donation.payment_method}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
```

### 10. Complete Dashboard Component

```javascript
import React, { useState, useEffect } from 'react';
import { fetchDashboardStats } from './api';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await fetchDashboardStats();
      setStats(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(loadStats, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={loadStats} />;
  }

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h1>Admin Dashboard</h1>
        <div className="header-actions">
          <span className="last-updated">
            Last updated: {lastUpdated?.toLocaleTimeString()}
          </span>
          <button onClick={loadStats} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <DashboardKPIs stats={stats} />

      {/* Recent Activity */}
      <RecentActivityPanel stats={stats} />

      {/* Charts Row */}
      <div className="charts-row">
        <div className="chart-col">
          <DonationTrendChart stats={stats} />
        </div>
        <div className="chart-col">
          <RegistrationTrendChart stats={stats} />
        </div>
      </div>

      {/* Distribution Row */}
      <div className="distribution-row">
        <div className="chart-col">
          <PatientStatusChart stats={stats} />
        </div>
        <div className="chart-col">
          <GeographicDistribution stats={stats} />
        </div>
      </div>

      {/* Tables */}
      <TopFundedPatientsTable stats={stats} />
      <TopDonorsTable stats={stats} />
      <RecentDonationsTable stats={stats} />
    </div>
  );
};

export default AdminDashboard;
```

## Styling Examples

### CSS for KPI Cards

```css
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.kpi-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.2s;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.kpi-icon {
  font-size: 2.5rem;
}

.kpi-value {
  font-size: 2rem;
  font-weight: bold;
  color: #1f2937;
}

.kpi-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
}

.kpi-trend {
  font-size: 0.875rem;
  color: #10b981;
  margin-top: 0.25rem;
}
```

### CSS for Activity Panel

```css
.recent-activity-panel {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.activity-periods {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-top: 1rem;
}

.activity-period {
  border-left: 3px solid #3b82f6;
  padding-left: 1rem;
}

.activity-metric {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.activity-metric .icon {
  font-size: 1.25rem;
}

.activity-metric .value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1f2937;
  min-width: 50px;
}

.activity-metric .label {
  font-size: 0.875rem;
  color: #6b7280;
}
```

## Mobile Responsive Layout

```css
@media (max-width: 768px) {
  .kpi-row {
    grid-template-columns: 1fr;
  }
  
  .activity-periods {
    grid-template-columns: 1fr;
  }
  
  .charts-row,
  .distribution-row {
    grid-template-columns: 1fr;
  }
  
  .data-table {
    overflow-x: auto;
  }
}
```

---

This component mapping provides everything needed to build a complete, production-ready admin dashboard!
