from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import datetime
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Create role-based test users for production testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-all',
            action='store_true',
            help='Create all test users (admin, donor, patient)',
        )
        parser.add_argument(
            '--admin',
            action='store_true',
            help='Create admin test user',
        )
        parser.add_argument(
            '--donor',
            action='store_true',
            help='Create donor test user',
        )
        parser.add_argument(
            '--patient',
            action='store_true',
            help='Create patient test user',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List existing test users',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete all test users',
        )
        parser.add_argument(
            '--split',
            action='store_true',
            help='Create multiple users per role with different scenarios',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of users to create per role when using --split (default: 3)',
        )
        parser.add_argument(
            '--env',
            type=str,
            default='prod',
            choices=['dev', 'staging', 'prod'],
            help='Environment (affects email domains)',
        )

    def handle(self, *args, **options):
        env = options.get('env', 'prod')
        split = options.get('split', False)
        count = options.get('count', 3)
        
        if options.get('list'):
            self.list_test_users(env)
            return
            
        if options.get('delete'):
            self.delete_test_users(env)
            return

        # Create users based on options
        created_count = 0
        
        if split:
            # Create multiple users per role with different scenarios
            if options.get('create_all') or options.get('admin'):
                created_count += self.create_split_admin_users(env, count)
                
            if options.get('create_all') or options.get('donor'):
                created_count += self.create_split_donor_users(env, count)
                
            if options.get('create_all') or options.get('patient'):
                created_count += self.create_split_patient_users(env, count)
        else:
            # Create single users per role (original behavior)
            if options.get('create_all') or options.get('admin'):
                if self.create_admin_user(env):
                    created_count += 1
                    
            if options.get('create_all') or options.get('donor'):
                if self.create_donor_user(env):
                    created_count += 1
                    
            if options.get('create_all') or options.get('patient'):
                if self.create_patient_user(env):
                    created_count += 1
        
        if created_count > 0:
            action = "split" if split else "test"
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully created {created_count} {action} users for {env.upper()}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ No users created. Use --create-all or specify roles.')
            )

    def get_email_domain(self, env):
        """Get email domain based on environment"""
        domains = {
            'dev': 'test.local',
            'staging': 'test.staging.com',
            'prod': 'test.rhci.co.tz'
        }
        return domains.get(env, 'test.rhci.co.tz')

    def create_admin_user(self, env):
        """Create admin test user"""
        domain = self.get_email_domain(env)
        email = f'admin.test@{domain}'
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'⚠️ Admin user already exists: {email}')
            )
            return False
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password='TestAdmin123!',
                    user_type='ADMIN',
                    first_name='Test',
                    last_name='Admin',
                    is_active=True,
                    is_verified=True,
                    is_staff=True,
                    is_superuser=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'👑 Created Admin: {email} | Password: TestAdmin123!')
                )
                return True
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create admin user: {e}')
            )
            return False

    def create_donor_user(self, env):
        """Create donor test user"""
        domain = self.get_email_domain(env)
        email = f'donor.test@{domain}'
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'⚠️ Donor user already exists: {email}')
            )
            return False
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password='TestDonor123!',
                    user_type='DONOR',
                    first_name='Test',
                    last_name='Donor',
                    phone_number='+255123456789',
                    is_active=True,
                    is_verified=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'💰 Created Donor: {email} | Password: TestDonor123!')
                )
                return True
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create donor user: {e}')
            )
            return False

    def create_patient_user(self, env):
        """Create patient test user"""
        domain = self.get_email_domain(env)
        email = f'patient.test@{domain}'
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'⚠️ Patient user already exists: {email}')
            )
            return False
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password='TestPatient123!',
                    user_type='PATIENT',
                    first_name='Test',
                    last_name='Patient',
                    phone_number='+255987654321',
                    date_of_birth='1990-01-01',
                    is_active=True,
                    is_verified=True,
                    is_patient_verified=True
                )
                
                # Create patient profile if patient app exists
                try:
                    from patient.models import PatientProfile
                    PatientProfile.objects.create(
                        user=user,
                        full_name='Test Patient',
                        gender='M',
                        country_fk_id=1,  # Assuming Tanzania exists
                        diagnosis='Test Diagnosis',
                        treatment_needed='Test Treatment',
                        funding_required=100000.00,
                        funding_currency='TZS'
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'🏥 Created Patient Profile for: {email}')
                    )
                except ImportError:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Patient app not found - created user only')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Could not create patient profile: {e}')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'👤 Created Patient: {email} | Password: TestPatient123!')
                )
                return True
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create patient user: {e}')
            )
            return False

    def list_test_users(self, env):
        """List existing test users"""
        domain = self.get_email_domain(env)
        test_users = User.objects.filter(email__endswith=domain)
        
        if not test_users:
            self.stdout.write(
                self.style.WARNING(f'⚠️ No test users found for {env.upper()}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'📋 Test Users for {env.upper()}:')
        )
        self.stdout.write('-' * 60)
        
        for user in test_users:
            status = '✅ Active' if user.is_active else '❌ Inactive'
            verified = '✅ Verified' if user.is_verified else '❌ Not Verified'
            
            self.stdout.write(
                f'{user.user_type}: {user.email}\n'
                f'  Name: {user.get_full_name()}\n'
                f'  Status: {status} | {verified}\n'
                f'  Staff: {"✅ Yes" if user.is_staff else "❌ No"}\n'
            )

    def delete_test_users(self, env):
        """Delete all test users"""
        domain = self.get_email_domain(env)
        test_users = User.objects.filter(email__endswith=domain)
        
        if not test_users:
            self.stdout.write(
                self.style.WARNING(f'⚠️ No test users found for {env.upper()}')
            )
            return
        
        count = test_users.count()
        
        # Confirm deletion
        self.stdout.write(
            self.style.WARNING(f'⚠️ About to delete {count} test users from {env.upper()}')
        )
        self.stdout.write('Users to be deleted:')
        for user in test_users:
            self.stdout.write(f'  - {user.email} ({user.user_type})')
        
        # In production, you might want to add confirmation here
        # For now, we'll proceed with deletion
        
        try:
            with transaction.atomic():
                # Delete patient profiles first if they exist
                try:
                    from patient.models import PatientProfile
                    patient_profiles = PatientProfile.objects.filter(user__in=test_users)
                    profile_count = patient_profiles.count()
                    patient_profiles.delete()
                    if profile_count > 0:
                        self.stdout.write(
                            self.style.SUCCESS(f'🗑️ Deleted {profile_count} patient profiles')
                        )
                except ImportError:
                    pass
                
                # Delete users
                test_users.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'🗑️ Successfully deleted {count} test users from {env.upper()}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to delete test users: {e}')
            )

    def create_split_admin_users(self, env, count):
        """Create multiple admin users with different scenarios"""
        domain = self.get_email_domain(env)
        created_count = 0
        
        admin_scenarios = [
            ('superadmin', 'Super Admin', 'TestSuper123!', True, True),
            ('admin', 'Regular Admin', 'TestAdmin123!', True, False),
            ('moderator', 'Moderator', 'TestMod123!', False, False),
        ]
        
        for i, (role, name, password, is_superuser, is_staff) in enumerate(admin_scenarios[:count]):
            email = f'{role}.test@{domain}'
            
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {role} admin already exists: {email}')
                )
                continue
            
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        user_type='ADMIN',
                        first_name='Test',
                        last_name=name,
                        is_active=True,
                        is_verified=True,
                        is_staff=is_staff,
                        is_superuser=is_superuser
                    )
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'👑 Created {name}: {email} | Password: {password}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create {role} admin: {e}')
                )
        
        return created_count

    def create_split_donor_users(self, env, count):
        """Create multiple donor users with different scenarios"""
        domain = self.get_email_domain(env)
        created_count = 0
        
        donor_scenarios = [
            ('verified', 'Verified Donor', 'TestVerified123!', True, True, '+255123456789'),
            ('unverified', 'Unverified Donor', 'TestUnverified123!', False, False, '+255123456780'),
            ('anonymous', 'Anonymous Donor', 'TestAnonymous123!', True, True, '+255123456788'),
        ]
        
        for i, (role, name, password, is_verified, is_active, phone) in enumerate(donor_scenarios[:count]):
            email = f'{role}.donor@{domain}'
            
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {role} donor already exists: {email}')
                )
                continue
            
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        user_type='DONOR',
                        first_name='Test',
                        last_name=name,
                        phone_number=phone,
                        is_active=is_active,
                        is_verified=is_verified
                    )
                    
                    created_count += 1
                    status = "✅ Active" if is_active else "❌ Inactive"
                    verified = "✅ Verified" if is_verified else "❌ Not Verified"
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'💰 Created {name}: {email} | Password: {password}')
                    )
                    self.stdout.write(f'   Status: {status} | {verified}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create {role} donor: {e}')
                )
        
        return created_count

    def create_split_patient_users(self, env, count):
        """Create multiple patient users with different scenarios"""
        domain = self.get_email_domain(env)
        created_count = 0
        
        patient_scenarios = [
            ('verified', 'Verified Patient', 'TestVerified123!', True, True, 'M', 'Active Treatment', 500000),
            ('pending', 'Pending Patient', 'TestPending123!', False, True, 'F', 'Awaiting Approval', 300000),
            ('inactive', 'Inactive Patient', 'TestInactive123!', True, False, 'M', 'Completed Treatment', 150000),
        ]
        
        for i, (role, name, password, is_verified, is_active, gender, treatment, funding) in enumerate(patient_scenarios[:count]):
            email = f'{role}.patient@{domain}'
            
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {role} patient already exists: {email}')
                )
                continue
            
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        user_type='PATIENT',
                        first_name='Test',
                        last_name=name,
                        phone_number=f'+255123456{i}00',
                        date_of_birth='1990-01-01',
                        is_active=is_active,
                        is_verified=is_verified,
                        is_patient_verified=is_verified
                    )
                    
                    # Create patient profile if patient app exists
                    try:
                        from patient.models import PatientProfile
                        PatientProfile.objects.create(
                            user=user,
                            full_name=f'Test {name}',
                            gender=gender,
                            country_fk_id=1,  # Assuming Tanzania exists
                            diagnosis='Test Diagnosis',
                            treatment_needed=treatment,
                            funding_required=funding,
                            funding_currency='TZS',
                            status='PUBLISHED' if is_verified else 'AWAITING_FUNDING'
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f'🏥 Created Patient Profile for: {email}')
                        )
                    except ImportError:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ Patient app not found - created user only')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ Could not create patient profile: {e}')
                        )
                    
                    created_count += 1
                    status = "✅ Active" if is_active else "❌ Inactive"
                    verified = "✅ Verified" if is_verified else "❌ Not Verified"
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'👤 Created {name}: {email} | Password: {password}')
                    )
                    self.stdout.write(f'   Status: {status} | {verified} | Funding: TZS {funding:,}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create {role} patient: {e}')
                )
        
        return created_count
