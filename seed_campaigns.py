#!/usr/bin/env python
"""
Campaign Database Seeding Script
Creates test data for campaigns, payment methods, photos, and updates
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from django.contrib.auth import get_user_model
from campaign.models import PaymentMethod, Campaign, CampaignPhoto, CampaignUpdate
from django.db import transaction

User = get_user_model()


def clear_campaign_data():
    """Clear existing campaign data"""
    print("🗑️  Clearing existing campaign data...")
    CampaignUpdate.objects.all().delete()
    CampaignPhoto.objects.all().delete()
    Campaign.objects.all().delete()
    PaymentMethod.objects.all().delete()
    print("✅ Campaign data cleared")


def create_payment_methods(admin_user):
    """Create payment methods (RHCI admin only)"""
    print("\n💳 Creating payment methods...")
    
    payment_methods = [
        {
            'name': 'M-Pesa',
            'account_name': 'RHCI Foundation',
            'account_number': '+254712345678',
            'bank_name': 'Safaricom',
            'additional_info': 'Send money via M-Pesa to this number. Please include your name in the reference.',
            'display_order': 1,
        },
        {
            'name': 'Bank Transfer (Kenya)',
            'account_name': 'RHCI Foundation Kenya',
            'account_number': '1234567890',
            'bank_name': 'Equity Bank',
            'swift_code': 'EQBLKENA',
            'additional_info': 'Account Type: Current Account\nBranch: Nairobi',
            'display_order': 2,
        },
        {
            'name': 'Bank Transfer (International)',
            'account_name': 'RHCI Foundation',
            'account_number': '0987654321',
            'bank_name': 'Standard Chartered Bank',
            'swift_code': 'SCBLKENX',
            'additional_info': 'For international wire transfers. Currency: USD',
            'display_order': 3,
        },
        {
            'name': 'PayPal',
            'account_name': 'RHCI Foundation',
            'account_number': 'donations@rhci.org',
            'additional_info': 'Send via PayPal to this email address',
            'display_order': 4,
        },
        {
            'name': 'Credit/Debit Card',
            'account_name': 'RHCI Foundation',
            'account_number': 'Online Payment Portal',
            'additional_info': 'Payment gateway: Stripe. Secure online payment.',
            'display_order': 5,
            'is_active': False,  # Not yet activated
        },
    ]
    
    created_methods = []
    for pm_data in payment_methods:
        pm = PaymentMethod.objects.create(
            **pm_data,
            created_by=admin_user
        )
        created_methods.append(pm)
        status = "✅ Active" if pm.is_active else "⏸️  Inactive"
        print(f"  {status} {pm.name} - {pm.account_number}")
    
    print(f"✅ Created {len(created_methods)} payment methods")
    return created_methods


def create_campaign_launchers():
    """Create test campaign launcher users"""
    print("\n👥 Creating campaign launchers...")
    
    launchers = []
    for i in range(1, 4):
        email = f"launcher{i}@example.com"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': f'Campaign',
                'last_name': f'Launcher {i}',
                'is_active': True,
                'user_type': 'DONOR',  # Campaign launchers can be donors
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            print(f"  ✅ Created {email}")
        else:
            print(f"  ℹ️  Using existing {email}")
        launchers.append(user)
    
    return launchers


def create_campaigns(launchers, payment_methods, admin_user):
    """Create test campaigns"""
    print("\n📢 Creating campaigns...")
    
    campaigns_data = [
        {
            'launcher': launchers[0],
            'title': "Help Sarah Get Life-Saving Surgery",
            'description': """Sarah is a bright 8-year-old girl who loves to dance and paint. 
            
Recently, she was diagnosed with a heart condition that requires urgent surgery. Her family has exhausted all their savings trying to get treatment locally, but the specialized procedure she needs is only available at a facility in Nairobi.

The surgery costs $15,000, which includes:
- Pre-operative tests and consultations
- The surgical procedure itself
- Post-operative care and monitoring
- Medications and follow-up visits

Sarah's mother is a single parent working as a teacher, and despite her best efforts, she cannot afford this life-saving treatment. Your donation, no matter how small, will help give Sarah a chance at a normal, healthy life.

Every dollar brings us closer to our goal. Please help us save Sarah's life.""",
            'goal_amount': Decimal('15000.00'),
            'raised_amount': Decimal('8500.00'),
            'end_date': date.today() + timedelta(days=30),
            'status': 'ACTIVE',
            'payment_methods': payment_methods[:3],  # M-Pesa, Bank Transfer Kenya, Bank Transfer International
        },
        {
            'launcher': launchers[1],
            'title': "Emergency Medical Fund for John's Cancer Treatment",
            'description': """John is a 45-year-old father of three who was recently diagnosed with Stage 3 cancer.
            
He needs immediate chemotherapy and radiation treatment to fight this disease. As the sole breadwinner of his family, John's illness has not only brought emotional distress but also severe financial strain.

Treatment costs breakdown:
- Chemotherapy sessions (6 months): $8,000
- Radiation therapy: $5,000
- Medications: $2,000
- Regular check-ups and tests: $1,000

Total needed: $16,000

John has always been a pillar of his community, helping others whenever he could. Now, it's our turn to help him. With your support, we can ensure John receives the treatment he desperately needs.

Time is of the essence. Please donate today.""",
            'goal_amount': Decimal('16000.00'),
            'raised_amount': Decimal('3200.00'),
            'end_date': date.today() + timedelta(days=45),
            'status': 'ACTIVE',
            'payment_methods': payment_methods[:4],  # All except credit card
        },
        {
            'launcher': launchers[2],
            'title': "Support Maria's Kidney Transplant",
            'description': """Maria is a 32-year-old teacher who has been battling kidney disease for the past 5 years.
            
She has been on dialysis three times a week, which has significantly impacted her quality of life. After years of waiting, a matching kidney donor has finally been found!

The transplant operation and recovery costs include:
- Pre-transplant evaluations: $3,000
- Transplant surgery: $35,000
- Hospital stay (2 weeks): $8,000
- Anti-rejection medications (first year): $12,000
- Follow-up care: $2,000

Total: $60,000

Maria's insurance covers only a portion of these costs, leaving her family with a gap of $40,000. This is where we need your help.

A successful transplant will give Maria her life back - she'll be able to return to teaching, spend quality time with her family, and live without the constant burden of dialysis.

Please help us make this miracle happen for Maria.""",
            'goal_amount': Decimal('40000.00'),
            'raised_amount': Decimal('12000.00'),
            'end_date': date.today() + timedelta(days=60),
            'status': 'ACTIVE',
            'payment_methods': payment_methods[:3],
        },
        {
            'launcher': launchers[0],
            'title': "Emergency Fund for Baby Emma's Heart Surgery",
            'description': """Baby Emma was born with a congenital heart defect that requires immediate surgical intervention.
            
At just 6 months old, Emma is fighting for her life. Her parents discovered the condition during a routine check-up, and doctors have advised that surgery must be performed within the next 2 months to give Emma the best chance at survival.

What we need:
- Cardiac surgery: $20,000
- Intensive care (1 week): $5,000
- Medications and medical supplies: $3,000
- Follow-up appointments (1 year): $2,000

Total: $30,000

Emma's parents are devastated and doing everything they can, but the costs are overwhelming. As young parents just starting their careers, they simply don't have the resources to cover these expenses.

Every donation counts. Your contribution will directly help save baby Emma's life and give her a chance to grow up healthy and happy.

Please donate today and share Emma's story.""",
            'goal_amount': Decimal('30000.00'),
            'raised_amount': Decimal('5400.00'),
            'end_date': date.today() + timedelta(days=20),
            'status': 'ACTIVE',
            'payment_methods': payment_methods[:3],
        },
        {
            'launcher': launchers[1],
            'title': "Pending: Support for David's Rehabilitation",
            'description': """David was involved in a serious accident that left him paralyzed from the waist down.
            
This campaign is currently under review by RHCI admin.""",
            'goal_amount': Decimal('25000.00'),
            'raised_amount': Decimal('0.00'),
            'end_date': date.today() + timedelta(days=90),
            'status': 'PENDING_REVIEW',
            'payment_methods': [],
        },
        {
            'launcher': launchers[2],
            'title': "Draft: Help Build a Medical Clinic",
            'description': """We are planning to build a medical clinic in a rural area that lacks healthcare facilities.
            
This is still in draft stage.""",
            'goal_amount': Decimal('100000.00'),
            'raised_amount': Decimal('0.00'),
            'end_date': date.today() + timedelta(days=180),
            'status': 'DRAFT',
            'payment_methods': [],
        },
    ]
    
    created_campaigns = []
    for camp_data in campaigns_data:
        payment_methods_list = camp_data.pop('payment_methods')
        
        # Set approved fields for active campaigns
        if camp_data['status'] == 'ACTIVE':
            camp_data['approved_by'] = admin_user
            camp_data['approved_at'] = date.today()
        
        campaign = Campaign.objects.create(**camp_data)
        
        # Add payment methods
        if payment_methods_list:
            campaign.payment_methods.set(payment_methods_list)
        
        created_campaigns.append(campaign)
        
        status_icon = {
            'ACTIVE': '🟢',
            'PENDING_REVIEW': '🟡',
            'DRAFT': '⚪',
            'APPROVED': '🟢',
            'PAUSED': '🟠',
            'COMPLETED': '✅',
            'REJECTED': '🔴',
        }.get(campaign.status, '❓')
        
        print(f"  {status_icon} {campaign.title[:50]}... (${campaign.raised_amount:,.0f} / ${campaign.goal_amount:,.0f})")
    
    print(f"✅ Created {len(created_campaigns)} campaigns")
    return created_campaigns


def create_campaign_updates(campaigns):
    """Create campaign updates"""
    print("\n📝 Creating campaign updates...")
    
    # Only create updates for active campaigns
    active_campaigns = [c for c in campaigns if c.status == 'ACTIVE']
    
    updates_count = 0
    for campaign in active_campaigns[:2]:  # Add updates to first 2 active campaigns
        # Update 1
        CampaignUpdate.objects.create(
            campaign=campaign,
            title=f"Thank you for your support!",
            content=f"""We are overwhelmed by the support we've received so far! 

We've raised ${campaign.raised_amount} towards our goal of ${campaign.goal_amount}. Every donation brings us closer to getting the treatment needed.

Thank you to everyone who has contributed and shared our campaign!""",
            author=campaign.launcher
        )
        updates_count += 1
        
        # Update 2
        CampaignUpdate.objects.create(
            campaign=campaign,
            title=f"Medical consultation completed",
            content=f"""Great news! We've completed the initial medical consultation and the doctors are optimistic.

The treatment plan is ready, and we're making progress. Please continue to support and share our campaign.

Together, we can make this happen!""",
            author=campaign.launcher
        )
        updates_count += 1
    
    print(f"✅ Created {updates_count} campaign updates")


def seed_campaign_data():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 CAMPAIGN DATABASE SEEDING")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # Get or create admin user
            admin_user, created = User.objects.get_or_create(
                email='admin@rhci.org',
                defaults={
                    'first_name': 'RHCI',
                    'last_name': 'Admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                    'user_type': 'ADMIN',
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                print(f"\n✅ Created admin user: {admin_user.email}")
            else:
                print(f"\nℹ️  Using existing admin user: {admin_user.email}")
            
            # Clear existing data
            clear_campaign_data()
            
            # Create payment methods
            payment_methods = create_payment_methods(admin_user)
            
            # Create campaign launchers
            launchers = create_campaign_launchers()
            
            # Create campaigns
            campaigns = create_campaigns(launchers, payment_methods, admin_user)
            
            # Create campaign updates
            create_campaign_updates(campaigns)
            
            print("\n" + "=" * 60)
            print("✅ CAMPAIGN SEEDING COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("\n📊 Summary:")
            print(f"  • Payment Methods: {len(payment_methods)}")
            print(f"  • Campaign Launchers: {len(launchers)}")
            print(f"  • Campaigns: {len(campaigns)}")
            print(f"    - Active: {len([c for c in campaigns if c.status == 'ACTIVE'])}")
            print(f"    - Pending Review: {len([c for c in campaigns if c.status == 'PENDING_REVIEW'])}")
            print(f"    - Draft: {len([c for c in campaigns if c.status == 'DRAFT'])}")
            
            print("\n🔑 Test Credentials:")
            print(f"  Admin: admin@rhci.org / admin123")
            print(f"  Launcher 1: launcher1@example.com / password123")
            print(f"  Launcher 2: launcher2@example.com / password123")
            print(f"  Launcher 3: launcher3@example.com / password123")
            
            print("\n🌐 Access URLs:")
            print(f"  Admin: http://127.0.0.1:8000/admin/")
            print(f"  API: http://127.0.0.1:8000/api/v1.0/campaigns/public/")
            print(f"  Swagger: http://127.0.0.1:8000/api/v1.0/swagger/")
            
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed campaign database with test data')
    parser.add_argument('--clear', action='store_true', help='Clear existing campaign data before seeding')
    
    args = parser.parse_args()
    
    if args.clear:
        confirm = input("⚠️  This will delete all existing campaign data. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Seeding cancelled")
            sys.exit(0)
    
    seed_campaign_data()
