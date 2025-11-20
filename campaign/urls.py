from django.urls import path
from .views import (
    # Public Campaign Views
    PublicCampaignListView,
    PublicCampaignDetailView,
    # Campaign Launcher Views
    MyCampaignsView,
    CreateCampaignView,
    UpdateCampaignView,
    SubmitCampaignForReviewView,
    UploadCampaignPhotoView,
    PostCampaignUpdateView,
    # Admin Campaign Views
    AdminCampaignListView,
    AdminCampaignDetailView,
    AdminApproveCampaignView,
    AdminRejectCampaignView,
    AdminActivateCampaignView,
    # Admin Payment Method Views
    AdminPaymentMethodListCreateView,
    AdminPaymentMethodDetailView,
)

app_name = 'campaign'

urlpatterns = [
    # ============ PUBLIC CAMPAIGN VIEWS ============
    path('public/', PublicCampaignListView.as_view(), name='public_campaign_list'),
    path('public/<int:id>/', PublicCampaignDetailView.as_view(), name='public_campaign_detail'),
    
    # ============ CAMPAIGN LAUNCHER VIEWS ============
    path('my-campaigns/', MyCampaignsView.as_view(), name='my_campaigns'),
    path('create/', CreateCampaignView.as_view(), name='create_campaign'),
    path('<int:id>/update/', UpdateCampaignView.as_view(), name='update_campaign'),
    path('<int:campaign_id>/submit/', SubmitCampaignForReviewView.as_view(), name='submit_campaign'),
    path('<int:campaign_id>/upload-photo/', UploadCampaignPhotoView.as_view(), name='upload_photo'),
    path('<int:campaign_id>/post-update/', PostCampaignUpdateView.as_view(), name='post_update'),
    
    # ============ ADMIN CAMPAIGN VIEWS ============
    path('admin/', AdminCampaignListView.as_view(), name='admin_campaign_list'),
    path('admin/<int:id>/', AdminCampaignDetailView.as_view(), name='admin_campaign_detail'),
    path('admin/<int:campaign_id>/approve/', AdminApproveCampaignView.as_view(), name='admin_approve_campaign'),
    path('admin/<int:campaign_id>/reject/', AdminRejectCampaignView.as_view(), name='admin_reject_campaign'),
    path('admin/<int:campaign_id>/activate/', AdminActivateCampaignView.as_view(), name='admin_activate_campaign'),
    
    # ============ ADMIN PAYMENT METHOD VIEWS ============
    path('admin/payment-methods/', AdminPaymentMethodListCreateView.as_view(), name='admin_payment_methods'),
    path('admin/payment-methods/<int:id>/', AdminPaymentMethodDetailView.as_view(), name='admin_payment_method_detail'),
]
