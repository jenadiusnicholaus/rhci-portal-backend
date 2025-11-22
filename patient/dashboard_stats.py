from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import serializers

from patient.models import PatientProfile
from donor.models import DonorProfile, Donation
from campaign.models import Campaign
from auth_app.models import CustomUser


class AdminDashboardStatsSerializer(serializers.Serializer):
    """Serializer for comprehensive admin dashboard statistics"""
    
    # Overview Stats
    total_users = serializers.IntegerField()
    total_patients = serializers.IntegerField()
    total_donors = serializers.IntegerField()
    total_admins = serializers.IntegerField()
    active_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    
    # Patient Stats
    patients_submitted = serializers.IntegerField()
    patients_published = serializers.IntegerField()
    patients_fully_funded = serializers.IntegerField()
    patients_featured = serializers.IntegerField()
    patients_pending_review = serializers.IntegerField()
    
    # Donor Stats
    active_donors = serializers.IntegerField()
    total_donations_count = serializers.IntegerField()
    unique_donors_count = serializers.IntegerField()
    
    # Campaign Stats
    total_campaigns = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    completed_campaigns = serializers.IntegerField()
    
    # Financial Stats
    total_funding_goal = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_funding_raised = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_donations_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_donation_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    overall_funding_percentage = serializers.FloatField()
    
    # Recent Activity (Last 30 days)
    new_patients_this_month = serializers.IntegerField()
    new_donors_this_month = serializers.IntegerField()
    donations_this_month = serializers.IntegerField()
    donations_amount_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Recent Activity (Last 7 days)
    new_patients_this_week = serializers.IntegerField()
    new_donors_this_week = serializers.IntegerField()
    donations_this_week = serializers.IntegerField()
    donations_amount_this_week = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Today's Activity
    new_patients_today = serializers.IntegerField()
    new_donors_today = serializers.IntegerField()
    donations_today = serializers.IntegerField()
    donations_amount_today = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Breakdown by Country
    patients_by_country = serializers.DictField(child=serializers.IntegerField())
    donors_by_country = serializers.DictField(child=serializers.IntegerField())
    
    # Breakdown by Status
    patients_by_status = serializers.DictField(child=serializers.IntegerField())
    
    # Breakdown by Gender
    patients_by_gender = serializers.DictField(child=serializers.IntegerField())
    
    # Top Performers
    top_funded_patients = serializers.ListField(child=serializers.DictField())
    top_donors = serializers.ListField(child=serializers.DictField())
    recent_donations = serializers.ListField(child=serializers.DictField())
    
    # Trends (Last 30 days)
    daily_donations_trend = serializers.ListField(child=serializers.DictField())
    daily_registrations_trend = serializers.ListField(child=serializers.DictField())


class AdminDashboardStatsView(APIView):
    """
    Comprehensive admin dashboard statistics endpoint.
    Provides complete overview of platform metrics including users, patients, donors,
    donations, campaigns, and recent activity.
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Dashboard Statistics",
        operation_description="""
        Get comprehensive statistics for admin dashboard including:
        - User overview (patients, donors, admins)
        - Patient statistics and status breakdown
        - Donor activity and engagement
        - Financial metrics and funding progress
        - Recent activity (today, this week, this month)
        - Geographic distribution
        - Top performers and trends
        """,
        tags=['Admin - Dashboard & Analytics'],
        manual_parameters=[
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Start date for trend analysis (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="End date for trend analysis (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
        ],
        responses={
            200: openapi.Response('Dashboard statistics', AdminDashboardStatsSerializer),
            403: 'Forbidden - Admin access required'
        }
    )
    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # ===== USER OVERVIEW =====
        total_users = CustomUser.objects.count()
        total_patients = CustomUser.objects.filter(user_type='PATIENT').count()
        total_donors = CustomUser.objects.filter(user_type='DONOR').count()
        total_admins = CustomUser.objects.filter(user_type='ADMIN').count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        verified_users = CustomUser.objects.filter(is_verified=True).count()
        
        # ===== PATIENT STATISTICS =====
        patients_submitted = PatientProfile.objects.filter(status='SUBMITTED').count()
        patients_published = PatientProfile.objects.filter(status='PUBLISHED').count()
        patients_fully_funded = PatientProfile.objects.filter(status='FULLY_FUNDED').count()
        patients_featured = PatientProfile.objects.filter(is_featured=True).count()
        patients_pending_review = PatientProfile.objects.filter(
            status='SUBMITTED'
        ).count()
        
        # ===== DONOR STATISTICS =====
        active_donors = DonorProfile.objects.filter(user__is_active=True).count()
        total_donations_count = Donation.objects.filter(status='COMPLETED').count()
        unique_donors_count = Donation.objects.filter(
            status='COMPLETED'
        ).values('donor').distinct().count()
        
        # ===== CAMPAIGN STATISTICS =====
        total_campaigns = Campaign.objects.count()
        active_campaigns = Campaign.objects.filter(
            status='ACTIVE',
            end_date__gte=now
        ).count()
        completed_campaigns = Campaign.objects.filter(status='COMPLETED').count()
        
        # ===== FINANCIAL STATISTICS =====
        funding_stats = PatientProfile.objects.aggregate(
            total_goal=Sum('funding_required'),
            total_raised=Sum('funding_received')
        )
        
        donation_stats = Donation.objects.filter(status='COMPLETED').aggregate(
            total_amount=Sum('amount'),
            avg_amount=Avg('amount'),
            count=Count('id')
        )
        
        total_funding_goal = funding_stats['total_goal'] or 0
        total_funding_raised = funding_stats['total_raised'] or 0
        total_donations_amount = donation_stats['total_amount'] or 0
        average_donation_amount = donation_stats['avg_amount'] or 0
        
        overall_funding_percentage = (
            (float(total_funding_raised) / float(total_funding_goal) * 100)
            if total_funding_goal > 0 else 0
        )
        
        # ===== RECENT ACTIVITY - THIS MONTH =====
        new_patients_this_month = PatientProfile.objects.filter(
            created_at__gte=month_ago
        ).count()
        new_donors_this_month = DonorProfile.objects.filter(
            created_at__gte=month_ago
        ).count()
        donations_this_month = Donation.objects.filter(
            status='COMPLETED',
            created_at__gte=month_ago
        ).count()
        donations_amount_this_month = Donation.objects.filter(
            status='COMPLETED',
            created_at__gte=month_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # ===== RECENT ACTIVITY - THIS WEEK =====
        new_patients_this_week = PatientProfile.objects.filter(
            created_at__gte=week_ago
        ).count()
        new_donors_this_week = DonorProfile.objects.filter(
            created_at__gte=week_ago
        ).count()
        donations_this_week = Donation.objects.filter(
            status='COMPLETED',
            created_at__gte=week_ago
        ).count()
        donations_amount_this_week = Donation.objects.filter(
            status='COMPLETED',
            created_at__gte=week_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # ===== RECENT ACTIVITY - TODAY =====
        new_patients_today = PatientProfile.objects.filter(
            created_at__gte=today_start
        ).count()
        new_donors_today = DonorProfile.objects.filter(
            created_at__gte=today_start
        ).count()
        donations_today = Donation.objects.filter(
            status='COMPLETED',
            created_at__gte=today_start
        ).count()
        donations_amount_today = Donation.objects.filter(
            status='COMPLETED',
            created_at__gte=today_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # ===== BREAKDOWN BY COUNTRY =====
        patients_by_country = dict(
            PatientProfile.objects.filter(country_fk__isnull=False)
            .values('country_fk__name')
            .annotate(count=Count('id'))
            .values_list('country_fk__name', 'count')
        )
        
        donors_by_country = dict(
            DonorProfile.objects.filter(country_fk__isnull=False)
            .values('country_fk__name')
            .annotate(count=Count('id'))
            .values_list('country_fk__name', 'count')
        )
        
        # ===== BREAKDOWN BY STATUS =====
        patients_by_status = dict(
            PatientProfile.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        
        # ===== BREAKDOWN BY GENDER =====
        patients_by_gender = dict(
            PatientProfile.objects.values('gender')
            .annotate(count=Count('id'))
            .values_list('gender', 'count')
        )
        
        # ===== TOP PERFORMERS =====
        # Top 5 funded patients
        top_funded_patients = list(
            PatientProfile.objects.filter(funding_received__gt=0)
            .order_by('-funding_received')[:5]
            .values(
                'id', 
                'full_name', 
                'funding_received', 
                'funding_required',
                'country_fk__name'
            )
        )
        
        # Calculate percentage for each
        for patient in top_funded_patients:
            patient['funding_percentage'] = (
                (float(patient['funding_received']) / float(patient['funding_required']) * 100)
                if patient['funding_required'] > 0 else 0
            )
            patient['country'] = patient.pop('country_fk__name')
        
        # Top 5 donors by total donations
        top_donors = list(
            Donation.objects.filter(status='COMPLETED', donor__isnull=False)
            .values('donor__first_name', 'donor__last_name', 'donor__email')
            .annotate(
                total_donated=Sum('amount'),
                donation_count=Count('id')
            )
            .order_by('-total_donated')[:5]
        )
        
        # Format donor names
        for donor in top_donors:
            donor['name'] = f"{donor.pop('donor__first_name', '')} {donor.pop('donor__last_name', '')}".strip()
            donor['email'] = donor.pop('donor__email')
        
        # Recent 10 donations
        recent_donations = list(
            Donation.objects.filter(status='COMPLETED')
            .select_related('donor', 'patient')
            .order_by('-created_at')[:10]
            .values(
                'id',
                'amount',
                'created_at',
                'donor__first_name',
                'donor__last_name',
                'patient__full_name',
                'payment_method'
            )
        )
        
        # Format recent donations
        for donation in recent_donations:
            donation['donor_name'] = f"{donation.pop('donor__first_name', '')} {donation.pop('donor__last_name', '')}".strip()
            donation['patient_name'] = donation.pop('patient__full_name')
        
        # ===== TRENDS - LAST 30 DAYS =====
        # Daily donations trend
        daily_donations = Donation.objects.filter(
            status='COMPLETED',
            created_at__gte=month_ago
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('date')
        
        daily_donations_trend = [
            {
                'date': item['date'].isoformat() if hasattr(item['date'], 'isoformat') else str(item['date']),
                'count': item['count'],
                'amount': float(item['total_amount'] or 0)
            }
            for item in daily_donations
        ]
        
        # Daily registrations trend
        daily_patients = PatientProfile.objects.filter(
            created_at__gte=month_ago
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            patient_count=Count('id')
        ).order_by('date')
        
        daily_donors = DonorProfile.objects.filter(
            created_at__gte=month_ago
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            donor_count=Count('id')
        ).order_by('date')
        
        # Combine into daily registrations
        registrations_by_date = {}
        for item in daily_patients:
            date_str = item['date'].isoformat() if hasattr(item['date'], 'isoformat') else str(item['date'])
            registrations_by_date[date_str] = {
                'date': date_str,
                'patients': item['patient_count'],
                'donors': 0
            }
        
        for item in daily_donors:
            date_str = item['date'].isoformat() if hasattr(item['date'], 'isoformat') else str(item['date'])
            if date_str in registrations_by_date:
                registrations_by_date[date_str]['donors'] = item['donor_count']
            else:
                registrations_by_date[date_str] = {
                    'date': date_str,
                    'patients': 0,
                    'donors': item['donor_count']
                }
        
        daily_registrations_trend = sorted(
            registrations_by_date.values(),
            key=lambda x: x['date']
        )
        
        # ===== COMPILE ALL STATS =====
        stats_data = {
            # Overview
            'total_users': total_users,
            'total_patients': total_patients,
            'total_donors': total_donors,
            'total_admins': total_admins,
            'active_users': active_users,
            'verified_users': verified_users,
            
            # Patients
            'patients_submitted': patients_submitted,
            'patients_published': patients_published,
            'patients_fully_funded': patients_fully_funded,
            'patients_featured': patients_featured,
            'patients_pending_review': patients_pending_review,
            
            # Donors
            'active_donors': active_donors,
            'total_donations_count': total_donations_count,
            'unique_donors_count': unique_donors_count,
            
            # Campaigns
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'completed_campaigns': completed_campaigns,
            
            # Financial
            'total_funding_goal': total_funding_goal,
            'total_funding_raised': total_funding_raised,
            'total_donations_amount': total_donations_amount,
            'average_donation_amount': average_donation_amount,
            'overall_funding_percentage': overall_funding_percentage,
            
            # This Month
            'new_patients_this_month': new_patients_this_month,
            'new_donors_this_month': new_donors_this_month,
            'donations_this_month': donations_this_month,
            'donations_amount_this_month': donations_amount_this_month,
            
            # This Week
            'new_patients_this_week': new_patients_this_week,
            'new_donors_this_week': new_donors_this_week,
            'donations_this_week': donations_this_week,
            'donations_amount_this_week': donations_amount_this_week,
            
            # Today
            'new_patients_today': new_patients_today,
            'new_donors_today': new_donors_today,
            'donations_today': donations_today,
            'donations_amount_today': donations_amount_today,
            
            # Breakdowns
            'patients_by_country': patients_by_country,
            'donors_by_country': donors_by_country,
            'patients_by_status': patients_by_status,
            'patients_by_gender': patients_by_gender,
            
            # Top Performers
            'top_funded_patients': top_funded_patients,
            'top_donors': top_donors,
            'recent_donations': recent_donations,
            
            # Trends
            'daily_donations_trend': daily_donations_trend,
            'daily_registrations_trend': daily_registrations_trend,
        }
        
        serializer = AdminDashboardStatsSerializer(stats_data)
        return Response(serializer.data)
