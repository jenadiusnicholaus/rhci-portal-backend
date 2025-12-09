from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from datetime import date
from utils.base_64_serializer_field import Base64AnyFileField

from auth_app.exceptions import (
    EmailAlreadyExistsException, PasswordTooShortException,
    InvalidDateException, InvalidCredentialsException,
    EmailNotVerifiedException, AccountInactiveException
)
from .models import (
    PatientProfile, PatientTimeline, TreatmentCostBreakdown, 
    ExpenseTypeLookup, DonationAmountOption, PatientImage, PatientVideo
)
from donor.models import Donation, DonationReceipt, DonationComment

User = get_user_model()


class PatientImageSerializer(serializers.ModelSerializer):
    """Serializer for patient images"""
    image = Base64AnyFileField(
        allowed_types=['jpg', 'jpeg', 'png'],
        max_file_size=5 * 1024 * 1024,  # 5MB
        required=False
    )
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientImage
        fields = ['id', 'image', 'image_url', 'caption', 'display_order', 'is_primary', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PatientVideoSerializer(serializers.ModelSerializer):
    """Serializer for patient video"""
    youtube_embed_url = serializers.ReadOnlyField()
    
    class Meta:
        model = PatientVideo
        fields = ['id', 'youtube_url', 'youtube_embed_url', 'video_title', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


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


class DonationAmountOptionSerializer(serializers.ModelSerializer):
    """Serializer for donation amount options (read-only for public/donor views)"""
    
    class Meta:
        model = DonationAmountOption
        fields = [
            'id', 'amount', 'display_order', 'is_active', 
            'is_recommended', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DonationAmountOptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating donation amount options (admin only)"""
    
    class Meta:
        model = DonationAmountOption
        fields = ['amount', 'display_order', 'is_active', 'is_recommended']
    
    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
    
    def validate_display_order(self, value):
        """Ensure display order is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Display order cannot be negative")
        return value


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
    from auth_app.serializers import CountryLookupSerializer
    
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
    country = CountryLookupSerializer(source='country_fk', read_only=True)
    photo_url = serializers.SerializerMethodField()
    images = PatientImageSerializer(many=True, read_only=True)
    video = PatientVideoSerializer(read_only=True)
    
    def get_photo_url(self, obj):
        """Return full URL for patient photo"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def to_representation(self, instance):
        """Override to ensure photo field also uses absolute URL"""
        representation = super().to_representation(instance)
        
        # Convert photo field to absolute URL if it exists
        if representation.get('photo'):
            request = self.context.get('request')
            if request:
                representation['photo'] = request.build_absolute_uri(instance.photo.url)
        
        return representation
    
    class Meta:
        model = PatientProfile
        fields = [
            'id', 'user', 'photo', 'photo_url', 'full_name', 'age', 'gender', 'country',
            'short_description', 'long_story', 'medical_partner',
            'diagnosis', 'treatment_needed', 'treatment_date',
            # Media
            'images', 'video',
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
            'cost_breakdowns', 'status', 'created_at', 'updated_at', 'country'
        ]


class PatientRegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=20, required=True)
    gender = serializers.ChoiceField(choices=PatientProfile.GENDER_CHOICES, write_only=True)
    country_id = serializers.IntegerField(write_only=True, required=False, allow_null=True, help_text="ID of country from CountryLookup")
    country = serializers.CharField(write_only=True, required=False, allow_null=True, help_text="Country name (alternative to country_id)")
    short_description = serializers.CharField(max_length=255, write_only=True)
    long_story = serializers.CharField(write_only=True)
    date_of_birth = serializers.DateField(write_only=True)
    photo = Base64AnyFileField(
        allowed_types=['jpg', 'jpeg', 'png'],
        max_file_size=5 * 1024 * 1024,  # 5MB
        write_only=True,
        required=False,
        allow_null=True,
        help_text="Primary profile photo (Base64 encoded)"
    )
    images = serializers.ListField(
        child=Base64AnyFileField(
            allowed_types=['jpg', 'jpeg', 'png'],
            max_file_size=5 * 1024 * 1024  # 5MB per image
        ),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="List of additional patient images (Base64 encoded)"
    )
    youtube_url = serializers.URLField(write_only=True, required=False, allow_null=True, allow_blank=True, help_text="YouTube video URL")
    video_title = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True, max_length=255, help_text="Optional video title")
    
    class Meta:
        model = User
        fields = ['email', 'phone_number', 'first_name', 'last_name', 'date_of_birth', 
                  'gender', 'country_id', 'country', 'photo', 'images', 'youtube_url', 'video_title',
                  'short_description', 'long_story']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise EmailAlreadyExistsException()
        return value
    
    def validate_phone_number(self, value):
        if not value or len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate(self, data):
        # Either country_id or country must be provided
        if not data.get('country_id') and not data.get('country'):
            raise serializers.ValidationError({
                'country': 'Either country_id or country name must be provided'
            })
        return data
    
    def validate_date_of_birth(self, value):
        if value > date.today():
            raise InvalidDateException()
        return value
    
    def validate_country_id(self, value):
        from auth_app.lookups import CountryLookup
        if not CountryLookup.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid country ID or country is not active.")
        return value
    
    def create(self, validated_data):
        from auth_app.lookups import CountryLookup
        
        # Extract patient profile fields
        gender = validated_data.pop('gender')
        country_id = validated_data.pop('country_id', None)
        country_name = validated_data.pop('country', None)
        photo = validated_data.pop('photo', None)
        short_description = validated_data.pop('short_description')
        long_story = validated_data.pop('long_story')
        date_of_birth = validated_data.pop('date_of_birth')
        
        # Get or create country lookup object
        if country_id:
            country_lookup = CountryLookup.objects.get(id=country_id)
        elif country_name:
            country_lookup, _ = CountryLookup.objects.get_or_create(
                name=country_name,
                defaults={'code': country_name[:3].upper(), 'display_order': 999}
            )
        else:
            country_lookup = None
        
        # Create user without password (patients register without login initially)
        user = User.objects.create(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            date_of_birth=date_of_birth,
            user_type='PATIENT',
            is_active=True  # Active by default, but not verified
        )
        
        # Build full name from first and last name
        full_name = f"{user.first_name} {user.last_name}".strip()
        
        # Extract images and video data
        images = validated_data.pop('images', [])
        youtube_url = validated_data.pop('youtube_url', None)
        video_title = validated_data.pop('video_title', '')
        
        # Create patient profile
        profile = PatientProfile.objects.create(
            user=user,
            photo=photo,
            full_name=full_name,
            gender=gender,
            country_fk=country_lookup,  # FK field
            short_description=short_description,
            long_story=long_story
        )
        
        # Create patient images if provided
        if images:
            for index, image in enumerate(images):
                PatientImage.objects.create(
                    patient_profile=profile,
                    image=image,
                    display_order=index,
                    is_primary=(index == 0 and not photo)  # First image is primary if no profile photo
                )
        
        # Create patient video if YouTube URL provided
        if youtube_url:
            PatientVideo.objects.create(
                patient_profile=profile,
                youtube_url=youtube_url,
                video_title=video_title or f"{full_name}'s Story"
            )
        
        # TODO: Send verification email here
        return user


# ============ ADMIN SERIALIZERS ============

class AdminPatientReviewSerializer(serializers.ModelSerializer):
    """
    Admin-only serializer for reviewing and editing patient profiles.
    Allows admin to edit medical details, funding, and story.
    """
    from auth_app.serializers import CountryLookupSerializer
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_verified = serializers.BooleanField(source='user.is_verified', read_only=True)
    patient_verified = serializers.BooleanField(source='user.is_patient_verified', read_only=True)
    age = serializers.ReadOnlyField()
    funding_percentage = serializers.ReadOnlyField()
    funding_remaining = serializers.ReadOnlyField()
    cost_breakdowns = TreatmentCostBreakdownSerializer(many=True, read_only=True)
    timeline_events = PatientTimelineSerializer(many=True, read_only=True)
    country = CountryLookupSerializer(source='country_fk', read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    def get_photo_url(self, obj):
        """Return full URL for patient photo"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    class Meta:
        model = PatientProfile
        fields = [
            'id', 'user', 'user_email', 'user_verified', 'patient_verified',
            'photo', 'photo_url', 'full_name', 'age', 'gender', 'country',
            'short_description', 'long_story', 'medical_partner',
            'diagnosis', 'treatment_needed', 'treatment_date',
            'funding_required', 'funding_received', 'total_treatment_cost',
            'funding_percentage', 'funding_remaining',
            'cost_breakdowns', 'cost_breakdown_notes',
            'timeline_events', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'age', 'funding_percentage', 'funding_remaining', 
                           'cost_breakdowns', 'timeline_events', 'created_at', 'updated_at', 'country']


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


class PatientActivationSerializer(serializers.Serializer):
    """
    Serializer for activating/deactivating patient accounts.
    """
    is_active = serializers.BooleanField(
        help_text="True to activate, False to deactivate"
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional reason for deactivation"
    )


class AdminPatientPublishSerializer(serializers.Serializer):
    """
    Serializer for admin to publish patient profiles.
    """
    publish = serializers.BooleanField(default=True)
    featured = serializers.BooleanField(default=False, required=False)


class AdminPatientManagementSerializer(serializers.ModelSerializer):
    """
    Comprehensive admin serializer for full patient management CRUD operations.
    Includes all fields and allows admin to manage patient profiles completely.
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_date_of_birth = serializers.DateField(source='user.date_of_birth', read_only=True)
    user_is_verified = serializers.BooleanField(source='user.is_verified', read_only=True)
    user_is_patient_verified = serializers.BooleanField(source='user.is_patient_verified', read_only=True)
    country_name = serializers.CharField(source='country_fk.name', read_only=True)
    age = serializers.ReadOnlyField()
    funding_percentage = serializers.ReadOnlyField()
    funding_remaining = serializers.ReadOnlyField()
    photo_url = serializers.SerializerMethodField()
    
    # Admin-specific fields for management
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    created_by_admin = serializers.SerializerMethodField()
    last_updated_by = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientProfile
        fields = [
            'id', 'user_id', 'user_email', 'user_date_of_birth', 'user_is_verified', 'user_is_patient_verified',
            'photo', 'photo_url', 'full_name', 'gender', 'country_fk', 'country_name', 'age',
            'short_description', 'long_story',
            'medical_partner', 'diagnosis', 'treatment_needed', 'treatment_date',
            'funding_required', 'funding_received', 'total_treatment_cost', 'cost_breakdown_notes',
            'funding_percentage', 'funding_remaining',
            'status', 'is_featured', 'rejection_reason',
            'created_by_admin', 'last_updated_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'user_email', 'created_at', 'updated_at']
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
        return None
    
    def get_created_by_admin(self, obj):
        # This would need to be tracked if we add a created_by field
        return "System"
    
    def get_last_updated_by(self, obj):
        # This would need to be tracked if we add an updated_by field
        return "Admin"


class AdminPatientCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for admin to create new patient profiles.
    """
    user_email = serializers.EmailField(write_only=True)
    user_first_name = serializers.CharField(write_only=True, max_length=150)
    user_last_name = serializers.CharField(write_only=True, max_length=150)
    user_date_of_birth = serializers.DateField(write_only=True, required=False)
    
    class Meta:
        model = PatientProfile
        fields = [
            'user_email', 'user_first_name', 'user_last_name', 'user_date_of_birth',
            'photo', 'full_name', 'gender', 'country_fk',
            'short_description', 'long_story',
            'medical_partner', 'diagnosis', 'treatment_needed', 'treatment_date',
            'funding_required', 'funding_received', 'total_treatment_cost', 'cost_breakdown_notes',
            'status', 'is_featured'
        ]
    
    def create(self, validated_data):
        # Extract user data
        user_data = {
            'email': validated_data.pop('user_email'),
            'first_name': validated_data.pop('user_first_name'),
            'last_name': validated_data.pop('user_last_name'),
            'user_type': 'PATIENT',
            'is_active': True,
            'is_verified': True,
            'is_patient_verified': True
        }
        
        if 'user_date_of_birth' in validated_data:
            user_data['date_of_birth'] = validated_data.pop('user_date_of_birth')
        
        # Create user
        from auth_app.models import CustomUser
        user = CustomUser.objects.create_user(**user_data)
        
        # Create patient profile
        validated_data['user'] = user
        return PatientProfile.objects.create(**validated_data)


class AdminPatientBulkActionSerializer(serializers.Serializer):
    """
    Serializer for bulk actions on patient profiles.
    """
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('publish', 'Publish'),
        ('unpublish', 'Unpublish'),
        ('feature', 'Feature'),
        ('unfeature', 'Unfeature'),
        ('delete', 'Delete'),
    ]
    
    patient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of patient profile IDs"
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    reason = serializers.CharField(required=False, help_text="Required for reject action")
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('reason'):
            raise serializers.ValidationError({
                'reason': 'Reason is required when rejecting patients.'
            })
        return data


class AdminPatientStatsSerializer(serializers.Serializer):
    """
    Serializer for patient statistics for admin dashboard.
    """
    total_patients = serializers.IntegerField(read_only=True)
    submitted_patients = serializers.IntegerField(read_only=True)
    published_patients = serializers.IntegerField(read_only=True)
    fully_funded_patients = serializers.IntegerField(read_only=True)
    featured_patients = serializers.IntegerField(read_only=True)
    total_funding_required = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_funding_received = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    average_funding_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    patients_by_country = serializers.DictField(read_only=True)
    patients_by_status = serializers.DictField(read_only=True)
    recent_submissions = serializers.IntegerField(read_only=True, help_text="Last 30 days")


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


class AdminPatientFeaturedSerializer(serializers.Serializer):
    """
    Serializer for updating patient featured status (admin only).
    """
    is_featured = serializers.BooleanField(
        required=True,
        help_text="Set to true to feature patient on homepage, false to unfeature"
    )
    
    def validate_is_featured(self, value):
        """
        Validate that we're not featuring more than a reasonable number of patients.
        """
        if value:
            # Check current featured count
            from .models import PatientProfile
            current_featured = PatientProfile.objects.filter(is_featured=True).count()
            
            # Get the patient we're updating (if it's not already featured)
            patient_id = self.context.get('patient_id')
            if patient_id:
                try:
                    patient = PatientProfile.objects.get(id=patient_id)
                    if not patient.is_featured and current_featured >= 10:
                        raise serializers.ValidationError(
                            f"Cannot feature more than 10 patients. Currently {current_featured} patients are featured."
                        )
                except PatientProfile.DoesNotExist:
                    pass
        return value


# ============ DONATION SERIALIZERS ============

class DonationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new donation (both anonymous and authenticated)
    """
    # Donor information (for anonymous donations)
    is_anonymous = serializers.BooleanField(default=False)
    anonymous_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    anonymous_email = serializers.EmailField(required=False, allow_blank=True)
    
    # Patient selection (optional)
    patient_id = serializers.IntegerField(required=False, allow_null=True, help_text="Specific patient to donate to, or null for general donation")
    
    # Donation details
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1.00)
    donation_type = serializers.ChoiceField(
        choices=[('ONE_TIME', 'One-time Donation'), ('MONTHLY', 'Monthly Recurring')],
        default='ONE_TIME'
    )
    
    # Optional fields
    message = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    dedication = serializers.CharField(required=False, allow_blank=True, max_length=200)
    
    # Payment information (will be added by payment processor)
    payment_method = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate donation data"""
        # If anonymous, require either name or email
        if data.get('is_anonymous', False):
            if not data.get('anonymous_name') and not data.get('anonymous_email'):
                raise serializers.ValidationError(
                    "Anonymous donations require either a name or email address"
                )
        
        # If patient_id provided, verify patient exists
        if data.get('patient_id'):
            from .models import PatientProfile
            if not PatientProfile.objects.filter(id=data['patient_id']).exists():
                raise serializers.ValidationError({"patient_id": "Patient not found"})
        
        return data
    
    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Donation amount must be greater than 0")
        return value


class DonationSerializer(serializers.ModelSerializer):
    """
    Serializer for donation details (read-only)
    """
    donor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    donation_type_display = serializers.CharField(source='get_donation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_recurring = serializers.ReadOnlyField()
    total_recurring_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = Donation
        fields = [
            'id', 'donor', 'donor_name', 'is_anonymous',
            'patient', 'patient_name',
            'amount', 'donation_type', 'donation_type_display',
            'status', 'status_display',
            'message', 'dedication',
            'payment_method', 'transaction_id',
            'is_recurring', 'is_recurring_active', 'total_recurring_amount',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']
    
    def get_donor_name(self, obj):
        return obj.get_donor_display_name()
    
    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else "General Fund"


class DonationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed donation serializer with all information (admin use)
    """
    donor_name = serializers.SerializerMethodField()
    donor_email = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    donation_type_display = serializers.CharField(source='get_donation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_recurring = serializers.ReadOnlyField()
    total_recurring_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    
    def get_donor_name(self, obj):
        return obj.get_donor_display_name()
    
    def get_donor_email(self, obj):
        if obj.donor:
            return obj.donor.email
        return obj.anonymous_email
    
    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else "General Fund"


class DonationReceiptSerializer(serializers.ModelSerializer):
    """Serializer for donation receipts"""
    donation_details = DonationSerializer(source='donation', read_only=True)
    
    class Meta:
        model = DonationReceipt
        fields = ['id', 'receipt_number', 'receipt_url', 'email_sent', 'email_sent_at', 'created_at', 'donation_details']
        read_only_fields = ['id', 'created_at']
