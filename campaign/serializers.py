from rest_framework import serializers
from datetime import date
from .models import PaymentMethod, Campaign, CampaignPhoto, CampaignUpdate
from patient.models import PatientProfile


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for payment methods (read-only for campaign launchers)"""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'account_name', 'account_number', 
            'bank_name', 'swift_code', 'additional_info', 'display_order'
        ]
        read_only_fields = fields


class CampaignPhotoSerializer(serializers.ModelSerializer):
    """Serializer for campaign photos"""
    
    class Meta:
        model = CampaignPhoto
        fields = ['id', 'image', 'caption', 'display_order', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']


class CampaignUpdateSerializer(serializers.ModelSerializer):
    """Serializer for campaign updates"""
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CampaignUpdate
        fields = ['id', 'title', 'content', 'author', 'author_name', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']
    
    def get_author_name(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.email
        return "Unknown"


class CampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating campaigns"""
    photos = CampaignPhotoSerializer(many=True, read_only=True)
    goal_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    patients = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=PatientProfile.objects.filter(status='PUBLISHED'),
        required=False,
        help_text="List of patient IDs (required if is_general_fund is False)"
    )
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'title', 'description', 'goal_amount', 
            'end_date', 'is_general_fund', 'patients', 'photos'
        ]
        read_only_fields = ['id']
    
    def validate_goal_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Goal amount must be greater than 0")
        return value
    
    def validate_end_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("End date cannot be in the past")
        return value
    
    def validate(self, data):
        """Validate campaign data"""
        is_general_fund = data.get('is_general_fund', False)
        patients = data.get('patients', [])
        
        # If not general fund, at least one patient must be selected
        if not is_general_fund and not patients:
            raise serializers.ValidationError({
                'patients': 'Patient-specific campaign must have at least one patient selected.'
            })
        
        # If general fund, patients should be empty
        if is_general_fund and patients:
            raise serializers.ValidationError({
                'patients': 'General fund campaigns cannot have specific patients selected.'
            })
        
        return data


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for campaign details (public view)"""
    launcher_name = serializers.SerializerMethodField()
    launcher_email = serializers.CharField(source='launcher.email', read_only=True)
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    photos = CampaignPhotoSerializer(many=True, read_only=True)
    updates = CampaignUpdateSerializer(many=True, read_only=True)
    goal_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    raised_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    funding_progress = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()
    is_funded = serializers.ReadOnlyField()
    patients = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'launcher', 'launcher_name', 'launcher_email',
            'title', 'description', 'goal_amount', 'raised_amount',
            'funding_progress', 'remaining_amount', 'is_funded',
            'end_date', 'status', 'is_general_fund', 'patients',
            'payment_methods', 'photos', 'updates',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'launcher', 'raised_amount', 'status', 
            'payment_methods', 'created_at', 'updated_at'
        ]
    
    def get_launcher_name(self, obj):
        return obj.launcher.get_full_name() or obj.launcher.email
    
    def get_patients(self, obj):
        """Return patient details for campaign"""
        if obj.is_general_fund:
            return []
        
        patients_data = []
        for patient in obj.patients.all():
            patients_data.append({
                'id': patient.id,
                'full_name': patient.full_name,
                'photo_url': patient.photo.url if patient.photo else None,
                'diagnosis': patient.diagnosis,
                'total_cost_usd': str(patient.total_cost_usd),
                'amount_raised_usd': str(patient.amount_raised_usd)
            })
        return patients_data


class CampaignDetailSerializer(serializers.ModelSerializer):
    """Detailed campaign serializer (for admin)"""
    launcher_name = serializers.SerializerMethodField()
    launcher_email = serializers.CharField(source='launcher.email', read_only=True)
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    photos = CampaignPhotoSerializer(many=True, read_only=True)
    updates = CampaignUpdateSerializer(many=True, read_only=True)
    goal_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    raised_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    funding_progress = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()
    is_funded = serializers.ReadOnlyField()
    approved_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = '__all__'
    
    def get_launcher_name(self, obj):
        return obj.launcher.get_full_name() or obj.launcher.email
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.email
        return None


class AdminPaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for admin to manage payment methods"""
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None
