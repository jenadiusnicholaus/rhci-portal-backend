from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix property management billing issues: calculation errors and auto-paid bills'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Available actions')
        
        # Billing calculation fix
        calc_parser = subparsers.add_parser('fix-calculations', help='Fix billing calculation errors (monthly_rate * months * 7)')
        calc_parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed')
        calc_parser.add_argument('--fix', action='store_true', help='Apply the fixes')
        
        # Auto-paid bills fix
        paid_parser = subparsers.add_parser('fix-auto-paid', help='Fix bills auto-marked as PAID during tenancy')
        paid_parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed')
        paid_parser.add_argument('--fix', action='store_true', help='Apply the fixes')
        paid_parser.add_argument('--tenant-id', type=int, help='Fix specific tenant only')
        
        # Summary of all issues
        summary_parser = subparsers.add_parser('summary', help='Show summary of all billing issues')

    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.stdout.write(self.style.ERROR('Please specify an action: fix-calculations, fix-auto-paid, or summary'))
            return
        
        if action == 'fix-calculations':
            self.handle_billing_calculations(options)
        elif action == 'fix-auto-paid':
            self.handle_auto_paid_bills(options)
        elif action == 'summary':
            self.show_summary()

    def handle_billing_calculations(self, options):
        """Handle billing calculation fixes"""
        dry_run = options.get('dry_run')
        fix = options.get('fix')
        
        if not dry_run and not fix:
            self.stdout.write(self.style.ERROR('Please specify --dry-run or --fix'))
            return
        
        self.stdout.write(self.style.SUCCESS('🔍 Checking for billing calculation errors...'))
        
        incorrect_records = self.find_calculation_errors()
        
        if not incorrect_records:
            self.stdout.write(self.style.SUCCESS('✅ No billing calculation errors found!'))
            return
        
        self.display_calculation_errors(incorrect_records)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN COMPLETE - No changes made'))
            self.stdout.write('Run with --fix to apply these corrections')
        else:
            self.fix_calculation_errors(incorrect_records)

    def handle_auto_paid_bills(self, options):
        """Handle auto-paid bills fixes"""
        dry_run = options.get('dry_run')
        fix = options.get('fix')
        tenant_id = options.get('tenant_id')
        
        if not dry_run and not fix:
            self.stdout.write(self.style.ERROR('Please specify --dry-run or --fix'))
            return
        
        self.stdout.write(self.style.SUCCESS('🔍 Checking for bills incorrectly marked as PAID...'))
        
        suspicious_bills = self.find_auto_paid_bills(tenant_id)
        
        if not suspicious_bills:
            self.stdout.write(self.style.SUCCESS('✅ No suspicious bills found!'))
            return
        
        self.display_auto_paid_bills(suspicious_bills)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN COMPLETE - No changes made'))
            self.stdout.write('Run with --fix to mark these bills as UNPAID')
        else:
            self.fix_auto_paid_bills(suspicious_bills, tenant_id)

    def find_calculation_errors(self):
        """Find billing records with calculation errors"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id,
                    monthly_rate,
                    number_of_months,
                    total_amount as current_total,
                    (monthly_rate * number_of_months) as correct_total,
                    (total_amount - (monthly_rate * number_of_months)) as overcharge_amount
                FROM billing_bills 
                WHERE total_amount = (monthly_rate * number_of_months * 7)
                   AND monthly_rate IS NOT NULL 
                   AND number_of_months IS NOT NULL
            """)
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def display_calculation_errors(self, records):
        """Display billing calculation errors"""
        total_overcharged = sum(record['overcharge_amount'] for record in records)
        
        self.stdout.write(self.style.WARNING(f'\n📊 Found {len(records)} billing calculation errors:'))
        self.stdout.write('-' * 80)
        
        for record in records:
            self.stdout.write(
                f"Bill #{record['id']}:\n"
                f"  Monthly Rate: TZS {record['monthly_rate']:,}\n"
                f"  Months: {record['number_of_months']}\n"
                f"  Current (Wrong) Total: TZS {record['current_total']:,}\n"
                f"  Correct Total: TZS {record['correct_total']:,}\n"
                f"  Overcharge: TZS {record['overcharge_amount']:,}\n"
            )
        
        self.stdout.write(self.style.ERROR(f'\n💰 Total Overcharged: TZS {total_overcharged:,}'))

    def fix_calculation_errors(self, records):
        """Fix billing calculation errors"""
        self.stdout.write(self.style.WARNING('\n🔧 FIXING CALCULATION ERRORS...'))
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE billing_bills 
                    SET total_amount = monthly_rate * number_of_months,
                        updated_at = NOW()
                    WHERE total_amount = (monthly_rate * number_of_months * 7)
                      AND monthly_rate IS NOT NULL 
                      AND number_of_months IS NOT NULL
                """)
                
                affected_rows = cursor.rowcount
                total_overcharged = sum(record['overcharge_amount'] for record in records)
                
                self.stdout.write(self.style.SUCCESS(f'✅ Fixed {affected_rows} billing calculations!'))
                self.stdout.write(self.style.SUCCESS(f'💰 Total corrected: TZS {total_overcharged:,}'))

    def find_auto_paid_bills(self, tenant_id=None):
        """Find bills that were auto-marked as paid"""
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    b.id,
                    b.tenant_id,
                    b.bill_number,
                    b.amount,
                    b.status,
                    b.created_at,
                    b.due_date,
                    b.paid_at,
                    t.created_at as tenancy_created_at,
                    CASE 
                        WHEN b.paid_at IS NOT NULL AND b.paid_at <= b.created_at + INTERVAL '1 minute'
                        THEN 'AUTO-MARKED PAID'
                        ELSE 'LEGITIMATELY PAID'
                    END as payment_type
                FROM bills b
                JOIN tenants t ON b.tenant_id = t.id
                WHERE b.status = 'PAID'
                AND (
                    b.paid_at <= b.created_at + INTERVAL '1 minute'
                    OR
                    (DATE(b.paid_at) = DATE(b.created_at) AND 
                     TIME(b.paid_at) = TIME(b.created_at))
                )
            """
            
            if tenant_id:
                query += " AND b.tenant_id = %s"
                cursor.execute(query, [tenant_id])
            else:
                cursor.execute(query)
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def display_auto_paid_bills(self, bills):
        """Display auto-paid bills"""
        total_amount = sum(float(bill['amount']) for bill in bills)
        
        self.stdout.write(self.style.WARNING(f'\n📊 Found {len(bills)} bills auto-marked as PAID:'))
        self.stdout.write('-' * 100)
        
        for bill in bills:
            self.stdout.write(
                f"Bill #{bill['id']} (Tenant {bill['tenant_id']}): {bill['bill_number']}\n"
                f"  Amount: TZS {bill['amount']:,}\n"
                f"  Created: {bill['created_at']}\n"
                f"  Auto-Marked Paid: {bill['paid_at']}\n"
                f"  Type: {bill['payment_type']}\n"
            )
        
        self.stdout.write(self.style.ERROR(f'\n💰 Total incorrectly marked as paid: TZS {total_amount:,}'))

    def fix_auto_paid_bills(self, bills, tenant_id=None):
        """Fix auto-paid bills"""
        self.stdout.write(self.style.WARNING('\n🔧 FIXING AUTO-PAID BILLS...'))
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                update_query = """
                    UPDATE bills 
                    SET status = 'UNPAID', 
                        paid_at = NULL,
                        updated_at = NOW()
                    WHERE id IN (
                        SELECT b.id
                        FROM bills b
                        JOIN tenants t ON b.tenant_id = t.id
                        WHERE b.status = 'PAID'
                        AND (
                            b.paid_at <= b.created_at + INTERVAL '1 minute'
                            OR
                            (DATE(b.paid_at) = DATE(b.created_at) AND 
                             TIME(b.paid_at) = TIME(b.created_at))
                        )
                """
                
                if tenant_id:
                    update_query += " AND b.tenant_id = %s"
                    cursor.execute(update_query, [tenant_id])
                else:
                    cursor.execute(update_query)
                
                affected_rows = cursor.rowcount
                total_amount = sum(float(bill['amount']) for bill in bills)
                
                self.stdout.write(self.style.SUCCESS(f'✅ Updated {affected_rows} bills to UNPAID!'))
                self.stdout.write(self.style.SUCCESS(f'💰 Total corrected: TZS {total_amount:,}'))

    def show_summary(self):
        """Show summary of all billing issues"""
        self.stdout.write(self.style.SUCCESS('📊 BILLING ISSUES SUMMARY'))
        self.stdout.write('=' * 50)
        
        # Calculation errors
        calc_errors = self.find_calculation_errors()
        self.stdout.write(f'\n🧮 Billing Calculation Errors: {len(calc_errors)}')
        if calc_errors:
            total_overcharged = sum(record['overcharge_amount'] for record in calc_errors)
            self.stdout.write(f'   💰 Total Overcharged: TZS {total_overcharged:,}')
        
        # Auto-paid bills
        auto_paid = self.find_auto_paid_bills()
        self.stdout.write(f'\n💳 Auto-Paid Bills: {len(auto_paid)}')
        if auto_paid:
            total_amount = sum(float(bill['amount']) for bill in auto_paid)
            self.stdout.write(f'   💰 Total Incorrectly Paid: TZS {total_amount:,}')
        
        # Overall summary
        total_issues = len(calc_errors) + len(auto_paid)
        if total_issues == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ No billing issues found!'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠️ Total Issues Found: {total_issues}'))
            self.stdout.write('\nTo fix issues, run:')
            self.stdout.write('  python manage.py fix_billing_issues fix-calculations --fix')
            self.stdout.write('  python manage.py fix_billing_issues fix-auto-paid --fix')
