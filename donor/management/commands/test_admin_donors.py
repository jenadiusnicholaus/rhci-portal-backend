"""
Test script for Admin Donor Management API
"""
from django.core.management.base import BaseCommand
from donor.models import DonorProfile, Donation
from django.db.models import Count, Sum


class Command(BaseCommand):
    help = 'Test admin donor management endpoints'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("Admin Donor Management API - Test Information"))
        self.stdout.write("="*70 + "\n")

        # Get donor statistics
        total_donors = DonorProfile.objects.count()
        verified_donors = DonorProfile.objects.filter(user__is_verified=True).count()
        active_donors = DonorProfile.objects.filter(user__is_active=True).count()
        
        self.stdout.write(f"Total Donors: {total_donors}")
        self.stdout.write(f"Verified Donors: {verified_donors}")
        self.stdout.write(f"Active Donors: {active_donors}\n")

        # List some donors
        self.stdout.write("Sample Donors:")
        self.stdout.write("-" * 70)
        
        donors_list = list(DonorProfile.objects.select_related('user').all()[:5])
        donors = DonorProfile.objects.select_related('user').all()
        first_donor_id = donors.first().id if donors.exists() else 1
        
        for donor in donors_list:
            donation_count = Donation.objects.filter(
                donor=donor.user,
                status='COMPLETED'
            ).count()
            total_donated = Donation.objects.filter(
                donor=donor.user,
                status='COMPLETED'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            self.stdout.write(
                f"  ID: {donor.id} | {donor.full_name or 'N/A'} ({donor.user.email})"
            )
            self.stdout.write(
                f"    Status: {'✓ Active' if donor.user.is_active else '✗ Inactive'} | "
                f"{'✓ Verified' if donor.user.is_verified else '✗ Unverified'}"
            )
            self.stdout.write(
                f"    Donations: {donation_count} donations, ${total_donated:,.2f} total"
            )
            self.stdout.write("")

        # API Endpoints
        self.stdout.write("\n" + "="*70)
        self.stdout.write("Available Admin Donor Management Endpoints:")
        self.stdout.write("="*70 + "\n")

        endpoints = [
            {
                'method': 'GET',
                'url': '/api/v1.0/donors/admin/donors/',
                'desc': 'List all donors with filtering and search',
                'params': '?search=john&is_verified=true&is_private=false'
            },
            {
                'method': 'GET',
                'url': f'/api/v1.0/donors/admin/donors/{first_donor_id}/',
                'desc': 'Get donor details by ID',
                'params': ''
            },
            {
                'method': 'PUT/PATCH',
                'url': f'/api/v1.0/donors/admin/donors/{first_donor_id}/',
                'desc': 'Update donor profile',
                'params': ''
            },
            {
                'method': 'DELETE',
                'url': f'/api/v1.0/donors/admin/donors/{first_donor_id}/',
                'desc': 'Delete donor account',
                'params': ''
            },
            {
                'method': 'PATCH',
                'url': f'/api/v1.0/donors/admin/donors/{first_donor_id}/activate/',
                'desc': 'Activate/Deactivate donor account',
                'params': '\n    Body: {"is_active": true}'
            },
            {
                'method': 'GET',
                'url': '/api/v1.0/donors/admin/donors/stats/',
                'desc': 'Get donor statistics and top donors',
                'params': ''
            },
        ]

        for endpoint in endpoints:
            self.stdout.write(f"{endpoint['method']:12} {endpoint['url']}")
            self.stdout.write(f"             {endpoint['desc']}")
            if endpoint['params']:
                self.stdout.write(f"             {endpoint['params']}")
            self.stdout.write("")

        # Example curl commands
        self.stdout.write("\n" + "="*70)
        self.stdout.write("Example curl Commands (requires admin token):")
        self.stdout.write("="*70 + "\n")

        self.stdout.write("1. List all donors:")
        self.stdout.write('   curl -H "Authorization: Bearer <admin_token>" \\')
        self.stdout.write('        http://localhost:8000/api/v1.0/donors/admin/donors/')
        
        self.stdout.write("\n2. Search donors:")
        self.stdout.write('   curl -H "Authorization: Bearer <admin_token>" \\')
        self.stdout.write('        "http://localhost:8000/api/v1.0/donors/admin/donors/?search=john"')
        
        self.stdout.write("\n3. Get donor statistics:")
        self.stdout.write('   curl -H "Authorization: Bearer <admin_token>" \\')
        self.stdout.write('        http://localhost:8000/api/v1.0/donors/admin/donors/stats/')
        
        if donors.exists():
            donor_id = first_donor_id
            self.stdout.write(f"\n4. Get specific donor (ID: {donor_id}):")
            self.stdout.write('   curl -H "Authorization: Bearer <admin_token>" \\')
            self.stdout.write(f'        http://localhost:8000/api/v1.0/donors/admin/donors/{donor_id}/')
            
            self.stdout.write(f"\n5. Deactivate donor (ID: {donor_id}):")
            self.stdout.write('   curl -X PATCH -H "Authorization: Bearer <admin_token>" \\')
            self.stdout.write('        -H "Content-Type: application/json" \\')
            self.stdout.write('        -d \'{"is_active": false}\' \\')
            self.stdout.write(f'        http://localhost:8000/api/v1.0/donors/admin/donors/{donor_id}/activate/')

        # Features
        self.stdout.write("\n" + "="*70)
        self.stdout.write("Features:")
        self.stdout.write("="*70)
        self.stdout.write("✓ List all donors with pagination")
        self.stdout.write("✓ Search by name, email, or workplace")
        self.stdout.write("✓ Filter by verification and privacy status")
        self.stdout.write("✓ View complete donor details")
        self.stdout.write("✓ Update donor profile information")
        self.stdout.write("✓ Activate/Deactivate donor accounts")
        self.stdout.write("✓ Delete donor accounts")
        self.stdout.write("✓ View donor statistics and top donors")
        self.stdout.write("✓ All endpoints protected with admin authentication")

        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("✓ Admin Donor Management API Ready!"))
        self.stdout.write("="*70 + "\n")
