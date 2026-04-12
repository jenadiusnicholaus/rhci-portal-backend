from django.core.management.base import BaseCommand
from django.db import transaction, connection
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix bills that were incorrectly marked as PAID during tenancy creation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Fix all incorrectly marked bills',
        )
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Fix bills for specific tenant only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_all = options['fix_all']
        tenant_id = options.get('tenant_id')

        if not fix_all and not dry_run:
            self.stdout.write(
                self.style.ERROR('Please specify either --dry-run or --fix-all')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('🔍 Checking for bills incorrectly marked as PAID...')
        )

        suspicious_bills = self.find_suspicious_bills(tenant_id)
        
        if not suspicious_bills:
            self.stdout.write(
                self.style.SUCCESS('✅ No suspicious bills found!')
            )
            return

        self.display_suspicious_bills(suspicious_bills)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n🔍 DRY RUN COMPLETE - No changes made')
            )
            self.stdout.write(
                'Run with --fix-all to mark these bills as UNPAID'
            )
        else:
            self.fix_bills(suspicious_bills, tenant_id)

    def find_suspicious_bills(self, tenant_id=None):
        """Find bills that were likely auto-marked as paid"""
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

    def display_suspicious_bills(self, bills):
        """Display the suspicious bills found"""
        total_amount = 0
        
        self.stdout.write(
            self.style.WARNING(f'\n📊 Found {len(bills)} bills that were auto-marked as PAID:')
        )
        self.stdout.write('-' * 100)
        
        for bill in bills:
            total_amount += float(bill['amount'])
            
            self.stdout.write(
                f"Bill #{bill['id']} (Tenant {bill['tenant_id']}): {bill['bill_number']}\n"
                f"  Amount: TZS {bill['amount']:,}\n"
                f"  Created: {bill['created_at']}\n"
                f"  Auto-Marked Paid: {bill['paid_at']}\n"
                f"  Type: {bill['payment_type']}\n"
            )
        
        self.stdout.write(
            self.style.ERROR(f'\n💰 Total amount incorrectly marked as paid: TZS {total_amount:,}')
        )

    def fix_bills(self, bills, tenant_id=None):
        """Fix the suspicious bills by marking them as UNPAID"""
        self.stdout.write(
            self.style.WARNING('\n🔧 APPLYING FIXES...')
        )
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Update suspicious bills to UNPAID status
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
                
                # Calculate total amount corrected
                total_amount = sum(float(bill['amount']) for bill in bills)
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully updated {affected_rows} bills to UNPAID status!')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'💰 Total amount corrected: TZS {total_amount:,}')
                )
                
                # Create audit log (if you have an audit table)
                try:
                    cursor.execute("""
                        INSERT INTO billing_audit_log 
                        (action, description, affected_records, total_amount, created_at)
                        VALUES ('FIX_AUTO_PAID', 'Fixed bills auto-marked as paid during tenancy creation', %s, %s, NOW())
                    """, [affected_rows, total_amount])
                    self.stdout.write(
                        self.style.SUCCESS('📝 Audit log created')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Could not create audit log: {e}')
                    )
