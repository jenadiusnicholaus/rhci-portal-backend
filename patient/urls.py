from django.urls import path
from .admin_views import (
    # Admin Patient Management
    AdminPatientListView,
    AdminPatientDetailView,
    AdminPatientApprovalView,
    AdminPatientPublishView,
    # Admin Timeline Management
    AdminTimelineEventCreateView,
    AdminTimelineEventUpdateView,
    AdminTimelineEventDeleteView,
    AdminTimelineEventListView,
    # Public Patient Views
    PublicPatientDetailView,
    PublicPatientListView,
    PublicFeaturedPatientsView,
)
from .donation_views import (
    # Public Donation Amount Views
    PatientDonationAmountsView,
    # Admin Donation Amount Management
    AdminDonationAmountListCreateView,
    AdminDonationAmountDetailView,
    AdminBulkCreateDonationAmountsView,
)

app_name = 'patient'

urlpatterns = [
    # ============ ADMIN PATIENT MANAGEMENT ============
    # Admin review and management
    path('admin/', AdminPatientListView.as_view(), name='admin_patient_list'),
    path('admin/<int:id>/', AdminPatientDetailView.as_view(), name='admin_patient_detail'),
    path('admin/<int:id>/approve/', AdminPatientApprovalView.as_view(), name='admin_patient_approval'),
    path('admin/<int:id>/publish/', AdminPatientPublishView.as_view(), name='admin_patient_publish'),
    
    # ============ ADMIN DONATION AMOUNT MANAGEMENT ============
    path('admin/<int:patient_id>/donation-amounts/', AdminDonationAmountListCreateView.as_view(), name='admin_donation_amounts'),
    path('admin/<int:patient_id>/donation-amounts/<int:id>/', AdminDonationAmountDetailView.as_view(), name='admin_donation_amount_detail'),
    path('admin/<int:patient_id>/donation-amounts/bulk-create/', AdminBulkCreateDonationAmountsView.as_view(), name='admin_donation_amounts_bulk_create'),
    
    # ============ ADMIN TIMELINE MANAGEMENT ============
    path('admin/<int:patient_id>/timeline/', AdminTimelineEventListView.as_view(), name='admin_timeline_list'),
    path('admin/timeline/create/', AdminTimelineEventCreateView.as_view(), name='admin_timeline_create'),
    path('admin/timeline/<int:id>/update/', AdminTimelineEventUpdateView.as_view(), name='admin_timeline_update'),
    path('admin/timeline/<int:id>/delete/', AdminTimelineEventDeleteView.as_view(), name='admin_timeline_delete'),
    
    # ============ PUBLIC PATIENT PROFILES ============
    # Public access - read-only for published patients
    path('public/', PublicPatientListView.as_view(), name='public_patient_list'),
    path('public/<int:id>/', PublicPatientDetailView.as_view(), name='public_patient_detail'),
    path('public/featured/', PublicFeaturedPatientsView.as_view(), name='public_featured_patients'),
    
    # ============ PUBLIC DONATION AMOUNTS ============
    # Public access - for donors to see suggested amounts during donation
    path('public/<int:patient_id>/donation-amounts/', PatientDonationAmountsView.as_view(), name='public_donation_amounts'),
]
