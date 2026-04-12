#!/usr/bin/env python3
"""
Fix bills that were incorrectly marked as PAID during tenancy creation
This script will find and update bills that should be UNPAID status
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

def main():
    import argparse
    from django.db import transaction, connection
    
    parser = argparse.ArgumentParser(description='Fix bills incorrectly marked as paid')
    parser.add_argument('--dry-run', action='store_true', help='Show what needs fixing')
    parser.add_argument('--fix', action='store_true', help='Apply the fixes')
    parser.add_argument('--tenant-id', type=int, help='Fix bills for specific tenant only')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.fix:
        print("Please specify --dry-run or --fix")
        return
    
    print("🔍 Checking for bills incorrectly marked as PAID...")
    
    with connection.cursor() as cursor:
        # Find bills marked as PAID that were created during tenancy creation
        # without actual payment confirmation
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
                -- Bills paid within 1 minute of creation (likely auto-marked)
                b.paid_at <= b.created_at + INTERVAL '1 minute'
                OR
                -- Bills with paid_at same as created_at (definitely auto-marked)
                DATE(b.paid_at) = DATE(b.created_at) AND 
                TIME(b.paid_at) = TIME(b.created_at)
            )
        """
        
        if args.tenant_id:
            query += " AND b.tenant_id = %s"
            cursor.execute(query, [args.tenant_id])
        else:
            cursor.execute(query)
        
        suspicious_bills = cursor.fetchall()
        
        if not suspicious_bills:
            print("✅ No suspicious bills found!")
            return
        
        print(f"\n📊 Found {len(suspicious_bills)} bills that were auto-marked as PAID:")
        print("-" * 100)
        
        total_amount = 0
        for bill in suspicious_bills:
            (bill_id, tenant_id, bill_number, amount, status, created_at, 
             due_date, paid_at, tenancy_created_at, payment_type) = bill
            total_amount += float(amount)
            
            print(f"Bill #{bill_id} (Tenant {tenant_id}): {bill_number}")
            print(f"  Amount: TZS {amount:,}")
            print(f"  Created: {created_at}")
            print(f"  Auto-Marked Paid: {paid_at}")
            print(f"  Type: {payment_type}")
            print()
        
        print(f"💰 Total amount incorrectly marked as paid: TZS {total_amount:,}")
        
        if args.dry_run:
            print("\n🔍 DRY RUN COMPLETE - No changes made")
            print("Run with --fix to mark these bills as UNPAID")
            return
        
        if args.fix:
            print("\n🔧 APPLYING FIXES...")
            with transaction.atomic():
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
                
                if args.tenant_id:
                    update_query += " AND b.tenant_id = %s"
                    cursor.execute(update_query, [args.tenant_id])
                else:
                    cursor.execute(update_query)
                
                affected_rows = cursor.rowcount
                print(f"✅ Successfully updated {affected_rows} bills to UNPAID status!")
                print(f"💰 Total amount corrected: TZS {total_amount:,}")
                
                # Create audit log of changes
                cursor.execute("""
                    INSERT INTO billing_audit_log 
                    (action, description, affected_records, total_amount, created_at)
                    VALUES ('FIX_AUTO_PAID', 'Fixed bills auto-marked as paid during tenancy creation', %s, %s, NOW())
                """, [affected_rows, total_amount])

if __name__ == '__main__':
    main()
