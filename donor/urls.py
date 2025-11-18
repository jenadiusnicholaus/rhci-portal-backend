from django.urls import path
from .views import (
    PublicDonorProfileView,
    DonorProfileListView
)

app_name = 'donor'

urlpatterns = [
    # ============ PUBLIC DONOR PROFILES ============
    # Public access - read-only for public donors
    path('public/', DonorProfileListView.as_view(), name='public_donor_list'),
    path('public/<int:id>/', PublicDonorProfileView.as_view(), name='public_donor_detail'),
]