from rest_framework import serializers
from django.contrib.auth import authenticate
from datetime import date
from .models import CustomUser
from .lookups import CountryLookup
from patient.models import PatientProfile, ExpenseTypeLookup, TreatmentCostBreakdown, PatientTimeline
from .exceptions import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    EmailNotVerifiedException,
    AccountInactiveException,
    PasswordTooShortException,
    InvalidDateException,
)


class CountryLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryLookup
        fields = ['id', 'name', 'code', 'display_order']


class PatientRegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=20, required=True)
    gender = serializers.ChoiceField(choices=PatientProfile.GENDER_CHOICES, write_only=True)
    country = serializers.CharField(max_length=100, write_only=True)
    short_description = serializers.CharField(max_length=255, write_only=True)
    long_story = serializers.CharField(write_only=True)
    date_of_birth = serializers.DateField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'first_name', 'last_name', 'date_of_birth', 
                  'gender', 'country', 'short_description', 'long_story']
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise EmailAlreadyExistsException()
        return value
    
    def validate_phone_number(self, value):
        # Basic validation - ensure it's not empty and has reasonable length
        if not value or len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate_date_of_birth(self, value):
        if value > date.today():
            raise InvalidDateException()
        return value
    
    def create(self, validated_data):
        # Extract profile-specific fields
        gender = validated_data.pop('gender')
        country_name = validated_data.pop('country')
        short_description = validated_data.pop('short_description')
        long_story = validated_data.pop('long_story')
        
        # Create user without password (patient accounts don't need login initially)
        user = CustomUser.objects.create(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            date_of_birth=validated_data['date_of_birth'],
            user_type='PATIENT',
            is_active=True  # Active by default, but not verified
        )
        
        # Get or create country lookup
        country_fk = None
        if country_name:
            country_fk, _ = CountryLookup.objects.get_or_create(
                name=country_name,
                defaults={'code': country_name[:3].upper(), 'display_order': 999}
            )
        
        # Create patient profile with registration data
        PatientProfile.objects.create(
            user=user,
            full_name=f"{user.first_name} {user.last_name}".strip(),
            gender=gender,
            country_fk=country_fk,
            short_description=short_description,
            long_story=long_story,
            # Medical details filled by admin during verification
            diagnosis='',
            treatment_needed='',
            funding_required=0.00,
            total_treatment_cost=0.00,
            status='SUBMITTED'
        )
        
        # TODO: Send verification email here
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise InvalidCredentialsException()
        if not user.is_active:
            raise AccountInactiveException()
        # Allow login even if email not verified
        # Frontend can check user.is_verified and show verification prompt
        return {'user': user}


class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'phone_number', 'user_type', 'first_name', 'last_name', 
                  'is_verified', 'is_patient_verified', 'date_joined', 'profile_picture_url']
        read_only_fields = ['email', 'user_type', 'is_verified', 'date_joined']
    
    def get_profile_picture_url(self, obj):
        """Return profile picture URL based on user type"""
        request = self.context.get('request')
        
        # For users with direct profile_picture field
        if obj.profile_picture:
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        
        # For donors, get photo from DonorProfile
        if obj.user_type == 'DONOR':
            try:
                from donor.models import DonorProfile
                donor_profile = DonorProfile.objects.filter(user=obj).first()
                if donor_profile and donor_profile.photo:
                    if request:
                        return request.build_absolute_uri(donor_profile.photo.url)
                    return donor_profile.photo.url
            except:
                pass
        
        # For patients, get photo from PatientProfile
        elif obj.user_type == 'PATIENT':
            try:
                from patient.models import PatientProfile
                patient_profile = PatientProfile.objects.filter(user=obj).first()
                if patient_profile and patient_profile.photo:
                    if request:
                        return request.build_absolute_uri(patient_profile.photo.url)
                    return patient_profile.photo.url
            except:
                pass
        
        return None


class ExpenseTypeLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseTypeLookup
        fields = ['id', 'name', 'slug', 'description', 'display_order']


class TreatmentCostBreakdownSerializer(serializers.ModelSerializer):
    expense_type_name = serializers.CharField(source='expense_type.name', read_only=True)
    expense_type_slug = serializers.CharField(source='expense_type.slug', read_only=True)
    
    class Meta:
        model = TreatmentCostBreakdown
        fields = ['id', 'expense_type', 'expense_type_name', 'expense_type_slug', 'amount', 'notes', 'created_at']
        read_only_fields = ['created_at']


class PatientTimelineSerializer(serializers.ModelSerializer):
    formatted_date = serializers.ReadOnlyField()
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    is_future = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientTimeline
        fields = [
            'id', 'event_type', 'event_type_display', 'title', 'description',
            'created_by', 'created_by_name', 'metadata', 'is_milestone', 
            'is_visible', 'formatted_date', 'created_at', 'is_future'
        ]
        read_only_fields = ['id', 'created_at', 'formatted_date', 'is_future']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return None


class PatientProfileSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    funding_percentage = serializers.ReadOnlyField()
    funding_remaining = serializers.ReadOnlyField()
    funding_percentage_display = serializers.ReadOnlyField()
    funding_raised_display = serializers.ReadOnlyField()
    funding_remaining_display = serializers.ReadOnlyField()
    funding_summary = serializers.ReadOnlyField()
    cost_breakdown_total = serializers.ReadOnlyField()
    other_contributions = serializers.ReadOnlyField()
    cost_breakdowns = TreatmentCostBreakdownSerializer(many=True, read_only=True)
    timeline_events = PatientTimelineSerializer(many=True, read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = [
            'id', 'user', 'full_name', 'age', 'gender', 'country',
            'short_description', 'long_story', 'medical_partner',
            'diagnosis', 'treatment_needed', 'treatment_date',
            # Funding summary
            'funding_required', 'funding_received', 'total_treatment_cost',
            'funding_percentage', 'funding_remaining', 'other_contributions',
            # Funding display fields
            'funding_percentage_display', 'funding_raised_display', 
            'funding_remaining_display', 'funding_summary',
            # Cost breakdown (dynamic items)
            'cost_breakdowns', 'cost_breakdown_notes', 'cost_breakdown_total',
            # Timeline
            'timeline_events',
            # Status & timestamps
            'status', 'created_at', 'updated_at'
        ]
        # Patients can update basic info and story, admin updates medical/funding via Django admin
        read_only_fields = [
            'user', 'age', 'medical_partner',
            'diagnosis', 'treatment_needed', 'treatment_date',
            'funding_required', 'funding_received', 'total_treatment_cost',
            'cost_breakdowns', 'status', 'created_at', 'updated_at'
        ]


# ============ ADMIN SERIALIZERS ============

class AdminPatientReviewSerializer(serializers.ModelSerializer):
    """
    Admin-only serializer for reviewing and editing patient profiles.
    Allows admin to edit medical details, funding, and story.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_verified = serializers.BooleanField(source='user.is_verified', read_only=True)
    patient_verified = serializers.BooleanField(source='user.is_patient_verified', read_only=True)
    age = serializers.ReadOnlyField()
    funding_percentage = serializers.ReadOnlyField()
    funding_remaining = serializers.ReadOnlyField()
    cost_breakdowns = TreatmentCostBreakdownSerializer(many=True, read_only=True)
    timeline_events = PatientTimelineSerializer(many=True, read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = [
            'id', 'user', 'user_email', 'user_verified', 'patient_verified',
            'full_name', 'age', 'gender', 'country',
            'short_description', 'long_story', 'medical_partner',
            'diagnosis', 'treatment_needed', 'treatment_date',
            'funding_required', 'funding_received', 'total_treatment_cost',
            'funding_percentage', 'funding_remaining',
            'cost_breakdowns', 'cost_breakdown_notes',
            'timeline_events', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'age', 'funding_percentage', 'funding_remaining', 
                           'cost_breakdowns', 'timeline_events', 'created_at', 'updated_at']


class AdminPatientApprovalSerializer(serializers.Serializer):
    """
    Serializer for admin to approve or reject patient profiles.
    """
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a profile.'
            })
        return data


class AdminPatientPublishSerializer(serializers.Serializer):
    """
    Serializer for admin to publish patient profiles.
    """
    publish = serializers.BooleanField(default=True)
    featured = serializers.BooleanField(default=False, required=False)


class AdminTimelineEventSerializer(serializers.ModelSerializer):
    """
    Admin serializer for creating and managing timeline events.
    Allows admin to add/edit/remove events and mark current state.
    """
    formatted_date = serializers.ReadOnlyField()
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientTimeline
        fields = [
            'id', 'patient_profile', 'event_type', 'event_type_display',
            'title', 'description', 'event_date', 'created_by', 'created_by_name',
            'metadata', 'is_milestone', 'is_visible', 'is_current_state',
            'formatted_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'formatted_date', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return None
    
    def validate_event_date(self, value):
        """Allow TBD events (future dates) for admin."""
        return value


class AdminBulkTimelineCreateSerializer(serializers.Serializer):
    """
    Serializer for creating multiple timeline events at once.
    """
    patient_profile_id = serializers.IntegerField()
    events = AdminTimelineEventSerializer(many=True)


class FinancialReportSerializer(serializers.ModelSerializer):
    """
    Serializer for financial reports with base64 document upload.
    """
    from utils.base_64_serializer_field import Base64AnyFileField
    
    document = Base64AnyFileField(
        allowed_types=['pdf', 'xlsx', 'xls', 'doc', 'docx'],
        max_file_size=20 * 1024 * 1024,  # 20MB for financial documents
        required=True
    )
    document_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        from .models import FinancialReport
        model = FinancialReport
        fields = [
            'id', 'title', 'description', 'document', 'document_url',
            'is_public', 'uploaded_by', 'uploaded_by_name',
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'updated_at']
    
    def get_document_url(self, obj):
        """Return full URL for the document"""
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None
    
    def get_uploaded_by_name(self, obj):
        """Return the name of the admin who uploaded"""
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name()
        return None
    
    def validate(self, data):
        """Validate document upload"""
        document = data.get('document')
        if not document:
            raise serializers.ValidationError({'document': 'Financial report document is required'})
        return data
    
    def create(self, validated_data):
        # Set the uploaded_by to the current user
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class PublicFinancialReportSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for public financial report viewing.
    """
    document_url = serializers.SerializerMethodField()
    
    class Meta:
        from .models import FinancialReport
        model = FinancialReport
        fields = ['id', 'title', 'description', 'document_url', 'uploaded_at']
        read_only_fields = ['id', 'title', 'description', 'document_url', 'uploaded_at']
    
    def get_document_url(self, obj):
        """Return full URL for the document"""
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None
