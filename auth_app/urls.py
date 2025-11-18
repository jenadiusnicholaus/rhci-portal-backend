from django.urls import path
from .views import LoginView, UserProfileView, CountryLookupListView, ExpenseTypeLookupListView
from donor.views import DonorRegisterView, DonorProfileView
from patient.views import PatientRegisterView, PatientProfileView

urlpatterns = [
    # ============ AUTHENTICATION ============
    path('login/', LoginView.as_view(), name='login'),
    
    # ============ REGISTRATION ============
    path('register/donor/', DonorRegisterView.as_view(), name='donor_register'),
    path('register/patient/', PatientRegisterView.as_view(), name='patient_register'),
    
    # ============ USER PROFILE (AUTHENTICATED) ============
    path('me/', UserProfileView.as_view(), name='user_profile'),
    
    # ============ DONOR PROFILE (AUTHENTICATED) ============
    # Authenticated - own profile management
    path('donor/profile/', DonorProfileView.as_view(), name='donor_profile'),
    
    # ============ PATIENT PROFILE (AUTHENTICATED) ============
    # Patient's own profile management
    path('patient/profile/', PatientProfileView.as_view(), name='patient_profile'),
    
    # ============ LOOKUPS ============
    path('lookups/countries/', CountryLookupListView.as_view(), name='country_lookup'),
    path('lookups/expense-types/', ExpenseTypeLookupListView.as_view(), name='expense_type_lookup'),
]
