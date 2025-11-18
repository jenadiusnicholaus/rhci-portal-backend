from django.urls import path
from .views import LoginView, UserProfileView, TokenRefreshView
from donor.views import DonorRegisterView, DonorProfileView
from patient.views import PatientRegisterView, PatientProfileView

urlpatterns = [
    # ============ AUTHENTICATION ============
    path('register/donor/', DonorRegisterView.as_view(), name='donor_register'),
    path('register/patient/', PatientRegisterView.as_view(), name='patient_register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ============ USER PROFILE (AUTHENTICATED) ============
    path('me/', UserProfileView.as_view(), name='user_profile'),
    
    # ============ DONOR PROFILE (AUTHENTICATED) ============
    # Authenticated - own profile management
    path('donor/profile/', DonorProfileView.as_view(), name='donor_profile'),
    
    # ============ PATIENT PROFILE (AUTHENTICATED) ============
    # Patient's own profile management
    path('patient/profile/', PatientProfileView.as_view(), name='patient_profile'),
]
