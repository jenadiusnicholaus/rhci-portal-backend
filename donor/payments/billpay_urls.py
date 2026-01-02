"""
URL Configuration for AzamPay Bill Pay API
"""

from django.urls import path
from . import billpay_views

urlpatterns = [
    # Bill Pay API endpoints (called by AzamPay)
    path('merchant/name-lookup', billpay_views.name_lookup, name='billpay_name_lookup'),
    path('merchant/payment', billpay_views.payment_notification, name='billpay_payment'),
    path('merchant/status-check', billpay_views.status_check, name='billpay_status_check'),
    
    # Public helper endpoint (for frontend)
    path('patients/by-bill/<str:bill_identifier>', billpay_views.get_patient_by_bill_identifier, name='patient_by_bill_identifier'),
]
