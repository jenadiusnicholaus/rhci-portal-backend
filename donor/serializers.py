from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import date
from django.utils import timezone

from auth_app.exceptions import (
    EmailAlreadyExistsException, PasswordTooShortException,
    InvalidDateException, FileSizeTooLargeException,
    InvalidFileTypeException
)
from .models import DonorProfile
from utils.email_verification import generate_verification_token, create_verification_token_hash

User = get_user_model()


class DonorProfileSerializer(serializers.ModelSerializer):
    from auth_app.serializers import CountryLookupSerializer
    
    age = serializers.ReadOnlyField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    country = CountryLookupSerializer(source='country_fk', read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    def get_photo_url(self, obj):
        """Return full URL for donor photo"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    class Meta:
        model = DonorProfile
        fields = [
            'id', 'user', 'user_email', 'photo', 'photo_url', 'full_name', 'short_bio',
            'country', 'website', 'birthday', 'age', 'workplace',
            'is_profile_private', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'age', 'created_at', 'updated_at', 'country']
    
    def validate_photo(self, value):
        if value:
            # Check file size (5MB limit)
            if value.size > 5 * 1024 * 1024:
                raise FileSizeTooLargeException()
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if value.content_type not in allowed_types:
                raise InvalidFileTypeException()
        
        return value
    
    def validate_birthday(self, value):
        if value and value > date.today():
            raise InvalidDateException()
        return value


class PublicDonorProfileSerializer(serializers.ModelSerializer):
    """Public-facing donor profile (respects privacy settings)"""
    from auth_app.serializers import CountryLookupSerializer
    
    age = serializers.ReadOnlyField()
    country = CountryLookupSerializer(source='country_fk', read_only=True)
    photo_url = serializers.SerializerMethodField()
    donations = serializers.SerializerMethodField()
    total_donated = serializers.SerializerMethodField()
    donation_count = serializers.SerializerMethodField()
    
    def get_photo_url(self, obj):
        """Return full URL for donor photo"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def get_donations(self, obj):
        """Get list of completed donations with patient/campaign details"""
        from .models import Donation
        
        # Get completed donations for this donor
        donations = Donation.objects.filter(
            donor=obj.user,
            status='COMPLETED',
            is_anonymous=False  # Only show non-anonymous donations
        ).select_related('patient').order_by('-completed_at')[:20]  # Limit to 20 most recent
        
        donations_list = []
        for donation in donations:
            donation_data = {
                'id': donation.id,
                'amount': str(donation.amount),
                'currency': donation.currency,
                'date': donation.completed_at or donation.created_at,
                'message': donation.message if donation.message else None,
            }
            
            # Add patient details if donation is to a specific patient
            if donation.patient:
                donation_data['patient'] = {
                    'id': donation.patient.id,
                    'full_name': donation.patient.full_name,
                    'diagnosis': donation.patient.diagnosis,
                    'photo_url': self.context.get('request').build_absolute_uri(donation.patient.photo.url) if donation.patient.photo and self.context.get('request') else None
                }
            else:
                donation_data['patient'] = None
                donation_data['donation_type'] = 'General Fund'
            
            donations_list.append(donation_data)
        
        return donations_list
    
    def get_total_donated(self, obj):
        """Calculate total amount donated (completed donations only)"""
        from .models import Donation
        from django.db.models import Sum
        
        total = Donation.objects.filter(
            donor=obj.user,
            status='COMPLETED',
            is_anonymous=False
        ).aggregate(total=Sum('amount'))['total']
        
        return str(total) if total else "0.00"
    
    def get_donation_count(self, obj):
        """Count of completed donations"""
        from .models import Donation
        
        return Donation.objects.filter(
            donor=obj.user,
            status='COMPLETED',
            is_anonymous=False
        ).count()
    
    class Meta:
        model = DonorProfile
        fields = [
            'id', 'photo', 'photo_url', 'full_name', 'short_bio', 'country',
            'website', 'age', 'workplace', 'created_at',
            'total_donated', 'donation_count', 'donations'
        ]
        read_only_fields = fields


class PatientDonorSerializer(serializers.Serializer):
    """Serializer for displaying donors who donated to a specific patient"""
    id = serializers.IntegerField(read_only=True)
    donor_profile_id = serializers.IntegerField(read_only=True, allow_null=True)
    donor_name = serializers.CharField(read_only=True)
    donor_photo = serializers.CharField(read_only=True, allow_null=True)
    donor_photo_url = serializers.CharField(read_only=True, allow_null=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    donation_date = serializers.DateTimeField(read_only=True)
    message = serializers.CharField(read_only=True)
    is_anonymous = serializers.BooleanField(read_only=True)
    
    class Meta:
        fields = ['id', 'donor_profile_id', 'donor_name', 'donor_photo', 'donor_photo_url', 'amount', 'donation_date', 'message', 'is_anonymous']


class DonorRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise EmailAlreadyExistsException()
        return value
    
    def validate_password(self, value):
        if len(value) < 8:
            raise PasswordTooShortException()
        return value
    
    def create(self, validated_data):
        # Generate verification token
        token = generate_verification_token()
        token_hash = create_verification_token_hash(token)
        
        # Create user with verification token
        user = User.objects.create_user(
            **validated_data,
            user_type='DONOR',
            is_active=False,  # Inactive until email verified
            is_verified=False,
            email_verification_token=token_hash,
            email_verification_sent_at=timezone.now()
        )
        # DonorProfile is auto-created by signal
        
        # Store plain token in context for view to send email
        # (we don't store plain token in DB, only the hash)
        self.context['verification_token'] = token
        
        return user