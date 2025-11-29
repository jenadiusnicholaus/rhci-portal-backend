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
    # Admin Donor Management
    AdminDonorListView,
    AdminDonorDetailView,
    AdminDonorActivationView,
    AdminDonorStatsView,
)
from .payment_views import (
    AzamPayMobileMoneyCheckoutView,
    AzamPayBankCheckoutView,
    AzamPayCallbackView,
    CheckPaymentStatusView,
)

app_name = 'donor'

urlpatterns = [
    # ============ PUBLIC DONOR PROFILES ============
    # Public access - read-only for public donors
    path('public/', DonorProfileListView.as_view(), name='public_donor_list'),
    path('public/<int:id>/', PublicDonorProfileView.as_view(), name='public_donor_detail'),
    
    # ============ DONATION ENDPOINTS ============
    # Public - Create donation (anonymous or authenticated)
    path('donations/create/', DonationCreateView.as_view(), name='donation_create'),
    
    # Public - View patient donations
    path('donations/patient/<int:patient_id>/', PatientDonationsView.as_view(), name='patient_donations'),
    
    # Authenticated - My donations
    path('donations/my-donations/', MyDonationsView.as_view(), name='my_donations'),
    path('donations/<int:id>/', DonationDetailView.as_view(), name='donation_detail'),
    
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
    # Mobile money payment
    path('payment/azampay/mobile-money/', AzamPayMobileMoneyCheckoutView.as_view(), name='azampay_mobile_checkout'),
    
    # Bank payment
    path('payment/azampay/bank/', AzamPayBankCheckoutView.as_view(), name='azampay_bank_checkout'),
    
    # Webhook callback (called by Azam Pay)
    path('payment/azampay/callback/', AzamPayCallbackView.as_view(), name='azampay_callback'),
    
    # Check payment status
    path('payment/status/', CheckPaymentStatusView.as_view(), name='payment_status'),
]