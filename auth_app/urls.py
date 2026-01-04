from django.urls import path
from .views import (
    LoginView, UserProfileView, CountryLookupListView, ExpenseTypeLookupListView,
    AdminExpenseTypeListCreateView, AdminExpenseTypeDetailView
)
from .admin_views import (
    AdminFinancialReportListCreateView,
    AdminFinancialReportDetailView,
    PublicFinancialReportView
)
from donor.views import (
    DonorRegisterView, DonorProfileView,
    DonorEmailVerificationView, DonorResendVerificationView
)
from patient.views import PatientRegisterView, PatientProfileView, RandomizedPatientListView

urlpatterns = [
    # ============ AUTHENTICATION ============
    path('login/', LoginView.as_view(), name='login'),
    
    # ============ REGISTRATION ============
    path('register/donor/', DonorRegisterView.as_view(), name='donor_register'),
    path('register/patient/', PatientRegisterView.as_view(), name='patient_register'),
    
    # ============ EMAIL VERIFICATION ============
    path('donor/verify-email/', DonorEmailVerificationView.as_view(), name='donor_verify_email'),
    path('donor/resend-verification/', DonorResendVerificationView.as_view(), name='donor_resend_verification'),
    
    # ============ USER PROFILE (AUTHENTICATED) ============
    path('me/', UserProfileView.as_view(), name='user_profile'),
    
    # ============ DONOR PROFILE (AUTHENTICATED) ============
    # Authenticated - own profile management
    path('donor/profile/', DonorProfileView.as_view(), name='donor_profile'),
    
    # ============ PATIENT PROFILE (AUTHENTICATED) ============
    # Patient's own profile management
    path('patient/profile/', PatientProfileView.as_view(), name='patient_profile'),
    
    # ============ PUBLIC PATIENT DISCOVERY ============
    # AI-powered randomized patient discovery (no auth required)
    path('patients/discover/', RandomizedPatientListView.as_view(), name='randomized_patient_list'),
    
    # ============ LOOKUPS ============
    path('lookups/countries/', CountryLookupListView.as_view(), name='country_lookup'),
    path('lookups/expense-types/', ExpenseTypeLookupListView.as_view(), name='expense_type_lookup'),
    
    # ============ ADMIN EXPENSE TYPE MANAGEMENT ============
    path('admin/expense-types/', AdminExpenseTypeListCreateView.as_view(), name='admin_expense_type_list_create'),
    path('admin/expense-types/<int:id>/', AdminExpenseTypeDetailView.as_view(), name='admin_expense_type_detail'),
    
    # ============ ADMIN FINANCIAL REPORTS ============
    path('admin/financial-reports/', AdminFinancialReportListCreateView.as_view(), name='admin_financial_report_list_create'),
    path('admin/financial-reports/<int:pk>/', AdminFinancialReportDetailView.as_view(), name='admin_financial_report_detail'),
    
    # ============ PUBLIC FINANCIAL TRANSPARENCY ============
    path('financial-report/public/', PublicFinancialReportView.as_view(), name='public_financial_report'),
]
