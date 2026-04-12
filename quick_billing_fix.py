#!/usr/bin/env python3
"""
Quick fix script for billing calculation errors
Usage: python quick_billing_fix.py --dry-run  # Check what needs fixing
       python quick_billing_fix.py --fix      # Apply the fixes
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

def main():
    import argparse
    from django.db import transaction, connection
    
    parser = argparse.ArgumentParser(description='Fix billing calculation errors')
    parser.add_argument('--dry-run', action='store_true', help='Show what needs fixing')
    parser.add_argument('--fix', action='store_true', help='Apply the fixes')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.fix:
        print("Please specify --dry-run or --fix")
        return
    
    print("🔍 Checking for billing calculation errors...")
    
    # This is a template - you'll need to adapt the table and column names
    # to match your actual billing database schema
    
    with connection.cursor() as cursor:
        # STEP 1: Find incorrect records (DRY RUN)
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
        
        incorrect_records = cursor.fetchall()
        
        if not incorrect_records:
            print("✅ No incorrect billing records found!")
            return
        
        print(f"\n📊 Found {len(incorrect_records)} incorrect billing records:")
        print("-" * 80)
        
        total_overcharged = Decimal('0.00')
        for record in incorrect_records:
            bill_id, monthly_rate, months, current_total, correct_total, overcharge = record
            total_overcharged += overcharge
            print(f"Bill #{bill_id}: TZS {monthly_rate:,} × {months} months = TZS {correct_total:,} (was TZS {current_total:,})")
        
        print(f"\n💰 Total overcharged: TZS {total_overcharged:,}")
        
        if args.dry_run:
            print("\n🔍 DRY RUN COMPLETE - No changes made")
            print("Run with --fix to apply these corrections")
            return
        
        if args.fix:
            print("\n🔧 APPLYING FIXES...")
            with transaction.atomic():
                cursor.execute("""
                    UPDATE billing_bills 
                    SET total_amount = monthly_rate * number_of_months
                    WHERE total_amount = (monthly_rate * number_of_months * 7)
                      AND monthly_rate IS NOT NULL 
                      AND number_of_months IS NOT NULL
                """)
                
                affected_rows = cursor.rowcount
                print(f"✅ Successfully fixed {affected_rows} billing records!")
                print(f"💰 Total amount corrected: TZS {total_overcharged:,}")

if __name__ == '__main__':
    main()
