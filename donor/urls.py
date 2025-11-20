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
]