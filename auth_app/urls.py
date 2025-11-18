from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    DonorRegisterView, PatientRegisterView, LoginView, 
    UserProfileView, DonorProfileView, PatientProfileView,
    PublicDonorProfileView, DonorProfileListView,
    PublicPatientProfileView, PatientProfileListView
)
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

urlpatterns = [
    # ============ AUTHENTICATION ============
    path('register/donor/', DonorRegisterView.as_view(), name='donor_register'),
    path('register/patient/', PatientRegisterView.as_view(), name='patient_register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ============ USER PROFILE (AUTHENTICATED) ============
    path('me/', UserProfileView.as_view(), name='user_profile'),
    
    # ============ DONOR PROFILES ============
    # Authenticated - own profile management
    path('donor/profile/', DonorProfileView.as_view(), name='donor_profile'),
    # Public access - read-only
    path('donors/', DonorProfileListView.as_view(), name='donor_list'),
    path('donors/<int:id>/', PublicDonorProfileView.as_view(), name='donor_public_profile'),
    
    # ============ PATIENT PROFILES (AUTHENTICATED) ============
    # Patient's own profile management
    path('patient/profile/', PatientProfileView.as_view(), name='patient_profile'),
    
    # ============ ADMIN PATIENT MANAGEMENT ============
    # Admin review and management
    path('admin/patients/', AdminPatientListView.as_view(), name='admin_patient_list'),
    path('admin/patients/<int:id>/', AdminPatientDetailView.as_view(), name='admin_patient_detail'),
    path('admin/patients/<int:id>/approve/', AdminPatientApprovalView.as_view(), name='admin_patient_approval'),
    path('admin/patients/<int:id>/publish/', AdminPatientPublishView.as_view(), name='admin_patient_publish'),
    
    # ============ ADMIN TIMELINE MANAGEMENT ============
    path('admin/patients/<int:patient_id>/timeline/', AdminTimelineEventListView.as_view(), name='admin_timeline_list'),
    path('admin/timeline/create/', AdminTimelineEventCreateView.as_view(), name='admin_timeline_create'),
    path('admin/timeline/<int:id>/update/', AdminTimelineEventUpdateView.as_view(), name='admin_timeline_update'),
    path('admin/timeline/<int:id>/delete/', AdminTimelineEventDeleteView.as_view(), name='admin_timeline_delete'),
    
    # ============ PUBLIC PATIENT PROFILES ============
    # Public access - read-only for published patients
    path('public/patients/', PublicPatientListView.as_view(), name='public_patient_list'),
    path('public/patients/<int:id>/', PublicPatientDetailView.as_view(), name='public_patient_detail'),
    path('public/patients/featured/', PublicFeaturedPatientsView.as_view(), name='public_featured_patients'),
]
