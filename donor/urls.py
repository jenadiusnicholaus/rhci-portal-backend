from django.urls import path
from .views import (
    PublicDonorProfileView,
    DonorProfileListView,
    DonationCreateView,
    MyDonationsView,
    DonationDetailView,
    AdminDonationListView,
    AdminDonationDetailView,
    PatientDonationsView,
    MyDonorStatsView,
    # Admin Donor Management
    AdminDonorListView,
    AdminDonorDetailView,
    AdminDonorActivationView,
    AdminDonorStatsView,
    PublicDonorStatsView,
)
from .payments.donation_type_views import (
    # One-time patient donations
    AnonymousOneTimePatientDonationView,
    AuthenticatedOneTimePatientDonationView,
    # Monthly patient donations
    AnonymousMonthlyPatientDonationView,
    AuthenticatedMonthlyPatientDonationView,
    # Organization donations
    AnonymousOrganizationDonationView,
    AuthenticatedOrganizationDonationView,
    AnonymousMonthlyOrganizationDonationView,
    AuthenticatedMonthlyOrganizationDonationView,
)
from .payments.callback_views import (
    AzamPayCallbackView,
    CheckPaymentStatusView,
    ManualPaymentUpdateView,
)

app_name = 'donor'

urlpatterns = [
    # ============ PUBLIC DONOR PROFILES ============
    # Public access - read-only for public donors
    path('public/', DonorProfileListView.as_view(), name='public_donor_list'),
    path('public/<int:id>/', PublicDonorProfileView.as_view(), name='public_donor_detail'),
    path('public/stats/', PublicDonorStatsView.as_view(), name='public_donor_stats'),
    
    # ============ DONATION ENDPOINTS ============
    # 🔴 ONE-TIME PATIENT DONATIONS
    path('donate/azampay/patient/anonymous/', AnonymousOneTimePatientDonationView.as_view(), name='donate_patient_onetime_anonymous'),
    path('donate/azampay/patient/', AuthenticatedOneTimePatientDonationView.as_view(), name='donate_patient_onetime_authenticated'),
    
    # 🔴 MONTHLY RECURRING PATIENT DONATIONS
    path('donate/azampay/patient/monthly/anonymous/', AnonymousMonthlyPatientDonationView.as_view(), name='donate_patient_monthly_anonymous'),
    path('donate/azampay/patient/monthly/', AuthenticatedMonthlyPatientDonationView.as_view(), name='donate_patient_monthly_authenticated'),
    
    # 🔴 ORGANIZATION DONATIONS (One-time)
    path('donate/azampay/organization/anonymous/', AnonymousOrganizationDonationView.as_view(), name='donate_organization_anonymous'),
    path('donate/azampay/organization/', AuthenticatedOrganizationDonationView.as_view(), name='donate_organization_authenticated'),
    
    # 🔴 ORGANIZATION DONATIONS (Monthly)
    path('donate/azampay/organization/monthly/anonymous/', AnonymousMonthlyOrganizationDonationView.as_view(), name='donate_organization_monthly_anonymous'),
    path('donate/azampay/organization/monthly/', AuthenticatedMonthlyOrganizationDonationView.as_view(), name='donate_organization_monthly_authenticated'),
    
    # Future: path('donate/paypal/...', PayPalDonationView.as_view()),
    # Future: path('donate/stripe/...', StripeDonationView.as_view()),
    
    # Public - View patient donations
    path('donations/patient/<int:patient_id>/', PatientDonationsView.as_view(), name='patient_donations'),
    
    # Authenticated - My donations and stats
    path('donations/my-donations/', MyDonationsView.as_view(), name='my_donations'),
    path('donations/<int:id>/', DonationDetailView.as_view(), name='donation_detail'),
    path('my-stats/', MyDonorStatsView.as_view(), name='my_donor_stats'),
    
    # Admin - Donation management
    path('admin/donations/', AdminDonationListView.as_view(), name='admin_donation_list'),
    path('admin/donations/<int:id>/', AdminDonationDetailView.as_view(), name='admin_donation_detail'),
    
    # ============ ADMIN DONOR MANAGEMENT ============
    # Admin - Donor account management
    path('admin/donors/', AdminDonorListView.as_view(), name='admin_donor_list'),
    path('admin/donors/<int:id>/', AdminDonorDetailView.as_view(), name='admin_donor_detail'),
    path('admin/donors/<int:id>/activate/', AdminDonorActivationView.as_view(), name='admin_donor_activation'),
    path('admin/donors/stats/', AdminDonorStatsView.as_view(), name='admin_donor_stats'),
    
    # ============ PAYMENT ENDPOINTS (AZAM PAY) ============
    # Webhook callback (called by Azam Pay when payment completes)
    path('payment/azampay/callback/', AzamPayCallbackView.as_view(), name='azampay_callback'),
    
    # Check payment status by transaction ID
    path('payment/status/', CheckPaymentStatusView.as_view(), name='payment_status'),
    
    # Manual status update (sandbox testing only - disable in production)
    path('payment/manual-update/', ManualPaymentUpdateView.as_view(), name='manual_payment_update'),
]